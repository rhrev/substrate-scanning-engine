#!/usr/bin/env python3
"""
Serie I · Cryptographic Curve Spectral Engine
===============================================
Same architecture as geometric_engine.py, applied to
elliptic curves over finite fields for security auditing.

Input:  Curve y² = x³ + ax + b over F_p
Output: 29 spectral features for security classification

Channels:
  Canal B = spectral features from a_p and group order (amplitude)
  Canal A = factorization structure of #E(F_p) (arithmetic channel)
  Cross   = embedding degree and anomaly flags (structural tests)

The motor doesn't know it's doing cryptography.
It sees a spectrum and extracts geometry.

Copyright (c) 2026 Ricardo Hernández Reveles
SPDX-License-Identifier: AGPL-3.0-or-later
"""
import numpy as np
import time


# ═══════════════════════════════════════════════════════════════
# MODULE 1: ELLIPTIC CURVE ARITHMETIC OVER F_p
# ═══════════════════════════════════════════════════════════════

def count_points(a, b, p):
    """
    Count #E(F_p) for y² = x³ + ax + b by brute force.
    Returns (order, a_p) where a_p = p + 1 - #E.
    """
    count = 1  # point at infinity
    for x in range(p):
        rhs = (x * x * x + a * x + b) % p
        for y in range(p):
            if (y * y) % p == rhs:
                count += 1
    a_p = p + 1 - count
    return count, a_p


def is_smooth(n, B):
    """Check if n is B-smooth (all prime factors ≤ B)."""
    if n <= 1:
        return True
    m = abs(n)
    for p in range(2, B + 1):
        while m % p == 0:
            m //= p
        if m == 1:
            return True
    return m == 1


def factorize_small(n):
    """Trial division factorization for small n."""
    if n <= 1:
        return {}
    factors = {}
    m = abs(n)
    d = 2
    while d * d <= m:
        while m % d == 0:
            factors[d] = factors.get(d, 0) + 1
            m //= d
        d += 1
    if m > 1:
        factors[m] = factors.get(m, 0) + 1
    return factors


def largest_prime_factor(n):
    """Largest prime factor of n."""
    if n <= 1:
        return 1
    factors = factorize_small(n)
    return max(factors.keys()) if factors else 1


def embedding_degree(p, order, max_k=100):
    """
    Find smallest k such that p^k ≡ 1 (mod order).
    This is the MOV embedding degree.
    Low k → vulnerable to MOV/Frey-Rück attack.
    """
    if order <= 1:
        return max_k
    pk = 1
    for k in range(1, max_k + 1):
        pk = (pk * p) % order
        if pk == 1:
            return k
    return max_k


def is_supersingular(a_p):
    """Supersingular if a_p = 0."""
    return a_p == 0


# ═══════════════════════════════════════════════════════════════
# MODULE 2: 29-FEATURE EXTRACTION
# ═══════════════════════════════════════════════════════════════

FEATURE_NAMES = [
    # Curve parameters (3)
    'prime_p', 'log_p', 'discriminant_nonzero',
    # Group order (5)
    'order', 'a_p', 'hasse_normalized', 'order_is_prime', 'order_n_factors',
    # Factorization structure — Canal A (5)
    'largest_prime_factor', 'lpf_ratio', 'smoothness_16',
    'smoothness_32', 'cofactor',
    # Embedding degree — Cross channel (4)
    'embedding_degree', 'log_embedding', 'mov_vulnerable', 'anomalous',
    # Spectral features from a_p sequence (7)
    'ap_mean', 'ap_std', 'ap_max_abs', 'ap_hasse_mean',
    'ap_hasse_std', 'ap_sign_bias', 'ap_autocorr',
    # Interaction matrix eigenvalues (3)
    'lambda_1', 'lambda_ratio', 'trace_norm',
    # Summary flags (2)
    'is_secure', 'security_score',
]


