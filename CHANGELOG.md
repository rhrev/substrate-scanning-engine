# Changelog

All notable changes to the Substrate Scanning Engine are documented in this file.

## [3.1.1] — 2026-03-31

### Changed
- DOIs updated to v3.1.1 deposit (.19379148) in: README.md, CITATION.cff,
  papers/quick_start.tex, TODO.md, .zenodo.json, papers/substrate_scanning_engine.tex
- STA bibitem DOI updated to new deposit (.19353699) in:
  papers/substrate_scanning_engine.tex, .zenodo.json
- .zenodo.json description: Canal A → Channel A

## [3.0.0] — 2026-03-30

### Added
- Pipeline: `pipelines/cf_features.py` — CF-integer feature extraction
  - 10 per-eigenvalue features (F1–F10) from continued fraction partial quotients
  - 4 cross-eigenvalue features (C1–C4) for pairwise CF correlation analysis
  - `batch_features()` for collection-level analysis
  - Excludes a_0 (magnitude leakage: Spearman ρ = 1.000 vs γ by definition)
  - F1 uses chi-squared against GK (not KS — KS inappropriate for discrete distributions)
- Pipeline: `pipelines/zero_locator.py` — STA-derived zero localization
  - Locates zeros of Riemann zeta via STA Phases I+II (scan + golden-section + altzeta)
  - Phase I: float64 valley detection (raw alternating sum, relative ordering)
  - Phase II: mpmath.altzeta refinement to target precision with residual verification
  - RESIDUAL_THRESHOLD = 1e-3 rejects false valleys (B9 fix)
  - scan_mpmath(): fast path via mpmath.zetazero with computed (not fabricated) residuals
  - from_values(): wraps externally-supplied zeros for any L-function (Dirichlet, EC)
  - scan() and scan_mpmath() raise NotImplementedError for non-Riemann L-functions
    (partial sums do not converge at sigma=1/2; see module docstring errata)
  - Returns Zero namedtuples with (gamma, residual, cf_terms, features)
- Documentation: `pipelines/doc/README_cf_features.md` (12 magic numbers)
- Documentation: `pipelines/doc/README_zero_locator.md` (9 magic numbers)
- Dependency: mpmath added to requirements.txt

### Changed
- substrate_scanning_engine.tex: added \bibitem{STA2026} and \bibitem{CriticalCircle};
  \cite{STA2026} in §3.3 (Scale 3, Lévy rate); \cite{CriticalCircle} in §3.8
  (Kronecker-Weyl for winding_var exclusion). §8 (Open Questions) UNCHANGED.
  Paper body does NOT yet describe cf_features, zero_locator, or pilot results.
  **Deferred**: §8.1–§8.3 (STA localization, CF features, negative results)
  require prose writing; results exist in pilot_experiment_results.json but
  are not in the paper. See TODO.md.
- README.md: added cf_features and zero_locator to pipeline listing
- CONTRIBUTING.md: added §8 Quality Standards (8.1–8.7)

### Pilot Results (100 zeros, 100-digit, K=50)
- Lévy rate: 3.422 ± 0.387 bits/term (theoretical: 3.42). Confirmed.
- H2 (cross-zero CF independence): NULL (z = 0.23). Canal D not justified.
- H3 (2-adic orthogonality): ORTHOGONAL (ρ = −0.08). Canal A ⊥ C extends to CF.
- H4 (large-a_k clustering): 1.04x over corrected null (CONFIRMED NULL).
  Original analysis showed 2.21x but used wrong GK constant (ln vs log2).
  Corrected null: P(a>10)² = 0.1254² = 0.01573. Observed: 0.0164.
- Trivial proxy check: all 10 features PASS (max |ρ| = 0.139 vs γ).
- Bugs caught: 7 (KS on discrete, marginal null, _eta_mp raw sum,
  dead code, GK ln/log2 confusion ×3, F10 uniform null).
  Ratio bugs:claims = 7:3.

### Unchanged
- geometric_engine.py: 31-feature vector, 9 modules — UNTOUCHED
- All 12 application engines: 29 features each — UNTOUCHED
- All 17 HTML visualizations — UNTOUCHED
- envelope_pipeline.py, envelope_v2.py — UNTOUCHED
- §0 Errata (7 overclaims) — UNTOUCHED

### Validation
- Dimensional stability: geometric_engine still 31, app engines still 29
- Zero locator: |gamma_1 - 14.134725...| < 1e-44 at dps=50 (genuine STA scan, not zetazero)
- Zero locator: scan(1, 5) returns 0 zeros (B9 residual gate rejects false valleys)
- Zero locator: scan() raises NotImplementedError for DirichletL (honest limitation)
- CF features: 0/10 trivial proxy leakage; all finite for 100 zeros
- CF features: F1 varies across zeros (chi-sq fix confirmed: std=0.97, was 0.0 with KS)
- CF features: F2 renamed levy_exponent (was levy_rate — naming mismatch B12)
- Timing: 19.4 ms/eigenvalue for CF features; ~0.5s/zero for STA scan at dps=50
- verify.sh: 20/20 local CI checks pass on Python 3.10

