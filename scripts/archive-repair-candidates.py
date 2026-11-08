"""Freeze selected round-3 candidates before a reviewed replacement."""
from pathlib import Path
import argparse,hashlib,json,shutil
ROOT=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('--exercise',action='append',default=[]);p.add_argument('--path',action='append',default=[]);a=p.parse_args()
    target=ROOT/'backups'/a.name
    if target.exists():raise ValueError('Archive already exists; refuse overwrite.')
    files=set()
    paths=[ROOT/x for x in a.path]
    for item in a.exercise:
        paths += [ROOT/'output/repair-animations'/item,ROOT/'docs/generated-frames-v3-repairs'/item]
        paths += list((ROOT/'dist/assets/animations-v3').glob(item+'.*'))
    paths += [ROOT/'docs/generated-frames-v3-repairs/config.json',ROOT/'docs/repair-animations-build.json',ROOT/'dist/assets/animations-v3/manifest.json',ROOT/'scripts/build-repair-animations.py']
    for entry in paths:
        if entry.is_file():files.add(entry)
        elif entry.is_dir():files.update(x for x in entry.rglob('*') if x.is_file())
    entries=[]
    for src in sorted(files):
        rel=src.relative_to(ROOT);dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
        checksum=sha(src);assert sha(dst)==checksum
        entries.append({'file':rel.as_posix(),'sha256':checksum,'bytes':src.stat().st_size})
    manifest={'reason':a.name,'files':entries,'totalBytes':sum(x['bytes'] for x in entries)}
    target.mkdir(parents=True,exist_ok=True);(target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Archived {len(entries)} verified files, {manifest["totalBytes"]} bytes to {target}')
if __name__=='__main__':main()
