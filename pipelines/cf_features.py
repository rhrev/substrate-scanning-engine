#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Ricardo Hernández Reveles
"""
CF-Integer Feature Extraction Pipeline
=======================================

Serie I · Substrate Scanning Engine — Parallel Analysis Channel

Extracts 10 per-eigenvalue features (F1–F10) and 4 cross-eigenvalue features
(C1–C4) from continued fraction coefficients of real numbers (eigenvalues,
zeros, frequencies).

Input:  A real number (or sequence of reals) at arbitrary precision (mpmath mpf).
Output: Feature vector of length 10 per eigenvalue; pairwise matrix for C1–C4.

This module is INDEPENDENT of geometric_engine.py.  It does not import
GeometricEngine, does not modify the 31-feature vector, and has its own
feature_names() method.  See the improvement plan (Report D) for the
architectural rationale (Option B: parallel pipeline).

Dependencies: mpmath, numpy, scipy (for KS test and Spearman).

Terminology:
  - "CF coefficient" or "partial quotient": the integer a_k in [a_0; a_1, ...]
  - NOT "Fourier coefficient" or "expansion coefficient" in any other sense.

Magic numbers are documented in pipelines/doc/README_cf_features.md.
"""

import numpy as np
from mpmath import mp, mpf, floor as mfloor, fabs, log as mlog
from scipy.stats import kstest, spearmanr
from math import log2, log10, gcd

# ═══════════════════════════════════════════════════════════════════
# CF EXPANSION
# ═══════════════════════════════════════════════════════════════════

def cf_expansion(x, max_terms=50, min_remainder=None):
    """
    Compute continued fraction expansion [a_0; a_1, ..., a_K] and convergents.

    Parameters
    ----------
    x : mpf
        The real number to expand.  Must be mpmath mpf at desired precision.
    max_terms : int
        Maximum CF terms to compute.
    min_remainder : mpf or None
        Stop when fractional part < this.  Default: 10^{-(mp.dps - 10)}.

    Returns
    -------
    terms : list of int
        CF partial quotients [a_0, a_1, ..., a_K].
    convergents : list of (mpf, mpf)
        Pairs (p_k, q_k) for each convergent.
    errors : list of mpf
        |x - p_k/q_k| for each convergent.
    """
    if min_remainder is None:
        min_remainder = mpf(10) ** (-(mp.dps - 10))

    terms = []
    convergents = []
    errors = []

    # Convergent recurrence: p_{-1}=1, p_{-2}=0; q_{-1}=0, q_{-2}=1
    p_prev, p_curr = mpf(0), mpf(1)
    q_prev, q_curr = mpf(1), mpf(0)

    r = x
    for k in range(max_terms):
        a = int(mfloor(r))
        terms.append(a)

        p_new = a * p_curr + p_prev
        q_new = a * q_curr + q_prev
        convergents.append((p_new, q_new))

        err = fabs(x - p_new / q_new) if q_new > 0 else fabs(x)
        errors.append(err)

        p_prev, p_curr = p_curr, p_new
        q_prev, q_curr = q_curr, q_new

        frac = r - a
        if frac < min_remainder:
            break
        r = mpf(1) / frac

    return terms, convergents, errors


# ═══════════════════════════════════════════════════════════════════
# GAUSS-KUZMIN DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════

# Retained for: public API (complements gauss_kuzmin_pmf for external callers)
def gauss_kuzmin_cdf(k):
    """CDF of the Gauss-Kuzmin distribution: P(a <= k) = 1 - log2(1 + 1/(k+1))."""
    return 1.0 - log2(1.0 + 1.0 / (k + 1))

def gauss_kuzmin_pmf(k):
    """PMF: P(a = k) = log2(1 + 1/(k*(k+2)))."""
    return log2(1.0 + 1.0 / (k * (k + 2)))

# Precomputed constants under GK distribution
GK_P_LARGE_10 = sum(gauss_kuzmin_pmf(k) for k in range(11, 10001))  # ~0.1254
GK_P_ODD = sum(gauss_kuzmin_pmf(k) for k in range(1, 10001, 2))     # ~0.6514
GK_P_PRIME = 0.0  # Compute on init
_small_primes = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47,
                 53, 59, 61, 67, 71, 73, 79, 83, 89, 97}
for _p in _small_primes:
    GK_P_PRIME += gauss_kuzmin_pmf(_p)
# Add tail estimate for primes > 100
for _k in range(101, 10001):
    if all(_k % _p != 0 for _p in range(2, min(int(_k**0.5) + 1, 100))):
        GK_P_PRIME += gauss_kuzmin_pmf(_k)


