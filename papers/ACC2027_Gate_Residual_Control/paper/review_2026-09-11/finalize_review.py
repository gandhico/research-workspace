"""Mechanical cleanup and minimal Overleaf source packaging; no result edits."""
from pathlib import Path
import re, shutil, zipfile, hashlib, json, sys

HERE=Path(__file__).resolve().parent
SRC=HERE/'revised'
main=SRC/'ACC2027.tex'
original_main=main.read_bytes()
original_bib=(SRC/'references.bib').read_bytes()
text=main.read_text(encoding='utf-8-sig')
# Remove non-rendered historical drafts and comment-only lines.
text=re.sub(r'\\begin\{comment\}.*?\\end\{comment\}\s*','',text,flags=re.S)
text='\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('%'))+'\n'
text=re.sub(r'\n{3,}','\n\n',text)
# Declare the final wide results figure earlier so it can float next to the
# discussion instead of being deferred behind the bibliography.
pattern=r'\\begin\{figure\*\}\[t\]\s*\\centering\s*\\includegraphics\[width=\\textwidth\]\{figures/08_Nengo_neuron_family/mechanism_both_platforms.pdf\}.*?\\end\{figure\*\}'
found=re.search(pattern,text,re.S)
if found:
    block=found.group()
    text=text[:found.start()]+text[found.end():]
    marker='\\subsection{Disturbance Rejection and Retention}'
    text=text.replace(marker,block+'\n\n'+marker)
main.write_text(text,encoding='utf-8')
# Keep only cited bibliography records; eliminate unused historical placeholders.
cited=set()
for keys in re.findall(r'\\cite\{([^}]+)\}',text): cited.update(keys.split(','))
bib=(SRC/'references.bib').read_text(encoding='utf-8-sig')
entries={}
for match in re.finditer(r'@\w+\s*\{\s*([^,]+),',bib):
    i=match.start(); start=bib.index('{',i); depth=1; end=start+1
    while depth:
        if bib[end]=='{': depth+=1
        elif bib[end]=='}': depth-=1
        end+=1
    entries[match[1]]=bib[i:end]
assert cited<=entries.keys(), cited-entries.keys()
(SRC/'references.bib').write_text('\n\n'.join(entries[k] for k in entries if k in cited)+'\n',encoding='utf-8')
print('Cleaned source and bibliography. Run the LaTeX build before packaging.')

def package():
    dest=HERE/'output'
    (dest/'pdf').mkdir(parents=True,exist_ok=True)
    shutil.copy2(SRC/'ACC2027.pdf',dest/'pdf/ACC2027_advisor_review.pdf')
    required={'ACC2027.tex','references.bib','ieeeconf.cls'}
    pending=['ACC2027.tex']
    while pending:
        name=pending.pop()
        content=(SRC/name).read_text(encoding='utf-8-sig')
        for token in re.findall(r'\\(?:input|includegraphics)(?:\[[^]]*\])?\{([^}]+)\}',content):
            file=token if Path(token).suffix else token+'.tex'
            assert (SRC/file).is_file(), file
            if file not in required:
                required.add(file)
                if file.endswith('.tex'): pending.append(file)
    bst=SRC/'template/IEEEtran.bst'
    if bst.exists(): shutil.copy2(bst,SRC/'IEEEtran.bst'); required.add('IEEEtran.bst')
    manifest=[]
    with zipfile.ZipFile(dest/'ACC2027_Overleaf_review.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name in sorted(required):
            p=SRC/name
            z.write(p,name)
            manifest.append({'path':name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        if (HERE/'REVIEW.md').exists(): z.write(HERE/'REVIEW.md','REVIEW_NOTES.md')
    (dest/'source_manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Packaged',len(required),'required sources/assets. No historical code/data archives included.')

if __name__=='__main__':
    if '--package' in sys.argv:
        # Packaging must not change the already compiled sources.
        main.write_bytes(original_main)
        (SRC/'references.bib').write_bytes(original_bib)
        package()