### QA Corrections (second-pass review, 2026-03-31)
- PA-1: CLAIMS.md Lévy formula π²/(6 ln 2) → π²/(6 (ln 2)²)
- PA-3: pyproject.toml: added mpmath to [project].dependencies
- PA-4: cf_features.py: gauss_kuzmin_cdf() annotated as retained for public API
- PA-8: cf_features.py: F1 docstring "KS statistic" → "reduced chi-squared"
- PA-15: substrate_scanning_engine.tex bibitems updated:
  CriticalCircle title "Quintuple Convergence" → "Topological Cartography" + DOI
  STA2026 version v1.1 → v1.2 + DOI updated
- DOIs updated to v3.0.0 record (.19104086) in: README.md, CITATION.cff,
  quick_start.tex, TODO.md. Old DOI (.19299719) retained only in CHANGELOG.
- Added: verify.sh (local CI replication, 20 checks)
- Added: README.md Quick Start section with install/verify/usage instructions
- .gitignore: added data/envelope_v2_results.json (runtime artifact)

## [2.2.0] — 2026-03-30

### Added
- QA_CHECKLIST_TEMPLATE.md in repo root (10 sections, 40+ checks)
- CONTRIBUTING.md §8: Quality Standards (8.1–8.7)
  - 8.1 QA Checklist mandatory for all changes
  - 8.2 Level-error filter
  - 8.3 Trivial-proxy check (ρ > 0.95 threshold)
  - 8.4 Permutation baseline for cross-eigenvalue signals
  - 8.5 Excluded feature documentation policy
  - 8.6 §0 Errata convention
  - 8.7 Negative results with equal prominence
- Bibliography: \bibitem{STA2026} and \bibitem{CriticalCircle} in paper
- Citation: \cite{STA2026} in §3.3 (Scale 3 Lévy rate validation)
- Citation: \cite{CriticalCircle} in §3.8 (Kronecker-Weyl for winding_var)

### Changed
- Version: 2.1.0 → 2.2.0 across pyproject.toml, CITATION.cff, .zenodo.json, README.md
- TODO.md: Critical Circle and Baker bounds citation items marked [x]

### Unchanged
- All .py files (15 files) — UNTOUCHED
- All HTML visualizations (17 files) — UNTOUCHED
- All feature vectors, APIs, class names — UNTOUCHED
- PDFs in papers/ remain stale (recompilation requires LaTeX environment)

## [2.1.0] — 2026-03-29

### Added
- Module 8: EulerPhase — accumulated angular coordinate arg(ζ_K(s)) and d(arg)/dt
  - Gaussian-windowed (w_k = exp(−π(k/K)²)) by default; 72–93% CV reduction in K-convergence
  - Orthogonal to V at σ ≤ 0.5 (Spearman ρ = 0.006)
  - euler_darg_dt: highest zero/non-zero separation of all 31 features (6.37σ)
  - winding_var excluded as trivial σ-proxy (Spearman ρ = 1.000 vs mean(p^{−2σ}); label leakage)
- Feature vector: 29 → 31 (29 core + 2 Euler-specific: euler_arg, euler_darg_dt)
- GeometricEngine renumbered: 8 → 9 modules

### Changed
- README.md: "29 Features" → "29 Core Features"; geometric_engine row 29 → 31 (29+2)
- quick_start.tex: code snippet updated (29 → 31 floats), description updated
- CONTRIBUTING.md: clarified 29 (application engines) vs 31 (geometric_engine)
- README_geometric_engine.md: added Module 8 magic numbers, renumbered Module 9
- sparam_engine.py: corrected dimension claim ("Same dimension as geometric_engine" → application engines)

### Unchanged
- All 12 application engines remain at 29 features (EulerPhase requires Euler product local factors)
- substrate_scanning_engine.tex/pdf: untouched (records v2.0.0 state; update deferred to next paper revision)
- All existing feature positions 0–28 unchanged (downstream ML compatibility preserved)

### Validation
- MVP test battery: 3 phases, 7 tests (mvp_test.py, mvp_deep_dive.py, mvp_multivariate.py)
- One false positive eliminated (winding_var d=3.66 was label leakage, not discovery)
- Motor ceiling confirmed architectural: LOO accuracy at σ=0.5 vs σ=0.55 = 54.2% (√γ barrier)

