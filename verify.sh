#!/bin/bash
# verify.sh — Local CI replication for SSE v3.1.1
# Run from the repository root.
# Prerequisites: python3 (3.10+), pip install -r requirements.txt
set -e

echo "========================================================================"
echo "SSE v3.1.1 — LOCAL VERIFICATION"
echo "========================================================================"
echo "Python: $(python3 --version 2>&1)"
echo ""

FAIL=0

run() {
    local label="$1"; shift
    echo "--- $label ---"
    if "$@" > /dev/null 2>&1; then
        echo "  [PASS] $label"
    else
        echo "  [FAIL] $label"
        FAIL=1
    fi
}

# Core pipelines
run "geometric_engine"    python3 pipelines/geometric_engine.py
run "cf_features"         python3 pipelines/cf_features.py
run "zero_locator"        python3 pipelines/zero_locator.py
run "envelope_pipeline"   python3 pipelines/envelope_pipeline.py
run "envelope_v2"         python3 pipelines/envelope_v2.py

# Standalone application engines
for eng in sparam_engine motor_diagnosis cavity_engine phonon_engine \
           colorimetry_engine wavelet_3d_engine turbulence_engine \
           image_spectral_engine crypto_curve_engine; do
    run "$eng" python3 "applications/${eng}.py"
done

# Engines with graph_engine dependency
cd applications
for eng in graph_engine ast_engine pathfinding_engine; do
    run "$eng" python3 "${eng}.py"
done
cd ..

# Dimensional assertion
run "dim_assert_31" python3 -c "
import sys; sys.path.insert(0, 'pipelines')
from geometric_engine import GeometricEngine, RiemannZeta
e = GeometricEngine(RiemannZeta())
v = e.feature_vector(0.5, 14.134725, 6)
assert len(v) == 31, f'Expected 31, got {len(v)}'
"

# CF features assertion
run "dim_assert_10" python3 -c "
import sys; sys.path.insert(0, 'pipelines')
from cf_features import CFFeatureExtractor
from mpmath import mp, zetazero
mp.dps = 50
v, _ = CFFeatureExtractor.extract(zetazero(1).imag, K=25, dps=50)
assert len(v) == 10, f'Expected 10, got {len(v)}'
"

# Dirichlet raises
run "dirichlet_raises" python3 -c "
import sys; sys.path.insert(0, 'pipelines')
from zero_locator import ZeroLocator
from geometric_engine import DirichletL
try:
    ZeroLocator(DirichletL(4, {1:1.0, 3:-1.0})).scan(0, 20)
    exit(1)
except NotImplementedError:
    pass
"

echo ""
echo "========================================================================"
if [ "$FAIL" -eq 0 ]; then
    echo "  ALL CHECKS PASSED"
else
    echo "  SOME CHECKS FAILED — review output above"
fi
echo "========================================================================"