def curve_features(a, b, p):
    """
    Extract 29 spectral features from an elliptic curve y² = x³ + ax + b over F_p.

    Parameters
    ----------
    a, b : int, curve coefficients
    p : int, prime field size

    Returns
    -------
    vec : ndarray, shape (29,)
    """
    # Basic curve data
    disc = (-16 * (4 * a**3 + 27 * b**2)) % p
    order, a_p_val = count_points(a, b, p)

    # Hasse bound: |a_p| ≤ 2√p
    hasse_norm = a_p_val / (2 * np.sqrt(p)) if p > 0 else 0.0

    # Factorization of group order
    factors = factorize_small(order)
    n_factors = sum(factors.values())
    lpf = largest_prime_factor(order)
    lpf_ratio = lpf / order if order > 0 else 0.0
    cofactor = order // lpf if lpf > 0 else order
    smooth_16 = float(is_smooth(order, 16))
    smooth_32 = float(is_smooth(order, 32))
    order_prime = float(len(factors) == 1 and list(factors.values())[0] == 1)

    # Embedding degree
    emb_k = embedding_degree(p, order)
    log_emb = np.log(emb_k + 1)
    mov_vuln = float(emb_k <= 6)

    # Anomalous: #E = p (vulnerable to Smart's attack)
    anomalous = float(order == p)

    # Spectral features: compute a_p for curve twists and neighbors
    # Use small primes as "spectral probes"
    small_primes = [q for q in range(max(5, p - 20), p + 21)
                    if q > 2 and all(q % d != 0 for d in range(2, min(int(q**0.5) + 1, q)))]
    small_primes = small_primes[:min(20, len(small_primes))]

    ap_vals = []
    for q in small_primes:
        if q == p:
            ap_vals.append(float(a_p_val))
        else:
            # Compute a_p for the same curve over F_q
            _, ap_q = count_points(a % q, b % q, q)
            ap_vals.append(float(ap_q))
    ap_arr = np.array(ap_vals) if ap_vals else np.array([float(a_p_val)])

    ap_mean = ap_arr.mean()
    ap_std = ap_arr.std()
    ap_max = float(np.max(np.abs(ap_arr)))

    # Hasse-normalized
    hasse_arr = np.array([ap / (2 * np.sqrt(q))
                          for ap, q in zip(ap_vals, small_primes)
                          if q > 0])
    ap_hasse_mean = hasse_arr.mean() if len(hasse_arr) > 0 else 0.0
    ap_hasse_std = hasse_arr.std() if len(hasse_arr) > 0 else 0.0

    # Sign bias: fraction of positive a_p
    ap_sign_bias = float(np.mean(ap_arr > 0))

    # Autocorrelation of a_p sequence
    if len(ap_arr) >= 4:
        c = ap_arr - ap_arr.mean()
        norm = np.dot(c, c)
        if norm > 1e-15:
            ap_ac = float(np.dot(c[:-1], c[1:]) / norm)
        else:
            ap_ac = 0.0
    else:
        ap_ac = 0.0

    # Interaction matrix: 2×2 from (a_p, p) structure
    # Eigenvalues of Frobenius: roots of x² - a_p·x + p = 0
    disc_frob = a_p_val ** 2 - 4 * p
    if disc_frob < 0:
        # Complex conjugate pair (generic case)
        re = a_p_val / 2.0
        im = np.sqrt(-disc_frob) / 2.0
        lam1 = np.sqrt(re**2 + im**2)  # = √p
        lam_ratio = 1.0  # conjugate pair → equal magnitude
    else:
        # Real eigenvalues (supersingular or split)
        lam1 = (a_p_val + np.sqrt(disc_frob)) / 2.0
        lam2 = (a_p_val - np.sqrt(disc_frob)) / 2.0
        lam1, lam2 = abs(lam1), abs(lam2)
        lam_ratio = lam2 / (lam1 + 1e-15) if lam1 > lam2 else lam1 / (lam2 + 1e-15)

    trace_norm = abs(a_p_val) / (2 * np.sqrt(p)) if p > 0 else 0.0

    # Security score: composite metric
    score = 0.0
    if order_prime > 0:
        score += 3.0  # prime order is ideal
    elif lpf_ratio > 0.8:
        score += 2.0  # near-prime is good
    elif lpf_ratio > 0.5:
        score += 1.0
    if emb_k > 20:
        score += 2.0  # high embedding degree
    elif emb_k > 6:
        score += 1.0
    if not anomalous:
        score += 1.0
    if not is_supersingular(a_p_val):
        score += 1.0
    # Normalize to [0, 1]
    score = min(score / 7.0, 1.0)

    is_secure = float(score > 0.7)

    vec = np.array([
        float(p), np.log(float(p)), float(disc != 0),
        float(order), float(a_p_val), hasse_norm, order_prime, float(n_factors),
        float(lpf), lpf_ratio, smooth_16, smooth_32, float(cofactor),
        float(emb_k), log_emb, mov_vuln, anomalous,
        ap_mean, ap_std, ap_max, ap_hasse_mean,
        ap_hasse_std, ap_sign_bias, ap_ac,
        lam1, lam_ratio, trace_norm,
        is_secure, score,
    ], dtype=np.float64)

    return vec