### Terminology alignment (Critical Circle cross-reference)
Nine docstring/documentation/paper corrections aligning SSE terminology with Critical Circle v2:
- T1: Class docstring rewritten — "accumulated angular coordinate of the Euler product"
  (Critical Circle §1 eq. 2), replacing "scattering phase" language throughout.
- T2: winding_var exclusion now documents theoretical cause — Kronecker-Weyl equidistribution
  (Critical Circle Theorem 2.1(iv)) implies Var ≈ (1/2)·E[p^{−2σ}], explaining the
  empirical ρ = 1.000.
- T3: README_geometric_engine.md: "Functionally identical to the Schwartz-Bruhat kernel"
  → "Same functional form as" — aligns with Critical Circle §6 Remark 6.3 ("interpretive
  but not foundational").
- T4: Gaussian window docstring and README now cite Conrad (2005) divergence of partial Euler
  products — the theoretical reason arg needs windowing while V does not.
- T5: euler_darg_dt discrimination (6.37σ) documented as derivative of the angular signature
  that Critical Circle Corollary 4.3 identifies as the only information surviving on the
  critical line. Zero sign-change → |darg/dt| maximized.
- T6: Class renamed ScatteringPhase → EulerPhase. Propagated to: attribute (self.euler_phase),
  dict key ('euler_phase'), feature names (euler_arg, euler_darg_dt), README, CONTRIBUTING,
  TODO, CHANGELOG. "Scattering" was never invoked in the paper; "Euler" aligns with
  EulerProduct (Module 1) and the paper's "Euler embedding" (Theorem 2.1).
- T7: "accumulated phase" → "accumulated argument" in EulerPhase docstrings, query() docstring,
  and README. Disambiguates from "phase" (= oscillatory angle θ_p = −t ln p, Canal C) vs
  "argument" (= arg(1−p^{−s}), non-linear geometry of local factor). Five senses of "phase"
  in the codebase now documented; EulerPhase uses only "argument".
- T8: substrate_scanning_engine.tex updated: abstract (29→31), §3 (eight→nine modules),
  new §3.8 EulerPhase with explicit disambiguation of "phase" vs "argument", §3.8→§3.9
  renumbered (31-dim breakdown), §4.1 (euler_darg_dt 6.37σ added to discrimination ranking),
  §7.1 (29→31), §9 Deliverables (9 modules, 31 features), §9 closing (29 core vs 31 Euler).
- T9: Disambiguation audit — two residual ambiguities found and fixed:
  (a) Section banner `# MODULE 8: SCATTERING PHASE` → `# MODULE 8: EULER PHASE`. The T6
      rename propagated to class, attribute, dict key, feature names, README, CONTRIBUTING,
      TODO, CHANGELOG, and paper, but missed the ASCII section header in the source file —
      the first thing a reader sees when scrolling to Module 8.
  (b) Paper §3.8 said 6.37σ while §4.1 said 6.4σ for the same measurement. Unified to 6.4σ
      in both (paper convention: round to 1–2 significant figures in rankings). The code
      docstring retains 6.37σ as the precise value from the validation run. CHANGELOG T5
      retains 6.37σ as historical record of the validation result.
  Four observations documented without action:
  (A) euler_arg (feature name) ← arg_total (dict key): follows v2.0.0 pattern (torus_xy ←
      xy_mag, weil_gap ← spectral_gap, etc.). Feature names are terse; dict keys descriptive.
  (B) "angular coordinate" (class docstring) vs "argument" (feature docstring): both standard
      mathematical terms for arg(z). Conceptual vs functional naming.
  (C) phase_cos/phase_sin/phase_coherence (features 21–23, Canal C) vs euler_phase (dict key,
      Module 8): two senses of "phase" in the same feature vector. Paper §3.8 disambiguates
      explicitly.
  (D) EnvelopeDecomposition.decompose() returns key 'phase' = arctan2(C,B) — a sixth sense
      of "phase", but outside the feature_vector path. No downstream confusion risk.

## [2.0.0] — 2026-03-28

### Corrected (27-finding audit, 21 with action)

#### Bloqueantes
- H5: Hardcoded `/home/claude/` paths in envelope pipelines → relative paths via `os.path`
- H20: Removed duplicate `zeros_r3_2000.html` (byte-identical to `zeros_r3.html`); updated "18 interactive" → "17 interactive" across 7 files
- H23: Fixed incorrect API calls in `quick_start.tex` (`RiemannZeta(K=30)` → `RiemannZeta()`, `full_vector()` → `feature_vector()`)

#### Infrastructure
- H1: Removed `[tool.setuptools.packages.find]` from `pyproject.toml` (no `__init__.py` in script-only dirs)
- H2: Added copyright header to LICENSE (AGPL-3.0 requires it)
- H3: Added SPDX/Copyright headers to 7 .py files missing them (15/15 now covered)
- H4: Resolved all `<YOUR_EMAIL>` and `<YOUR_GITHUB_ID>` placeholders
- H6: Bare `except:` → `except Exception:` in `envelope_v2.py` (2 sites)
- ci.yml: Added `permissions: contents: read`
- Google Fonts (IBM Plex Mono, Cormorant Garamond) added to THIRD-PARTY-LICENSES

#### Documentation
- H8: Corrected cavity README Laplacian diagonal description (always 4/h², not variable)
- H24/H27: Added `\cite{Connes2026}` and `\cite{GuthMaynard2024}` to match existing bibitems
- H25: Completed WaveFormer2025 (12 authors, LNCS 15963) and WDM2024 (5 authors, LNCS 15224) bibitems

#### Code
- H11: Removed dead walrus variable `n_nonsync_high` in `motor_diagnosis.py`
- H14: Adjusted sparam lossy profile coefficients so "lossy" classifies as MARGINAL/FAIL

#### Visualizations
- H17: Added resize handlers to `geodesicas.html` and `lambda_surface.html`
- H21: Added Weil matrix simplification comment to `tres_operadores.html`
- H22: Added superseded comment to `zeros_action.html`

### Changed
- DOI: `10.5281/zenodo.19104330` → `10.5281/zenodo.19299719`
- Version: 1.0.0 → 2.0.0 across pyproject.toml, .zenodo.json, CITATION.cff, README.md, quick_start.tex, TODO.md
- File count: 73 → 72 (duplicate removed)

### Unchanged
- All mathematical content, formulas, and numerical results
- 29-feature vector definition and f(b) = b/(b+1) implementation
- §0 Errata (7 overclaims) — unchanged
- 13 engines table in README — unchanged
- envelope_results.json data values — unchanged (only output path fixed)


## [1.0.0] — 2026-03-28

### Added
- 12 application engines: sparam, motor_diagnosis, graph, ast, cavity, phonon, colorimetry, wavelet_3d, turbulence, image_spectral, pathfinding, crypto_curve
- 3 pipeline files: geometric_engine.py (core), envelope_pipeline.py (v1), envelope_v2.py (v2)
- 17 interactive HTML visualizations (Three.js r128)
- 15 magic-number README files documenting every numerical constant
- Paper: substrate_scanning_engine.docx (§0–§10, 129 paragraphs, 16 domains)
- Paper: substrate_scanning_engine.tex (LaTeX conversion, amsart, 14 pages)
- Technical reports: dual_role_f_v3.docx, class_number_report.docx, two_windows.docx
- Methodology: curva_aprendizaje_serie_I.md (hallucination audit)
- Dashboards: dual_test_dashboard.jsx, preguntas_abiertas.jsx
- Repository infrastructure: pyproject.toml, CITATION.cff, CONTRIBUTING.md, CI workflow
- Zenodo metadata: .zenodo.json

### Corrected (§0 Errata — documented in paper before all results)
1. Cumulative exponent is −1.4±0.1, not −1.0 ("exactly as f(b)")
2. Spiral exponent α = −0.96 was fixed-reference artifact; true value −1.4±0.1
3. Poincaré compactification: points move toward origin, not ∂B³
4. f(b) bridge between digit-sum and toroidal channels: falsified (ρ < 0.01)
5. γ·|ω| ≈ constant: CV = 36%, removed
6. Cone of radial directions does not close: N^{−0.19} decay too slow
7. "Zeros exist as points on ∂B³": reification corrected

### Paper self-consistency audit (applied to v3)
- §7.11: "16 materials" → "12 materials"; "skutterudites" → "clathrates (skutterudite proxy)"
- §7.9: "11 graph families...tree" → "9 graph configurations...ER sparse and dense"
- §9(c): "9 interactive HTML" → "17 interactive HTML" with complete listing
- Stale §8 stub deleted; note migrated to real §8
- §7.8: "(Prospective — No Engine Implemented)" tag removed
- README.md: Zenodo DOI section added

## [0.9.0] — 2026-03-28

### Added (internal, pre-audit)
- Initial 7 application engines (sparam through colorimetry)
- Core geometric_engine.py with 8 modules, 29 features
- 17 interactive visualizations
- Paper draft at 11 domains

### Known Limitations
- AST spectral similarity too coarse for tree discrimination (documented)
- Cylinder/torus ambiguously classified in wavelet_3d (genuine ambiguity)
- Haar wavelet has poor frequency resolution for turbulence K41 recovery
- crypto_curve brute-force counting limited to p ≲ 500
- Image forensics tested at 64×64 only
