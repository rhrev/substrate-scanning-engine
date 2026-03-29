#!/usr/bin/env python3
"""
Serie I · Physical Cavity Spectral Engine
===========================================
Same architecture. Input: 2D cavity shape.
Output: 29 spectral features for application scoring.

Copyright (c) 2026 Ricardo Hernández Reveles
SPDX-License-Identifier: AGPL-3.0-or-later
"""
import numpy as np
from numpy.linalg import eigh
from scipy.stats import kurtosis
import time

class Cavity2D:
    def __init__(self, shape, params, N_grid=30):
        self.shape = shape; self.params = params; self.N = N_grid
        self.mask, self.n_interior = self._build_mask()
        self.eigenvalues, self.eigenvectors = self._solve()

    def _build_mask(self):
        N = self.N; mask = np.zeros((N, N), dtype=bool)
        for i in range(N):
            for j in range(N):
                x, y = (i/(N-1))*2-1, (j/(N-1))*2-1
                if self.shape == 'circle':
                    r = self.params.get('r', 0.9)
                    if x*x+y*y < r*r: mask[i,j] = True
                elif self.shape == 'ellipse':
                    a, b = self.params.get('a', 0.9), self.params.get('b', 0.5)
                    if (x/a)**2+(y/b)**2 < 1: mask[i,j] = True
                elif self.shape == 'rectangle':
                    w, h = self.params.get('w', 0.9), self.params.get('h', 0.6)
                    if abs(x) < w and abs(y) < h: mask[i,j] = True
                elif self.shape == 'stadium':
                    w, r = self.params.get('w', 0.5), self.params.get('r', 0.4)
                    if abs(x)<w and abs(y)<r: mask[i,j]=True
                    elif (x-w)**2+y*y<r*r: mask[i,j]=True
                    elif (x+w)**2+y*y<r*r: mask[i,j]=True
                elif self.shape == 'parabolic':
                    a, b = self.params.get('a', 0.8), self.params.get('b', 1.0)
                    ymax = a - b*x*x; ymin = self.params.get('ymin', -0.8)
                    if y > ymin and y < ymax and abs(x) < 0.9: mask[i,j] = True
                elif self.shape == 'L_shape':
                    if abs(x)<0.8 and abs(y)<0.8 and not (x>0 and y>0): mask[i,j]=True
        return mask, int(mask.sum())

    def _solve(self):
        N = self.N; mask = self.mask
        idx_map = np.full((N,N), -1, dtype=int); n = 0
        for i in range(N):
            for j in range(N):
                if mask[i,j]: idx_map[i,j] = n; n += 1
        if n < 4: return np.array([0.0]), np.array([[1.0]])
        h = 2.0/(N-1); L = np.zeros((n,n))
        for i in range(N):
            for j in range(N):
                if not mask[i,j]: continue
                k = idx_map[i,j]; neighbors = 0
                for di,dj in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ni,nj = i+di, j+dj
                    if 0<=ni<N and 0<=nj<N and mask[ni,nj]:
                        L[k, idx_map[ni,nj]] = -1.0/(h*h)
                    neighbors += 1
                L[k,k] = neighbors/(h*h)
        vals, vecs = eigh(L)
        return vals, vecs

    def spectrum(self, n_modes=20):
        return self.eigenvalues[:min(n_modes, len(self.eigenvalues))]

FEATURE_NAMES = [
    'n_interior', 'param_a', 'param_b',
    'f_0', 'f_1', 'gap', 'ratio_21',
    'mean_spacing', 'std_spacing', 'spacing_cv', 'weyl_resid', 'level_repulsion', 'harmonicity',
    'spec_dim', 'degeneracy', 'near_degen', 'f_4', 'f_9',
    'ratio_31', 'f_max', 'bandwidth', 'median_spacing', 'spacing_growth', 'n_modes',
    'Q_factor', 'regularity', 'non_degen',
    'antenna_score', 'acoustic_score',
]

