# TODO — Publication Checklist (v2.0.0)

First Zenodo deposit. Subsequent versions are editorial and verification only.

## Before deposit

- [x] Replace `<YOUR_EMAIL>` in `pyproject.toml` with contact email → `rhreve@gmail.com`
- [x] Replace `<YOUR_GITHUB_ID>` in `pyproject.toml`, `CITATION.cff`, `papers/quick_start.tex` → `rhrev`
- [x] Complete BibTeX entries in `substrate_scanning_engine.tex`:
  - [x] WaveFormer2025: Al Hasan et al. (12 authors), MICCAI 2025, LNCS 15963
  - [x] WDM2024: Friedrich et al. (5 authors), DGM4MICCAI 2024, LNCS 15224, pp. 11–21
- [ ] Recompile `substrate_scanning_engine.tex` after BibTeX edits (two pdflatex passes)
- [ ] Recompile `quick_start.tex` after corrections (H23 API fix + GitHub ID + DOI)
- [ ] Recompile `supplementary_hallucination_audit.pdf` — subsection numbering skips (H26)
- [ ] Verify `\email{}` field in `.tex` (currently empty — add or leave blank)
- **Note**: PDFs in `papers/` are from v1.0.0 and do NOT reflect v2.0.0 .tex changes.
  Recompile all three before arXiv submission.

## Zenodo v1 deposit

- [ ] Create GitHub repository, push all 72 files
- [ ] Create release tag `v2.0.0`
- [ ] Link GitHub repo to Zenodo (Settings → GitHub → flip switch)
- [ ] Zenodo auto-generates DOI on release; note the assigned DOI
- [ ] If DOI differs from `10.5281/zenodo.19104086`, update in:
  - `.zenodo.json` (`related_identifiers.identifier`)
  - `CITATION.cff` (`identifiers[0].value`)
  - `README.md` (Zenodo section)
  - `papers/quick_start.tex` (DOI line near end)
- [ ] Verify Zenodo landing page: title, author, ORCID, keywords, license

## arXiv submission

- [ ] Upload `substrate_scanning_engine.tex` + compiled PDF as ancillary
- [ ] Primary category: math.NT
- [ ] Cross-list: cs.LG, physics.comp-ph
- [ ] Abstract: copy from LaTeX `\begin{abstract}...\end{abstract}`
- [ ] Comments field: "16 domains, 12 application engines, code at [Zenodo DOI]"
- [ ] License: CC-BY-4.0 (paper only; code is AGPL-3.0)

## Post-deposit verification (v1.0.1 if needed)

These are editorial — no new results, no new engines.

- [ ] Confirm all 15 `.py` files run on a clean `pip install -r requirements.txt`
- [ ] Confirm CI workflow passes on GitHub Actions (Python 3.10, 3.11, 3.12)
- [ ] Spot-check 3 magic-number READMEs against their engine source
- [ ] Verify paper PDF renders correctly on arXiv (fonts, equations, hyperlinks)
- [ ] Fix any arXiv compilation warnings (if they use their own TeX Live)
- [ ] If corrections needed: tag `v1.0.1`, Zenodo auto-updates

## v2.1.0 paper reconciliation

- [x] Update substrate_scanning_engine.tex: "eight modules" → "nine modules", add §3.8 EulerPhase
- [x] Update substrate_scanning_engine.tex: "29-dimensional" → "31-dimensional (29 core + 2 Euler-specific)" in abstract, §3, §3.9, §7.1, §9
- [x] Update substrate_scanning_engine.tex §4.1: add euler_darg_dt (6.37σ) to zero discrimination ranking
- [x] Disambiguate "phase" vs "argument" in new §3.8
- [ ] Recompile substrate_scanning_engine.pdf after §3.8 addition (two pdflatex passes)
- [ ] Recompile quick_start.pdf (quick_start.tex already edited)
- [x] When Critical Circle paper receives its DOI: add \bibitem{CriticalCircle} to
  substrate_scanning_engine.tex and cite in §3.8 (Kronecker-Weyl reference for winding_var
  exclusion, Corollary 4.3 for darg/dt discrimination, §1 eq. 2 for angular coordinate
  definition). Currently cross-references live only in code docstrings; the paper is
  self-contained without the citation but would benefit from it.
- [x] When Baker bounds paper receives its DOI: add \bibitem{BakerBounds} to
  substrate_scanning_engine.tex and cite in §3.8 as second theoretical grounding for
  winding_var exclusion (Observation 3.1: single-prime angular observables carry no
  zero-specific information — the elimination of γ requires at least a pair of primes).
  Also relevant to §3.8's note that euler_darg_dt is a multi-prime observable: consistent
  with Remark 2.6 (additional primes beyond {2,3} don't improve the bound, but the SSE
  computes actual values, not bounds — accumulation over K primes adds signal).
  No code or feature changes implied: the bounds are numerically vacuous (Remark 2.4).
- **Note**: .tex source updated; PDFs in papers/ are stale until recompilation.

## v3.0.0 STA integration

- [x] Create pipelines/cf_features.py (10 per-eigenvalue + 4 cross-eigenvalue features)
- [x] Create pipelines/zero_locator.py (STA Phases I+II for RiemannZeta; from_values() for others)
- [x] Create pipelines/doc/README_cf_features.md (12 magic numbers)
- [x] Create pipelines/doc/README_zero_locator.md (9 magic numbers)
- [x] Add mpmath to requirements.txt
- [x] Fix F1: KS test → chi-squared for discrete GK distribution
- [x] Fix F2: rename levy_rate → levy_exponent (docstring mismatch B12)
- [x] Fix B8: restrict scan() to RiemannZeta; raise NotImplementedError for Dirichlet/EC
- [x] Fix B9: add RESIDUAL_THRESHOLD to reject false valleys
- [x] Fix B11: compute real residuals in scan_mpmath (was fabricated 0.0)
- [x] Run validation battery: 11/11 PASS
- [x] Run pilot experiment: 100 zeros, 100-digit, K=50
  - H1 (GK typicality): CONSISTENT (Lévy rate 3.422 ± 0.387)
  - H2 (cross-zero CF independence): NULL (z = 0.23)
  - H3 (2-adic orthogonality): ORTHOGONAL (ρ = −0.08)
  - H4 (large-a_k clustering): marginal artifact (corrected null: ~1.14x)
- [x] Add QA_CHECKLIST_TEMPLATE.md to repo root
- [x] Add CONTRIBUTING.md §8 Quality Standards (8.1–8.7)
- [x] Add \bibitem{STA2026} and \bibitem{CriticalCircle} to paper
- [x] Update CHANGELOG.md with [2.2.0] and [3.0.0]
- [x] Update version strings: 2.1.0 → 3.0.0 across 4 files
- [ ] Recompile substrate_scanning_engine.pdf (requires LaTeX)
- [ ] Recompile quick_start.pdf (requires LaTeX)
- [ ] Update paper §8 with pilot results (§8.1–§8.3)
- [ ] GitHub deposit + Zenodo release

## v3.1.0 Dirichlet extension (planned)

- [ ] Run zero_locator on DirichletL for q = 3, 4, 5, 7, 8
- [ ] Extract CF features across multiple L-functions
- [ ] Test H5 (modulus imprint) and H6 (character orthogonality at CF level)
- [ ] Extend paper §8 with Dirichlet results

## v3.2.0 BSD pilot (prospective)

- [ ] LMFDB integration for EllipticCurveL (precomputed a_p)
- [ ] STA zero localization near s=1 for elliptic curve L-functions
- [ ] Test H7 (rank signature in CF) and H8 (conductor imprint)
