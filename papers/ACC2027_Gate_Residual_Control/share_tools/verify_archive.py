"""Verify ZIP member hashes without extraction. Uses only the standard library."""
import csv
import hashlib
import io
from pathlib import Path
import sys
import zipfile

with zipfile.ZipFile(Path(sys.argv[1])) as z:
    manifests = [n for n in z.namelist() if n.count('/') == 1 and n.endswith('/FILES.csv')]
    if len(manifests) != 1:
        raise SystemExit('Expected one top-level FILES.csv')
    rows = list(csv.DictReader(io.StringIO(z.read(manifests[0]).decode('utf-8'))))
    for row in rows:
        digest = hashlib.sha256()
        size = 0
        with z.open(row['archive_path']) as f:
            for block in iter(lambda: f.read(1024*1024), b''):
                size += len(block)
                digest.update(block)
        if digest.hexdigest() != row['sha256'] or size != int(row['bytes']):
            raise SystemExit('Integrity mismatch: '+row['archive_path'])
    expected = {row['archive_path'] for row in rows} | set(manifests)
    if expected != set(z.namelist()):
        raise SystemExit('Unexpected/unlisted ZIP members')
    print(f'PASS: {len(rows)} payload files verified byte-for-byte in {sys.argv[1]}')
