# Substrate Scanning Engine — QA Checklist Template

Version: 2.0 · Derived from v2.0.0 → v2.1.0 session + v3.0.0 audit (2026-03-30)

Use this checklist for any change to the repository.
Copy to a new file per change, fill in, attach to the commit or handoff.

Changes from v1.0: see §14 (Revision History) for additions and the bugs they prevent.

---

## 0. Pre-flight: Scope Classification

- [ ] **Change type** (circle one): New module / Feature addition / Bugfix / Rename / Documentation-only / Version bump
- [ ] **Files touched** (list all):
- [ ] **Files NOT touched** (list with reason for each):
- [ ] **Does this change the public API?** (feature_vector length, feature_names, query() dict keys, class names, imports)
  - If YES → breaking change protocol (section 1–7 all mandatory)
  - If NO → sections 5–7 may be skipped

---

## 1. Code Invariants

### 1a. Dimensional Consistency

```python
names = engine.feature_names()
vec = engine.feature_vector(0.5, 14.134725, 30)
assert len(names) == len(vec)
```

- [ ] `len(feature_names()) == len(feature_vector())` — **PASS / FAIL / N/A**
- [ ] Expected dimension: ___
- [ ] Actual dimension: ___

### 1b. Position Stability (existing features unchanged)

```python
assert names[:N_old] == expected_old_names
```

- [ ] Features 0 through N_old−1 retain identical names and identical positions — **PASS / FAIL**
- [ ] Any downstream ML pipeline that indexes by position will not break — **confirmed / at risk**

### 1c. Value Stability (existing feature values unchanged)

Run the engine at a **fixed reference point** (σ=0.5, t=14.134725, K=30) and compare:

- [ ] All existing feature values match baseline to ≤ 1e-10 — **PASS / FAIL**
- [ ] Reference values recorded:
  - `V` = ___
  - `phase_coherence` = ___
  - (new feature) = ___

### 1d. No NaN/Inf in Output

```python
assert np.all(np.isfinite(vec))
```

- [ ] All features finite at reference point — **PASS / FAIL**
- [ ] Tested at edge cases (σ→0, σ→1, t=0, K=2, K=200) — **PASS / FAIL / not tested**

### 1e. Cross-L-Function Compatibility

```python
GeometricEngine(DirichletL(4, {2:0, 3:-1})).feature_vector(0.5, 6.02, 30)
GeometricEngine(EllipticCurveL(0, -1, label='11a')).feature_vector(1.0, 6.36, 20)
```

- [ ] ζ(s): correct dimension, all finite — **PASS / FAIL**
- [ ] L(s,χ): correct dimension, all finite — **PASS / FAIL**
- [ ] L(s,E): correct dimension, all finite — **PASS / FAIL**

### 1f. Edge-Case Inputs (v2.0)

Test the new code with inputs outside the "happy path":

| Input type | Example | Expected behavior | Actual | PASS/FAIL |
|-----------|---------|-------------------|--------|-----------|
| Rational number | 355/113 | Terminates early or NaN in depth-dependent features | ___ | |
| Quadratic irrational | √2 | Eventually-periodic CF, constant Spearman = NaN | ___ | |
| Zero or negative | t = 0, t = −1 | Graceful error or skip, no crash | ___ | |
| Low precision | float64 input to 100-dps code | Degraded CF depth, not garbage | ___ | |

*Rationale (B1, B8, B14): The demo path (8 zeta zeros, float64) exercised none of these.*

---

## 2. Naming Consistency

### 2a. Internal Naming Chain

For each NEW feature, verify the full chain:

| Layer | Name | Matches? |
|-------|------|----------|
| Class name | ___ | |
| `self.___` attribute | ___ | |
| dict key in query() | ___ | |
| `feature_names()` string | ___ | |
| Demo print label | ___ | |

- [ ] All layers use consistent naming — **PASS / FAIL**
- [ ] Feature name prefix matches module convention — **PASS / FAIL**

