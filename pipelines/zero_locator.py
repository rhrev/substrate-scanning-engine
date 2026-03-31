#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright (C) 2026 Ricardo Hernández Reveles
"""
Zero Locator Pipeline
=====================

Serie I · Substrate Scanning Engine — STA-Derived Zero Localization

Locates zeros of the Riemann zeta function on the critical line via
STA Phases I+II (modulus scanning + golden-section refinement with
mpmath.altzeta). For other L-functions (Dirichlet, elliptic curve),
zeros must be supplied externally via from_values(); autonomous
localization requires convergent evaluation at sigma=1/2, which partial
sums do not provide.

Input:  Search window [t_min, t_max] (Riemann), or list of mpf values (any L).
Output: List of Zero namedtuples with (gamma, residual, cf_terms, features).

This module imports EulerProduct from geometric_engine.py (abstract base class)
but does NOT modify geometric_engine or its feature vector.

Dependencies: mpmath, numpy.

Derived from: DOI 10.5281/zenodo.18916007 (STA Technical Report, v1.1).
Operates in Canal C (phase channel) of the SSE framework.

Limitations (errata):
  (a) scan() only works for RiemannZeta. The Dirichlet eta function has an
      alternating series converging at sigma=1/2; no analogous convergent
      representation exists in this code for L(s,chi) or L(s,E).
  (b) Phase I (float64) uses raw alternating partial sums. These detect
      valleys by relative ordering but give |eta| ~ 0.04 at zeros, not 0.
      Phase II (mpmath.altzeta) converges to machine epsilon.
  (c) RESIDUAL_THRESHOLD = 1e-3 rejects false valleys. Genuine zeros at
      dps=50 have residual < 1e-30. The threshold is conservative.

Magic numbers documented in pipelines/doc/README_zero_locator.md.
"""

import numpy as np
from collections import namedtuple
from mpmath import mp, mpf, mpc, fabs

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from geometric_engine import EulerProduct, RiemannZeta
from cf_features import CFFeatureExtractor, cf_expansion


# ═══════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

Zero = namedtuple('Zero', ['gamma', 'residual', 'cf_terms', 'features'])
"""
Fields:
  gamma    : mpf   -- imaginary part of the zero
  residual : float -- |eta(1/2 + i*gamma)|; NaN if externally supplied
  cf_terms : list  -- CF expansion [a_0; a_1, ..., a_K]
  features : array -- CF-integer features (F1-F10), shape (10,)
"""


# ═══════════════════════════════════════════════════════════════════
# RIEMANN ETA EVALUATION
# ═══════════════════════════════════════════════════════════════════

def _eta_fast(t_float, M=80):
    """
    Float64 |eta(1/2 + it)| via raw alternating partial sum.

    For Phase I valley DETECTION only. Does not converge to 0 at zeros.
    Relative ordering is preserved: valleys are at correct positions.
    """
    s = complex(0.5, t_float)
    ns = np.arange(1, M + 1, dtype=np.float64)
    signs = np.array([(-1.0) ** (n + 1) for n in range(1, M + 1)])
    return abs(np.sum(signs * np.exp(-s * np.log(ns))))


def _eta_mp(t):
    """
    Arbitrary-precision |eta(1/2 + it)| via mpmath.altzeta.

    Uses Euler-Maclaurin summation internally. Converges to machine
    epsilon at zeros. This is the Phase II evaluator.
    """
    from mpmath import altzeta
    return fabs(altzeta(mpc(mpf('0.5'), t)))


# ═══════════════════════════════════════════════════════════════════
# PHASE I + II (Riemann zeta only)
# ═══════════════════════════════════════════════════════════════════

def _phase_i_scan(t_min, t_max, step=0.05):
    """Sweep and find local minima in |eta(1/2+it)| below 10th percentile."""
    ts = np.arange(t_min, t_max, step)
    vals = np.array([_eta_fast(t) for t in ts])
    threshold = np.quantile(vals, 0.1)
    valleys = []
    for i in range(1, len(vals) - 1):
        if vals[i] < vals[i - 1] and vals[i] < vals[i + 1] and vals[i] < threshold:
            valleys.append(float(ts[i]))
    return valleys


RESIDUAL_THRESHOLD = 1e-3

def _phase_ii_refine(t_approx, dps=100, bracket=0.1, max_iter=200):
    """Golden-section search on |eta| via mpmath.altzeta. Returns (gamma, residual, accepted)."""
    old_dps = mp.dps
    mp.dps = dps + 20
    a = mpf(t_approx) - mpf(bracket)
    b = mpf(t_approx) + mpf(bracket)
    gr = (mpf(1) + mpf(5) ** mpf('0.5')) / 2
    for _ in range(max_iter):
        if b - a < mpf(10) ** (-(dps - 2)):
            break
        c = b - (b - a) / gr
        d = a + (b - a) / gr
        if _eta_mp(c) < _eta_mp(d):
            b = d
        else:
            a = c
    gamma = (a + b) / 2
    residual = float(_eta_mp(gamma))
    mp.dps = old_dps
    return gamma, residual, residual < RESIDUAL_THRESHOLD


# ═══════════════════════════════════════════════════════════════════
# SHARED: ZERO -> FEATURES
# ═══════════════════════════════════════════════════════════════════

def _build_zero(gamma, residual, cf_depth, dps):
    """Build a Zero namedtuple with CF expansion and features."""
    old_dps = mp.dps
    mp.dps = dps + 20
    terms, _, _ = cf_expansion(gamma, max_terms=cf_depth)
    features, _ = CFFeatureExtractor.extract(gamma, K=cf_depth, dps=dps)
    mp.dps = old_dps
    return Zero(gamma=gamma, residual=residual, cf_terms=terms, features=features)


