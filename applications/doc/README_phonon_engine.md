# phonon_engine.py — Magic Numbers

Phonon spectral engine. 29 features from 1D chain dynamical matrix.

## Spectrum computation

| Value | Location | Meaning |
|-------|----------|---------|
| `n_q = 50` | `phonon_spectrum` default | Number of wavevector points in [0, π]. 50 q-points gives a smooth dispersion curve with Δq = π/50 ≈ 0.063 rad/cell. Sufficient for band gap detection and group velocity estimation. |
| `np.pi` | `qs = np.linspace(0, np.pi, n_q)` | Brillouin zone boundary for a 1D chain with lattice constant a = 1. The full zone is [-π, π] but is symmetric, so [0, π] suffices. |
| `np.exp(1j*q)` | Bloch phase | The phase factor e^{iqα} for periodic boundary conditions. This is the Bloch theorem applied to the 1D chain. |

## Dynamical matrix construction

| Value | Location | Meaning |
|-------|----------|---------|
| `(kl+kr)/masses[i]` | diagonal | D_{ii} = (k_left + k_right)/m_i. Sum of spring constants divided by mass — the restoring force per unit displacement. Standard harmonic crystal dynamics. |
| `-kl/np.sqrt(masses[i]*masses[i-1])` | off-diagonal | D_{ij} = -k_{ij}/√(m_i·m_j). Mass-weighted coupling. The √(m_i·m_j) normalization ensures the dynamical matrix is Hermitian with eigenvalues ω². |
| `np.maximum(eigs, 0)` | after eigh | Clamp negative eigenvalues to zero. Numerical noise can produce slightly negative ω² (< 10⁻¹⁴); taking sqrt of negative would give NaN. |

## Material parameters

All masses are atomic masses in amu. All spring constants are in arbitrary units (eV/Å² scale), chosen to produce phonon frequencies in the correct relative order.

| Material | Masses (amu) | Springs | Physical basis |
|----------|-------------|---------|----------------|
| Cu | [63.5] | [50.0] | Monatomic FCC metal. Single atom/cell → 1 acoustic branch, no gap. |
| Fe | [55.8] | [70.0] | Monatomic BCC. Stiffer springs than Cu (higher Debye T). |
| Al | [27.0] | [35.0] | Light monatomic metal. Low mass → high frequencies. |
| NaCl | [23.0, 35.5] | [30.0, 30.0] | Ionic crystal, 2 atoms/cell → 1 acoustic + 1 optical branch with gap. Equal springs model the Coulomb interaction. |
| GaAs | [69.7, 74.9] | [45.0, 45.0] | III-V semiconductor. Similar masses → small band gap. |
| SiC | [28.0, 12.0] | [80.0, 80.0] | Wide-gap semiconductor. Large mass ratio (2.33) + stiff bonds → large gap + high sound velocity. |
| PbTe | [207.0, 127.6] | [20.0, 20.0] | Thermoelectric material. Heavy atoms + soft bonds → low thermal conductivity (low κ). |
| MgO | [24.3, 16.0] | [60.0, 60.0] | Refractory oxide. Moderate mass ratio, stiff bonds. |
| polymer | [12.0, 12.0] | [80.0, 5.0] | Polymer chain model. Equal masses but very different spring constants (strong covalent backbone vs. weak van der Waals between chains). Large spring ratio → large gap. |
| perovskite | [40.0, 16.0, 137.0] | [50.0, 50.0, 30.0] | 3-atom unit cell (A-B-X₃ simplified). The heavy X atom (137 amu, modeling Ba or Cs) creates low-frequency rattler modes. |
| clathrate | [72.6, 28.0, 28.0] | [40.0, 10.0, 40.0] | Skutterudite/clathrate proxy. The weak middle spring (10.0) models the guest atom rattling inside the cage — a known mechanism for low thermal conductivity. |
| BiTe | [209.0, 127.6] | [15.0, 15.0] | Bi₂Te₃ proxy. Very heavy atoms + very soft bonds → excellent thermoelectric (low κ, flat optical branches). |

## Feature computation

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-10` | `af > 1e-10` | Filter out acoustic modes at q=0 (ω = 0 exactly). |
| `30` | `np.histogram(af, bins=30)` | Density of states histogram: 30 bins across the frequency range. Resolution sufficient for peak detection without overfitting to discrete modes. |
| `1e-15` | multiple denominators | Zero-guards in DOS entropy, mean spacing, etc. |
| `0.048` | `af.max() * 0.048` | Debye temperature proxy: T_D ≈ ℏω_max/k_B. The factor 0.048 comes from ℏ/k_B ≈ 7.64×10⁻¹² K·s and a frequency scale normalization. This is a proxy, not an exact conversion — the 1D chain frequencies are in arbitrary units. |
| `0.1` | multiple thresholds | Band gap significance: `bg > 0.1` for insulator flag. Dispersive branch threshold: `bw > af.max() * 0.1`. Smoothing constant in ZT proxy denominator: `κ + 0.1`. All serve to separate signal from noise in the 1D model. |
| `0.8` | `of > 0.8` | Flat optical branch flag: mean flatness > 80%. Indicates rattler modes with nearly dispersionless optical branches — the key indicator for thermoelectric materials. |
| `1.0` | `vs > 1.0` | High sound velocity flag. In the arbitrary frequency units, v_sound > 1.0 indicates a stiff material. |
| `0.5` | `scv < 0.5` | Regular spacing flag: coefficient of variation of level spacings < 0.5. Regular spacing indicates an integrable system (vs. chaotic). |

## Thermoelectric screening

| Value | Location | Meaning |
|-------|----------|---------|
| `(gap + 0.1) × (flatness + 0.1) / (κ + 0.1)` | ZT proxy | Simplified figure of merit proxy. Real ZT = S²σT/κ, but the 1D phonon model only accesses: gap (proxy for electronic band gap → large Seebeck), flatness (proxy for low group velocity → low lattice κ), and κ_proxy (direct thermal conductivity estimate). The +0.1 offsets prevent zero denominators and give non-zero scores to all materials. |

## Inverse design

| Value | Location | Meaning |
|-------|----------|---------|
| `29,241` | paper claim | Number of compositions swept in 32 seconds. This comes from a mass grid × spring grid sweep (e.g., 171 × 171), not hardcoded in the engine file. The paper reports the throughput as 905/s. |
