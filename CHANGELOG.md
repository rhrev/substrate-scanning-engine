# Changelog

All notable changes to the Substrate Scanning Engine are documented in this file.

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
