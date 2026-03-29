# cavity_engine.py — Magic Numbers

Physical cavity spectral engine. 29 features from 2D Laplacian eigenvalues.

## Cavity discretization

| Value | Location | Meaning |
|-------|----------|---------|
| `N_grid = 30` | `Cavity2D.__init__` default | Finite-difference grid: 30 × 30 = 900 points. Trade-off between spectral accuracy (eigenvalue error ~ h² = (2/29)² ≈ 0.005) and speed. At N=30, a single cavity solves in ~50 ms. The paper reports N=35 in demos. |
| `35` | demo calls | Grid size used in the demo section. Slightly higher resolution than default for publication-quality results. |
| `2.0/(N-1)` | `_solve: h` | Grid spacing in normalized coordinates. The cavity lives in [-1,1]², so h = 2/(N-1). |
| `4` | `n < 4` early return | Minimum interior points for a meaningful spectrum. Fewer than 4 points cannot define a 2D Laplacian with enough modes. |
| `-1.0/(h*h)` | off-diagonal Laplacian | Standard 5-point stencil: -1/h² for each neighbor. The discrete Laplacian is ΔV ≈ (V_E + V_W + V_N + V_S - 4V_C)/h². |
| `neighbors/(h*h)` | diagonal Laplacian | Diagonal entry = 4/h² always (the loop counter increments unconditionally). This is correct for Dirichlet BC: missing neighbors contribute zero to the stencil, so the coefficient 4/h² is preserved at boundaries. |

## Cavity shapes

| Value | Shape | Meaning |
|-------|-------|---------|
| `r = 0.85` | circle | Radius slightly less than 1 to ensure the circle fits within [-1,1]² with a boundary margin. |
| `a=0.9, b=0.4` | ellipse_w | Wide ellipse: semi-major 0.9, semi-minor 0.4. Eccentricity ≈ 0.90. |
| `a=0.5, b=0.85` | ellipse_n | Narrow (tall) ellipse. Rotated orientation of the wide ellipse. |
| `w=0.85, h=0.5` | rectangle | Half-widths. Aspect ratio 1.7:1. Eigenvalues are known analytically: λ_{mn} = π²(m²/w² + n²/h²). |
| `w=0.7, h=0.7` | square | Square cavity. Degenerate eigenvalues expected (λ_{12} = λ_{21}). |
| `w=0.45, r=0.4` | stadium | Bunimovich stadium: rectangle of half-width 0.45 with semicircular caps of radius 0.4. The stadium is the canonical example of a chaotic billiard — its level spacing statistics follow GOE (Gaussian Orthogonal Ensemble). |
| `a=0.8, b=0.9, ymin=-0.7` | parabolic | Parabolic cavity: upper boundary y = 0.8 - 0.9x², lower boundary y = -0.7. Models a parabolic reflector cross-section. High Q-factor due to focusing geometry. |
| `0.8` | L_shape interior bound | L-shaped cavity: the square [-0.8, 0.8]² with the upper-right quadrant (x>0, y>0) removed. Has a re-entrant corner that creates singularity in the eigenfunctions. |
| `0.9` | parabolic x-bound | Lateral extent of the parabolic cavity. |

## Feature computation

| Value | Location | Meaning |
|-------|----------|---------|
| `n_modes = 20` | `cavity_features` default | Number of eigenvalues to use. 20 modes captures the Weyl law behavior and level statistics. |
| `1e-10` | `eigs[0] > 1e-10` | Guard against degenerate ground state. If the lowest eigenvalue is essentially zero, ratios like r₂₁ = λ₁/λ₀ are meaningless. |
| `1e-15` | multiple denominators | Standard zero-guard for spacing ratios, CV, Q-factor. |
| `0.01` | `s < ms * 0.01` | Degeneracy threshold: spacing less than 1% of mean spacing counts as degenerate. |
| `0.1` | `s < ms * 0.1` | Near-degeneracy threshold: spacing less than 10% of mean. |
| `10` | `norm[:min(10,n)]` | Harmonicity check uses first 10 eigenvalues: how close are λ_n/λ_0 to integers? |
| `5` | `n > 5` for spectral dimension | Minimum modes for a meaningful power-law fit log(N) vs log(λ). |

## Application scores

| Value | Location | Meaning |
|-------|----------|---------|
| `0.4` | `ant = Q * 0.4` | Antenna score: Q-factor weight. High Q = narrow bandwidth = good for antenna (strong resonance at a single frequency). |
| `0.003` | `reg * 0.003` | Regularity weight in antenna score. Regular spacing helps maintain clean radiation pattern. Small coefficient because regularity and Q can both be > 100. |
| `0.2` | `nd * 0.2` | Non-degeneracy bonus: degenerate modes create mode-coupling issues in antennas. nd ∈ {0, 1}. |
| `0.3, 0.3, 0.4` | acoustic score weights | Acoustic room score: balances uniform spacing (1/CV), Weyl conformity (1/residual), and harmonicity (1 - deviation). Equal weight on spacing and Weyl; slightly higher on harmonicity because audible coloration comes from inharmonic modes. |
| `0.01` | `scv + 0.01`, `wr + 0.01` | Regularization in acoustic score denominators. Prevents score explosion when CV or Weyl residual is near zero. |