### 2b. Section Banner Match

```bash
grep "^# MODULE" pipelines/geometric_engine.py
```

- [ ] Every `# MODULE N: NAME` banner matches the class it precedes — **PASS / FAIL**
- [ ] Module numbers sequential with no gaps — **PASS / FAIL**

### 2c. Docstring Module List

- [ ] Module list in file docstring matches section banners — **PASS / FAIL**
- [ ] Module count in docstring matches actual count — **PASS / FAIL**

### 2d. Name-Semantics Alignment (v2.0)

For each feature name, verify the name describes what the code computes:

| Feature name | Docstring claim | Code actually computes | Match? |
|-------------|----------------|----------------------|--------|
| ___ | ___ | ___ | YES/NO |

- [ ] No feature name claims a statistic the code does not compute — **PASS / FAIL**

*Rationale (B12): `levy_rate` claimed to be a rate in bits/term but computed the Lévy exponent (half the rate).*

---

## 3. Terminology Disambiguation

### 3a. Polysemous Terms

| Term | Sense 1 | Where | Sense 2 | Where | Disambiguated? |
|------|---------|-------|---------|-------|----------------|
| ___ | ___ | ___ | ___ | ___ | YES/NO |

- [ ] Every polysemous term disambiguated in docstring or paper — **PASS / FAIL**
- [ ] No new sense introduced without documenting distinction — **confirmed**

### 3b. Nomenclature Alignment with Papers

- [ ] Every observable name in code has a counterpart in the paper — **PASS / FAIL / N/A**
- [ ] No code term imports theory not invoked in the paper (level error check) — **PASS / FAIL**
- [ ] Cross-references cite correct section/theorem numbers — **verified**

---

## 4. Excluded Feature Documentation

| Feature | Reason for exclusion | Empirical evidence | Theoretical cause | Documented in |
|---------|---------------------|--------------------|-------------------|---------------|
| ___ | ___ | ___ | ___ | docstring / README / CHANGELOG |

- [ ] Every excluded feature has BOTH empirical evidence AND theoretical cause — **PASS / partial / FAIL**
- [ ] No excluded feature appears in functional code — **confirmed**

---

## 5. Repository Propagation

### 5a. Numeric Claims

- [ ] All stale counts updated — **PASS / FAIL**
- [ ] All correct counts confirmed unchanged — **PASS / FAIL**

### 5a-ii. Comment-vs-Code Consistency (v2.0)

For every numeric constant in a comment or README, verify against runtime:

```python
computed = sum(gauss_kuzmin_pmf(k) for k in range(11, 10001))
documented = 0.0861  # ← value in comment — DOES IT MATCH computed?
```

- [ ] Every numeric constant in a comment matches runtime value — **PASS / FAIL**
- [ ] Every numeric constant in a README matches runtime value — **PASS / FAIL**

*Rationale (B5→B6→B7): A single wrong comment ("~0.0861" vs actual 0.1254) cascaded to README, F10 null, and H4 pilot result.*

### 5b. Version Strings

- [ ] `pyproject.toml`, `CITATION.cff`, `.zenodo.json`, `README.md`, `quick_start.tex`: all updated — **PASS / N/A**
- [ ] Zip folder name matches version — **PASS**
- [ ] Zero residual old version outside CHANGELOG/TODO — **confirmed**

### 5c. Old Name Residuals (for renames)

- [ ] Zero residuals of old name outside CHANGELOG — **PASS / FAIL**

### 5d. Application Engines (12 engines × 29 features)

- [ ] Feature counts unchanged at 29 — **confirmed**
- [ ] No application engine imports new classes — **confirmed**

### 5e. Paper .tex

- [ ] Abstract, §3, §4, §9 counts match code — **PASS / FAIL / deferred**
- [ ] No numeric inconsistencies within the paper — **PASS / FAIL**