# ═══════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def _v2(n):
    """2-adic valuation of integer n."""
    if n == 0:
        return 0
    v = 0
    while n % 2 == 0:
        v += 1
        n //= 2
    return v

def _is_prime(n):
    """Simple primality test for small n."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


# ═══════════════════════════════════════════════════════════════════
# PER-EIGENVALUE FEATURES (F1–F10)
# ═══════════════════════════════════════════════════════════════════

class CFFeatureExtractor:
    """
    Extract 10 deterministic features from the CF partial quotients of a
    real number.

    Features (computed from a_1, ..., a_K — a_0 is EXCLUDED to avoid
    magnitude leakage; see §0.3 of STA v1.1):

      F1  gk_deviation    : reduced chi-squared vs Gauss-Kuzmin distribution
      F2  levy_exponent   : log2(q_K)/(K-1) — Khinchin-Lévy exponent (NOT bits/term; multiply by 2 for bits)
      F3  large_a_freq    : fraction of a_k > 10
      F4  adic2_depth     : mean v_2(a_k)
      F5  odd_even_ratio  : fraction of odd a_k
      F6  prime_fraction  : fraction of prime a_k
      F7  consec_corr     : Spearman rho(a_k, a_{k+1})
      F8  run_length_1    : mean length of consecutive runs where a_k = 1
      F9  max_coeff       : max(a_k)
      F10 digit_mod       : chi-squared statistic of a_k mod 3

    EXCLUDED feature (documented per QA §4):
      a_0 — directly encodes eigenvalue magnitude (floor(gamma)).
             Including it leaks the label in any classification task.
             Empirical evidence: Spearman rho(a_0, gamma) = 1.000.
             Theoretical cause: a_0 = floor(gamma) by definition.
    """

    # Feature names (fixed order, stable across versions)
    NAMES = [
        'gk_deviation',   # F1 (reduced chi-squared vs GK)
        'levy_exponent',  # F2
        'large_a_freq',   # F3
        'adic2_depth',    # F4
        'odd_even_ratio', # F5
        'prime_fraction', # F6
        'consec_corr',    # F7
        'run_length_1',   # F8
        'max_coeff',      # F9
        'digit_mod',      # F10
    ]

    @staticmethod
    def feature_names():
        """Return ordered list of 10 feature names."""
        return list(CFFeatureExtractor.NAMES)

    @staticmethod
    def extract(x, K=50, dps=None):
        """
        Extract 10 CF features from a real number x.

        Parameters
        ----------
        x : float or mpf
            The eigenvalue / zero / frequency to analyze.
        K : int
            Maximum number of CF terms to extract.
        dps : int or None
            mpmath decimal places.  If None, uses current mp.dps.

        Returns
        -------
        features : np.ndarray of shape (10,)
            Feature vector [F1, ..., F10].
        terms : list of int
            The CF partial quotients (for downstream use).
        """
        if dps is not None:
            old_dps = mp.dps
            mp.dps = dps

        x_mp = mpf(x) if not isinstance(x, mpf) else x
        terms, convergents, errors = cf_expansion(x_mp, max_terms=K + 1)

        if dps is not None:
            mp.dps = old_dps

        # Work with a_1, ..., a_K (exclude a_0)
        coeffs = terms[1:] if len(terms) > 1 else []
        n = len(coeffs)

        if n < 3:
            return np.full(10, np.nan), terms

        coeffs_arr = np.array(coeffs, dtype=np.float64)

        # F1: GK deviation (chi-squared on binned counts, not KS)
        # KS is inappropriate for discrete distributions (pilot bug #1).
        # Bin coefficients into a_k = 1, 2, 3, ..., 10, 11+
        bins = np.zeros(11)  # bins[0]=count(a=1), ..., bins[9]=count(a=10), bins[10]=count(a>=11)
        for a in coeffs:
            idx = min(int(a) - 1, 10)
            if idx >= 0:
                bins[idx] += 1
        # Expected counts under GK
        expected = np.zeros(11)
        for k in range(1, 11):
            expected[k - 1] = n * gauss_kuzmin_pmf(k)
        expected[10] = n * sum(gauss_kuzmin_pmf(k) for k in range(11, 201))
        # Merge bins with expected < 5 (chi-sq validity)
        mask = expected >= 3
        if mask.sum() >= 3:
            chi2 = float(np.sum((bins[mask] - expected[mask]) ** 2 / expected[mask]))
            dof = mask.sum() - 1
            f1_gk = chi2 / max(dof, 1)  # reduced chi-squared
        else:
            f1_gk = np.nan

        # F2: Lévy rate — (1/(K-1)) * log2(q_K)
        if len(convergents) > 1:
            q_K = convergents[-1][1]
            if q_K > 0:
                f2_levy = float(mlog(q_K, 2)) / (len(convergents) - 1)
            else:
                f2_levy = 0.0
        else:
            f2_levy = 0.0

        # F3: large-a frequency (a > 10)
        f3_large = float(np.sum(coeffs_arr > 10)) / n

        # F4: mean 2-adic depth
        f4_v2 = np.mean([_v2(int(a)) for a in coeffs])

        # F5: odd/even ratio
        f5_odd = float(np.sum(coeffs_arr % 2 == 1)) / n

        # F6: prime fraction
        f6_prime = sum(1 for a in coeffs if _is_prime(int(a))) / n

        # F7: consecutive correlation
        if n > 3:
            rho, _ = spearmanr(coeffs_arr[:-1], coeffs_arr[1:])
            f7_corr = float(rho) if not np.isnan(rho) else 0.0
        else:
            f7_corr = 0.0

        # F8: mean run length of 1s
        runs = []
        current_run = 0
        for a in coeffs:
            if a == 1:
                current_run += 1
            else:
                if current_run > 0:
                    runs.append(current_run)
                current_run = 0
        if current_run > 0:
            runs.append(current_run)
        f8_run = np.mean(runs) if runs else 0.0

        # F9: max coefficient
        f9_max = float(np.max(coeffs_arr))

        # F10: chi-squared of a_k mod 3 against GK mod-3 distribution
        # GK mod 3 is NOT uniform: P(1)≈0.547, P(2)≈0.274, P(0)≈0.179
        mod3_counts = np.zeros(3)
        for a in coeffs:
            mod3_counts[int(a) % 3] += 1
        # Compute expected from GK PMF (not uniform)
        gk_mod3 = np.zeros(3)
        for k in range(1, 201):
            gk_mod3[k % 3] += gauss_kuzmin_pmf(k)
        gk_mod3 /= gk_mod3.sum()  # normalize (tail correction)
        expected = n * gk_mod3
        # Chi-squared with GK null
        mask_f10 = expected > 3
        if mask_f10.sum() >= 2:
            f10_chi2 = float(np.sum((mod3_counts[mask_f10] - expected[mask_f10]) ** 2
                                     / expected[mask_f10]))
        else:
            f10_chi2 = np.nan

        features = np.array([
            f1_gk, f2_levy, f3_large, f4_v2, f5_odd,
            f6_prime, f7_corr, f8_run, f9_max, f10_chi2
        ])

        return features, terms

    @staticmethod
    def feature_vector(x, K=50, dps=None):
        """Convenience: return only the feature array."""
        features, _ = CFFeatureExtractor.extract(x, K, dps)
        return features


# ═══════════════════════════════════════════════════════════════════
# CROSS-EIGENVALUE FEATURES (C1–C4)
# ═══════════════════════════════════════════════════════════════════

class CrossCFFeatures:
    """
    Compute 4 pairwise features between CF expansions of two eigenvalues.

    Features:
      C1  cross_corr      : Spearman rho(a_k(x1), a_k(x2)) at same depth k
      C2  shared_large    : fraction of k where both a_k > 10
      C3  gcd_coprime     : fraction of k where gcd(a_k(x1), a_k(x2)) = 1
      C4  mod_mutual_info : mutual information of a_k mod 3 between x1, x2
    """

    NAMES = ['cross_corr', 'shared_large', 'gcd_coprime', 'mod_mutual_info']

    @staticmethod
    def feature_names():
        return list(CrossCFFeatures.NAMES)

    @staticmethod
    def extract(terms1, terms2):
        """
        Compute C1–C4 from two CF term sequences (excluding a_0).

        Parameters
        ----------
        terms1, terms2 : list of int
            CF partial quotients [a_0, a_1, ...] from cf_expansion().

        Returns
        -------
        features : np.ndarray of shape (4,)
        """
        # Exclude a_0, align lengths
        c1 = terms1[1:]
        c2 = terms2[1:]
        K = min(len(c1), len(c2))
        if K < 3:
            return np.full(4, np.nan)

        a1 = np.array(c1[:K], dtype=np.float64)
        a2 = np.array(c2[:K], dtype=np.float64)

        # C1: cross-correlation at same depth
        rho, _ = spearmanr(a1, a2)
        c1_corr = float(rho) if not np.isnan(rho) else 0.0

        # C2: shared large (both > 10)
        c2_shared = float(np.sum((a1 > 10) & (a2 > 10))) / K

        # C3: coprime fraction
        coprime_count = sum(1 for i in range(K) if gcd(int(a1[i]), int(a2[i])) == 1)
        c3_coprime = coprime_count / K

        # C4: mutual information of a_k mod 3
        mod1 = (a1.astype(int) % 3)
        mod2 = (a2.astype(int) % 3)
        joint = np.zeros((3, 3))
        for i in range(K):
            joint[mod1[i], mod2[i]] += 1
        joint /= K
        marg1 = joint.sum(axis=1)
        marg2 = joint.sum(axis=0)
        mi = 0.0
        for i in range(3):
            for j in range(3):
                if joint[i, j] > 1e-15 and marg1[i] > 1e-15 and marg2[j] > 1e-15:
                    mi += joint[i, j] * log2(joint[i, j] / (marg1[i] * marg2[j]))
        c4_mi = mi

        return np.array([c1_corr, c2_shared, c3_coprime, c4_mi])


# ═══════════════════════════════════════════════════════════════════
# BATCH ANALYSIS
# ═══════════════════════════════════════════════════════════════════

def batch_features(eigenvalues, K=50, dps=100):
    """
    Compute per-eigenvalue and cross-eigenvalue features for a list.

    Parameters
    ----------
    eigenvalues : list of float or mpf
        The values to analyze.
    K : int
        CF depth.
    dps : int
        mpmath precision.

    Returns
    -------
    per_features : np.ndarray of shape (N, 10)
    cross_features : np.ndarray of shape (N*(N-1)/2, 4)
    all_terms : list of list of int
    """
    mp.dps = dps
    N = len(eigenvalues)

    per_features = np.zeros((N, 10))
    all_terms = []

    for i, ev in enumerate(eigenvalues):
        feats, terms = CFFeatureExtractor.extract(ev, K=K)
        per_features[i] = feats
        all_terms.append(terms)

    # Cross features
    n_pairs = N * (N - 1) // 2
    cross_features = np.zeros((n_pairs, 4))
    idx = 0
    for i in range(N):
        for j in range(i + 1, N):
            cross_features[idx] = CrossCFFeatures.extract(
                all_terms[i], all_terms[j]
            )
            idx += 1

    return per_features, cross_features, all_terms


# ═══════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from mpmath import zetazero

    print("=" * 72)
    print("CF-INTEGER FEATURE EXTRACTION — DEMO")
    print("=" * 72)

    mp.dps = 120
    N_ZEROS = 8
    K = 50

    zeros = [zetazero(n).imag for n in range(1, N_ZEROS + 1)]
    print(f"\n  Zeros: {N_ZEROS}")
    print(f"  Precision: {mp.dps} digits")
    print(f"  CF depth: {K} terms")
    print(f"  Feature dimension: {len(CFFeatureExtractor.feature_names())}")
    print(f"  Features: {', '.join(CFFeatureExtractor.feature_names())}")

    per_f, cross_f, all_t = batch_features(zeros, K=K, dps=120)

    print(f"\n  Per-eigenvalue features: shape {per_f.shape}")
    print(f"  Cross-eigenvalue features: shape {cross_f.shape}")

    print("\n  Per-eigenvalue results:")
    names = CFFeatureExtractor.feature_names()
    for i in range(N_ZEROS):
        print(f"\n    gamma_{i+1} = {float(zeros[i]):.6f}")
        print(f"    CF[1:6] = {all_t[i][1:6]}")
        for j, name in enumerate(names):
            print(f"      {name:18s} = {per_f[i, j]:.4f}")

    print(f"\n  Cross-eigenvalue summary (mean over {cross_f.shape[0]} pairs):")
    cnames = CrossCFFeatures.feature_names()
    for j, name in enumerate(cnames):
        vals = cross_f[:, j]
        print(f"    {name:20s}: mean={np.nanmean(vals):.4f}, "
              f"std={np.nanstd(vals):.4f}")

    # Trivial proxy check (QA §6a)
    print("\n  TRIVIAL PROXY CHECK (QA §6a):")
    gamma_arr = np.array([float(z) for z in zeros])
    for j, name in enumerate(names):
        rho, p = spearmanr(per_f[:, j], gamma_arr)
        status = "LEAKAGE" if abs(rho) > 0.95 else "PASS"
        print(f"    rho({name}, gamma) = {rho:+.3f}  p={p:.3f}  [{status}]")

    print("\n" + "=" * 72)
    print("DEMO COMPLETE")
    print("=" * 72)
