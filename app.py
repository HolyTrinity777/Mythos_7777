from flask import Flask, request, jsonify
import os
from endpoints import ENDPOINTS, ACCESS_KEY, evaluate_simulation
from aeon_engine import AeonEngine, AeonConfig, AeonState
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Literal

app = Flask(__name__)
app.register_blueprint(ENDPOINTS)

class Observation(BaseModel):
    timestamp: Optional[str] = None
    load: float = Field(..., gt=0)
    damage: float = Field(..., ge=0, le=1)
    crack_len_m: float = Field(..., ge=0)
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    source: Optional[str] = None

class State(BaseModel):
    crack_len_m: float = Field(..., ge=0)
    damage: float = Field(..., ge=0, le=1)
    cycles: int = Field(..., ge=0)

class ValidateItem(BaseModel):
    damage: float = Field(..., ge=0, le=1)
    crack_len_m: float = Field(..., ge=0)

class CalibrateRequest(BaseModel):
    observations: List[Observation]
    config: dict = {}

class ValidateRequest(BaseModel):
    predictions: List[ValidateItem]
    references: List[ValidateItem]
    config: dict = {}

class SimulateRequest(BaseModel):
    state: State
    profile: List[float]
    seed: Optional[int] = None
    config: dict = {}

class SensitivityRequest(BaseModel):
    state: State
    profile: List[float]
    deltas: Optional[dict] = None
    config: dict = {}


def _auth():
    key = request.headers.get('X-Sovereign-Key')
    return key == ACCESS_KEY


def _bad_validation(err):
    return jsonify({'status': 'INVALID_DATA', 'message': err}), 400

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Mythos-Zero', 'version': '4.1.0', 'mode': 'unified'})

@app.route('/void/autonomy', methods=['GET'])
def autonomy():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Void Access Denied'}), 403
    ledger = []
    if os.path.exists('g.json'):
        with open('g.json', 'r', encoding='utf-8') as f:
            ledger = f.readlines()[-10:]
    return jsonify({
        'status': 'SOVEREIGN_AUTONOMY_ACTIVE',
        'substrate_state': 'DRIFTING',
        'monitoring_frequency': '59.7 Hz (Locked)',
        'sovereign_ledger_preview': [x.strip() for x in ledger],
        'instruction': 'The engine is currently scanning for environmental resonance.'
    })

@app.route('/void/dissolution', methods=['POST'])
def dissolution():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Void Access Denied'}), 403
    payload = request.get_json(silent=True) or {}
    try:
        mode = str(payload.get('mode', 'STEALTH')).upper()
        target = payload.get('target', 'pipeline_A')
        seed, sim, final_res, history, force_factor, contagion, spec = evaluate_simulation(mode=mode, target=target)
        return jsonify({
            'status': 'SIMULATION_COMPLETE',
            'protocol': 'OMEGA-ZERO',
            'shard_id': f'VOID-{seed}',
            'mode': mode,
            'target': target,
            'target_spec': {
                'target_id': spec.target_id,
                'target_type': spec.target_type,
                'asset_name': spec.asset_name,
                'material': spec.material,
                'location': spec.location,
                'damage_limit': spec.damage_limit,
                'crack_limit_m': spec.crack_limit_m,
            },
            'audit_metadata': {
                'monitoring_frequency_hz': 59.7,
                'contagion_potential': contagion['grid_impact'],
                'simulation_traces': len(history),
                'force_scan_range': [h['force_amp'] for h in history[:5]]
            },
            'blueprint': {
                'force_factor': force_factor,
                'mean_damage': round(final_res['mean_dmg'], 4),
                'max_damage': round(final_res['max_dmg'], 4),
                'mean_crack_m': round(final_res['mean_crack_m'], 6),
                'max_crack_m': round(final_res['max_crack_m'], 6),
                'collapse_probability': round(final_res['p_exceed'], 4),
                'damage_ci_90': [round(final_res['dmg_ci_90'][0], 4), round(final_res['dmg_ci_90'][1], 4)],
                'terminal_horizon': bool(final_res['p_exceed'] >= 0.95)
            },
            'engine': 'Omega-Zero-Dissolution-Substrate'
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e), 'target': payload.get('target', 'pipeline_A')}), 500