### 5e-ii. Cross-Document Citation Consistency (v2.0)

If the paper cites a numeric value from another document:

- [ ] Every cited value matches the current best measurement — **PASS / STALE**
- [ ] If citing an older value when newer data exists: updated or acknowledged — **verified**

*Rationale (P10): Inserted "3.33 ± 0.54" while holding pilot data showing 3.422 ± 0.387.*

### 5e-iii. CHANGELOG → Paper Diff Verification (v2.0)

- [ ] Every CHANGELOG claim about paper changes corresponds to an actual `.tex` diff — **PASS / FAIL**
- [ ] No CHANGELOG entry describes planned changes as completed — **PASS / FAIL**
- [ ] Deferred items marked `**Deferred**:` with reason, NOT in `### Changed` — **verified**

*Rationale (P9): CHANGELOG said "§8: added §8.1, §8.2, §8.3" — they were never written.*

### 5e-iv. CITATION.cff ↔ Paper Abstract Alignment (v2.0)

- [ ] Every capability in CITATION.cff abstract exists in the paper — **PASS / FAIL / noted**
- [ ] If CITATION describes repo beyond paper: stated explicitly in CITATION — **verified**

*Rationale (P13): CITATION said "5 pipelines" while paper abstract mentioned none.*

### 5e-v. §9 Deliverables ↔ File Inventory (v2.0)

- [ ] Every `.py` in repo appears in §9 — **PASS / FAIL / deferred with note**
- [ ] If §9 covers a subset: stated (e.g., "as of v2.1.0") — **verified**

*Rationale (P14): cf_features.py and zero_locator.py added to repo but not to §9.*

### 5e-vi. Content Completeness After Rewrite (v2.0)

If the .tex was rewritten (not just patched):

```bash
# Compare section/subsection counts
grep -c 'section{' old.tex
grep -c 'section{' new.tex
# Compare table counts
grep -c 'begin{table}' old.tex
grep -c 'begin{table}' new.tex
```

- [ ] Every table in the original is present in the rewrite — **PASS / FAIL**
- [ ] Every subsection in the original is present or its removal is documented — **PASS / FAIL**
- [ ] No worked examples dropped without acknowledgment — **PASS / FAIL**

