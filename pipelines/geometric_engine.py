#!/usr/bin/env python3
# Copyright (c) 2026 Ricardo Hernández Reveles
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Serie I · Geometric Parameter Generator for L-functions
========================================================
A modular engine that takes any Euler product and produces
geometric parameters for non-statistical ML.

Input:  Euler factors {(p, α_p)} or {(p, χ(p))} or {(p, a_p)}
Output: Geometric feature tensor per (s, K) query point

The parameters are NOT learned from data — they are computed
from the geometry of the Euler product. ML operates on top
of this geometric substrate.

Modules:
  1. EulerProduct — abstract base, concrete for ζ, L(s,χ), L(s,E)
  2. ToroidalEmbedding — p^{-s} → torus coordinates
  3. ThreeScales — drift / spiral / CF decomposition
  4. EnvelopeDecomposition — f(b) × cos(ω) factorization
  5. PotentialLandscape — V(σ,t) and Laplacian
  6. WeilSpectrum — discretized quadratic form
  7. ChannelOrthogonality — A/B/C independence test
  8. GeometricFeatureVector — combined output for ML

Usage:
  engine = GeometricEngine(RiemannZeta())
  features = engine.query(sigma=0.5, t=14.13, K=30)
  # features is a dict with ~40 geometric parameters
  # ready for any ML pipeline (no statistical assumptions)