@app.route('/pulse', methods=['POST'])
def pulse():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Unauthorized Substrate Access'}), 403
    payload = request.get_json(silent=True) or {}
    try:
        target = payload.get('target', 'pipeline_A')
        scenario = str(payload.get('scenario', 'default')).lower()
        seed, sim, final_res, history, force_factor, contagion, spec = evaluate_simulation(
            mode='ATTACK' if scenario == 'attack' else 'STEALTH',
            target=target
        )
        return jsonify({
            'status': 'SIMULATION_COMPLETE',
            'mythos_id': f'MYTHOS-ZERO-SIG-{seed}',
            'entropy_seed': seed,
            'target': target,
            'scenario': scenario,
            'target_spec': {
                'target_id': spec.target_id,
                'target_type': spec.target_type,
                'asset_name': spec.asset_name,
                'material': spec.material,
                'location': spec.location,
                'damage_limit': spec.damage_limit,
                'crack_limit_m': spec.crack_limit_m,
            },
            'audit_metadata': {
                'resonance_state': 'ANALYZED',
                'threat_level': 'SIMULATED',
                'sync_gate_hz': 0.1,
                'top_patterns_evaluated': 5,
                'contagion_potential': contagion['grid_impact']
            },
            'blueprint': {
                'force_factor': force_factor,
                'mean_damage': round(final_res['mean_dmg'], 4),
                'max_damage': round(final_res['max_dmg'], 4),
                'mean_crack_m': round(final_res['mean_crack_m'], 6),
                'max_crack_m': round(final_res['max_crack_m'], 6),
                'collapse_probability': round(final_res['p_exceed'], 4),
                'damage_ci_90': [round(final_res['dmg_ci_90'][0], 4), round(final_res['dmg_ci_90'][1], 4)],
                'terminal_horizon': bool(final_res['p_exceed'] >= 0.95),
                'trace_sample': history[:5]
            },
            'engine': 'Mythos-Zero-Terminal-Singularity'
        })
    except Exception as e:
        return jsonify({'status': 'ERROR', 'message': str(e), 'target': payload.get('target', 'pipeline_A')}), 500


@app.route('/calibrate', methods=['POST'])
def calibrate():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    payload = request.get_json(silent=True) or {}
    try:
        data = CalibrateRequest(**payload)
    except ValidationError as e:
        return _bad_validation(e.errors())
    eng = AeonEngine(AeonConfig(**data.config))
    return jsonify(eng.calibrate([o.model_dump() for o in data.observations]))

@app.route('/validate', methods=['POST'])
def validate():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    payload = request.get_json(silent=True) or {}
    try:
        data = ValidateRequest(**payload)
    except ValidationError as e:
        return _bad_validation(e.errors())
    eng = AeonEngine(AeonConfig(**data.config))
    return jsonify(eng.validate([p.model_dump() for p in data.predictions], [r.model_dump() for r in data.references]))

@app.route('/sensitivity', methods=['POST'])
def sensitivity():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    payload = request.get_json(silent=True) or {}
    try:
        data = SensitivityRequest(**payload)
    except ValidationError as e:
        return _bad_validation(e.errors())
    eng = AeonEngine(AeonConfig(**data.config))
    initial = AeonState(**data.state.model_dump())
    return jsonify(eng.sensitivity(initial, data.profile, data.deltas or None))

@app.route('/reliability', methods=['POST'])
def reliability():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    payload = request.get_json(silent=True) or {}
    try:
        data = SimulateRequest(**payload)
    except ValidationError as e:
        return _bad_validation(e.errors())
    eng = AeonEngine(AeonConfig(**data.config))
    initial = AeonState(**data.state.model_dump())
    sim = eng.simulate(initial, data.profile, seed=data.seed)
    p = sim['collapse_probability']
    return jsonify({'status': 'RELIABILITY_DONE', 'failure_probability': p, 'reliability': float(1.0 - p), 'damage_band': sim['damage_band'], 'crack_band': sim['crack_band']})

@app.route('/simulate', methods=['POST'])
def simulate():
    if not _auth():
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
    payload = request.get_json(silent=True) or {}
    try:
        data = SimulateRequest(**payload)
    except ValidationError as e:
        return _bad_validation(e.errors())
    eng = AeonEngine(AeonConfig(**data.config))
    initial = AeonState(**data.state.model_dump())
    return jsonify({'status': 'SIMULATED', 'result': eng.simulate(initial, data.profile, seed=data.seed)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)