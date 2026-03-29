#!/usr/bin/env python3
# Copyright (c) 2026 Ricardo Hernández Reveles
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Serie I · AST Spectral Engine
================================
Same architecture. Input: Python source code.
Output: 29 spectral features from the AST graph.

Applications:
  - Clone detection: similar spectrum = semantic clone
  - Vulnerability patterns: spectral signature of unsafe code
  - Complexity analysis: Poisson spectrum = spaghetti, gapped = modular
  - Malware detection: obfuscated code has anomalous spectral statistics
  - Refactoring guidance: critical nodes = functions to split

The motor sees a tree and extracts geometry.
It doesn't know what the code does.
"""

import ast
import numpy as np
from numpy.linalg import eigh
import time, sys, os, textwrap

# Import graph engine
sys.path.insert(0, os.path.dirname(__file__))
from graph_engine import Graph, graph_features, classify_graph, critical_nodes, FNAMES

# ═══════════════════════════════════════════════════════════════
# MODULE 1: AST → GRAPH
# ═══════════════════════════════════════════════════════════════

class ASTGraph:
    """Convert Python AST to labeled graph"""
    
    def __init__(self, source, name='code'):
        self.source = source
        self.name = name
        self.tree = ast.parse(source)
        self.nodes = []      # (id, type_name, depth)
        self.edges = []      # (parent_id, child_id)
        self.node_types = {} # id → type string
        self._walk(self.tree, depth=0)
        self.N = len(self.nodes)
        self.graph = self._build_graph()
    
    def _walk(self, node, depth=0, parent_id=None):
        node_id = len(self.nodes)
        type_name = type(node).__name__
        self.nodes.append((node_id, type_name, depth))
        self.node_types[node_id] = type_name
        
        if parent_id is not None:
            self.edges.append((parent_id, node_id))
        
        for child in ast.iter_child_nodes(node):
            self._walk(child, depth + 1, node_id)
    
    def _build_graph(self):
        if self.N < 2:
            return Graph(np.zeros((2, 2)), name=self.name)
        
        adj = np.zeros((self.N, self.N))
        for i, j in self.edges:
            adj[i, j] = 1
            adj[j, i] = 1
        
        labels = [self.node_types[i] for i in range(self.N)]
        return Graph(adj, labels=labels, name=self.name)
    
    def type_distribution(self):
        """Count of each AST node type"""
        counts = {}
        for _, t, _ in self.nodes:
            counts[t] = counts.get(t, 0) + 1
        return counts
    
    def depth_profile(self):
        """Number of nodes at each depth"""
        max_d = max(d for _, _, d in self.nodes)
        profile = [0] * (max_d + 1)
        for _, _, d in self.nodes:
            profile[d] += 1
        return profile


# ═══════════════════════════════════════════════════════════════
# MODULE 2: CODE-SPECIFIC FEATURES (on top of 29 graph features)
# ═══════════════════════════════════════════════════════════════

def ast_features(source, name='code'):
    """Extract 29 spectral + 15 code-specific = 44 features"""
    ag = ASTGraph(source, name)
    
    # Base: 29 graph spectral features
    gf = graph_features(ag.graph)
    
    # Code-specific features
    types = ag.type_distribution()
    depths = ag.depth_profile()
    N = ag.N
    
    # Structural metrics
    max_depth = len(depths) - 1
    mean_depth = sum(d * c for d, c in enumerate(depths)) / (N + 1e-15)
    branching = np.mean([ag.graph.degrees[i] - 1 for i in range(N) if ag.graph.degrees[i] > 1]) if N > 1 else 0
    
    # Type diversity
    n_types = len(types)
    type_entropy = 0
    for c in types.values():
        p = c / N
        type_entropy -= p * np.log(p + 1e-15)
    
    # Control flow indicators
    n_if = types.get('If', 0)
    n_for = types.get('For', 0) + types.get('While', 0)
    n_try = types.get('Try', 0) + types.get('ExceptHandler', 0)
    n_call = types.get('Call', 0)
    n_func = types.get('FunctionDef', 0) + types.get('AsyncFunctionDef', 0)
    n_class = types.get('ClassDef', 0)
    n_assign = types.get('Assign', 0) + types.get('AugAssign', 0) + types.get('AnnAssign', 0)
    
    # Complexity ratios
    control_ratio = (n_if + n_for + n_try) / (N + 1e-15)
    call_ratio = n_call / (N + 1e-15)
    func_ratio = n_func / (N + 1e-15)
    depth_width_ratio = max_depth / (max(depths) + 1e-15)
    
    # Leaf ratio (nodes with degree 1 = leaves in the tree)
    n_leaves = sum(1 for i in range(N) if ag.graph.degrees[i] <= 1)
    leaf_ratio = n_leaves / (N + 1e-15)
    
    code_feats = np.array([
        max_depth, mean_depth, branching,
        n_types, type_entropy,
        control_ratio, call_ratio, func_ratio,
        depth_width_ratio, leaf_ratio,
        float(n_if), float(n_for), float(n_call),
        float(n_func), float(n_class),
    ], dtype=np.float64)
    
    return np.concatenate([gf, code_feats]), ag

AST_FNAMES = FNAMES + [
    'max_depth', 'mean_depth', 'branching',
    'n_types', 'type_entropy',
    'control_ratio', 'call_ratio', 'func_ratio',
    'depth_width_ratio', 'leaf_ratio',
    'n_if', 'n_for', 'n_call', 'n_func', 'n_class',
]


# ═══════════════════════════════════════════════════════════════
# MODULE 3: CODE CLASSIFIER
# ═══════════════════════════════════════════════════════════════

def classify_code(vec):
    """Classify code quality from spectral + AST features"""
    tags = []
    
    # Graph-level tags
    gtags = classify_graph(vec[:29])
    
    # Code-specific
    max_d = vec[29]
    mean_d = vec[30]
    branch = vec[31]
    n_types = vec[32]
    type_ent = vec[33]
    ctrl = vec[34]
    call_r = vec[35]
    func_r = vec[36]
    dw_ratio = vec[37]
    leaf_r = vec[38]
    n_if = vec[39]
    n_for = vec[40]
    n_call = vec[41]
    n_func = vec[42]
    N = vec[20]
    gap_n = vec[2]
    eff_r = vec[17]
    
    # Complexity
    if max_d > 12:
        tags.append(('DEEP-NESTING', f'depth={int(max_d)}'))
    if ctrl > 0.15:
        tags.append(('CONTROL-HEAVY', f'{ctrl:.0%} control flow'))
    if n_if > 10:
        tags.append(('BRANCH-HEAVY', f'{int(n_if)} if-statements'))
    
    # Modularity
    if func_r > 0.02 and gap_n > 0.1:
        tags.append(('WELL-MODULAR', f'{int(n_func)} functions, gap={gap_n:.3f}'))
    elif func_r < 0.005 and N > 50:
        tags.append(('MONOLITHIC', f'{int(n_func)} functions in {int(N)} nodes'))
    
    # Call complexity
    if call_r > 0.2:
        tags.append(('CALL-HEAVY', f'{call_r:.0%} calls'))
    
    # Tree shape
    if leaf_r > 0.6:
        tags.append(('FLAT', f'{leaf_r:.0%} leaves'))
    elif leaf_r < 0.35:
        tags.append(('DEEPLY-CHAINED', f'{leaf_r:.0%} leaves'))
    
    # Diversity
    if type_ent > 3.0:
        tags.append(('DIVERSE-AST', f'entropy={type_ent:.2f}'))
    elif type_ent < 1.5 and N > 30:
        tags.append(('REPETITIVE', f'entropy={type_ent:.2f}'))
    
    # Robustness
    if eff_r > 0.3:
        tags.append(('FRAGILE-STRUCTURE', f'eff_R={eff_r:.3f}'))
    
    if not tags:
        tags.append(('CLEAN', 'No anomalous signatures'))
    
    return tags


# ═══════════════════════════════════════════════════════════════
# MODULE 4: CLONE DETECTION
# ═══════════════════════════════════════════════════════════════

def spectral_similarity(vec1, vec2):
    """Cosine similarity of spectral feature vectors"""
    # Use graph features only (first 29) for structural comparison
    v1, v2 = vec1[:29], vec2[:29]
    # Normalize
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 < 1e-10 or n2 < 1e-10:
        return 0.0
    return float(np.dot(v1, v2) / (n1 * n2))


# ═══════════════════════════════════════════════════════════════
# DEMO
# ═══════════════════════════════════════════════════════════════

# Sample code snippets for testing
SAMPLES = {
'clean_function': '''
def fibonacci(n):
    if n <= 1:
        return n
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
    return b
''',

'nested_complex': '''
def process(data, config):
    results = []
    for item in data:
        if item.get('type') == 'A':
            for sub in item['children']:
                if sub['value'] > config['threshold']:
                    try:
                        result = transform(sub)
                        if result is not None:
                            for r in result:
                                if validate(r):
                                    results.append(r)
                    except ValueError:
                        if config.get('strict'):
                            raise
                        else:
                            log_error(sub)
    return results
''',

'clone_fibonacci': '''
def fib(x):
    if x <= 1:
        return x
    prev, curr = 0, 1
    for _ in range(2, x + 1):
        prev, curr = curr, prev + curr
    return curr
''',

'spaghetti': '''
x = input()
if x == '1':
    a = 5
    b = a + 3
    if b > 7:
        c = b * 2
        print(c)
    else:
        c = b - 1
        if c < 3:
            print("low")
        else:
            print("mid")
elif x == '2':
    a = 10
    if a > 5:
        b = a / 2
        print(b)
    else:
        print(a)
else:
    print("unknown")
    a = 0
    b = 0
    c = 0
''',

'well_structured': '''
class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.results = []
    
    def validate(self, item):
        return item is not None and item.get('value', 0) > 0
    
    def transform(self, item):
        return item['value'] * self.config.get('factor', 1)
    
    def process(self, data):
        for item in data:
            if self.validate(item):
                self.results.append(self.transform(item))
        return self.results
    
    def summary(self):
        if not self.results:
            return {'count': 0, 'mean': 0}
        return {
            'count': len(self.results),
            'mean': sum(self.results) / len(self.results),
        }
''',

'obfuscated': '''
_ = lambda __: __import__('builtins').getattr(__import__('builtins'), 'print')(__);
__ = lambda ___, ____: (lambda _____: _____(_____, ___, ____))(lambda ______, ___, ____: ___ if ___ <= 1 else ______(_______,  ___ - 1, ____) + ______(_______,  ___ - 2, ____))
_(_('hello'))
''',

'data_pipeline': '''
def load(path):
    with open(path) as f:
        return f.readlines()

def parse(lines):
    return [line.strip().split(',') for line in lines]

def filter_valid(records):
    return [r for r in records if len(r) >= 3]

def transform(records):
    return [{'name': r[0], 'value': float(r[1]), 'tag': r[2]} for r in records]

def aggregate(records):
    totals = {}
    for r in records:
        tag = r['tag']
        totals[tag] = totals.get(tag, 0) + r['value']
    return totals

def pipeline(path):
    lines = load(path)
    records = parse(lines)
    valid = filter_valid(records)
    transformed = transform(valid)
    return aggregate(transformed)
''',
}


if __name__ == '__main__':
    print("=" * 72)
    print("AST SPECTRAL ENGINE — DEMO")
    print("29 graph + 15 code = 44 features from Python source")
    print("=" * 72)
    
    # ── Analyze all samples ──
    print(f"\n{'─'*72}")
    print("1. CODE CLASSIFICATION")
    print(f"{'─'*72}")
    
    results = {}
    for name, code in SAMPLES.items():
        vec, ag = ast_features(code, name)
        tags = classify_code(vec)
        results[name] = {'vec': vec, 'ag': ag, 'tags': tags}
        
        tag_str = ', '.join(t[0] for t in tags)
        print(f"\n  {name:>20} (N={ag.N:3d}, depth={int(vec[29])}): {tag_str}")
        for t, d in tags:
            print(f"    {t:>20}: {d}")
    
    # ── Key features ──
    print(f"\n{'─'*72}")
    print("2. KEY FEATURES")
    print(f"{'─'*72}")
    
    display = list(SAMPLES.keys())[:7]
    key_feats = ['algebraic_conn', 'gap_norm', 'level_repulsion', 'eff_resistance',
                 'partition_bal', 'health',
                 'max_depth', 'mean_depth', 'branching', 'control_ratio',
                 'call_ratio', 'func_ratio', 'type_entropy', 'leaf_ratio']
    
    print(f"\n  {'feature':>16}", end='')
    for n in display:
        print(f" {n[:7]:>7}", end='')
    print()
    
    for fn in key_feats:
        j = AST_FNAMES.index(fn)
        print(f"  {fn:>16}", end='')
        vals = [results[n]['vec'][j] for n in display]
        for v in vals:
            print(f" {v:7.3f}", end='')
        if np.std(vals) > 0.1 * (np.mean(np.abs(vals)) + 1e-10):
            print("  *", end='')
        print()
    
    # ── Clone detection ──
    print(f"\n{'─'*72}")
    print("3. CLONE DETECTION (spectral similarity)")
    print(f"{'─'*72}")
    
    names = list(SAMPLES.keys())
    print(f"\n  {'':>14}", end='')
    for n in names:
        print(f" {n[:7]:>7}", end='')
    print()
    
    for ni in names:
        print(f"  {ni[:14]:>14}", end='')
        for nj in names:
            sim = spectral_similarity(results[ni]['vec'], results[nj]['vec'])
            marker = '█' if sim > 0.95 else '▓' if sim > 0.8 else '░' if sim > 0.6 else ' '
            print(f" {sim:6.3f}{marker}", end='')
        print()
    
    # Highlight clones
    print(f"\n  Potential clones (similarity > 0.85):")
    for i, ni in enumerate(names):
        for j, nj in enumerate(names):
            if j <= i: continue
            sim = spectral_similarity(results[ni]['vec'], results[nj]['vec'])
            if sim > 0.85:
                print(f"    {ni} ↔ {nj}: {sim:.4f}")
    
    # ── Critical nodes (refactoring targets) ──
    print(f"\n{'─'*72}")
    print("4. REFACTORING TARGETS (critical AST nodes)")
    print(f"{'─'*72}")
    
    for name in ['nested_complex', 'spaghetti', 'well_structured']:
        ag = results[name]['ag']
        crits = critical_nodes(ag.graph, top_k=5)
        print(f"\n  {name}:")
        print(f"  {'rank':>4} {'node':>5} {'type':>18} {'degree':>7} {'score':>8}")
        for i, c in enumerate(crits):
            print(f"  {i+1:4d} {c['node']:5d} {str(c['label']):>18} {c['degree']:7d} {c['score']:8.3f}")
    
    # ── AST node type distribution ──
    print(f"\n{'─'*72}")
    print("5. AST TYPE DISTRIBUTION")
    print(f"{'─'*72}")
    
    for name in ['clean_function', 'obfuscated', 'data_pipeline']:
        ag = results[name]['ag']
        types = ag.type_distribution()
        top = sorted(types.items(), key=lambda x: -x[1])[:8]
        print(f"\n  {name}: {', '.join(f'{t}({c})' for t,c in top)}")
    
    # ── Cross-domain ──
    print(f"\n{'─'*72}")
    print("6. CROSS-DOMAIN MAPPING")
    print(f"{'─'*72}")
    print(f"""
  ζ engine:              AST engine:
  ─────────              ────────────
  t                      tree traversal order
  zeros of ζ             eigenvalues of AST Laplacian
  spectral gap           modularity of code
  f(b) envelope          depth decay of AST
  cos(ln(p)·γ) phase     node type pattern
  Canal A (arithmetic)   node labels (If, For, Call...)
  Canal B (amplitude)    spectral structure of tree
  orthogonality          semantic vs syntactic similarity
  V(σ,t) landscape       code complexity surface
  critical nodes         refactoring targets
  
  The spectrum is the spectrum.
""")
    
    # ── Throughput ──
    code = SAMPLES['well_structured']
    t0 = time.time()
    for _ in range(200):
        ast_features(code)
    dt = time.time() - t0
    
    print(f"  Throughput: {200/dt:.0f} analyses/second")
    print(f"  Per file: {dt/200*1000:.1f} ms")
    
    print(f"\n{'='*72}")
    print("ENGINE READY")
    print(f"  Input: Python source code (string or file)")
    print(f"  Output: 44 features + tags + clones + refactoring targets")
    print(f"{'='*72}")