"""

import numpy as np
from numpy.linalg import eigh, lstsq, norm
from scipy.stats import spearmanr
from abc import ABC, abstractmethod
import json, time


# ═══════════════════════════════════════════════════════════════════
# MODULE 1: EULER PRODUCT (abstract + concrete implementations)
# ═══════════════════════════════════════════════════════════════════

class EulerProduct(ABC):
    """Abstract Euler product: Π_p (local factor at p)^{-1}"""
    
    @abstractmethod
    def primes(self, K):
        """Return first K primes relevant to this L-function"""
        pass
    
    @abstractmethod
    def local_factor(self, p, s):
        """Return (1 - α_p · p^{-s})^{-1} as complex number"""
        pass
    
    @abstractmethod
    def log_deriv_term(self, p, s):
        """Return ln(p) · α_p · p^{-s} / (1 - α_p · p^{-s})"""
        pass
    
    @abstractmethod
    def arithmetic_channel(self, p):
        """Return Canal A features for prime p (arithmetic of p-1, χ(p), a_p, etc.)"""
        pass
    
    @property
    @abstractmethod
    def name(self):
        pass


class RiemannZeta(EulerProduct):
    """ζ(s) = Π_p (1 - p^{-s})^{-1}"""
    
    def __init__(self, max_prime=1500):
        s = np.ones(max_prime+1, dtype=bool); s[0]=s[1]=False
        for i in range(2, int(max_prime**0.5)+1):
            if s[i]: s[i*i::i] = False
        self._primes = np.where(s)[0]
        self._ln = np.log(self._primes.astype(np.float64))
    
    @property
    def name(self): return "ζ(s)"
    
    def primes(self, K):
        return self._primes[:K]
    
    def ln_primes(self, K):
        return self._ln[:K]
    
    def local_factor(self, p, s):
        ps = complex(p)**(-s)
        return 1.0 / (1.0 - ps)
    
    def log_deriv_term(self, p, s):
        lnp = np.log(p)
        ps = complex(p)**(-s)
        return lnp * ps / (1.0 - ps)
    
    def arithmetic_channel(self, p):
        """Canal A: v₂(p-1), ord₂(p)/(p-1)"""
        pm1 = int(p) - 1
        v2 = 0
        n = pm1
        while n % 2 == 0: v2 += 1; n //= 2
        # ord_2(p)
        r, x = 1, 2 % int(p)
        if x == 0: ord2 = 0
        else:
            cur = x
            while cur != 1:
                cur = (cur * x) % int(p); r += 1
                if r > p: r = 0; break
            ord2 = r
        return {'v2_pm1': float(v2), 'ord2_ratio': float(ord2)/float(pm1) if pm1 > 0 else 0.0}


class DirichletL(EulerProduct):
    """L(s, χ) = Π_p (1 - χ(p)·p^{-s})^{-1}"""
    
    def __init__(self, q, chi_values, max_prime=1500):
        """q: modulus, chi_values: dict {a: χ(a)} for (a,q)=1"""
        self.q = q
        self.chi = chi_values
        s = np.ones(max_prime+1, dtype=bool); s[0]=s[1]=False
        for i in range(2, int(max_prime**0.5)+1):
            if s[i]: s[i*i::i] = False
        self._primes = np.where(s)[0]
        self._ln = np.log(self._primes.astype(np.float64))
    
    @property
    def name(self): return f"L(s,χ_{self.q})"
    
    def primes(self, K): return self._primes[:K]
    def ln_primes(self, K): return self._ln[:K]
    
    def _chi(self, p):
        p_mod = int(p) % self.q
        return self.chi.get(p_mod, 0.0)
    
    def local_factor(self, p, s):
        chi_p = self._chi(p)
        ps = complex(p)**(-s)
        return 1.0 / (1.0 - chi_p * ps)
    
    def log_deriv_term(self, p, s):
        lnp = np.log(p)
        chi_p = self._chi(p)
        ps = complex(p)**(-s)
        return lnp * chi_p * ps / (1.0 - chi_p * ps)
    
    def arithmetic_channel(self, p):
        return {'chi_p': self._chi(p), 'p_mod_q': float(int(p) % self.q)}


class EllipticCurveL(EulerProduct):
    """
    L(s, E) = Π_p (1 - a_p·p^{-s} + p^{1-2s})^{-1}  (good reduction)
    
    a_p = p + 1 - #E(F_p)
    
    For small p: brute-force point counting.
    For large p: supply precomputed a_p (e.g. from LMFDB).
    """
    
    def __init__(self, a, b, label="E", max_prime=500, ap_table=None):
        """
        y² = x³ + ax + b
        ap_table: optional dict {p: a_p} for precomputed coefficients
        """
        self.a_coeff = a
        self.b_coeff = b
        self.label = label
        
        s = np.ones(max_prime+1, dtype=bool); s[0]=s[1]=False
        for i in range(2, int(max_prime**0.5)+1):
            if s[i]: s[i*i::i] = False
        self._primes = np.where(s)[0]
        self._ln = np.log(self._primes.astype(np.float64))
        
        # Precompute a_p
        self._ap = {}
        for p in self._primes:
            if ap_table and int(p) in ap_table:
                self._ap[int(p)] = ap_table[int(p)]
            elif self._is_bad(int(p)):
                self._ap[int(p)] = 0
            else:
                self._ap[int(p)] = self._count_ap(int(p))
    
    def _is_bad(self, p):
        """Check if p divides discriminant Δ = -16(4a³+27b²)"""
        disc = -16 * (4*self.a_coeff**3 + 27*self.b_coeff**2)
        return disc % p == 0 if p > 3 else True
    
    def _count_ap(self, p):
        """a_p = p + 1 - #E(F_p) by brute force"""
        count = 1  # point at infinity
        for x in range(p):
            rhs = (x*x*x + self.a_coeff*x + self.b_coeff) % p
            for y in range(p):
                if (y*y) % p == rhs:
                    count += 1
        return p + 1 - count
    
    @property
    def name(self): return f"L(s,{self.label})"
    
    def primes(self, K): return self._primes[:K]
    def ln_primes(self, K): return self._ln[:K]
    
    def local_factor(self, p, s):
        ap = self._ap.get(int(p), 0)
        ps = complex(p)**(-s)
        return 1.0 / (1.0 - ap*ps + p*ps*ps)
    
    def log_deriv_term(self, p, s):
        """d/ds log(local factor), negated"""
        ap = self._ap.get(int(p), 0)
        lnp = np.log(float(p))
        ps = complex(p)**(-s)
        num = ap*lnp*ps - 2*p*lnp*ps*ps
        den = 1.0 - ap*ps + p*ps*ps
        if abs(den) < 1e-30: return complex(0)
        return num / den
    
    def arithmetic_channel(self, p):
        ap = self._ap.get(int(p), 0)
        return {
            'a_p': float(ap),
            'a_p_norm': float(ap) / (2*np.sqrt(float(p))),  # Hasse bound: |a_p| ≤ 2√p
        }
    
    def get_ap(self, K):
        """Return array of a_p for first K primes"""
        return np.array([self._ap.get(int(p), 0) for p in self._primes[:K]])


