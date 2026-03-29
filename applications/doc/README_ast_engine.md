# ast_engine.py — Magic Numbers

AST spectral engine. 29 graph features + 15 code-specific = 44 features from Python source.

## Dependencies

Imports `graph_features`, `classify_graph`, `critical_nodes`, `FNAMES` from `graph_engine.py`. All 29 graph features and their magic numbers are documented in README_graph_engine.md.

## Code-specific features (the 15 additions)

No magic numbers in the 15 code feature computations themselves — they are direct counts and ratios from the AST structure. The only numerical constant is:

| Value | Location | Meaning |
|-------|----------|---------|
| `1e-15` | multiple denominators | Zero-guard in ratios: `N + 1e-15`, `max(depths) + 1e-15`. Prevents division by zero on empty or trivial ASTs. |

## Classifier thresholds

| Value | Location | Meaning |
|-------|----------|---------|
| `12` | `max_d > 12` | DEEP-NESTING: max AST depth > 12. A function nested 12 levels deep is unreadable by any reasonable standard. Linux kernel style guide limits to ~3 levels of indentation; 12 is extreme. |
| `0.15` | `ctrl > 0.15` | CONTROL-HEAVY: more than 15% of AST nodes are control flow (If, For, While, Try, ExceptHandler). Typical clean code has 5-10% control flow; > 15% indicates complex branching logic. |
| `10` | `n_if > 10` | BRANCH-HEAVY: more than 10 if-statements in a single scope. Suggests a switch-case pattern or deeply branching logic. |
| `0.02` | `func_r > 0.02` | Modular code: function definitions are > 2% of nodes. Combined with `gap_n > 0.1` (spectral gap indicates separation), this identifies well-structured code with multiple functions. |
| `0.1` | `gap_n > 0.1` | Spectral gap threshold for modularity. A gap in the Laplacian eigenvalues means the AST has natural clusters (functions, classes). |
| `0.005` | `func_r < 0.005` | MONOLITHIC: fewer than 0.5% of nodes are function definitions. In a 200-node AST, this means 0-1 functions. |
| `50` | `N > 50` | Minimum AST size for MONOLITHIC diagnosis. A 20-node script without functions is normal; a 200-node script without functions is a code smell. |
| `0.2` | `call_r > 0.2` | CALL-HEAVY: more than 20% of nodes are function calls. High call density may indicate deeply chained operations or a pipeline pattern. |
| `0.6` | `leaf_r > 0.6` | FLAT: more than 60% of nodes are leaves (degree ≤ 1). Typical of linear code without nesting. |
| `0.35` | `leaf_r < 0.35` | DEEPLY-CHAINED: fewer than 35% leaves. Most nodes have children, indicating deeply nested structure. |
| `3.0` | `type_ent > 3.0` | DIVERSE-AST: Shannon entropy of node types > 3.0 bits. Indicates a variety of constructs (functions, classes, loops, exceptions, comprehensions). |
| `1.5` | `type_ent < 1.5` | REPETITIVE: entropy < 1.5 bits and N > 30. The code uses only a few node types repeatedly (e.g., all assignments). |
| `30` | `N > 30` | Minimum size for REPETITIVE diagnosis. Small scripts are naturally low-entropy. |
| `0.3` | `eff_r > 0.3` | FRAGILE-STRUCTURE: high normalized effective resistance. The AST graph is structurally vulnerable — removing a critical node disconnects large subtrees. |

## Clone detection

| Value | Location | Meaning |
|-------|----------|---------|
| `29` | `vec1[:29]` | Uses only the 29 graph spectral features for structural similarity, not the 15 code-specific features. This ensures comparison is purely structural (isomorphism-like) rather than syntactic. |
| `1e-10` | norm guard | Cosine similarity is undefined for zero vectors. |
| `0.85` | `sim > 0.85` | Clone detection threshold: cosine similarity > 0.85 flags a potential clone pair. Empirically, renamed clones (same structure, different variable names) yield similarity ≈ 1.0. |
| `0.95, 0.8, 0.6` | visualization markers | `█` > 0.95 (near-identical), `▓` > 0.8 (strong structural similarity), `░` > 0.6 (moderate similarity). |
