# Serie I · Substrate Scanning Engine
## 16 Domains, 1 Architecture, 29 Core Features, 13 Engines, 5 Pipelines

Ricardo Hernández Reveles — ORCID: 0009-0003-2000-0737 · March 2026

---

### Quick Start

```bash
# Install
pip install -r requirements.txt   # numpy, scipy, mpmath

# Verify (runs all 17 engines + 3 assertions)
bash verify.sh

# Run individual pipelines
python pipelines/geometric_engine.py      # 31-feature geometric atlas
python pipelines/cf_features.py           # CF-integer features (10 per-eigenvalue)
python pipelines/zero_locator.py          # STA zero localization

# Run individual application engines
python applications/sparam_engine.py      # S-parameter analysis
python applications/motor_diagnosis.py    # Vibration fault diagnosis
# ... (all 12 engines are standalone)
```

### Requirements

- Python 3.10, 3.11, or 3.12
- numpy ≥ 1.24
- scipy ≥ 1.10
- mpmath ≥ 1.3

---

### The Fundamental Equation

    p⁻ˢ = p⁻σ · e⁻ⁱ ˡⁿ⁽ᵖ⁾ · ᵗ

This is a fact, not a choice. p⁻σ is the amplitude. e⁻ⁱωᵗ is the phase.
The zeros are the values of t where all phases conspire.
f(b) organises the amplitude. cos(ω) organises the phase.
Canal A is orthogonal to both.

### The Decomposition

    θ*(k, γ) = f(b) · [A + B·cos(ln(p)·γ) + C·sin(ln(p)·γ)]

Shared algebra does not imply shared information.

---

### On Democratisation

The engine lowers the barrier of access: anyone with Python and
a browser can explore ζ, diagnose a turbine, or screen a material.

What it does not lower is the barrier of judgement.

**Democratising scepticism is worth more than democratising computation.**

---

### Engines (all verified, all standalone)

| # | Domain | Engine | Throughput | Features |
|---|--------|--------|-----------|----------|
| 1 | ζ(s), L(s,χ), L(s,E) | geometric_engine.py | 125/s | 31 (29+2) |
| 2 | S-parameters | sparam_engine.py | 1,709/s | 29 |
| 3 | Motor diagnosis | motor_diagnosis.py | 1,132/s | 29 |
| 4 | General graphs | graph_engine.py | 833/s | 29 |
| 5 | AST / code analysis | ast_engine.py | 139/s | 44 (29+15) |
| 6 | Physical cavities | cavity_engine.py | 20/s | 29 |
| 7 | Phonon / materials | phonon_engine.py | 478/s | 29 |
| 8 | Colorimetry | colorimetry_engine.py | 1,677/s | 29 |
| 9 | 3D wavelet subbands | wavelet_3d_engine.py | 50/s | 29 |
| 10 | Turbulence cascades | turbulence_engine.py | 476/s | 29 |
| 11 | Image spectral / forensics | image_spectral_engine.py | 816/s | 29 |
| 12 | Spectral pathfinding | pathfinding_engine.py | 22/s | 29 |
| 13 | Elliptic curve crypto audit | crypto_curve_engine.py | 274/s | 29 |

Constraint: linear operator + discrete spectrum.

### Pipelines

| # | Pipeline | Purpose | Input | Output |
|---|----------|---------|-------|--------|
| 1 | geometric_engine.py | 31-feature geometric atlas | (σ, t, K) + EulerProduct | 31-dim vector |
| 2 | envelope_pipeline.py | Envelope decomposition v1 | geometric_engine output | θ*(k,γ) weights |
| 3 | envelope_v2.py | Envelope decomposition v2 | geometric_engine output | Weil + NN comparison |
| 4 | cf_features.py | CF-integer features | γ_n at D digits | 10 per-eigenvalue + 4 cross |
| 5 | zero_locator.py | STA zero localization (Riemann only) | [t_min, t_max] | list of Zero tuples |

Pipelines 4–5 are new in v3.0.0. They are parallel to the geometric engine
(which remains at 31 features). zero_locator.scan() works for RiemannZeta only;
for other L-functions, use from_values() with externally computed zeros.

### Zenodo Deposit

This repository corresponds to Zenodo record **10.5281/zenodo.19378670**.
Cite as: Hernández Reveles, R. (2026). *Substrate Scanning Engine* (v3.1.1). Zenodo. https://zenodo.org/records/19378670

### License

Code: AGPL-3.0-or-later | Papers: CC-BY-4.0
Dependencies: numpy (BSD-3-Clause), scipy (BSD-3-Clause), mpmath (BSD-3-Clause), Three.js (MIT)

### Attribution

This work was developed with computational assistance from Claude (Anthropic).
All results were independently verified by the author.
All errors are the author's responsibility.

*The spectrum is the spectrum.*