# ═══════════════════════════════════════════════════════════════════
# MODULE 2: TOROIDAL EMBEDDING
# ═══════════════════════════════════════════════════════════════════

class ToroidalEmbedding:
    """Maps Euler product to torus coordinates"""
    
    def __init__(self, L: EulerProduct, R=1.5):
        self.L = L
        self.R = R
    
    def embed(self, K, sigma, t):
        """
        Weighted average on 𝕋²_{(p_k, p_{k+1})}
        Returns: (x, y, z) in ℝ³, plus per-prime data
        """
        P = self.L.primes(K+1)
        ln_p = np.log(P.astype(np.float64))
        
        # Weights
        w = np.zeros(K)
        for k in range(K):
            w[k] = P[k]**(-sigma) * P[k+1]**(-sigma)
        w /= w.sum()
        
        sx = sy = sz = 0.0
        per_prime = []
        for k in range(K):
            rk = P[k]**(-sigma)
            thA = ln_p[k] * t
            thB = ln_p[k+1] * t
            
            xk = w[k] * (self.R + rk * np.cos(thA)) * np.cos(thB)
            yk = w[k] * (self.R + rk * np.cos(thA)) * np.sin(thB)
            zk = w[k] * rk * np.sin(thA)
            
            sx += xk; sy += yk; sz += zk
            per_prime.append({
                'w': w[k], 'r': rk,
                'phaseA': thA % (2*np.pi), 'phaseB': thB % (2*np.pi),
                'x': xk, 'y': yk, 'z': zk,
            })
        
        return np.array([sx, sy, sz]), per_prime
    
    def trajectory(self, N_range, sigma, t):
        """Compute P(N) for N in N_range"""
        pts = []
        for N in N_range:
            p, _ = self.embed(max(N, 2), sigma, t)
            pts.append(p)
        return np.array(pts)


# ═══════════════════════════════════════════════════════════════════
# MODULE 3: THREE SCALES
# ═══════════════════════════════════════════════════════════════════

