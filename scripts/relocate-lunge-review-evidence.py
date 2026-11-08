"""Move frozen QA provenance into tracked docs, without regenerating motion."""
from pathlib import Path
import copy,hashlib,importlib.util,json,shutil
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('evidence_adapter',ROOT/'scripts/build-repair-animations.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads(adapter.CONFIG.read_text(encoding='utf-8-sig'));report=json.loads(adapter.REPORT.read_text())
s=c['exercises']['alternating-lunge'];record=next(r for r in report['animations'] if r['id']=='alternating-lunge')
before=adapter.frame_spec_digest(s);assert before==record['frameSpecSha256']
for frame in record['frames']:assert sha(ROOT/frame['file'])==frame['sha256']
frozen_frames=copy.deepcopy(record['frames'])
target=ROOT/'docs/generated-frames-v3-repairs/alternating-lunge/timing-v2';target.mkdir(parents=True,exist_ok=True)
relocations=[]
for item in s['extraReviewedInputs']:
    src=ROOT/item['file'];dst=target/src.name
    assert sha(src)==item['sha256'];shutil.copy2(src,dst);assert sha(dst)==item['sha256']
    relocations.append({'from':item['file'],'to':dst.relative_to(ROOT).as_posix(),'sha256':item['sha256']})
    item['file']=dst.relative_to(ROOT).as_posix()
after=adapter.frame_spec_digest(s)
adapter.CONFIG.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
record['frameSpecSha256']=after;record['configSha256']=sha(adapter.CONFIG)
assert record['frames']==frozen_frames
report['configSha256']=sha(adapter.CONFIG)
adapter.REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
prepare=ROOT/'output/repair-animations/alternating-lunge/prepare.json'
p=json.loads(prepare.read_text());p['configSha256']=sha(adapter.CONFIG);prepare.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
proof={'reason':'Only frozen evidence path relocation into Git-tracked docs; identical byte SHA and unchanged72 reviewed PNGs. No source motion/timing edits and no RIFE.',
 'relocations':relocations,'previousFrameSpecSha256':before,'relocatedFrameSpecSha256':after,
 'unchangedFrameDigestBin32':hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in frozen_frames)).hexdigest()}
(target/'relocation-proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print('Relocated3 byte-identical QA JSONs into tracked docs; all72 PNG hashes retained.')