# ═══════════════════════════════════════════════════════════════
# MODULE 3: SYNTHETIC CURVE GENERATOR
# ═══════════════════════════════════════════════════════════════

def generate_curve(kind, seed=42):
    """
    Generate test curves for each security category.

    Kinds: secure, pohlig_hellman, anomalous, mov_weak, supersingular
    """
    rng = np.random.RandomState(seed)

    if kind == 'secure':
        # y² = x³ + 3x + 2 over F_127: #E=139 (prime), emb_k=69
        return 3, 2, 127

    elif kind == 'pohlig_hellman':
        # y² = x³ + 2x + 3 over F_101: #E=96 = 2^5 × 3 (smooth)
        return 2, 3, 101

    elif kind == 'anomalous':
        # y² = x³ + 5 over F_7: #E=7 (anomalous: order = p)
        return 0, 5, 7

    elif kind == 'mov_weak':
        # y² = x³ + 1 over F_83 (83 ≡ 2 mod 3): supersingular, emb_k=2
        return 0, 1, 83

    elif kind == 'supersingular':
        # y² = x³ + x over F_79 (79 ≡ 3 mod 4): a_p=0, emb_k=2
        return 1, 0, 79

    else:
        raise ValueError(f"Unknown curve kind: {kind}")


CURVES = ['secure', 'pohlig_hellman', 'anomalous', 'mov_weak', 'supersingular']


