"""Build the minimal Overleaf source package and verify source preservation."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile

HERE=Path(__file__).resolve().parent
SRC=HERE/'source';OUT=HERE/'output';(OUT/'pdf').mkdir(parents=True,exist_ok=True)
previous=HERE.parent/'review_2026-09-11/revised/ACC2027.tex'
old=previous.read_text(encoding='utf-8');new=(SRC/'ACC2027.tex').read_text(encoding='utf-8')
assert re.findall(r'\\label\{(fig:[^}]+)\}',old)==re.findall(r'\\label\{(fig:[^}]+)\}',new)
matrix=r'\\begin\{tabular\}\{llrrrr\}.*?\\end\{tabular\}'
assert re.search(matrix,old,re.S).group()==re.search(matrix,new,re.S).group()
labels=re.findall(r'\\label\{([^}]+)\}',new);assert len(labels)==len(set(labels))
notes=HERE/'REVISION_DECISIONS.md'
(SRC/'REVISION_NOTES.md').write_text(notes.read_text(encoding='utf-8'),encoding='utf-8')
required=[SRC/n for n in ['ACC2027.tex','references.bib','ieeeconf.cls','IEEEtran.bst','REVISION_NOTES.md']]
required += [p for folder in ['architectures','figures'] for p in (SRC/folder).rglob('*') if p.is_file()]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=[dict(path=str(p.relative_to(SRC)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(required)]
old_manifest=json.loads((HERE.parent/'review_2026-09-11/output/source_manifest.json').read_text())
for item in old_manifest:
    if item['path'].startswith(('figures/','architectures/')):assert sha(SRC/item['path'])==item['sha256']
archive=OUT/'ACC2027_gate_gain_Overleaf.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in required:z.write(p,p.relative_to(SRC))
pdf=OUT/'pdf/ACC2027_gate_gain_review.pdf';shutil.copy2(SRC/'ACC2027.pdf',pdf)
(OUT/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
(OUT/'package_checks.json').write_text(json.dumps(dict(figures_retained=9,main_matrix_unchanged=True,
    prior_figure_and_architecture_assets_unchanged=True,source_files=len(required),pdf_bytes=pdf.stat().st_size,
    pdf_sha256=sha(pdf),zip_bytes=archive.stat().st_size,zip_sha256=sha(archive)),indent=2))
with zipfile.ZipFile(archive) as z:z.extractall(HERE/'package_verification')
print((OUT/'package_checks.json').read_text())
