#!/usr/bin/env python3
# Copyright (c) 2026 Ricardo Hernández Reveles
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Serie I · S-Parameter Spectral Engine
======================================
Same architecture as geometric_engine.py, applied to
differential signal integrity.

Input:  S-matrix S(f) from 4-port VNA measurement (.s4p touchstone)
Output: 29 spectral features for pass/marginal/fail classification

Channels:
  Canal B = Sdd (differential signal) — the useful channel
  Canal A = Scc (common mode) — should be independent
  Cross   = Sdc, Scd (mode conversion) — the dual test

The motor doesn't know it's doing signal integrity.
It sees a spectrum and extracts geometry.
"""

import numpy as np
from numpy.linalg import eigh, norm
from scipy.signal import find_peaks
import json, os

# ═══════════════════════════════════════════════════════════════
# MODULE 1: TOUCHSTONE PARSER
# ═══════════════════════════════════════════════════════════════

class SParameterData:
    """Holds S-parameter data from a 4-port measurement"""
    
    def __init__(self, freqs, S):
        """
        freqs: array of frequencies [Hz], shape (N_freq,)
        S: complex S-matrix, shape (N_freq, 4, 4)
        """
        self.freqs = freqs
        self.S = S
        self.N_freq = len(freqs)
        self.f_min = freqs[0]
        self.f_max = freqs[-1]
        
        # Mixed-mode transformation matrix
        # Ports 1,3 = positive; 2,4 = negative (standard differential pair)
        M = np.array([
            [ 1, -1,  0,  0],  # diff in
            [ 1,  1,  0,  0],  # common in
            [ 0,  0,  1, -1],  # diff out
            [ 0,  0,  1,  1],  # common out
        ], dtype=complex) / np.sqrt(2)
        
        self.Smm = np.zeros_like(S)
        for i in range(self.N_freq):
            self.Smm[i] = M @ S[i] @ M.conj().T
        
        # Extract blocks: Smm is [[Sdd, Sdc], [Scd, Scc]]
        self.Sdd = self.Smm[:, 0:2, 0:2]  # diff → diff
        self.Scc = self.Smm[:, 2:4, 2:4]  # common → common
        self.Sdc = self.Smm[:, 0:2, 2:4]  # common → diff (mode conversion)
        self.Scd = self.Smm[:, 2:4, 0:2]  # diff → common
    
    @staticmethod
    def from_touchstone(filepath):
        """Parse .s4p Touchstone v1 file"""
        freqs = []
        s_data = []
        freq_mult = 1e9  # default GHz
        fmt = 'MA'  # default Magnitude/Angle
        z0 = 50.0
        
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        data_lines = []
        for line in lines:
            line = line.strip()
            if not line or line.startswith('!'):
                continue
            if line.startswith('#'):
                parts = line[1:].upper().split()
                for p in parts:
                    if p in ('HZ','KHZ','MHZ','GHZ'):
                        freq_mult = {'HZ':1,'KHZ':1e3,'MHZ':1e6,'GHZ':1e9}[p]
                    elif p in ('MA','DB','RI'):
                        fmt = p
                continue
            data_lines.append(line)
        
        # 4-port: 4 lines per frequency point (4 S-params per line = 16 total)
        i = 0
        while i < len(data_lines):
            # Collect enough values for one frequency point
            values = []
            while len(values) < 33 and i < len(data_lines):  # 1 freq + 16 complex = 33 values
                parts = data_lines[i].split()
                values.extend([float(p) for p in parts])
                i += 1
            
            if len(values) < 33:
                break
            
            freq = values[0] * freq_mult
            freqs.append(freq)
            
            # Parse 16 S-parameter values (pairs)
            S = np.zeros((4, 4), dtype=complex)
            idx = 1
            for row in range(4):
                for col in range(4):
                    v1, v2 = values[idx], values[idx+1]
                    idx += 2
                    if fmt == 'RI':
                        S[row, col] = complex(v1, v2)
                    elif fmt == 'MA':
                        S[row, col] = v1 * np.exp(1j * np.radians(v2))
                    elif fmt == 'DB':
                        S[row, col] = 10**(v1/20) * np.exp(1j * np.radians(v2))
            s_data.append(S)
        
        return SParameterData(np.array(freqs), np.array(s_data))
    
    @staticmethod
    def generate_synthetic(profile='good', N_freq=401, f_max=20e9):
        """Generate synthetic S-parameter data for testing"""
        freqs = np.linspace(0.1e9, f_max, N_freq)
        S = np.zeros((N_freq, 4, 4), dtype=complex)
        
        for i, f in enumerate(freqs):
            fn = f / f_max  # normalized frequency
            
            if profile == 'good':
                # Clean differential channel, low mode conversion
                loss = 0.3 * fn  # gradual rolloff
                phase = -2 * np.pi * f * 1e-9  # 1ns delay
                Sdd21 = (1 - loss) * np.exp(1j * phase)
                Sdd11 = 0.05 * np.exp(1j * phase * 0.1)  # good match
                Scc21 = 0.1 * np.exp(1j * phase * 0.95)
                Sdc21 = 0.01 * fn * np.exp(1j * phase * 1.1)  # low conversion
                
            elif profile == 'resonant':
                # Resonance at f_max/3
                f_res = f_max / 3
                Q = 20
                loss = 0.2 * fn + 0.6 / (1 + Q**2 * (f/f_res - f_res/f)**2)
                phase = -2 * np.pi * f * 1e-9
                Sdd21 = (1 - loss) * np.exp(1j * phase)
                Sdd11 = (0.05 + 0.3 / (1 + Q**2 * (f/f_res - f_res/f)**2)) * np.exp(1j * phase * 0.1)
                Scc21 = 0.15 * np.exp(1j * phase * 0.95)
                Sdc21 = (0.02 + 0.15 / (1 + (Q/2)**2 * (f/f_res - f_res/f)**2)) * np.exp(1j * phase)
                
            elif profile == 'lossy':
                # High loss, poor matching
                loss = 1.5 * fn + 0.3 * fn**2
                phase = -2 * np.pi * f * 1.2e-9
                Sdd21 = (1 - loss) * np.exp(1j * phase)
                Sdd11 = (0.15 + 0.1 * np.sin(2 * np.pi * fn * 5)) * np.exp(1j * phase * 0.2)
                Scc21 = 0.3 * np.exp(1j * phase * 0.9)
                Sdc21 = 0.05 * (1 + fn) * np.exp(1j * phase * 0.8)
                
            elif profile == 'crosstalk':
                # Good channel but high mode conversion
                loss = 0.25 * fn
                phase = -2 * np.pi * f * 0.9e-9
                Sdd21 = (1 - loss) * np.exp(1j * phase)
                Sdd11 = 0.04 * np.exp(1j * phase * 0.1)
                Scc21 = 0.12 * np.exp(1j * phase)
                Sdc21 = (0.1 + 0.2 * fn) * np.exp(1j * phase * 1.05)  # high conversion
                
            elif profile == 'multi_resonant':
                # Multiple resonances (bad via design)
                loss = 0.2 * fn
                for f_res in [f_max*0.2, f_max*0.45, f_max*0.7]:
                    Q = 15
                    loss += 0.4 / (1 + Q**2 * (f/f_res - f_res/f)**2)
                phase = -2 * np.pi * f * 1.1e-9
                Sdd21 = max(0.01, 1 - loss) * np.exp(1j * phase)
                Sdd11 = 0.1 * np.exp(1j * phase * 0.15)
                Scc21 = 0.2 * np.exp(1j * phase * 0.9)
                Sdc21 = 0.08 * (1 + 0.5*fn) * np.exp(1j * phase)
            
            else:
                Sdd21 = Sdd11 = Scc21 = Sdc21 = 0.0
            
            # Build 4x4 single-ended S-matrix (simplified: embed mixed-mode back)
            # For synthetic data, store mixed-mode directly
            S[i, 0, 0] = Sdd11
            S[i, 0, 1] = Sdd21
            S[i, 1, 0] = Sdd21
            S[i, 1, 1] = Sdd11
            S[i, 2, 2] = 0.05  # Scc11
            S[i, 2, 3] = Scc21
            S[i, 3, 2] = Scc21
            S[i, 3, 3] = 0.05
            S[i, 0, 2] = Sdc21
            S[i, 0, 3] = Sdc21 * 0.5
            S[i, 2, 0] = Sdc21
            S[i, 3, 0] = Sdc21 * 0.5
        
        spd = SParameterData.__new__(SParameterData)
        spd.freqs = freqs
        spd.S = S
        spd.N_freq = N_freq
        spd.f_min = freqs[0]
        spd.f_max = freqs[-1]
        # For synthetic, mixed-mode blocks are direct
        spd.Smm = S
        spd.Sdd = S[:, 0:2, 0:2]
        spd.Scc = S[:, 2:4, 2:4]
        spd.Sdc = S[:, 0:2, 2:4]
        spd.Scd = S[:, 2:4, 0:2]
        return spd


# ═══════════════════════════════════════════════════════════════
# MODULE 2: SPECTRAL FEATURE EXTRACTION (29 features)
# ═══════════════════════════════════════════════════════════════

def sp_features(spd):
    """
    Extract 29 spectral features from S-parameter data.
    Same dimension as application engines (geometric_engine produces 31: 29 core + 2 Euler-specific).
    """
    freqs = spd.freqs
    N = spd.N_freq
    
    # ── Canal B: Sdd21 (insertion loss) ──
    Sdd21_mag = np.abs(spd.Sdd[:, 0, 1])
    Sdd21_dB = 20 * np.log10(Sdd21_mag + 1e-15)
    Sdd11_mag = np.abs(spd.Sdd[:, 0, 0])
    Sdd11_dB = 20 * np.log10(Sdd11_mag + 1e-15)
    
    # ── Canal A: Scc21 (common mode) ──
    Scc21_mag = np.abs(spd.Scc[:, 0, 1])
    Scc21_dB = 20 * np.log10(Scc21_mag + 1e-15)
    
    # ── Cross-channel: Sdc (mode conversion) ──
    Sdc21_mag = np.abs(spd.Sdc[:, 0, 1])
    Sdc21_dB = 20 * np.log10(Sdc21_mag + 1e-15)
    
    # ── Feature 1-3: Bandwidth metrics ──
    # -3dB bandwidth of Sdd21
    bw_3dB = 0.0
    ref_dB = Sdd21_dB[0]
    for i in range(N):
        if Sdd21_dB[i] < ref_dB - 3:
            bw_3dB = freqs[i]
            break
    if bw_3dB == 0: bw_3dB = freqs[-1]
    
    # -6dB bandwidth
    bw_6dB = 0.0
    for i in range(N):
        if Sdd21_dB[i] < ref_dB - 6:
            bw_6dB = freqs[i]
            break
    if bw_6dB == 0: bw_6dB = freqs[-1]
    
    # Insertion loss at Nyquist (half of f_max)
    idx_nyq = N // 2
    IL_nyquist = -Sdd21_dB[idx_nyq]
    
    # ── Feature 4-7: Resonance detection ──
    # Find notches (dips) in Sdd21
    neg_mag = -Sdd21_mag
    peaks, props = find_peaks(neg_mag, prominence=0.02, distance=max(1, N//50))
    n_resonances = len(peaks)
    
    if n_resonances > 0:
        f_first_res = freqs[peaks[0]]
        worst_notch_dB = np.min(Sdd21_dB[peaks])
    else:
        f_first_res = freqs[-1]
        worst_notch_dB = Sdd21_dB.min()
    
    # Resonance spacing regularity
    if n_resonances > 2:
        res_spacings = np.diff(freqs[peaks])
        res_cv = res_spacings.std() / (res_spacings.mean() + 1e-15)
    else:
        res_cv = 0
    
    # ── Feature 8-11: Return loss / matching ──
    mean_RL = -np.mean(Sdd11_dB)
    worst_RL = -np.min(Sdd11_dB)  # worst case (highest reflection)
    
    # RL peaks (impedance discontinuities)
    rl_peaks, _ = find_peaks(Sdd11_mag, prominence=0.01, distance=max(1, N//50))
    n_rl_peaks = len(rl_peaks)
    
    # ── Feature 12-15: Mode conversion ──
    mean_Sdc = np.mean(Sdc21_dB)
    worst_Sdc = np.max(Sdc21_dB)
    
    # Mode conversion growth rate (slope of Sdc vs frequency)
    if N > 10:
        f_norm = freqs / freqs[-1]
        mc_slope = np.polyfit(f_norm, Sdc21_dB, 1)[0]
    else:
        mc_slope = 0
    
    # Channel orthogonality: correlation between Sdd and Sdc patterns
    if np.std(Sdd21_mag) > 1e-10 and np.std(Sdc21_mag) > 1e-10:
        ortho_dd_dc = abs(np.corrcoef(Sdd21_mag, Sdc21_mag)[0, 1])
    else:
        ortho_dd_dc = 0
    
    # ── Feature 16-19: Phase / group delay ──
    Sdd21_phase = np.unwrap(np.angle(spd.Sdd[:, 0, 1]))
    
    if N > 3:
        df = np.diff(freqs)
        dphi = np.diff(Sdd21_phase)
        group_delay = -dphi / (2 * np.pi * df + 1e-15)
        mean_gd = np.mean(group_delay)
        gd_variation = np.std(group_delay) / (abs(mean_gd) + 1e-15)
    else:
        mean_gd = 0
        gd_variation = 0
    
    # Phase linearity
    if N > 5:
        phase_fit = np.polyfit(freqs, Sdd21_phase, 1)
        phase_residual = np.sqrt(np.mean((Sdd21_phase - np.polyval(phase_fit, freqs))**2))
    else:
        phase_residual = 0
    
    # ── Feature 20-23: Spectral quality ──
    # Envelope smoothness (high frequency variation in IL)
    if N > 10:
        il_diff = np.diff(Sdd21_dB)
        roughness = np.sqrt(np.mean(il_diff**2))
    else:
        roughness = 0
    
    # Symmetry (Sdd21 vs Sdd12)
    Sdd12_mag = np.abs(spd.Sdd[:, 1, 0])
    reciprocity = np.mean(np.abs(Sdd21_mag - Sdd12_mag)) / (np.mean(Sdd21_mag) + 1e-15)
    
    # Common mode rejection ratio
    CMRR = np.mean(Sdd21_dB - Scc21_dB)
    
    # ── Feature 24-26: Derived quality metrics ──
    # Effective bandwidth × IL product (figure of merit)
    fom = bw_3dB * 1e-9 * (1 - IL_nyquist / 30)  # higher = better
    
    # Worst-case margin (how far from spec)
    # Typical spec: IL < 10dB, RL > 10dB, Sdc < -20dB at Nyquist
    il_margin = 10 - IL_nyquist  # positive = pass
    rl_margin = mean_RL - 10     # positive = pass
    mc_margin = -20 - worst_Sdc  # positive = pass
    
    # ── Pack into 29-dim vector ──
    vec = np.array([
        # Bandwidth (3)
        bw_3dB * 1e-9,          # GHz
        bw_6dB * 1e-9,
        IL_nyquist,              # dB at Nyquist
        # Resonances (4)
        float(n_resonances),
        f_first_res * 1e-9,
        worst_notch_dB,
        res_cv,
        # Return loss (4)
        mean_RL,
        worst_RL,
        float(n_rl_peaks),
        Sdd11_dB[idx_nyq],
        # Mode conversion (4)
        mean_Sdc,
        worst_Sdc,
        mc_slope,
        ortho_dd_dc,
        # Phase (4)
        mean_gd * 1e9,          # ns
        gd_variation,
        phase_residual,
        float(N),               # frequency points
        # Spectral quality (4)
        roughness,
        reciprocity,
        CMRR,
        fom,
        # Quality metrics (3)
        il_margin,
        rl_margin,
        mc_margin,
        # Classification helpers (3)
        float(n_resonances == 0),  # clean flag
        float(worst_Sdc < -25),    # low conversion flag
        float(il_margin > 0 and rl_margin > 0 and mc_margin > 0),  # overall pass
    ], dtype=np.float64)
    
    return vec

FEATURE_NAMES = [
    'BW_3dB_GHz', 'BW_6dB_GHz', 'IL_Nyquist_dB',
    'n_resonances', 'f_1st_res_GHz', 'worst_notch_dB', 'res_spacing_CV',
    'mean_RL_dB', 'worst_RL_dB', 'n_RL_peaks', 'RL_Nyquist_dB',
    'mean_Sdc_dB', 'worst_Sdc_dB', 'Sdc_slope', 'ortho_dd_dc',
    'group_delay_ns', 'GD_variation', 'phase_nonlin', 'N_freq',
    'roughness', 'reciprocity', 'CMRR_dB', 'FoM',
    'IL_margin', 'RL_margin', 'MC_margin',
    'clean_flag', 'low_conv_flag', 'PASS',
]


# ═══════════════════════════════════════════════════════════════
# MODULE 3: CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def classify(vec):
    """Rule-based classifier: PASS / MARGINAL / FAIL"""
    il_m = vec[FEATURE_NAMES.index('IL_margin')]
    rl_m = vec[FEATURE_NAMES.index('RL_margin')]
    mc_m = vec[FEATURE_NAMES.index('MC_margin')]
    n_res = vec[FEATURE_NAMES.index('n_resonances')]
    worst = vec[FEATURE_NAMES.index('worst_notch_dB')]
    
    if il_m > 3 and rl_m > 3 and mc_m > 5 and n_res == 0:
        return 'PASS', 'Clean channel, all margins > 3dB'
    elif il_m > 0 and rl_m > 0 and mc_m > 0:
        reasons = []
        if il_m < 3: reasons.append(f'IL margin thin ({il_m:.1f}dB)')
        if rl_m < 3: reasons.append(f'RL margin thin ({rl_m:.1f}dB)')
        if mc_m < 5: reasons.append(f'mode conversion high ({mc_m:.1f}dB margin)')
        if n_res > 0: reasons.append(f'{int(n_res)} resonance(s), worst {worst:.1f}dB')
        return 'MARGINAL', '; '.join(reasons) if reasons else 'Borderline'
    else:
        reasons = []
        if il_m <= 0: reasons.append(f'IL FAIL ({il_m:.1f}dB)')
        if rl_m <= 0: reasons.append(f'RL FAIL ({rl_m:.1f}dB)')
        if mc_m <= 0: reasons.append(f'Mode conversion FAIL ({mc_m:.1f}dB)')
        return 'FAIL', '; '.join(reasons)


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("=" * 72)
    print("S-PARAMETER SPECTRAL ENGINE — DEMO")
    print("29 features from S(f) · Same architecture as ζ engine")
    print("=" * 72)
    
    profiles = ['good', 'resonant', 'lossy', 'crosstalk', 'multi_resonant']
    
    results = {}
    for prof in profiles:
        spd = SParameterData.generate_synthetic(prof, N_freq=401, f_max=20e9)
        vec = sp_features(spd)
        verdict, reason = classify(vec)
        results[prof] = {'vec': vec, 'verdict': verdict, 'reason': reason}
    
    # ── Classification results ──
    print(f"\n{'─'*72}")
    print("CLASSIFICATION")
    print(f"{'─'*72}")
    
    for prof in profiles:
        r = results[prof]
        color = {'PASS': '✓', 'MARGINAL': '~', 'FAIL': '✗'}[r['verdict']]
        print(f"\n  {color} {prof:>16}: {r['verdict']}")
        print(f"    {r['reason']}")
    
    # ── Feature comparison ──
    print(f"\n{'─'*72}")
    print("FEATURE VECTORS (29-dim)")
    print(f"{'─'*72}")
    
    print(f"\n  {'feature':>18}", end='')
    for prof in profiles:
        print(f" {prof[:8]:>8}", end='')
    print()
    
    for j, fname in enumerate(FEATURE_NAMES):
        print(f"  {fname:>18}", end='')
        vals = [results[p]['vec'][j] for p in profiles]
        for v in vals:
            if abs(v) > 100:
                print(f" {v:8.1f}", end='')
            else:
                print(f" {v:8.3f}", end='')
        if np.std(vals) > 0.1 * (np.mean(np.abs(vals)) + 1e-10):
            print("  *", end='')
        print()
    
    # ── Channel orthogonality ──
    print(f"\n{'─'*72}")
    print("CHANNEL ORTHOGONALITY (Canal B=Sdd, Canal A=Scc, Cross=Sdc)")
    print(f"{'─'*72}")
    
    for prof in profiles:
        spd = SParameterData.generate_synthetic(prof, N_freq=401, f_max=20e9)
        dd = np.abs(spd.Sdd[:, 0, 1])
        cc = np.abs(spd.Scc[:, 0, 1])
        dc = np.abs(spd.Sdc[:, 0, 1])
        
        r_dd_cc = abs(np.corrcoef(dd, cc)[0,1]) if np.std(cc) > 1e-10 else 0
        r_dd_dc = abs(np.corrcoef(dd, dc)[0,1]) if np.std(dc) > 1e-10 else 0
        r_cc_dc = abs(np.corrcoef(cc, dc)[0,1]) if np.std(cc) > 1e-10 and np.std(dc) > 1e-10 else 0
        
        orth = "ORTHOGONAL" if r_dd_dc < 0.3 else "COUPLED" if r_dd_dc > 0.7 else "PARTIAL"
        
        print(f"  {prof:>16}: |ρ(Sdd,Scc)|={r_dd_cc:.3f}  |ρ(Sdd,Sdc)|={r_dd_dc:.3f}  |ρ(Scc,Sdc)|={r_cc_dc:.3f}  → {orth}")
    
    # ── Cross-domain mapping ──
    print(f"\n{'─'*72}")
    print("CROSS-DOMAIN MAPPING")
    print(f"{'─'*72}")
    print(f"""
  ζ engine:                S-param engine:
  ─────────                ────────────────
  t (critical line)        f (frequency)
  zeros of ζ               resonances (notches)
  P(N) spiral              Sdd21(f) rolloff
  f(b) envelope            insertion loss envelope
  cos(ln(p)·γ) phase       phase(Sdd21) linearity
  Canal A (v₂)             Scc (common mode)
  Canal B (ln p)           Sdd (differential)
  Cross (ρ=0.001)          Sdc (mode conversion)
  V(σ,t) landscape         |Sdd21(f)| surface
  gap espectral            bandwidth
  Ramanujan bound          spec mask (IL<10, RL>10)
  
  The spectrum is the spectrum.
""")
    
    # ── Throughput estimate ──
    import time
    spd = SParameterData.generate_synthetic('good', N_freq=401, f_max=20e9)
    t0 = time.time()
    for _ in range(1000):
        vec = sp_features(spd)
        classify(vec)
    dt = time.time() - t0
    
    print(f"  Throughput: {1000/dt:.0f} classifications/second")
    print(f"  Per file: {dt/1000*1000:.2f} ms")
    print(f"  At 120 boards/second: {'OK' if dt/1000 < 1/120 else 'TOO SLOW'}")
    
    print(f"\n{'='*72}")
    print("ENGINE READY")
    print(f"  Accepts: .s4p touchstone files or synthetic profiles")
    print(f"  Output: 29 features + PASS/MARGINAL/FAIL + reason")
    print(f"{'='*72}")
