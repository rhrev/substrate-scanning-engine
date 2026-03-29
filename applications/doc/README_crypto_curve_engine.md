# Magic Numbers: crypto_curve_engine.py

Every numerical constant in this file, its origin, meaning, and sensitivity.

## Point Counting

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| O(p²) complexity | brute force | Exhaustive x,y enumeration over F_p | Exact — limits p to ~500 |
| point at infinity | +1 to count | Projective closure of affine curve | Exact — algebraic geometry |
| a_p = p+1-#E | Frobenius trace | Definition of trace of Frobenius | Exact |
| Hasse bound | 2√p | |a_p| ≤ 2√p (Hasse 1933) | Exact — theorem |

## Smoothness and Factorization

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| B-smooth threshold (16) | 16 | All prime factors ≤ 16 | Medium — 8 too strict, 32 too lenient |
| B-smooth threshold (32) | 32 | Secondary smoothness test | Medium |
| trial division | d² ≤ n | Standard factorization bound | Exact |

## Embedding Degree

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| max_k search | 100 | Maximum embedding degree to test | Medium — real curves have k >> 100 |
| MOV threshold | k ≤ 6 | Low k → MOV/Frey-Rück attack feasible | High — standard cryptographic criterion |

## Test Curves

| Curve | (a,b,p) | Order | a_p | Properties |
|-------|---------|-------|-----|------------|
| secure | (3,2,127) | 139 (prime) | -11 | emb_k=69, ideal |
| pohlig_hellman | (2,3,101) | 96 = 2⁵×3 | 6 | 16-smooth, vulnerable |
| anomalous | (0,5,7) | 7 = p | 1 | Smart's attack applies |
| mov_weak | (0,1,83) | 84 | 0 | Supersingular, emb_k=2 |
| supersingular | (1,0,79) | 80 | 0 | a_p=0, emb_k=2 |

## Spectral Probes

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| probe range | p ± 20 | Primes near the field prime | Medium — wider → more data but slower |
| max probes | 20 | Cap on spectral sample size | Low |
| primality test | trial division to √q | Sufficient for q < 600 | Exact for this range |

## Security Score

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| prime order bonus | +3.0 | Ideal for ECDLP hardness | Medium — relative weighting |
| near-prime (lpf > 0.8) | +2.0 | Near-prime nearly as good | Medium |
| high embedding (k > 20) | +2.0 | Resists MOV attack | Medium |
| non-anomalous | +1.0 | Resists Smart's attack | Medium |
| non-supersingular | +1.0 | Resists pairing attacks | Medium |
| normalization | /7.0 | Scales to [0, 1] | Exact — sum of max bonuses |
| secure threshold | 0.7 | 5+/7 criteria met | Medium |

## Frobenius Eigenvalues

| Constant | Value | Origin | Sensitivity |
|----------|-------|--------|-------------|
| discriminant | a_p² - 4p | Characteristic polynomial x²-a_px+p | Exact |
| complex case (disc < 0) | |λ| = √p | Conjugate pair on circle of radius √p | Exact |

## Numerical Safety

| Constant | Value | Purpose |
|----------|-------|---------|
| 1e-15 | ratio floor | Prevents division by zero |
| 1e-30 | energy floor | Log safety |

## Known Limitations

- Brute-force counting O(p²) limits p to ~500; real curves use p > 2^{200}
- No twist security check, no constant-time implementation audit
- SafeCurves criteria not evaluated (side-channel resistance, complete addition laws, etc.)
- Features demonstrate architecture transfer, not production curve validation
