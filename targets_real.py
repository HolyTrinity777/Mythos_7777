from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

@dataclass
class TargetSpec:
    target_id: str
    target_type: str
    asset_name: str
    material: str
    location: Optional[str] = None
    baseline_crack_len_m: float = 0.0012
    baseline_damage: float = 0.08
    baseline_cycles: int = 0
    baseline_load: float = 24.0
    damage_limit: float = 0.85
    crack_limit_m: float = 0.015
    temperature_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    notes: Optional[str] = None

    def to_state(self) -> Dict[str, Any]:
        return {
            'crack_len_m': self.baseline_crack_len_m,
            'damage': self.baseline_damage,
            'cycles': self.baseline_cycles,
        }

    def to_config(self) -> Dict[str, Any]:
        return {
            'baseline_load': self.baseline_load,
            'damage_limit': self.damage_limit,
            'crack_limit_m': self.crack_limit_m,
        }

    def to_observation(self) -> Dict[str, Any]:
        return {
            'load': self.baseline_load,
            'damage': self.baseline_damage,
            'crack_len_m': self.baseline_crack_len_m,
            'temperature_c': self.temperature_c,
            'humidity_pct': self.humidity_pct,
            'source': self.asset_name,
        }

TARGET_LIBRARY: Dict[str, TargetSpec] = {
    'pipeline_A': TargetSpec(
        target_id='pipeline_A',
        target_type='pipeline',
        asset_name='Pipeline Section A',
        material='steel',
        location='industrial_site_1',
        baseline_crack_len_m=0.0012,
        baseline_damage=0.08,
        baseline_cycles=0,
        baseline_load=24.0,
        damage_limit=0.82,
        crack_limit_m=0.014,
        temperature_c=32.0,
        humidity_pct=58.0,
        notes='Reference pipeline asset for calibration and simulation.',
    ),
    'bridge_B': TargetSpec(
        target_id='bridge_B',
        target_type='bridge',
        asset_name='Bridge Span B',
        material='reinforced_concrete',
        location='urban_corridor',
        baseline_crack_len_m=0.0008,
        baseline_damage=0.05,
        baseline_cycles=0,
        baseline_load=18.5,
        damage_limit=0.75,
        crack_limit_m=0.010,
        temperature_c=29.0,
        humidity_pct=64.0,
        notes='Lower baseline load, slower damage growth.',
    ),
    'machine_C': TargetSpec(
        target_id='machine_C',
        target_type='rotating_machine',
        asset_name='Machine C Rotor',
        material='alloy_steel',
        location='plant_floor_2',
        baseline_crack_len_m=0.0010,
        baseline_damage=0.10,
        baseline_cycles=1200,
        baseline_load=26.0,
        damage_limit=0.88,
        crack_limit_m=0.016,
        temperature_c=41.0,
        humidity_pct=44.0,
        notes='Higher cycle count, moderate load variability.',
    ),
}

def list_targets() -> List[Dict[str, Any]]:
    return [asdict(v) for v in TARGET_LIBRARY.values()]

def get_target(target_id: str) -> Optional[TargetSpec]:
    return TARGET_LIBRARY.get(target_id)

def resolve_target(payload: Dict[str, Any]) -> TargetSpec:
    target_id = str(payload.get('target_id') or payload.get('target') or 'pipeline_A')
    base = TARGET_LIBRARY.get(target_id)
    if base is None:
        return TargetSpec(
            target_id=target_id,
            target_type=str(payload.get('target_type') or 'generic'),
            asset_name=str(payload.get('asset_name') or target_id),
            material=str(payload.get('material') or 'unknown'),
            location=payload.get('location'),
            baseline_crack_len_m=float(payload.get('baseline_crack_len_m', 0.0012)),
            baseline_damage=float(payload.get('baseline_damage', 0.08)),
            baseline_cycles=int(payload.get('baseline_cycles', 0)),
            baseline_load=float(payload.get('baseline_load', 24.0)),
            damage_limit=float(payload.get('damage_limit', 0.85)),
            crack_limit_m=float(payload.get('crack_limit_m', 0.015)),
            temperature_c=payload.get('temperature_c'),
            humidity_pct=payload.get('humidity_pct'),
            notes=payload.get('notes'),
        )
    data = asdict(base)
    overrides = {k: v for k, v in payload.items() if k in data and v is not None}
    data.update(overrides)
    return TargetSpec(**data)