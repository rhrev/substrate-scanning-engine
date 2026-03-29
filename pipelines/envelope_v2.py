#!/usr/bin/env python3
# Copyright (c) 2026 Ricardo Hernández Reveles
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Serie I · Envelope Optimization Pipeline v2
=============================================
Neural net θ(p; features) with Weil quadratic form as loss.
Investigates the third axis beyond Canal A and Canal B.

Changes from v1:
  - Neural net replaces L-BFGS (2-layer MLP, numpy)
  - Weil quadratic form loss alongside log-derivative loss
  - Systematic third-axis decomposition
  - σ sweep for zero-free region mapping
  - Comparison with prolate-like eigenvectors
"""

import numpy as np
from scipy.optimize import minimize
from scipy.stats import spearmanr, pearsonr
from numpy.linalg import lstsq, eigh
import json, time, os

# ── Primes ──
def sieve(n):
    s = np.ones(n+1, dtype=bool); s[0]=s[1]=False
    for i in range(2, int(n**0.5)+1):
        if s[i]: s[i*i::i]=False
    return np.where(s)[0]

P = sieve(1500)[:200]
LN = np.log(P.astype(np.float64))
ZEROS = [14.134725141734694, 21.022039638771555, 25.010857580145688,
         30.424876125859513, 32.935061587739189, 37.586178158825671,
         40.918719012147495, 43.327073280914999, 48.005150881167160,
         49.773832477672302]

def v2(n):
    if n==0: return 0
    c=0
    while n%2==0: c+=1; n//=2
    return c

def ord_mod(b,p):
    if p<=1: return 0
    r,x=1,b%p
    if x==0: return 0
    cur=x
    while cur!=1:
        cur=(cur*x)%p; r+=1
        if r>p: return 0
    return r

V2 = np.array([v2(int(p)-1) for p in P])
ORD2 = np.array([ord_mod(2,int(p)) for p in P])
ORD_RATIO = ORD2/(P-1).astype(float)

# ── Feature matrix for each prime ──
def build_features(K):
    """Build feature matrix [K, n_features] for primes p_1..p_K"""
    F = np.column_stack([
        LN[:K],                          # f0: ln(p) — Canal B
        P[:K]**(-0.5),                    # f1: p^{-1/2} — natural amplitude
        V2[:K].astype(float),             # f2: v₂(p−1) — Canal A
        ORD_RATIO[:K],                    # f3: ord₂(p)/(p−1) — Canal A
        np.log(np.arange(1,K+1)),         # f4: ln(k) — index
        np.ones(K),                       # f5: bias
    ])
    # Normalize each column to [0,1]
    for j in range(F.shape[1]-1):  # skip bias
        rng = F[:,j].max() - F[:,j].min()
        if rng > 1e-15:
            F[:,j] = (F[:,j] - F[:,j].min()) / rng
    return F

FEAT_NAMES = ['ln(p)', 'p^{-1/2}', 'v₂(p−1)', 'ord₂/(p−1)', 'ln(k)', 'bias']

print("=" * 72)
print("SERIE I · ENVELOPE PIPELINE v2 — NEURAL NET + WEIL LOSS")
print("=" * 72)

# ═══════════════════════════════════════════
# MODULE 1: Weil quadratic form (discretized)
# ═══════════════════════════════════════════

def weil_matrix(K, gamma):
    """
    Discretized Weil quadratic form W_{jk} for a target zero γ.
    W_{jk} = ln(p_j)^{1/2} · ln(p_k)^{1/2} · p_j^{-1/4} · p_k^{-1/4}
              · cos(ln(p_j/p_k) · γ)
    This is a K×K real symmetric matrix. Its minimum eigenvalue
    measures how well K primes can detect the zero at γ.
    """
    W = np.zeros((K, K))
    for j in range(K):
        for k in range(K):
            w_j = np.sqrt(LN[j]) * P[j]**(-0.25)
            w_k = np.sqrt(LN[k]) * P[k]**(-0.25)
            phase = (LN[j] - LN[k]) * gamma
            W[j, k] = w_j * w_k * np.cos(phase)
    return W

def weil_loss(theta, K, gamma):
    """
    Loss = θᵀ W θ — minimizing this with ||θ||=1
    gives the eigenvector for the smallest eigenvalue,
    which is the optimal weight for detecting zero at γ.
    """
    W = weil_matrix(K, gamma)
    return theta @ W @ theta

def weil_eigenvectors(K, gamma, n_eig=3):
    """Return smallest eigenvectors of Weil matrix"""
    W = weil_matrix(K, gamma)
    vals, vecs = eigh(W)
    return vals[:n_eig], vecs[:, :n_eig]

# ═══════════════════════════════════════════
# MODULE 2: Log-derivative loss
# ═══════════════════════════════════════════

def log_deriv_weighted(theta, sigma, t, K):
    re = im = 0.0
    for k in range(K):
        ps = P[k]**(-sigma)
        th = -LN[k]*t
        pr, pi = ps*np.cos(th), ps*np.sin(th)
        dr, di = 1-pr, -pi
        dd = dr*dr+di*di
        if dd < 1e-30: continue
        qr = (pr*dr+pi*di)/dd
        qi = (pi*dr-pr*di)/dd
        re += theta[k]*LN[k]*qr
        im += theta[k]*LN[k]*qi
    return re, im

def logderiv_loss(theta, K, zeros, sigma=0.5):
    total = 0.0
    for g in zeros:
        re, im = log_deriv_weighted(theta, sigma, g, K)
        total += re*re + im*im
    return total

# ═══════════════════════════════════════════
# MODULE 3: Simple MLP (numpy)
# ═══════════════════════════════════════════

class MLP:
    """2-layer MLP: features → hidden → 1 weight per prime"""
    def __init__(self, n_in, n_hidden):
        # Xavier init
        self.W1 = np.random.randn(n_in, n_hidden) * np.sqrt(2.0/n_in)
        self.b1 = np.zeros(n_hidden)
        self.W2 = np.random.randn(n_hidden, 1) * np.sqrt(2.0/n_hidden)
        self.b2 = np.zeros(1)
    
    def forward(self, X):
        """X: [K, n_in] → theta: [K]"""
        self.h = np.tanh(X @ self.W1 + self.b1)  # [K, hidden]
        out = self.h @ self.W2 + self.b2           # [K, 1]
        return out.ravel()
    
    def get_params(self):
        return np.concatenate([self.W1.ravel(), self.b1, self.W2.ravel(), self.b2])
    
    def set_params(self, p):
        n_in, n_h = self.W1.shape
        i = 0
        self.W1 = p[i:i+n_in*n_h].reshape(n_in, n_h); i += n_in*n_h
        self.b1 = p[i:i+n_h]; i += n_h
        self.W2 = p[i:i+n_h].reshape(n_h, 1); i += n_h
        self.b2 = p[i:i+1]; i += 1
    
    def n_params(self):
        return self.W1.size + self.b1.size + self.W2.size + self.b2.size

# ═══════════════════════════════════════════
# STAGE 1: Weil eigenvector analysis
# ═══════════════════════════════════════════

print(f"\n{'─'*72}")
print("STAGE 1: WEIL EIGENVECTOR ANALYSIS")
print(f"{'─'*72}")

for K in [6, 10, 20, 30]:
    print(f"\n  K = {K}:")
    for zi, gamma in enumerate(ZEROS[:3]):
        vals, vecs = weil_eigenvectors(K, gamma, 3)
        v_min = vecs[:, 0]  # eigenvector for smallest eigenvalue
        print(f"    γ{zi+1}={gamma:.3f}: λ_min={vals[0]:.6f}, λ₂={vals[1]:.6f}, gap={vals[1]-vals[0]:.6f}")
        if K <= 10:
            print(f"      v_min = [{', '.join(f'{x:.4f}' for x in v_min)}]")

# ═══════════════════════════════════════════
# STAGE 2: Neural net optimization
# ═══════════════════════════════════════════

print(f"\n{'─'*72}")
print("STAGE 2: NEURAL NET θ(p; features)")
print(f"{'─'*72}")

nn_results = {}

for K in [10, 20, 30, 50]:
    F = build_features(K)
    n_feat = F.shape[1]
    n_hidden = 8
    train_zeros = ZEROS[:5]
    
    mlp = MLP(n_feat, n_hidden)
    
    def nn_loss(params):
        mlp.set_params(params)
        theta = mlp.forward(F)
        # Combined loss: log-derivative + regularization
        ld = logderiv_loss(theta, K, train_zeros, 0.5)
        reg = 0.001 * np.sum(params**2)
        return ld + reg
    
    p0 = mlp.get_params()
    
    # Multiple random restarts
    best_loss = np.inf
    best_params = None
    for restart in range(5):
        mlp_r = MLP(n_feat, n_hidden)
        p_init = mlp_r.get_params()
        try:
            res = minimize(nn_loss, p_init, method='L-BFGS-B',
                          options={'maxiter': 3000, 'ftol': 1e-18})
            if res.fun < best_loss:
                best_loss = res.fun
                best_params = res.x.copy()
        except Exception:
            pass
    
    if best_params is not None:
        mlp.set_params(best_params)
        theta_nn = mlp.forward(F)
        theta_nn_norm = theta_nn / np.max(np.abs(theta_nn))
        
        # Evaluate on all zeros
        errors = []
        for g in ZEROS[:8]:
            re, im = log_deriv_weighted(theta_nn, 0.5, g, K)
            errors.append(np.sqrt(re**2+im**2))
        
        nn_results[K] = {
            'theta': theta_nn_norm,
            'loss': best_loss,
            'errors': errors,
            'hidden_weights': mlp.W1.copy(),
            'output_weights': mlp.W2.copy(),
        }
        
        print(f"\n  K={K}: loss={best_loss:.4e}, n_params={mlp.n_params()}")
        print(f"  {'γ':>6} {'|residual|':>12} {'log10':>8}")
        for i, (g, e) in enumerate(zip(ZEROS[:8], errors)):
            mark = " ←" if i < 5 else ""
            print(f"  γ{i+1:>2}={g:8.3f} {e:12.4e} {np.log10(e+1e-99):8.2f}{mark}")

# ═══════════════════════════════════════════
# STAGE 3: Compare NN weights vs Weil eigenvector
# ═══════════════════════════════════════════

print(f"\n{'─'*72}")
print("STAGE 3: NN θ* vs WEIL EIGENVECTOR")
print(f"{'─'*72}")

for K in [10, 20, 30]:
    if K not in nn_results: continue
    theta_nn = nn_results[K]['theta']
    
    # Get Weil eigenvector (average over train zeros)
    weil_avg = np.zeros(K)
    for g in ZEROS[:5]:
        _, vecs = weil_eigenvectors(K, g, 1)
        v = vecs[:, 0]
        # Align sign
        if np.dot(v, theta_nn) < 0: v = -v
        weil_avg += v
    weil_avg /= np.max(np.abs(weil_avg))
    
    # Correlation
    pr, pp = pearsonr(theta_nn[:K] / np.max(np.abs(theta_nn[:K])), weil_avg)
    sr, sp = spearmanr(theta_nn[:K], weil_avg)
    
    # Angle between vectors
    cos_angle = np.dot(theta_nn[:K], weil_avg) / (np.linalg.norm(theta_nn[:K]) * np.linalg.norm(weil_avg) + 1e-15)
    angle = np.degrees(np.arccos(np.clip(cos_angle, -1, 1)))
    
    print(f"\n  K={K}: Pearson r={pr:.4f}, Spearman ρ={sr:.4f}, angle={angle:.1f}°")
    
    if K <= 20:
        print(f"  {'k':>4} {'p':>5} {'θ_NN':>10} {'θ_Weil':>10} {'diff':>10}")
        for k in range(K):
            t_nn = theta_nn[k] / np.max(np.abs(theta_nn[:K]))
            print(f"  {k:4d} {P[k]:5d} {t_nn:10.4f} {weil_avg[k]:10.4f} {t_nn-weil_avg[k]:10.4f}")

# ═══════════════════════════════════════════
# STAGE 4: Feature importance (ablation)
# ═══════════════════════════════════════════

print(f"\n{'─'*72}")
print("STAGE 4: FEATURE IMPORTANCE (ABLATION)")
print(f"{'─'*72}")

K_abl = 30
if K_abl in nn_results:
    F_full = build_features(K_abl)
    base_loss = nn_results[K_abl]['loss']
    
    print(f"\n  K={K_abl}, base loss = {base_loss:.4e}")
    print(f"  {'removed feature':>18} {'loss':>12} {'Δloss':>12} {'importance':>12}")
    
    for j, fname in enumerate(FEAT_NAMES):
        F_ablated = F_full.copy()
        F_ablated[:, j] = 0  # zero out feature j
        
        mlp_abl = MLP(F_full.shape[1], 8)
        train_zeros = ZEROS[:5]
        
        def abl_loss(params):
            mlp_abl.set_params(params)
            theta = mlp_abl.forward(F_ablated)
            return logderiv_loss(theta, K_abl, train_zeros, 0.5) + 0.001*np.sum(params**2)
        
        best_abl = np.inf
        for _ in range(3):
            mlp_r = MLP(F_full.shape[1], 8)
            try:
                res = minimize(abl_loss, mlp_r.get_params(), method='L-BFGS-B',
                              options={'maxiter': 2000, 'ftol': 1e-18})
                if res.fun < best_abl: best_abl = res.fun
            except Exception: pass
        
        delta = best_abl - base_loss
        importance = delta / (base_loss + 1e-20)
        print(f"  {fname:>18} {best_abl:12.4e} {delta:12.4e} {importance:12.4f}")

# ═══════════════════════════════════════════
# STAGE 5: Third axis decomposition
# ═══════════════════════════════════════════

print(f"\n{'─'*72}")
print("STAGE 5: THIRD AXIS DECOMPOSITION")
print(f"{'─'*72}")

for K in [20, 30, 50]:
    if K not in nn_results: continue
    theta = nn_results[K]['theta']
    theta_n = theta / np.max(np.abs(theta))
    
    # Canal A: v₂(p−1), ord₂/(p−1)
    A = np.column_stack([V2[:K].astype(float), ORD_RATIO[:K], np.ones(K)])
    # Canal B: ln(p), p^{-1/2}
    B = np.column_stack([LN[:K], P[:K]**(-0.5), np.ones(K)])
    # Combined
    AB = np.column_stack([V2[:K].astype(float), ORD_RATIO[:K], LN[:K], P[:K]**(-0.5), np.ones(K)])
    
    r2 = {}
    for name, X in [("A (digits)", A), ("B (phases)", B), ("A+B", AB)]:
        c, _, _, _ = lstsq(X, theta_n, rcond=None)
        pred = X @ c
        ss_res = np.sum((theta_n - pred)**2)
        ss_tot = np.sum((theta_n - theta_n.mean())**2)
        r2[name] = 1 - ss_res/ss_tot if ss_tot > 0 else 0
    
    # Residual = the third axis
    c_ab, _, _, _ = lstsq(AB, theta_n, rcond=None)
    residual = theta_n - AB @ c_ab
    res_norm = np.linalg.norm(residual) / np.linalg.norm(theta_n)
    
    # Correlate residual with available features
    print(f"\n  K={K}:")
    print(f"    R²(A) = {r2['A (digits)']:.4f}  R²(B) = {r2['B (phases)']:.4f}  R²(A+B) = {r2['A+B']:.4f}")
    print(f"    Residual norm: {res_norm:.4f} → {'THIRD AXIS' if res_norm > 0.3 else 'Mostly A+B'}")
    
    if res_norm > 0.15:
        # What does the residual correlate with?
        candidates = {
            'CF a₁(γ₁)·ln(p)': np.array([1/(1+LN[k]*ZEROS[0]%1) for k in range(K)]),
            'sin(ln(p)·γ₁)': np.sin(LN[:K]*ZEROS[0]),
            'cos(ln(p)·γ₁)': np.cos(LN[:K]*ZEROS[0]),
            'ln(p)·v₂': LN[:K]*V2[:K],
            'p mod 8': (P[:K]%8).astype(float),
            '(-1)^k': np.array([(-1)**k for k in range(K)], dtype=float),
            'Weil v_min': np.zeros(K),  # filled below
        }
        # Get Weil eigenvector
        _, vecs = weil_eigenvectors(K, ZEROS[0], 1)
        candidates['Weil v_min'] = vecs[:, 0]
        
        print(f"    Residual correlations:")
        print(f"    {'candidate':>20} {'Spearman ρ':>12} {'p-value':>10}")
        for cname, cvec in candidates.items():
            if np.std(cvec) < 1e-10: continue
            sr, sp = spearmanr(residual, cvec)
            marker = " ← !" if abs(sr) > 0.3 and sp < 0.05 else ""
            print(f"    {cname:>20} {sr:12.4f} {sp:10.2e}{marker}")

# ═══════════════════════════════════════════
# STAGE 6: σ sweep — zero-free region mapping
# ═══════════════════════════════════════════

print(f"\n{'─'*72}")
print("STAGE 6: σ SWEEP — ZERO-FREE REGION")
print(f"{'─'*72}")

K_sweep = 30
if K_sweep in nn_results:
    theta_opt = nn_results[K_sweep]['theta']
    
    print(f"\n  K={K_sweep}, sweeping σ from 0.40 to 1.05")
    print(f"  {'σ':>6} {'|LD| at γ₁':>14} {'|LD| at γ₂':>14} {'|LD| between':>14} {'ratio':>10}")
    
    for sigma in np.arange(0.40, 1.06, 0.05):
        # At zero
        re1, im1 = log_deriv_weighted(theta_opt, sigma, ZEROS[0], K_sweep)
        mag1 = np.sqrt(re1**2+im1**2)
        re2, im2 = log_deriv_weighted(theta_opt, sigma, ZEROS[1], K_sweep)
        mag2 = np.sqrt(re2**2+im2**2)
        # Between zeros
        re_b, im_b = log_deriv_weighted(theta_opt, sigma, 17.5, K_sweep)
        mag_b = np.sqrt(re_b**2+im_b**2)
        ratio = mag_b / (mag1 + 1e-15)
        print(f"  {sigma:6.2f} {mag1:14.4e} {mag2:14.4e} {mag_b:14.4e} {ratio:10.2f}")

# ═══════════════════════════════════════════
# STAGE 7: Per-zero optimal weights
# ═══════════════════════════════════════════

print(f"\n{'─'*72}")
print("STAGE 7: PER-ZERO OPTIMAL WEIGHTS — DO DIFFERENT ZEROS WANT DIFFERENT θ?")
print(f"{'─'*72}")

K_pz = 20
per_zero_theta = []

for zi, gamma in enumerate(ZEROS[:6]):
    theta0 = np.ones(K_pz) / K_pz
    res = minimize(
        lambda th: logderiv_loss(th, K_pz, [gamma], 0.5) + 0.001*np.sum(th**2),
        theta0, method='L-BFGS-B', options={'maxiter': 2000, 'ftol': 1e-20}
    )
    th = res.x / np.max(np.abs(res.x))
    per_zero_theta.append(th)

# Cross-correlations between per-zero weights
print(f"\n  K={K_pz}: pairwise Pearson between θ* optimized for each zero:")
print(f"  {'':>6}", end='')
for zi in range(6): print(f"{'γ'+str(zi+1):>8}", end='')
print()
for zi in range(6):
    print(f"  γ{zi+1:>2}  ", end='')
    for zj in range(6):
        r, _ = pearsonr(per_zero_theta[zi], per_zero_theta[zj])
        print(f"{r:8.3f}", end='')
    print()

# Average similarity
cors = []
for i in range(6):
    for j in range(i+1,6):
        r, _ = pearsonr(per_zero_theta[i], per_zero_theta[j])
        cors.append(r)
print(f"\n  Mean pairwise |r| = {np.mean(np.abs(cors)):.4f}")
print(f"  → {'UNIVERSAL weights' if np.mean(np.abs(cors)) > 0.7 else 'ZERO-SPECIFIC weights' if np.mean(np.abs(cors)) < 0.3 else 'PARTIALLY universal'}")

# ═══════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════

print(f"\n{'='*72}")
print("PIPELINE v2 SUMMARY")
print(f"{'='*72}")
print(f"""
  ARCHITECTURE: 2-layer MLP, {FEAT_NAMES}
  LOSS: |Σ θ_k ln(p_k) p_k^{{-s}} / (1-p_k^{{-s}})|² + L2
  
  KEY FINDINGS:
  1. NN θ* vs Weil eigenvector: see Stage 3 alignment
  2. Feature importance: see Stage 4 ablation  
  3. Third axis: see Stage 5 residual analysis
  4. Zero-free region: see Stage 6 σ-sweep
  5. Universal vs specific weights: see Stage 7
  
  THE QUESTION:
  Does θ* = f(arithmetic features of p)?
  If yes → the "right" operator for RH encodes
  arithmetic structure beyond ln(p).
  If no → the weights are purely spectral (Connes).
""")

# Save
output = {'version': 'v2'}
for K in nn_results:
    output[f'K{K}_loss'] = float(nn_results[K]['loss'])
    output[f'K{K}_errors'] = [float(e) for e in nn_results[K]['errors']]
    output[f'K{K}_theta'] = [float(t) for t in nn_results[K]['theta']]

_dir = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_dir, '..', 'data', 'envelope_v2_results.json'), 'w') as f:
    json.dump(output, f, indent=2)
print(f"  Results saved to envelope_v2_results.json")
