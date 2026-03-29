# Contributing to Substrate Scanning Engine

## How to Add a New Domain

The engine architecture is designed for extension. Any system with a linear operator
and discrete spectrum can be scanned. To add a new domain:

### 1. Identify the Spectrum

Your system needs eigenvalues {λ_k}. These can come from:
- A differential operator (Laplacian, Hamiltonian, transfer matrix)
- A graph adjacency or Laplacian matrix
- A Fourier transform (spatial frequencies as spectrum)
- Any linear map with computable discrete spectrum

### 2. Create the Engine File

Use `applications/sparam_engine.py` as the reference template. Your engine must:

1. Be a standalone `.py` file in `applications/`
2. Depend only on `numpy` and `scipy` (no pip install beyond these)
3. Extract exactly 29 features from the spectrum (you may add domain-specific extras)
4. Include a `FEATURE_NAMES` list matching feature vector indices
5. Include a synthetic data generator (the engine demos itself, no external data needed)
6. Include a rule-based classifier demonstrating the features discriminate
7. Print a cross-domain mapping to ζ(s) at the end of execution
8. Measure and report throughput
9. Carry the copyright header:
   ```
   Copyright (c) 2026 Ricardo Hernández Reveles
   SPDX-License-Identifier: AGPL-3.0-or-later
   ```

### 3. The 29 Core Features

These are computed by `geometric_engine.py` and must be replicated (or mapped) in
every domain engine. See `pipelines/doc/README_geometric_engine.md` for the complete
list with definitions.

### 4. Document Magic Numbers

Create `applications/doc/README_your_engine.md` documenting every numerical constant
in your engine: its origin, meaning, and sensitivity to perturbation.

### 5. Cross-Domain Mapping

Every engine must print a mapping showing how the domain's structures correspond to:
- Primes → [your spectral basis elements]
- p^{−σ} → [your amplitude decay]
- f(b) = b/(b+1) → [your universal envelope]
- cos(ln(p)·γ) → [your signal component]
- Canal A → [your arithmetic/structural channel]

End the mapping with: *The spectrum is the spectrum.*

### 6. Audit

Run the 7-point audit protocol (see handoff Part 6):
1. Does it run?
2. Correct feature count?
3. All features finite?
4. Classifier correct on ≥3/5 synthetic cases?
5. Throughput matches claims?
6. Dependencies importable?
7. Cross-domain mapping testable?

### 7. Update the Paper

Add a section §7.N to `papers/substrate_scanning_engine.docx` describing your domain,
and update §9 (Deliverables) with the new engine listing.

## Style

- Austere prose. No hype. No adjectives not earned by data.
- If a feature does not discriminate, say so.
- The engines are demonstrations. They show the architecture transfers.
  They do not solve the application.

## License

By contributing, you agree that your contributions will be licensed under AGPL-3.0-or-later.
Papers and documentation are licensed under CC-BY-4.0.
