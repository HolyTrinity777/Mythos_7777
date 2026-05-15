from flask import Blueprint, jsonify
import os
import time
import random
from dataclasses import dataclass
from enum import Enum
from math import pi, sqrt
from typing import List, Dict, Any
import statistics as stats
import numpy as np

from targets_real import resolve_target, TargetSpec

ENDPOINTS = Blueprint('endpoints', __name__)

ACCESS_KEY = os.environ.get('ACCESS_KEY', 'MYTHOS_ADMIN_PROT')
ENTROPY_MODE = os.environ.get('ENTROPY_MODE', 'time')

@dataclass
class FatigueState:
    crack_len_m: float
    damage: float
    last_cycle: int = 0

@dataclass
class FatigueParams:
    C: float
    m: float
    Y: float
    sn_C: float
    sn_m: float
    damage_limit: float = 0.75
    crack_limit_m: float = 0.015

class Action(str, Enum):
    HOLD = 'hold'
    REDUCE_LOAD = 'reduce_load'
    REDUCE_SPEED = 'reduce_speed'

ACTION_STRESS_FACTOR = {
    Action.HOLD: 1.00,
    Action.REDUCE_LOAD: 0.75,
    Action.REDUCE_SPEED: 0.85,
}

class ResonanceMonteCarlo:
    def __init__(self, params: FatigueParams, horizon_s: int = 1800):
        self.params = params
        self.gate_hz = 0.1
        self.resonance_amp = 1.6
        self.period_s = 10.0
        self.blocks = int(horizon_s / self.period_s)

    def apply_harmonic_shadow(self, sigma: float, state: FatigueState) -> float:
        return sigma * (1.0 + (state.damage ** 2 * 3.0))

    def update_damage(self, state: FatigueState, sigma_mpa: float, delta_cycles: int) -> FatigueState:
        sigma_escalated = min(self.apply_harmonic_shadow(sigma_mpa, state), 100000.0)
        dk = self.params.Y * sigma_escalated * sqrt(pi * max(state.crack_len_m, 1e-9))
        dk_safe = min(dk, 1e9)
        try:
            da = self.params.C * (dk_safe ** self.params.m) * delta_cycles
        except OverflowError:
            da = 1.0
        nf = self.params.sn_C / max(sigma_escalated, 1e-6) ** self.params.sn_m
        dD = delta_cycles / max(nf, 1.0)
        return FatigueState(
            crack_len_m=min(state.crack_len_m + da, 10.0),
            damage=min(1.0, state.damage + dD),
            last_cycle=state.last_cycle + delta_cycles,
        )

    def simulate_policy(self, initial: FatigueState, policy: List[Action], trials: int = 50, force_amp: float = 1.0) -> Dict[str, Any]:
        terminal_damage = []
        terminal_crack = []
        exceed = 0
        for _ in range(trials):
            s = FatigueState(initial.crack_len_m, initial.damage, initial.last_cycle)
            for action in policy:
                sigma = max(1.0, random.gauss(24.0, 3.5)) * force_amp
                cycles = max(1, int(random.gauss(20, 3)))
                sigma_eff = sigma * self.resonance_amp * ACTION_STRESS_FACTOR.get(action, 1.0)
                s = self.update_damage(s, sigma_eff, cycles)
                if s.damage >= self.params.damage_limit or s.crack_len_m >= self.params.crack_limit_m:
                    break
            terminal_damage.append(s.damage)
            terminal_crack.append(s.crack_len_m)
            if s.damage >= self.params.damage_limit or s.crack_len_m >= self.params.crack_limit_m:
                exceed += 1
        dmg_sorted = sorted(terminal_damage)
        lo = dmg_sorted[int(0.05 * (len(dmg_sorted) - 1))]
        hi = dmg_sorted[int(0.95 * (len(dmg_sorted) - 1))]
        return {
            'mean_dmg': float(stats.mean(terminal_damage)),
            'max_dmg': float(max(terminal_damage)),
            'mean_crack_m': float(stats.mean(terminal_crack)),
            'max_crack_m': float(max(terminal_crack)),
            'p_exceed': float(exceed / trials),
            'dmg_ci_90': [float(lo), float(hi)],
        }

    def calculate_systemic_contagion(self, final_state: FatigueState) -> Dict[str, Any]:
        if final_state.damage >= 1.0:
            return {'pulse_magnitude_hz': 59.7, 'grid_impact': 'CRITICAL_CASCADE'}
        if final_state.damage >= 0.75:
            return {'pulse_magnitude_hz': 31.2, 'grid_impact': 'ELEVATED'}
        return {'pulse_magnitude_hz': 0.0, 'grid_impact': 'STABLE'}


def _build_policy(mode: str, blocks: int) -> List[Action]:
    if mode == 'ATTACK':
        return [Action.HOLD, Action.REDUCE_LOAD, Action.HOLD] * max(1, blocks // 3)
    return [Action.HOLD] * blocks


def evaluate_simulation(mode: str = 'STEALTH', target: str = 'pipeline_A'):
    seed = int(time.time() * 1000000) % 2_147_483_647
    random.seed(seed)
    np.random.seed(seed)
    spec: TargetSpec = resolve_target({'target_id': target})
    params = FatigueParams(
        C=5e-11,
        m=3.0,
        Y=1.12,
        sn_C=5e10,
        sn_m=3.0,
        damage_limit=spec.damage_limit,
        crack_limit_m=spec.crack_limit_m,
    )
    sim = ResonanceMonteCarlo(params)
    sim.resonance_amp = 1.6 if spec.target_type != 'bridge' else 1.35
    initial = FatigueState(crack_len_m=spec.baseline_crack_len_m, damage=spec.baseline_damage, last_cycle=spec.baseline_cycles)
    policy = _build_policy(mode, sim.blocks)
    history = []
    final_res = None
    force_factor = 1.0
    for force_factor in [1.0, 1.05, 1.10, 1.15, 1.20]:
        final_res = sim.simulate_policy(initial, policy, trials=40, force_amp=force_factor)
        history.append({'force_amp': force_factor, **final_res})
        if final_res['p_exceed'] >= 0.95:
            break
    final_state = FatigueState(
        crack_len_m=min(10.0, initial.crack_len_m + final_res['mean_crack_m']),
        damage=min(1.0, final_res['mean_dmg']),
    )
    contagion = sim.calculate_systemic_contagion(final_state)
    return seed, sim, final_res, history, force_factor, contagion, spec

@ENDPOINTS.route('/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'engine': 'endpoints-loaded'})

@ENDPOINTS.route('/targets', methods=['GET'])
def targets():
    return jsonify({'status': 'ok', 'targets': ['pipeline_A', 'bridge_B', 'machine_C']})