class ThreeScales:
    """Decompose trajectory into drift / spiral / CF modulation"""
    
    def __init__(self, torus: ToroidalEmbedding):
        self.torus = torus
    
    def decompose(self, sigma, t, N_max=500, window=50):
        """
        Returns:
          drift_rate: rate of center migration (~1/ln N)
          spiral_exponent: α in |spiral| ~ N^α
          coherence_length: N where consecutive directions align
        """
        # Cap N_max by available primes (embed needs K+1 primes)
        max_avail = len(self.torus.L.primes(999999)) - 2  # primes(K) returns first K
        N_max = min(N_max, max_avail, 500)
        N_range = range(2, N_max+1)
        traj = self.torus.trajectory(N_range, sigma, t)
        N_pts = len(traj)
        
        if N_pts < 60:
            return {'drift_rate': np.nan, 'spiral_alpha': np.nan,
                    'coherence_N': np.nan, 'scales_valid': False}
        
        # Scale 1: Drift — moving average center
        centers = []
        for i in range(window, N_pts):
            centers.append(traj[max(0,i-window):i].mean(axis=0))
        centers = np.array(centers)
        
        if len(centers) < 20:
            return {'drift_rate': np.nan, 'spiral_alpha': np.nan,
                    'coherence_N': np.nan, 'scales_valid': False}
        
        # Drift rate: |center(N) - center(N-1)| averaged
        diffs = np.diff(centers, axis=0)
        drift_mags = np.sqrt((diffs**2).sum(axis=1))
        drift_rate = np.median(drift_mags)
        
        # Scale 2: Spiral — deviation from center
        deviations = traj[window:] - centers
        dev_mags = np.sqrt((deviations**2).sum(axis=1))
        
        # Fit |dev| ~ N^α
        Ns = np.arange(window+2, window+2+len(dev_mags))
        mask = dev_mags > 1e-10
        if mask.sum() > 10:
            c = np.polyfit(np.log(Ns[mask]), np.log(dev_mags[mask]), 1)
            spiral_alpha = c[0]
        else:
            spiral_alpha = np.nan
        
        # Scale 3: Coherence — cosine between consecutive steps
        steps = np.diff(traj, axis=0)
        step_norms = np.sqrt((steps**2).sum(axis=1))
        cos_angles = []
        for i in range(1, len(steps)):
            if step_norms[i] > 1e-15 and step_norms[i-1] > 1e-15:
                cos_a = np.dot(steps[i], steps[i-1]) / (step_norms[i] * step_norms[i-1])
                cos_angles.append(np.clip(cos_a, -1, 1))
        
        cos_arr = np.array(cos_angles)
        # Coherence length: N where median cos > 0.9
        coherence_N = len(cos_arr)
        for n in range(10, len(cos_arr)):
            if np.median(cos_arr[n-10:n]) > 0.9:
                coherence_N = n + 2
                break
        
        return {
            'drift_rate': float(drift_rate),
            'spiral_alpha': float(spiral_alpha),
            'coherence_N': int(coherence_N),
            'drift_direction': centers[-1] - centers[0],
            'final_dev_mag': float(dev_mags[-1]) if len(dev_mags) > 0 else np.nan,
            'median_cos': float(np.median(cos_arr[-50:])) if len(cos_arr) > 50 else np.nan,
            'scales_valid': True,
        }


# ═══════════════════════════════════════════════════════════════════
# MODULE 4: ENVELOPE DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════

class EnvelopeDecomposition:
    """Decompose optimal weights as f(b) × cos(ω)"""
    
    def __init__(self, L: EulerProduct):
        self.L = L
    
    def natural_weights(self, K, sigma=0.5):
        """f(b) weights: the per-step contraction"""
        P = self.L.primes(K)
        w = P.astype(float)**(-sigma)
        Z = np.cumsum(w)
        fb = np.zeros(K)
        for k in range(K):
            b = w[k] / (Z[k] if k > 0 else w[0])
            fb[k] = b / (1 + b)
        return fb
    
    def phase_modulation(self, K, gamma):
        """cos(ln(p)·γ) — the zero-specific tuning"""
        ln_p = self.L.ln_primes(K)
        return np.cos(ln_p * gamma), np.sin(ln_p * gamma)
    
    def decompose(self, theta_opt, K, gamma, sigma=0.5):
        """
        Factor θ* = f(b) · [A + B·cos(ω) + C·sin(ω)]
        Returns coefficients and R²
        """
        fb = self.natural_weights(K, sigma)
        fb_norm = fb / np.max(np.abs(fb))
        
        correction = theta_opt / (fb_norm + 1e-15)
        
        cos_w, sin_w = self.phase_modulation(K, gamma)
        X = np.column_stack([np.ones(K), cos_w, sin_w])
        c, _, _, _ = lstsq(X, correction, rcond=None)
        
        pred = X @ c
        ss_res = np.sum((correction - pred)**2)
        ss_tot = np.sum((correction - correction.mean())**2)
        r2 = 1 - ss_res/ss_tot if ss_tot > 0 else 0
        
        A, B, C = c
        amplitude = np.sqrt(B**2 + C**2)
        phase = np.arctan2(C, B)
        
        return {
            'A': float(A), 'B': float(B), 'C': float(C),
            'amplitude': float(amplitude), 'phase': float(phase),
            'R2': float(r2),
            'fb_weights': fb_norm,
            'correction': correction,
        }


