#!/usr/bin/env python3
"""
Serie I · Phonon Spectral Engine (1D chain model)
===================================================
Same architecture. Input: masses + spring constants.
Output: 29 features from phonon spectrum.

Copyright (c) 2026 Ricardo Hernández Reveles
SPDX-License-Identifier: AGPL-3.0-or-later
"""
import numpy as np
from numpy.linalg import eigh
import time

def phonon_spectrum(masses, springs, n_q=50):
    n = len(masses); qs = np.linspace(0, np.pi, n_q); all_eigs = []
    for q in qs:
        D = np.zeros((n,n), dtype=complex)
        for i in range(n):
            kl, kr = springs[i%len(springs)], springs[(i+1)%len(springs)]
            D[i,i] = (kl+kr)/masses[i]
            if i>0:
                D[i,i-1] = -kl/np.sqrt(masses[i]*masses[i-1])
                D[i-1,i] = D[i,i-1]
            if i==n-1 and n>1:
                ph = np.exp(1j*q)
                D[0,n-1] += -kr/np.sqrt(masses[0]*masses[n-1])*ph
                D[n-1,0] += -kr/np.sqrt(masses[0]*masses[n-1])*np.conj(ph)
        eigs = np.real(eigh(D)[0]); eigs = np.maximum(eigs, 0)
        all_eigs.append(np.sqrt(eigs))
    return qs, np.array(all_eigs)

FEATURE_NAMES = [
    'band_gap', 'omega_max', 'omega_mean', 'n_branches',
    'acoustic_BW', 'mean_BW', 'std_BW',
    'v_sound', 'v_group_max', 'v_group_mean',
    'DOS_max', 'DOS_entropy', 'einstein_ind', 'optical_flat',
    'spacing_mean', 'spacing_CV', 'level_repulsion',
    'mass_ratio', 'spring_ratio', 'atoms_per_cell',
    'kappa_proxy', 'debye_T_proxy', 'impedance',
    'norm_gap', 'n_dispersive', 'is_insulator', 'has_flat', 'high_v', 'regular',
]

def phonon_features(masses, springs):
    qs, bands = phonon_spectrum(masses, springs)
    n_q, nb = bands.shape
    af = bands.flatten(); af = af[af>1e-10]
    if len(af)<3: return np.zeros(29)
    bg = max(0, bands[:,1].min()-bands[:,0].max()) if nb>1 else 0
    bws = [bands[:,b].max()-bands[:,b].min() for b in range(nb)]
    dos, _ = np.histogram(af, bins=30, density=True)
    dm = dos.max(); de = -np.sum(dos/dos.sum()*np.log(dos/dos.sum()+1e-15)) if dos.sum()>0 else 0
    dq = qs[1]-qs[0] if len(qs)>1 else 1
    vg = [np.mean(np.abs(np.gradient(bands[:,b], dq))) for b in range(nb)]
    vs = (bands[1,0]-bands[0,0])/dq if n_q>5 and bands[0,0]<bands[1,0] else 0
    of = np.mean([1-bw/(af.max()+1e-15) for bw in bws[1:]]) if nb>1 else 0
    sp = np.diff(np.sort(af)); sp = sp[sp>1e-10]
    if len(sp)>2:
        sm=sp.mean(); scv=sp.std()/(sm+1e-15)
        rats=[min(sp[i],sp[i+1])/(max(sp[i],sp[i+1])+1e-15) for i in range(len(sp)-1)]
        lr=np.mean(rats)
    else: sm=scv=lr=0
    mr = max(masses)/(min(masses)+1e-15); sr = max(springs)/(min(springs)+1e-15)
    kp = vs**2/(scv+0.1); ei = dm/(dos.mean()+1e-15)
    return np.array([
        bg, af.max(), af.mean(), float(nb),
        bws[0] if bws else 0, np.mean(bws), np.std(bws) if len(bws)>1 else 0,
        vs, max(vg) if vg else 0, np.mean(vg) if vg else 0,
        dm, de, ei, of, sm, scv, lr, mr, sr, float(len(masses)),
        kp, af.max()*0.048, vs*np.sqrt(mr),
        bg/(af.max()+1e-15), sum(bw>af.max()*0.1 for bw in bws), float(bg>0.1),
        float(of>0.8), float(vs>1.0), float(scv<0.5),
    ], dtype=np.float64)

MATERIALS = {
    'Cu':         ([63.5],  [50.0]),
    'Fe':         ([55.8],  [70.0]),
    'Al':         ([27.0],  [35.0]),
    'NaCl':       ([23.0, 35.5], [30.0, 30.0]),
    'GaAs':       ([69.7, 74.9], [45.0, 45.0]),
    'SiC':        ([28.0, 12.0], [80.0, 80.0]),
    'PbTe':       ([207.0, 127.6], [20.0, 20.0]),
    'MgO':        ([24.3, 16.0], [60.0, 60.0]),
    'polymer':    ([12.0, 12.0], [80.0, 5.0]),
    'perovskite': ([40.0, 16.0, 137.0], [50.0, 50.0, 30.0]),
    'clathrate':  ([72.6, 28.0, 28.0], [40.0, 10.0, 40.0]),
    'BiTe':       ([209.0, 127.6], [15.0, 15.0]),
}

if __name__ == '__main__':
    print("="*72)
    print("PHONON ENGINE — 29 features per material")
    print("="*72)
    for name, (m, k) in MATERIALS.items():
        vec = phonon_features(m, k)
        print(f"  {name:>12}: gap={vec[0]:.2f}  ωmax={vec[1]:.2f}  vs={vec[7]:.3f}  κ={vec[20]:.3f}  flat={vec[13]:.3f}")
    print("\n  Thermoelectric ranking (ZT proxy):")
    ranked = sorted(MATERIALS.items(), key=lambda x: -(lambda v: (v[0]+0.1)*(v[13]+0.1)/(v[20]+0.1))(phonon_features(*x[1])))
    for i,(name,_) in enumerate(ranked[:5]):
        v = phonon_features(*MATERIALS[name])
        print(f"    {i+1}. {name:>12}: ZT={((v[0]+0.1)*(v[13]+0.1)/(v[20]+0.1)):.3f}")
    t0=time.time()
    for _ in range(100): phonon_features([28.0,12.0],[80.0,80.0])
    dt=time.time()-t0
    print(f"\n  Throughput: {100/dt:.0f}/s ({dt/100*1000:.1f}ms)")
