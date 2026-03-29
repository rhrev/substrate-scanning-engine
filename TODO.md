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
- [ ] If DOI differs from `10.5281/zenodo.19299719`, update in:
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

## Future versions (v1.1.0+)

Not planned. If pursued, candidates are:

- Real data validation for one application engine (e.g., CWRU bearing dataset for motor_diagnosis)
- LMFDB integration for BSD verification at scale (§8 open question (c))
- Daubechies/Morlet upgrade for turbulence_engine (documented Haar limitation)
- Schoof/SEA point counting for crypto_curve_engine beyond p ~ 500