# ═══════════════════════════════════════════════════════════════════
# MODULE 5: POTENTIAL LANDSCAPE
# ═══════════════════════════════════════════════════════════════════

class PotentialLandscape:
    """V(σ,t) = -log|-ζ'/ζ(s)| and its Laplacian"""
    
    def __init__(self, L: EulerProduct):
        self.L = L
    
    def V(self, sigma, t, K):
        """Potential at (σ, t)"""
        s = complex(sigma, t)
        re = im = 0.0
        P = self.L.primes(K)
        ln_p = np.log(P.astype(float))
        for k in range(K):
            term = self.L.log_deriv_term(P[k], s)
            re += term.real
            im += term.imag
        mag = np.sqrt(re**2 + im**2)
        return -np.log(mag + 1e-300)
    
    def gradient(self, sigma, t, K, h=0.003):
        """∇V = (∂V/∂σ, ∂V/∂t)"""
        ds = (self.V(sigma+h, t, K) - self.V(sigma-h, t, K)) / (2*h)
        dt = (self.V(sigma, t+h, K) - self.V(sigma, t-h, K)) / (2*h)
        return np.array([ds, dt])
    
    def laplacian(self, sigma, t, K, h=0.003):
        """ΔV = ∂²V/∂σ² + ∂²V/∂t²"""
        Vc = self.V(sigma, t, K)
        d2s = (self.V(sigma+h, t, K) - 2*Vc + self.V(sigma-h, t, K)) / (h*h)
        d2t = (self.V(sigma, t+h, K) - 2*Vc + self.V(sigma, t-h, K)) / (h*h)
        return d2s + d2t
    
    def query(self, sigma, t, K):
        """Full potential query: V, ∇V, ΔV"""
        v = self.V(sigma, t, K)
        grad = self.gradient(sigma, t, K)
        lap = self.laplacian(sigma, t, K)
        return {
            'V': float(v),
            'grad_sigma': float(grad[0]),
            'grad_t': float(grad[1]),
            'grad_mag': float(norm(grad)),
            'laplacian': float(lap),
            'harmonicity': float(abs(lap) / (abs(v) + 1e-15)),
        }


# ═══════════════════════════════════════════════════════════════════
# MODULE 6: WEIL SPECTRUM
# ═══════════════════════════════════════════════════════════════════

class WeilSpectrum:
    """Discretized Weil quadratic form"""
    
    def __init__(self, L: EulerProduct):
        self.L = L
    
    def matrix(self, K, gamma):
        """W_{jk} for target zero γ"""
        P = self.L.primes(K)
        ln_p = np.log(P.astype(float))
        W = np.zeros((K, K))
        for j in range(K):
            for k in range(K):
                w_j = np.sqrt(ln_p[j]) * P[j]**(-0.25)
                w_k = np.sqrt(ln_p[k]) * P[k]**(-0.25)
                W[j, k] = w_j * w_k * np.cos((ln_p[j] - ln_p[k]) * gamma)
        return W
    
    def spectrum(self, K, gamma, n_eig=5):
        """Eigenvalues and vectors"""
        W = self.matrix(K, gamma)
        vals, vecs = eigh(W)
        return vals[:n_eig], vecs[:, :n_eig]
    
    def query(self, K, gamma):
        n_eig = min(5, K)
        vals, vecs = self.spectrum(K, gamma, n_eig)
        return {
            'lambda_min': float(vals[0]),
            'lambda_2': float(vals[1]) if n_eig > 1 else np.nan,
            'spectral_gap': float(vals[1] - vals[0]) if n_eig > 1 else np.nan,
            'lambda_max': float(vals[-1]),
            'trace': float(vals.sum()),
            'eigenvector_min': vecs[:, 0].tolist(),
        }