# ═══════════════════════════════════════════════════════════════════
# ZERO LOCATOR CLASS
# ═══════════════════════════════════════════════════════════════════

class ZeroLocator:
    """
    Locate zeros of the Riemann zeta function, or wrap externally-supplied
    zeros of any L-function.

    RiemannZeta:
        loc = ZeroLocator(RiemannZeta())
        zeros = loc.scan(0, 50, dps=100)          # STA Phase I+II
        zeros = loc.scan_mpmath(n_zeros=100)       # mpmath.zetazero

    Other L-functions:
        loc = ZeroLocator(DirichletL(4, chi4))
        zeros = loc.from_values([6.02, 10.24], dps=50)  # external zeros

    scan() and scan_mpmath() raise NotImplementedError for non-Riemann.
    This is an honest limitation: partial sums of L(s,chi) do not converge
    at sigma=1/2. See module docstring errata (a).
    """

    def __init__(self, L):
        self.L = L

    def scan(self, t_min=0, t_max=100, step=0.05, dps=100, cf_depth=50):
        """
        STA Phases I+II for RiemannZeta ONLY.

        Raises NotImplementedError for other L-functions.
        Returns only verified zeros (residual < RESIDUAL_THRESHOLD).
        """
        if not isinstance(self.L, RiemannZeta):
            raise NotImplementedError(
                f"scan() requires RiemannZeta, got {type(self.L).__name__}. "
                f"Use from_values() with externally computed zeros."
            )
        zeros = []
        for t_approx in _phase_i_scan(t_min, t_max, step):
            if t_approx < 1.0:
                continue
            gamma, residual, accepted = _phase_ii_refine(t_approx, dps=dps)
            if accepted:
                zeros.append(_build_zero(gamma, residual, cf_depth, dps))
        return zeros

    def scan_mpmath(self, t_min=0, t_max=None, n_zeros=None, dps=100, cf_depth=50):
        """
        Use mpmath.zetazero for RiemannZeta ONLY.

        Raises NotImplementedError for other L-functions.
        Residual is computed (not fabricated).
        """
        if not isinstance(self.L, RiemannZeta):
            raise NotImplementedError(
                f"scan_mpmath() requires RiemannZeta, got {type(self.L).__name__}. "
                f"Use from_values() with externally computed zeros."
            )
        from mpmath import zetazero
        old_dps = mp.dps
        mp.dps = dps + 20
        zeros = []
        n = 1
        while True:
            gamma = zetazero(n).imag
            if t_max is not None and float(gamma) > t_max:
                break
            if float(gamma) >= t_min:
                residual = float(_eta_mp(gamma))
                zeros.append(_build_zero(gamma, residual, cf_depth, dps))
            n += 1
            if n_zeros is not None and len(zeros) >= n_zeros:
                break
        mp.dps = old_dps
        return zeros

    def from_values(self, gamma_values, dps=100, cf_depth=50):
        """
        Build Zero tuples from externally-supplied zero locations.

        Works for ANY L-function. Caller provides correct zeros.
        Residual is set to NaN (not independently verified by this code).
        """
        old_dps = mp.dps
        mp.dps = dps + 20
        zeros = []
        for g in gamma_values:
            gamma = mpf(g) if not isinstance(g, mpf) else g
            zeros.append(_build_zero(gamma, float('nan'), cf_depth, dps))
        mp.dps = old_dps
        return zeros


# ═══════════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import time

    print("=" * 72)
    print("ZERO LOCATOR — DEMO")
    print("=" * 72)

    mp.dps = 100
    locator = ZeroLocator(RiemannZeta())

    # --- mpmath path ---
    print("\n--- scan_mpmath(n_zeros=5) ---")
    t0 = time.time()
    zeros = locator.scan_mpmath(n_zeros=5, dps=100, cf_depth=25)
    elapsed = time.time() - t0
    print(f"  Found {len(zeros)} zeros in {elapsed:.1f}s")
    for z in zeros:
        print(f"  gamma={float(z.gamma):.10f}, residual={z.residual:.2e}, "
              f"CF[0:5]={z.cf_terms[:5]}")

    # --- STA scan ---
    print("\n--- scan(13, 45, dps=50) ---")
    t0 = time.time()
    zeros_sta = locator.scan(13, 45, dps=50, cf_depth=15)
    elapsed = time.time() - t0
    print(f"  Found {len(zeros_sta)} zeros in {elapsed:.1f}s")
    for z in zeros_sta:
        print(f"  gamma={float(z.gamma):.10f}, residual={z.residual:.2e}")

    # --- from_values for Dirichlet ---
    print("\n--- from_values (Dirichlet L(s,chi_4)) ---")
    from geometric_engine import DirichletL
    loc_dir = ZeroLocator(DirichletL(4, {1: 1.0, 3: -1.0}))
    zeros_dir = loc_dir.from_values([6.0209489, 10.2437703], dps=50, cf_depth=15)
    print(f"  Loaded {len(zeros_dir)} zeros (external)")
    for z in zeros_dir:
        print(f"  gamma={float(z.gamma):.6f}, CF[1:5]={z.cf_terms[1:5]}")

    # --- NotImplementedError ---
    print("\n--- scan() on Dirichlet: correctly raises ---")
    try:
        loc_dir.scan(0, 20)
    except NotImplementedError as e:
        print(f"  NotImplementedError: {e}")

    print("\n" + "=" * 72)
    print("DEMO COMPLETE")
    print("=" * 72)
