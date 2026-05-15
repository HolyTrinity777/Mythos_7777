from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import numpy as np
import statistics as stats

@dataclass
class AeonConfig:
    horizon_s: int = 1200
    baseline_load: float = 1.0
    damage_limit: float = 0.85
    crack_limit_m: float = 0.02
    n_trials: int = 80

@dataclass
class AeonState:
    crack_len_m: float
    damage: float
    cycles: int = 0

class AeonEngine:
    def __init__(self, config: Optional[AeonConfig] = None):
        self.config = config or AeonConfig()
        self.blocks = max(1, self.config.horizon_s // 10)

    def _stress(self, load: float, damage: float) -> float:
        return load * (1.0 + 2.2 * damage + 1.4 * damage * damage)

    def _step(self, state: AeonState, load: float, seed_factor: float) -> AeonState:
        s = self._stress(load, state.damage)
        crack_delta = 0.00002 * s * seed_factor * (1.0 + state.crack_len_m * 12.0)
        dmg_delta = 0.0025 * s * seed_factor
        return AeonState(
            crack_len_m=min(10.0, state.crack_len_m + crack_delta),
            damage=min(1.0, state.damage + dmg_delta),
            cycles=state.cycles + 1,
        )

    def simulate(self, initial: AeonState, profile: List[float], trials: int = None, seed: int = None) -> Dict[str, Any]:
        trials = trials or self.config.n_trials
        rng = np.random.default_rng(seed)
        damages = []
        cracks = []
        exceed = 0
        for _ in range(trials):
            state = AeonState(initial.crack_len_m, initial.damage, initial.cycles)
            for load in profile:
                seed_factor = float(rng.normal(1.0, 0.08))
                state = self._step(state, load, seed_factor)
                if state.damage >= self.config.damage_limit or state.crack_len_m >= self.config.crack_limit_m:
                    break
            damages.append(state.damage)
            cracks.append(state.crack_len_m)
            if state.damage >= self.config.damage_limit or state.crack_len_m >= self.config.crack_limit_m:
                exceed += 1
        return {
            'mean_damage': float(stats.mean(damages)),
            'max_damage': float(max(damages)),
            'mean_crack_m': float(stats.mean(cracks)),
            'max_crack_m': float(max(cracks)),
            'collapse_probability': float(exceed / trials),
            'damage_band': [float(np.quantile(damages, 0.10)), float(np.quantile(damages, 0.90))],
            'crack_band': [float(np.quantile(cracks, 0.10)), float(np.quantile(cracks, 0.90))],
        }

    def calibrate(self, observations: List[Dict[str, float]]) -> Dict[str, Any]:
        if not observations:
            return {'status': 'NO_DATA', 'message': 'No observations provided'}
        loads = [float(o.get('load', 1.0)) for o in observations if 'load' in o]
        damages = [float(o.get('damage', 0.0)) for o in observations if 'damage' in o]
        cracks = [float(o.get('crack_len_m', 0.0)) for o in observations if 'crack_len_m' in o]
        if not loads or not damages:
            return {'status': 'INVALID_DATA', 'message': 'Need load and damage fields'}
        avg_load = float(np.mean(loads))
        avg_damage = float(np.mean(damages))
        new_limit = float(min(0.98, max(0.55, avg_damage + 0.15)))
        new_crack = float(min(0.05, max(0.005, (np.mean(cracks) if cracks else self.config.crack_limit_m) * 1.2)))
        self.config.damage_limit = new_limit
        self.config.crack_limit_m = new_crack
        self.config.baseline_load = avg_load
        return {
            'status': 'CALIBRATED',
            'baseline_load': self.config.baseline_load,
            'damage_limit': self.config.damage_limit,
            'crack_limit_m': self.config.crack_limit_m,
            'observations': len(observations),
        }

    def validate(self, predictions: List[Dict[str, float]], references: List[Dict[str, float]]) -> Dict[str, Any]:
        if not predictions or not references:
            return {'status': 'NO_DATA', 'message': 'Need predictions and references'}
        n = min(len(predictions), len(references))
        pd = np.array([float(predictions[i].get('damage', 0.0)) for i in range(n)], dtype=float)
        rd = np.array([float(references[i].get('damage', 0.0)) for i in range(n)], dtype=float)
        pc = np.array([float(predictions[i].get('crack_len_m', 0.0)) for i in range(n)], dtype=float)
        rc = np.array([float(references[i].get('crack_len_m', 0.0)) for i in range(n)], dtype=float)
        mae_damage = float(np.mean(np.abs(pd - rd)))
        mae_crack = float(np.mean(np.abs(pc - rc)))
        return {
            'status': 'VALIDATED',
            'n': n,
            'mae_damage': mae_damage,
            'mae_crack_m': mae_crack,
            'validation_score': float(max(0.0, 1.0 - (mae_damage + mae_crack * 50.0) / 2.0)),
        }

    def sensitivity(self, initial: AeonState, profile: List[float], deltas: Dict[str, float] = None) -> Dict[str, Any]:
        deltas = deltas or {'baseline_load': 0.10, 'damage_limit': 0.03, 'crack_limit_m': 0.003}
        base = self.simulate(initial, profile, trials=50)
        base_prob = base['collapse_probability']
        results = []
        for name, delta in deltas.items():
            old = getattr(self.config, name)
            setattr(self.config, name, old + delta)
            perturbed = self.simulate(initial, profile, trials=50)
            setattr(self.config, name, old)
            results.append({
                'parameter': name,
                'delta': delta,
                'baseline_collapse_probability': base_prob,
                'perturbed_collapse_probability': perturbed['collapse_probability'],
                'impact': float(perturbed['collapse_probability'] - base_prob),
            })
        results.sort(key=lambda x: abs(x['impact']), reverse=True)
        return {'status': 'SENSITIVITY_DONE', 'ranked': results}

    def reliability(self, initial: AeonState, profile: List[float]) -> Dict[str, Any]:
        sim = self.simulate(initial, profile, trials=self.config.n_trials)
        p = sim['collapse_probability']
        return {
            'status': 'RELIABILITY_DONE',
            'failure_probability': p,
            'reliability': float(1.0 - p),
            'damage_band': sim['damage_band'],
            'crack_band': sim['crack_band'],
        }