# ═══════════════════════════════════════════════════════════════════
# MODULE 7: CHANNEL ORTHOGONALITY
# ═══════════════════════════════════════════════════════════════════

class ChannelOrthogonality:
    """Test independence between arithmetic, amplitude, and phase channels"""
    
    def __init__(self, L: EulerProduct):
        self.L = L
    
    def test(self, K, gamma):
        P = self.L.primes(K)
        ln_p = np.log(P.astype(float))
        
        # Canal B: amplitude features
        canal_b = np.column_stack([ln_p, P**(-0.5)])
        
        # Canal C: phase features
        canal_c = np.column_stack([np.cos(ln_p * gamma), np.sin(ln_p * gamma)])
        
        # Canal A: arithmetic features
        arith = [self.L.arithmetic_channel(p) for p in P]
        keys = sorted(arith[0].keys())
        canal_a = np.column_stack([[a[k] for a in arith] for k in keys])
        
        # Cross-correlations
        results = {}
        for name_i, ci in [('A', canal_a), ('B', canal_b), ('C', canal_c)]:
            for name_j, cj in [('A', canal_a), ('B', canal_b), ('C', canal_c)]:
                if name_i >= name_j: continue
                # Max absolute Spearman between any pair of columns
                max_rho = 0.0
                for a in range(ci.shape[1]):
                    for b in range(cj.shape[1]):
                        if np.std(ci[:, a]) < 1e-10 or np.std(cj[:, b]) < 1e-10: continue
                        rho, _ = spearmanr(ci[:, a], cj[:, b])
                        max_rho = max(max_rho, abs(rho))
                results[f'{name_i}_{name_j}_max_rho'] = float(max_rho)
        
        return results


# ═══════════════════════════════════════════════════════════════════
# MODULE 8: GEOMETRIC FEATURE VECTOR
# ═══════════════════════════════════════════════════════════════════

