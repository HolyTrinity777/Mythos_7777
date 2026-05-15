

```md
# Mythos-Zero

Mythos-Zero is a **target-driven structural simulation API** for modeling resonance, fatigue, damage accumulation, calibration, and validation over named asset targets such as `pipeline_A`, `bridge_B`, and `machine_C`.

It is built as a Flask service with a Monte Carlo fatigue engine and a real target registry. The system is designed to run on lightweight cloud infrastructure such as Render while still exposing a clear, data-driven simulation workflow.

## What this project is

Mythos-Zero is an HTTP API that provides:

- Target-aware simulation.
- Calibration from observations.
- Validation against references.
- Reliability estimation.
- Sensitivity analysis.
- Deployment-friendly JSON responses.

## Core architecture

The codebase is split into a few layers:

- `app.py` — Flask app and route layer.
- `endpoints.py` — higher-level simulation routes such as `/void/dissolution` and `/pulse`.
- `targets_real.py` — target registry and target metadata.
- `aeon_engine.py` — fatigue, calibration, validation, sensitivity, and reliability logic.

## How it works

- A target is selected by `target_id`.
- The target provides baseline state and limits.
- A load profile is supplied through the API.
- The engine simulates damage and crack growth over repeated trials.
- The API returns summarized results in JSON.

## API endpoints

### `GET /health`
Returns service status and version.

### `GET /targets`
Lists available built-in targets.

### `GET /void/autonomy`
Returns sovereign access state and a ledger preview.
Requires `X-Sovereign-Key`.

### `POST /void/dissolution`
Runs a target-based simulation using the selected asset profile.
Requires `X-Sovereign-Key`.

### `POST /pulse`
Runs the same simulation path with a scenario flag for `STEALTH` or `ATTACK`.
Requires `X-Sovereign-Key`.

### `POST /calibrate`
Fits model values from observations.
Requires `X-Sovereign-Key`.

### `POST /validate`
Compares predictions and references.
Requires `X-Sovereign-Key`.

### `POST /sensitivity`
Measures how parameters affect collapse probability.
Requires `X-Sovereign-Key`.

### `POST /reliability`
Returns failure probability and reliability from the simulation output.
Requires `X-Sovereign-Key`.

### `POST /simulate`
Runs the core Monte Carlo simulation.
Requires `X-Sovereign-Key`.

## Target model

Built-in targets currently include:

- `pipeline_A` — pipeline section.
- `bridge_B` — bridge span.
- `machine_C` — rotating machine rotor.

Each target contains:

- Baseline crack length.
- Baseline damage.
- Load baseline.
- Damage limit.
- Crack limit.
- Material and location metadata.

## Example response shape

```json
{
  "status": "SIMULATION_COMPLETE",
  "target": "pipeline_A",
  "blueprint": {
    "force_factor": 1.2,
    "mean_damage": 0.0877,
    "max_damage": 0.0885,
    "mean_crack_m": 0.001206,
    "max_crack_m": 0.001207,
    "collapse_probability": 0.0
  }
}
```

## Calibration

Calibration expects real observation data.

Example payload:

```json
{
  "observations": [
    {
      "load": 1.0,
      "damage": 0.78,
      "crack_len_m": 0.0067,
      "temperature_c": 32.0,
      "humidity_pct": 58.0,
      "source": "pipeline_A"
    }
  ],
  "config": {
    "horizon_s": 1200,
    "baseline_load": 1.0,
    "damage_limit": 0.88,
    "crack_limit_m": 0.016,
    "n_trials": 80
  }
}
```

## Validation

Validation expects paired predictions and references.

Example payload:

```json
{
  "predictions": [
    {"damage": 0.79, "crack_len_m": 0.0067}
  ],
  "references": [
    {"damage": 0.785, "crack_len_m": 0.00672}
  ]
}
```

## Sensitivity

Sensitivity expects a top-level `state` and `profile`.

Example payload:

```json
{
  "state": {
    "crack_len_m": 0.005,
    "damage": 0.45,
    "cycles": 1200
  },
  "profile": [1.3, 1.35, 1.4, 1.45, 1.5, 1.55, 1.6],
  "config": {
    "baseline_load": 1.0,
    "crack_limit_m": 0.016,
    "damage_limit": 0.88,
    "horizon_s": 1200,
    "n_trials": 80
  }
}
```

## Deployment

The service is designed to run on Render or any similar Flask host.

Typical setup:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT --log-level debug --access-logfile - --error-logfile -`
- Environment variables: `ACCESS_KEY`, `PORT`, `PYTHONUNBUFFERED`

## Security

The API uses a header-based access check:

- `X-Sovereign-Key`

The value must match `ACCESS_KEY` in the environment.

## What this project is not

This is not a general intelligence system or autonomous agent by itself. It is a structured simulation backend with a brand and naming layer built around the Mythos-Zero concept.

## License

MIT.

## Author

YOIHENBA SOUGAIJAM
date 15 may 2026
```