def cavity_features(cav, n_modes=20):
    eigs = cav.spectrum(n_modes); n = len(eigs)
    if n < 3: return np.zeros(29)
    gap = eigs[1]-eigs[0] if n>1 else 0
    r21 = eigs[1]/eigs[0] if eigs[0]>1e-10 else 0
    r31 = eigs[2]/eigs[0] if n>2 and eigs[0]>1e-10 else 0
    sp = np.diff(eigs)
    ms = sp.mean() if len(sp)>0 else 0
    ss = sp.std() if len(sp)>1 else 0
    scv = ss/(ms+1e-15)
    # Weyl residual
    en = np.arange(1,n+1)
    if eigs[-1]>eigs[0]:
        wp = en*(eigs[-1]-eigs[0])/n+eigs[0]
        wr = np.sqrt(np.mean((eigs-wp)**2))/(ms+1e-15)
    else: wr = 0
    # Level repulsion
    if len(sp)>2:
        rats = [min(sp[i],sp[i+1])/(max(sp[i],sp[i+1])+1e-15) for i in range(len(sp)-1)]
        lr = np.mean(rats)
    else: lr = 0
    # Harmonicity
    if eigs[0]>1e-10:
        norm = eigs/eigs[0]; idev = np.mean([abs(v-round(v)) for v in norm[:min(10,n)]])
    else: idev = 1.0
    # Spectral dimension
    if n>5:
        sd = np.polyfit(np.log(eigs+1e-15)[:n], np.log(en), 1)[0]*2
    else: sd = 0
    deg = sum(1 for s in sp if s < ms*0.01) if len(sp)>0 else 0
    ndeg = sum(1 for s in sp if s < ms*0.1) if len(sp)>0 else 0
    # Q and regularity
    Q = gap/(eigs[0]+1e-15)
    reg = 1.0/(scv+1e-15)
    nd = float(deg==0)
    # Application scores
    ant = Q*0.4 + reg*0.003 + nd*0.2
    aco = (1/(scv+0.01))*0.3 + (1/(wr+0.01))*0.3 + (1-idev)*0.4
    return np.array([
        cav.n_interior,
        cav.params.get('a', cav.params.get('r', cav.params.get('w', 0))),
        cav.params.get('b', cav.params.get('h', cav.params.get('r', 0))),
        eigs[0], eigs[1] if n>1 else 0, gap, r21,
        ms, ss, scv, wr, lr, idev,
        sd, float(deg), float(ndeg), eigs[min(4,n-1)], eigs[min(9,n-1)],
        r31, eigs[-1], eigs[-1]/(eigs[0]+1e-15),
        np.median(sp) if len(sp)>0 else 0,
        sp[-1]/(sp[0]+1e-15) if len(sp)>1 and sp[0]>1e-10 else 0,
        float(n), Q, reg, nd, ant, aco,
    ], dtype=np.float64)

SHAPES = {
    'circle':    ('circle',    {'r': 0.85}),
    'ellipse_w': ('ellipse',   {'a': 0.9, 'b': 0.4}),
    'ellipse_n': ('ellipse',   {'a': 0.5, 'b': 0.85}),
    'rectangle': ('rectangle', {'w': 0.85, 'h': 0.5}),
    'square':    ('rectangle', {'w': 0.7, 'h': 0.7}),
    'stadium':   ('stadium',   {'w': 0.45, 'r': 0.4}),
    'parabolic': ('parabolic', {'a': 0.8, 'b': 0.9, 'ymin': -0.7}),
    'L_shape':   ('L_shape',   {}),
}

if __name__ == '__main__':
    print("="*72)
    print("PHYSICAL CAVITY ENGINE — 29 features per shape")
    print("="*72)
    for name, (shape, params) in SHAPES.items():
        cav = Cavity2D(shape, params, 35)
        vec = cavity_features(cav)
        eigs = cav.spectrum(6)
        print(f"  {name:>12} ({cav.n_interior:3d} pts): λ=[{' '.join(f'{e:.1f}' for e in eigs)}]  Q={vec[24]:.3f}  ant={vec[27]:.3f}  aco={vec[28]:.3f}")
    t0 = time.time()
    for _ in range(100): cavity_features(Cavity2D('ellipse', {'a':0.9,'b':0.5}, 35))
    dt = time.time()-t0
    print(f"\n  Throughput: {100/dt:.0f}/s ({dt/100*1000:.1f}ms)")