class GeometricEngine:
    """
    Master engine: combines all modules into a single query interface.
    
    Input:  EulerProduct + (sigma, t, K)
    Output: ~40 geometric features, zero statistical assumptions
    """
    
    def __init__(self, L: EulerProduct, R=1.5):
        self.L = L
        self.torus = ToroidalEmbedding(L, R)
        self.scales = ThreeScales(self.torus)
        self.envelope = EnvelopeDecomposition(L)
        self.potential = PotentialLandscape(L)
        self.weil = WeilSpectrum(L)
        self.channels = ChannelOrthogonality(L)
    
    def query(self, sigma, t, K, compute_scales=False):
        """
        Full geometric feature vector at (σ, t) with K primes.
        
        Returns dict with ~40 parameters, grouped by module.
        """
        features = {
            'meta': {
                'L_function': self.L.name,
                'sigma': sigma, 't': t, 'K': K,
            }
        }
        
        # Torus position
        pos, per_prime = self.torus.embed(K, sigma, t)
        features['torus'] = {
            'position': pos.tolist(),
            'radius': float(norm(pos)),
            'xy_mag': float(np.sqrt(pos[0]**2 + pos[1]**2)),
            'z_mag': float(abs(pos[2])),
            'z_xy_ratio': float(abs(pos[2]) / (np.sqrt(pos[0]**2+pos[1]**2) + 1e-15)),
        }
        
        # Potential landscape
        features['potential'] = self.potential.query(sigma, t, K)
        
        # Weil spectrum
        features['weil'] = self.weil.query(K, t)
        
        # Envelope: f(b) weights and phase modulation at this t
        fb = self.envelope.natural_weights(K, sigma)
        cos_w, sin_w = self.envelope.phase_modulation(K, t)
        features['envelope'] = {
            'fb_mean': float(fb.mean()),
            'fb_max': float(fb.max()),
            'fb_decay_rate': float(np.polyfit(np.log(np.arange(1,K+1)), np.log(fb+1e-15), 1)[0]),
            'phase_cos_mean': float(cos_w.mean()),
            'phase_sin_mean': float(sin_w.mean()),
            'phase_coherence': float(np.sqrt(cos_w.mean()**2 + sin_w.mean()**2)),
        }
        
        # Poincaré compactification
        r = norm(pos)
        poincare_r = r / (1 + r) if r > 1e-15 else 0
        features['poincare'] = {
            'radius': float(poincare_r),
            'gap': float(1 - poincare_r),
            'direction': (pos / (r + 1e-15)).tolist(),
        }
        
        # Three scales (expensive — optional)
        if compute_scales:
            features['scales'] = self.scales.decompose(sigma, t, N_max=min(K*4, 500))
        
        # Channel orthogonality
        features['channels'] = self.channels.test(K, t)
        
        return features
    
    def feature_vector(self, sigma, t, K, compute_scales=False):
        """Flat numpy array of all scalar features — ready for ML input"""
        f = self.query(sigma, t, K, compute_scales)
        
        vec = [
            f['meta']['sigma'],
            f['meta']['t'],
            f['meta']['K'],
            # Torus
            f['torus']['radius'],
            f['torus']['xy_mag'],
            f['torus']['z_mag'],
            f['torus']['z_xy_ratio'],
            # Potential
            f['potential']['V'],
            f['potential']['grad_sigma'],
            f['potential']['grad_t'],
            f['potential']['grad_mag'],
            f['potential']['laplacian'],
            f['potential']['harmonicity'],
            # Weil
            f['weil']['lambda_min'],
            f['weil']['lambda_2'],
            f['weil']['spectral_gap'],
            f['weil']['lambda_max'],
            f['weil']['trace'],
            # Envelope
            f['envelope']['fb_mean'],
            f['envelope']['fb_max'],
            f['envelope']['fb_decay_rate'],
            f['envelope']['phase_cos_mean'],
            f['envelope']['phase_sin_mean'],
            f['envelope']['phase_coherence'],
            # Poincaré
            f['poincare']['radius'],
            f['poincare']['gap'],
            # Channels
            f['channels'].get('A_B_max_rho', 0),
            f['channels'].get('A_C_max_rho', 0),
            f['channels'].get('B_C_max_rho', 0),
        ]
        
        return np.array(vec, dtype=np.float64)
    
    @staticmethod
    def feature_names():
        return [
            'sigma', 't', 'K',
            'torus_radius', 'torus_xy', 'torus_z', 'torus_z_xy_ratio',
            'V', 'grad_sigma', 'grad_t', 'grad_mag', 'laplacian', 'harmonicity',
            'weil_lambda_min', 'weil_lambda_2', 'weil_gap', 'weil_lambda_max', 'weil_trace',
            'fb_mean', 'fb_max', 'fb_decay', 'phase_cos', 'phase_sin', 'phase_coherence',
            'poincare_r', 'poincare_gap',
            'ortho_AB', 'ortho_AC', 'ortho_BC',
        ]