*Rationale (S1): The STA v1.1 rewrite dropped Table 2 (convergent cascade for γ₁ — the paper's most concrete worked example) and §3.1. The 9-fix session focused on corrections and missed that content was lost.*

### 5e-vii. Table/Figure Reference Integrity (v2.0)

- [ ] All table references use `\ref{tab:label}`, not hardcoded `Table~N` — **PASS / FAIL**
- [ ] If any table was added or removed: all references renumbered or converted to `\ref` — **verified**

*Rationale (S2): After dropping Table 2, three hardcoded "Table~3" references pointed to the wrong table (efficiency, not comparison).*

### 5e-viii. Bibliography Completeness (v2.0)

```bash
# Find bibitems with no corresponding \cite
for bib in $(grep -oP 'bibitem\{[^}]+\}' paper.tex | sed 's/bibitem{//;s/}//'); do
  count=$(grep -c "cite{$bib}" paper.tex)
  [ "$count" -eq 0 ] && echo "UNCITED: $bib"
done
```

- [ ] Every `\bibitem` has at least one `\cite` in the text — **PASS / FAIL**
- [ ] If a \bibitem was present in the original: the \cite that referenced it is preserved or replaced — **verified**

*Rationale (S3): Borwein and Titchmarsh bibitems were defined but never cited after the rewrite dropped the sentences that originally referenced them.*

### 5f. Magic Numbers READMEs

- [ ] New module has magic-numbers README — **PASS / FAIL / N/A**
- [ ] All constants documented with origin and sensitivity — **PASS / FAIL**

---

## 6. Validation (for functional changes)

### 6a. MVP Test Design

- [ ] At least one test per claimed property
- [ ] At least one NEGATIVE result test
- [ ] TRIVIAL PROXY check: `abs(rho) < 0.95` for all input parameters

### 6a-ii. Anti-Tautology Check (v2.0)

For each test: **"Could this test pass if the code did nothing useful?"**

| Test | What it checks | Could a no-op pass? | Verdict |
|------|---------------|---------------------|---------|
| ___ | ___ | YES → **rewrite** / NO → OK | |

Tautologies to reject:
- Comparing a value against the function that produced it
- Checking only that a constructor runs without error
- Verifying dimension/type without verifying content
- Testing only demo inputs without adversarial inputs

*Rationale (B3, B8, P1): Three "PASS" tests hid critical bugs by testing form, not content.*

### 6a-iii. Statistical Test Appropriateness (v2.0)

- [ ] Test assumptions match data (continuous vs discrete) — **verified**
- [ ] Null hypothesis correctly specified — **verified**
- [ ] Expected values from correct distribution — **verified**
- [ ] Sample size sufficient for power — **verified / documented limitation**

*Rationale (B1, B6): KS on discrete data; uniform null for non-uniform GK.*

### 6b. Discrimination Tests

- [ ] Cohen's d reported — **done**
- [ ] Multivariate LOO if applicable — **done / N/A**

### 6c. Stability Tests

- [ ] K-convergence CV reported — **done / N/A**

### 6d. Orthogonality Tests

- [ ] New features tested for independence from existing features — **done / partial / N/A**

### 6e. Timing

- [ ] ms/call within budget — **PASS / FAIL**

### 6f. Convergence Verification (v2.0)

If the code evaluates a function via partial sums/series/products:

- [ ] Series converges in the region of application — **proved / cited / tested**
- [ ] If NOT convergent: accelerated method used or limitation documented — **verified**
- [ ] Docstring does NOT claim acceleration the code doesn't implement — **verified**

*Rationale (B3, B4, B8): Raw partial sums at σ=1/2; docstring claimed "Borwein" for raw sum.*

### 6g. Permutation Baseline (v2.0)

If cross-sample statistics are computed:

- [ ] Null from permutation shuffle — **done**
- [ ] z-score reported; z < 2.0 = null — **done**
- [ ] Theoretical null constants verified against runtime (§5a-ii) — **done**

*Rationale (B7): H4 "2.21x" was artifact of wrong constant (0.0861² vs 0.1254²).*

---

## 7. CHANGELOG Completeness

- [ ] Version, date match pyproject.toml and CITATION.cff — **PASS / FAIL**
- [ ] ### Added, ### Changed, ### Unchanged sections complete — **PASS / FAIL**
- [ ] ### Validation section with key numbers — **complete / N/A**

### 7a. Bugs:Claims Ratio (v2.0)

- [ ] Bugs found: ___
- [ ] Claims surviving: ___
- [ ] Ratio: ___ — **documented in CHANGELOG**

---

## 8. TODO.md Consistency

- [ ] Completed [x], pending [ ] — **PASS / FAIL**
- [ ] Deferred items have `**Note**` — **PASS / FAIL**
- [ ] No stale items referencing completed work — **PASS / FAIL**

---

## 9. Final Smoke Test

- [ ] Main demo runs without errors — **PASS / FAIL**
- [ ] Dimensions and names printed correctly — **PASS / FAIL**

### 9a. Cross-Module Smoke Test (v2.0)

- [ ] Each module's demo runs independently — **PASS / FAIL**
- [ ] Integration path produces finite results — **PASS / FAIL**

### 9b. Failure-Path Smoke Test (v2.0)

- [ ] Code that should raise errors does raise them — **PASS / FAIL**
- [ ] Code that should return NaN/empty for bad input does so — **PASS / FAIL**

*Rationale (B8): scan() silently returned ζ zeros for Dirichlet. Should have raised NotImplementedError.*

---

## 10. Packaging

- [ ] Zip folder name matches version — **PASS / FAIL**
- [ ] No `.cache/`, `__pycache__/` in zip — **PASS / FAIL**
- [ ] No absolute paths in packaged files — **PASS / FAIL**
- [ ] All `.py` importable on clean install — **tested / not tested**

### 10a. Dead Code Removal (v2.0)

- [ ] No function defined but never called — **PASS / FAIL**
- [ ] If kept intentionally: `# Retained for: [reason]` — **confirmed**

*Rationale (B4): `_borwein_coefficients()` and `eta_modulus()` were dead code with false docstrings.*

### 10b. Fabricated Values Check (v2.0)

- [ ] No output field contains a hardcoded value pretending to be computed — **PASS / FAIL**
- [ ] Uncomputable fields set to NaN with documentation — **confirmed**

*Rationale (B11): `residual=0.0` pretended to be verified when it was fabricated.*

### 10c. CI ↔ API Consistency (v2.0)

```bash
# Extract all assertions in CI workflow
grep "assert len\|assert all\|Expected.*features" .github/workflows/ci.yml
# Compare against actual API
python -c "from geometric_engine import ...; print(len(vec))"
```

- [ ] Every `assert len(vec) == N` in CI matches current API dimension — **PASS / FAIL**
- [ ] CI tests every pipeline (not just geometric_engine) — **PASS / FAIL**
- [ ] CI tests at least one failure path (e.g., NotImplementedError) — **PASS / FAIL**

*Rationale (D1): CI asserted `len(vec) == 29` when the engine produced 31 since v2.1.0. Never executed, so never caught. D2: new pipelines had zero CI coverage.*

### 10d. Dependency License Completeness (v2.0)

```bash
# Every package in requirements.txt should appear in THIRD-PARTY-LICENSES
diff <(grep -v '^#' requirements.txt | sed 's/[><=].*//' | sort) \
     <(grep '^## ' THIRD-PARTY-LICENSES/README.md | sed 's/## //' | tr 'A-Z' 'a-z' | sort)
```

- [ ] Every dependency in requirements.txt has an entry in THIRD-PARTY-LICENSES — **PASS / FAIL**
- [ ] License type and URL are correct — **verified**

*Rationale (D4): mpmath added to requirements.txt but missing from THIRD-PARTY-LICENSES.*

### 10e. Tutorial/Quick-Start Freshness (v2.0)

- [ ] Version string in quick_start matches pyproject.toml — **PASS / FAIL**
- [ ] Feature counts in quick_start match current API — **PASS / FAIL**
- [ ] Dependency list in quick_start matches requirements.txt — **PASS / FAIL**
- [ ] Code examples in quick_start run without errors on current code — **tested / not tested**
- [ ] If new pipelines were added: quick_start includes usage examples — **PASS / FAIL / N/A**

*Rationale (D3): quick_start.tex said "v2.1.0", "29 features", "NumPy/SciPy only" after v3.0.0 added 2 pipelines, changed to 31 features, and added mpmath.*

---

## 11. Scope Honesty (v2.0)

| Claim | Where | Actually works for | Honest? |
|-------|-------|-------------------|---------|
| ___ | ___ | ___ | YES / OVERCLAIM |

- [ ] No docstring claims functionality that silently gives wrong results — **PASS / FAIL**
- [ ] Unsupported inputs raise NotImplementedError, not silent wrong output — **confirmed**
- [ ] Known limitations in module docstring, not buried in comments — **confirmed**

*Rationale (B8): "Works for all L-functions" was most dangerous bug. Silent wrong output, not an error.*

---

## 12. Mathematical Constants Verification (v2.0)

| Constant | Comment/README value | Runtime value | Formula | Match? |
|----------|---------------------|---------------|---------|--------|
| ___ | ___ | ___ | ___ | YES/NO |

- [ ] Every documented constant matches runtime — **PASS / FAIL**
- [ ] No constant transcribed from a different base (ln vs log2) — **PASS / FAIL**
- [ ] Source formula cited — **PASS / FAIL**

*Rationale (B5): ln/log2 confusion in a single comment caused three downstream errors.*

---

## 13. CONTRIBUTING.md Consistency (v2.0)

- [ ] §8 references correct QA checklist version — **PASS / FAIL**
- [ ] Every §8 standard has a check in this template — **PASS / FAIL**
- [ ] Precedent examples still accurate — **PASS / FAIL**

---

## Sign-off

| Check | Status |
|-------|--------|
| §1 Code invariants | |
| §2 Naming consistency | |
| §3 Terminology | |
| §4 Excluded features | |
| §5 Propagation (incl. 5e paper checks) | |
| §6 Validation | |
| §7 CHANGELOG | |
| §8 TODO.md | |
| §9 Smoke test | |
| §10 Packaging | |
| §11 Scope honesty | |
| §12 Constants | |
| §13 CONTRIBUTING | |

**Overall**: PASS / PASS WITH NOTES / FAIL

**Bugs found**: ___ · **Claims surviving**: ___ · **Ratio**: ___

**Notes**:

---

## 14. Revision History

### v2.0 (2026-03-30) — from v3.0.0 audit (14 bugs found, all fixed)

| Addition | Bug it prevents | Pattern |
|----------|----------------|---------|
| §1f Edge-Case Inputs | B1, B8, B14 | Narrow test inputs miss real failures |
| §2d Name-Semantics Alignment | B12 | Feature name lies about what code computes |
| §5a-ii Comment-vs-Code Consistency | B5→B6→B7 | Documentation drifts from runtime values |
| §6a-ii Anti-Tautology Check | B3, P1 | Self-validating tests hide bugs |
| §6a-iii Statistical Test Appropriateness | B1, B6 | Wrong test for data type |
| §6f Convergence Verification | B3, B4, B8 | Partial sums used where they don't converge |
| §6g Permutation Baseline | B7 | Wrong null constant inflates signal |
| §7a Bugs:Claims Ratio | — | Serie I diagnostic metric |
| §9a Cross-Module Smoke Test | B8 | Integration path passes wrong data |
| §9b Failure-Path Smoke Test | B8 | Missing error handling on bad inputs |
| §10a Dead Code Removal | B4 | Misleading unused functions |
| §10b Fabricated Values Check | B11 | Hardcoded output pretends to be computed |
| §5e-ii Cross-Document Citation | P10 | Paper cites stale value while newer data exists |
| §5e-iii CHANGELOG→Paper Diff | P9 | CHANGELOG claims paper changes that don't exist |
| §5e-iv CITATION↔Paper Alignment | P13 | Citable abstract diverges from paper abstract |
| §5e-v §9 Deliverables↔Files | P14 | New files missing from paper's file inventory |
| §5e-vi Content Completeness | S1 | Rewrite drops tables/sections without noticing |
| §5e-vii Table Reference Integrity | S2 | Hardcoded Table~N wrong after table deletion |
| §5e-viii Bibliography Completeness | S3 | Bibitems orphaned when citing text is rewritten |
| §10c CI ↔ API Consistency | D1, D2 | CI assertions stale after API change; new code untested |
| §10d Dependency License Completeness | D4 | New dependency added without license documentation |
| §10e Tutorial/Quick-Start Freshness | D3 | Tutorial claims stale version, counts, dependencies |
| §11 Scope Honesty | B8 | Overclaimed capabilities pass API tests |
| §12 Constants Verification | B5 | Transcription error in mathematical constants |
| §13 CONTRIBUTING Consistency | — | Policy references stay current |

### v1.0 (2026-03-29) — from v2.0.0 → v2.1.0 session

Original 10 sections. Covers: EulerPhase addition, ScatteringPhase→EulerPhase rename,
winding_var exclusion, Critical Circle cross-referencing, disambiguation audit.
