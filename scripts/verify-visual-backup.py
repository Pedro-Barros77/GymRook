"""Verify the frozen pre-correction snapshot and optionally current originals.

python scripts/verify-visual-backup.py
python scripts/verify-visual-backup.py --current --scope dist/assets --scope output/leg-animations
"""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', type=Path, default=ROOT/'backups/visual-v1-before-fixes-20261107')
    parser.add_argument('--current', action='store_true')
    parser.add_argument('--scope', action='append', default=[])
    args = parser.parse_args()
    manifest = json.loads((args.backup/'manifest.json').read_text(encoding='utf-8'))
    selected = [r for r in manifest['files'] if not args.scope or any(r['file']==p or r['file'].startswith(p.rstrip('/')+'/') for p in args.scope)]
    base = ROOT if args.current else args.backup
    errors = []
    for record in selected:
        path = base/record['file']
        if not path.is_file():
            errors.append({'file':record['file'],'error':'missing'})
        elif path.stat().st_size != record['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            errors.append({'file':record['file'],'error':'changed bytes'})
    print(json.dumps({'base':str(base),'verifiedFiles':len(selected),'errors':errors,'passed':not errors},indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