# ═══════════════════════════════════════════════════════════════════
# DEMO: Run the engine on ζ(s)
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    ZEROS = [14.134725, 21.022040, 25.010858, 30.424876, 32.935062]
    
    print("=" * 72)
    print("GEOMETRIC PARAMETER GENERATOR — DEMO")
    print("=" * 72)
    
    # Initialize
    zeta = RiemannZeta()
    engine = GeometricEngine(zeta)
    
    print(f"\n  L-function: {zeta.name}")
    print(f"  Feature dimension: {len(engine.feature_names())}")
    print(f"  Features: {', '.join(engine.feature_names())}")
    
    # ── Query at known zeros ──
    print(f"\n{'─'*72}")
    print("QUERY AT KNOWN ZEROS (σ=0.5)")
    print(f"{'─'*72}")
    
    K = 30
    for gamma in ZEROS[:5]:
        t0 = time.time()
        f = engine.query(0.5, gamma, K)
        dt = time.time() - t0
        print(f"\n  γ = {gamma:.3f} (K={K}, {dt:.3f}s):")
        print(f"    V = {f['potential']['V']:.4f}")
        print(f"    |∇V| = {f['potential']['grad_mag']:.4f}")
        print(f"    ΔV = {f['potential']['laplacian']:.4f}")
        print(f"    harmonicity = {f['potential']['harmonicity']:.6f}")
        print(f"    λ_min(Weil) = {f['weil']['lambda_min']:.6f}")
        print(f"    gap(Weil) = {f['weil']['spectral_gap']:.6f}")
        print(f"    Poincaré gap = {f['poincare']['gap']:.4f}")
        print(f"    phase coherence = {f['envelope']['phase_coherence']:.4f}")
    
    # ── Compare zero vs non-zero ──
    print(f"\n{'─'*72}")
    print("ZERO vs NON-ZERO DISCRIMINATION")
    print(f"{'─'*72}")
    
    zero_vecs = []
    for g in ZEROS[:5]:
        zero_vecs.append(engine.feature_vector(0.5, g, K))
    
    nonzero_vecs = []
    for t in [16.0, 19.0, 23.0, 27.5, 34.0]:
        nonzero_vecs.append(engine.feature_vector(0.5, t, K))
    
    zero_arr = np.array(zero_vecs)
    nonzero_arr = np.array(nonzero_vecs)
    names = engine.feature_names()
    
    print(f"\n  {'feature':>20} {'mean(zero)':>12} {'mean(non)':>12} {'separation':>12}")
    for j, name in enumerate(names):
        if j < 3: continue  # skip meta
        mz = zero_arr[:, j].mean()
        mn = nonzero_arr[:, j].mean()
        sz = zero_arr[:, j].std()
        sn = nonzero_arr[:, j].std()
        pool_std = np.sqrt((sz**2 + sn**2) / 2) + 1e-15
        sep = abs(mz - mn) / pool_std
        marker = " ← !" if sep > 1.0 else ""
        print(f"  {name:>20} {mz:12.4f} {mn:12.4f} {sep:12.4f}{marker}")
    
    # ── σ sweep ──
    print(f"\n{'─'*72}")
    print("σ SWEEP AT γ₁")
    print(f"{'─'*72}")
    
    gamma1 = ZEROS[0]
    print(f"\n  {'σ':>6} {'V':>8} {'|∇V|':>8} {'ΔV':>8} {'λ_min':>8} {'P_gap':>8}")
    for sigma in np.arange(0.35, 1.10, 0.05):
        f = engine.query(sigma, gamma1, K)
        print(f"  {sigma:6.2f} {f['potential']['V']:8.3f} {f['potential']['grad_mag']:8.4f} "
              f"{f['potential']['laplacian']:8.4f} {f['weil']['lambda_min']:8.5f} "
              f"{f['poincare']['gap']:8.4f}")
    
    # ── Output format ──
    print(f"\n{'─'*72}")
    print("OUTPUT FORMAT FOR ML PIPELINE")
    print(f"{'─'*72}")
    
    vec = engine.feature_vector(0.5, ZEROS[0], K)
    print(f"\n  Feature vector dimension: {len(vec)}")
    print(f"  dtype: {vec.dtype}")
    print(f"  Values: [{', '.join(f'{v:.4f}' for v in vec[:10])}  ...]")
    print(f"\n  Ready for: sklearn, PyTorch, JAX, or any ML framework.")
    print(f"  No statistical assumptions. Pure geometry.")
    
    print(f"\n{'='*72}")
    print("GENERATOR READY")
    print(f"{'='*72}")