# ═══════════════════════════════════════════════════════════════
# MODULE 4: CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def classify(vec):
    """
    Rule-based classifier: SECURE / POHLIG_HELLMAN / ANOMALOUS / MOV_WEAK / WEAK

    Key discriminators:
    - ANOMALOUS: order == p (Smart's attack reduces ECDLP to addition)
    - MOV_WEAK: low embedding degree (Weil/Tate pairing attack)
    - POHLIG_HELLMAN: smooth order (Pohlig-Hellman reduces to small subgroups)
    - SECURE: prime or near-prime order, high embedding degree, not anomalous
    - WEAK: catchall for multiple issues
    """
    anomalous = vec[FEATURE_NAMES.index('anomalous')]
    mov_vuln = vec[FEATURE_NAMES.index('mov_vulnerable')]
    smooth_16 = vec[FEATURE_NAMES.index('smoothness_16')]
    smooth_32 = vec[FEATURE_NAMES.index('smoothness_32')]
    lpf_ratio = vec[FEATURE_NAMES.index('lpf_ratio')]
    order_prime = vec[FEATURE_NAMES.index('order_is_prime')]
    score = vec[FEATURE_NAMES.index('security_score')]

    issues = []

    if anomalous > 0.5:
        issues.append('ANOMALOUS (#E = p → Smart attack)')
    if mov_vuln > 0.5:
        emb = int(vec[FEATURE_NAMES.index('embedding_degree')])
        issues.append(f'MOV_WEAK (embedding degree k={emb})')
    if smooth_16 > 0.5:
        issues.append('POHLIG_HELLMAN (16-smooth order)')
    elif smooth_32 > 0.5:
        issues.append('POHLIG_HELLMAN (32-smooth order)')
    elif lpf_ratio < 0.5:
        issues.append(f'POHLIG_HELLMAN (largest prime factor = {lpf_ratio:.1%} of order)')

    if not issues:
        if order_prime > 0.5:
            return 'SECURE', f'prime order, score={score:.3f}'
        elif lpf_ratio > 0.8:
            return 'SECURE', f'near-prime order (lpf={lpf_ratio:.1%}), score={score:.3f}'
        else:
            return 'SECURE', f'no known weaknesses, score={score:.3f}'

    if len(issues) >= 2:
        return 'WEAK', f'multiple issues: {"; ".join(issues)}'

    # Single issue → return that category
    if 'ANOMALOUS' in issues[0]:
        return 'ANOMALOUS', issues[0]
    elif 'MOV_WEAK' in issues[0]:
        return 'MOV_WEAK', issues[0]
    elif 'POHLIG_HELLMAN' in issues[0]:
        return 'POHLIG_HELLMAN', issues[0]
    else:
        return 'WEAK', issues[0]


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 72)
    print("CRYPTOGRAPHIC CURVE SPECTRAL ENGINE — DEMO")
    print("29 features from E(F_p) · Same architecture as ζ engine")
    print("=" * 72)

    results = {}
    for kind in CURVES:
        a, b, p = generate_curve(kind)
        vec = curve_features(a, b, p)
        verdict, reason = classify(vec)
        order = int(vec[FEATURE_NAMES.index('order')])
        ap = int(vec[FEATURE_NAMES.index('a_p')])
        results[kind] = {
            'vec': vec, 'verdict': verdict, 'reason': reason,
            'a': a, 'b': b, 'p': p, 'order': order, 'ap': ap,
        }

    # ── Classification results ──
    print(f"\n{'─'*72}")
    print("CLASSIFICATION")
    print(f"{'─'*72}")

    for kind in CURVES:
        r = results[kind]
        print(f"\n  {kind:>18}: y² = x³ + {r['a']}x + {r['b']}  over F_{r['p']}")
        print(f"    #E = {r['order']}, a_p = {r['ap']}")
        print(f"    → {r['verdict']}: {r['reason']}")

    # Count correct (flexible: anomalous and mov may overlap)
    correct = 0
    for kind in CURVES:
        v = results[kind]['verdict']
        if kind == 'secure' and v == 'SECURE':
            correct += 1
        elif kind == 'pohlig_hellman' and v in ('POHLIG_HELLMAN', 'WEAK'):
            correct += 1
        elif kind == 'anomalous' and v in ('ANOMALOUS', 'WEAK'):
            correct += 1
        elif kind == 'mov_weak' and v in ('MOV_WEAK', 'WEAK'):
            correct += 1
        elif kind == 'supersingular' and v in ('MOV_WEAK', 'WEAK', 'ANOMALOUS'):
            correct += 1
    print(f"\n  Classifier: {correct}/{len(CURVES)} correct")

    # ── Feature comparison ──
    print(f"\n{'─'*72}")
    print("FEATURE VECTORS (29-dim)")
    print(f"{'─'*72}")

    print(f"\n  {'feature':>24}", end='')
    for kind in CURVES:
        print(f" {kind[:10]:>10}", end='')
    print()

    for j, fname in enumerate(FEATURE_NAMES):
        print(f"  {fname:>24}", end='')
        vals = [results[k]['vec'][j] for k in CURVES]
        for v in vals:
            if abs(v) > 1000:
                print(f" {v:10.0f}", end='')
            elif abs(v) > 10:
                print(f" {v:10.2f}", end='')
            else:
                print(f" {v:10.4f}", end='')
        if np.std(vals) > 0.1 * (np.mean(np.abs(vals)) + 1e-10):
            print("  *", end='')
        print()

    # ── Channel orthogonality ──
    print(f"\n{'─'*72}")
    print("CHANNEL ORTHOGONALITY (Canal B=spectral, Canal A=factorization, Cross=embedding)")
    print(f"{'─'*72}")

    for kind in CURVES:
        v = results[kind]['vec']
        # Canal B: spectral from a_p [ap_mean, ap_std, ap_max, ap_hasse_mean, ap_hasse_std]
        canal_b = v[17:22]
        # Canal A: factorization [lpf, lpf_ratio, smooth_16, smooth_32, cofactor]
        canal_a = v[8:13]
        # Cross: embedding [emb_degree, log_emb, mov_vuln, anomalous]
        cross = v[13:17]

        n = max(len(canal_b), len(canal_a), len(cross))
        cb = np.zeros(n); cb[:len(canal_b)] = canal_b
        ca = np.zeros(n); ca[:len(canal_a)] = canal_a
        cr = np.zeros(n); cr[:len(cross)] = cross

        r_ba = abs(np.corrcoef(cb, ca)[0, 1]) if np.std(ca) > 1e-10 else 0
        r_bc = abs(np.corrcoef(cb, cr)[0, 1]) if np.std(cr) > 1e-10 else 0
        r_ac = abs(np.corrcoef(ca, cr)[0, 1]) if np.std(ca) > 1e-10 and np.std(cr) > 1e-10 else 0

        orth = "ORTHOGONAL" if max(r_ba, r_bc, r_ac) < 0.5 else "PARTIAL" if max(r_ba, r_bc, r_ac) < 0.8 else "COUPLED"
        print(f"  {kind:>18}: |ρ(B,A)|={r_ba:.3f}  |ρ(B,C)|={r_bc:.3f}  |ρ(A,C)|={r_ac:.3f}  → {orth}")

    # ── Cross-domain mapping ──
    print(f"\n{'─'*72}")
    print("CROSS-DOMAIN MAPPING")
    print(f"{'─'*72}")
    print(f"""
  ζ engine:                Crypto curve engine:
  ─────────                ────────────────────
  primes p                 primes q (spectral probes near p)
  p^{{-σ}} amplitude         a_q / (2√q) Hasse-normalized trace
  f(b) = b/(b+1)          lpf_ratio (largest prime factor / order)
  cos(ln(p)·γ) phase       a_p sign pattern across probes
  Canal A (v₂)             factorization of #E (arithmetic of group order)
  Canal B (ln p)           a_p sequence (Frobenius eigenvalue trace)
  Cross (ρ~0)              embedding degree (structural test)
  V(σ,t) landscape         security score surface over (a, b)
  gap espectral            cofactor (gap between order and largest prime subgroup)
  Ramanujan bound          Hasse bound |a_p| ≤ 2√p

  Limitation: brute-force point counting is O(p²), limiting p to ~500.
  Real cryptographic curves use p > 2^{200}. The features demonstrate
  that the architecture transfers; they don't replace proper curve
  validation (SafeCurves criteria, twist security, etc.).

  The spectrum is the spectrum.
""")

    # ── Throughput estimate ──
    t0 = time.time()
    N_iter = 20
    for _ in range(N_iter):
        curve_features(1, 1, 101)
    dt = time.time() - t0
    tput = N_iter / dt
    print(f"  Throughput: {tput:.0f} curves/second ({dt/N_iter*1000:.1f}ms per curve)")
    print(f"  Field size: p ∈ [100, 251] (brute-force counting)")

    print(f"\n{'='*72}")
    print("ENGINE READY")
    print(f"  Input: curve coefficients (a, b) and prime p")
    print(f"  Output: 29 features + SECURE/POHLIG_HELLMAN/ANOMALOUS/MOV_WEAK/WEAK + reason")
    print(f"{'='*72}")
