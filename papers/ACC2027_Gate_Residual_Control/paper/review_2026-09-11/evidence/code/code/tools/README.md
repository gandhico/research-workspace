# Build and verification tools

These produced and checked the distribution; you do not need them to
use the package. They are here so the portability claims can be
re-checked rather than taken on trust.

| Script | What it does |
|---|---|
| `test_portability.py <root>` | copies the package elsewhere, imports every module from an unrelated working directory, and fails if any path points back at the original tree |
| `scan_latex_strings.py <root>` | finds LaTeX written into non-raw Python strings, where `\t` and `\r` are silently eaten |
| `make_portable.py <root>` | the rewrite that replaced every absolute path with an `acc2027_paths` symbol (with `rules_extra.py`) |
| `fix_quality.py <root>` | the LaTeX and BOM fixes |
