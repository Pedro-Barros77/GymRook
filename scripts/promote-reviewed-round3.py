"""Import root/owner-approved frozen study inputs; no artwork mutation."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent.parent
P=ROOT/'docs/generated-frames-v3-repairs/config.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads(P.read_text(encoding='utf-8-sig'))
name='lying-leg-curl';path=ROOT/'docs/generated-frames-v3-repairs'/name/'rig-v2/source-index-rig.json'
index=json.loads(path.read_text());s=c['exercises'][name]
for key in ['staticMask','preserveOutsideRectsFromFrameLoop']:
    s.pop(key,None)
s.update(sourceKind='reviewed-png-loop',sheet=path.relative_to(ROOT).as_posix(),sheetSha256=sha(path),grid=[1,1],anchors=[],sourceFrames=index['sourceFrames'],prepareReady=True,motionReady=True,exportReady=True,
    sourceReview='Root and legs owner approved native V2 after all19 contact crops/full views. Original generated raster leg restored to approved girth, rigid tibia100px and lever92.892px; tangent pad stays outside leg core. Final36PNG bytes copied without RIFE or old static mask. See rig-v2/freeze-verification.json and owner/root reviews.')
inputs={index['generator']:index['generatorSha256'],index['parameters']:sha(ROOT/index['parameters']),**index['inputs']}
s['extraReviewedInputs']=[{'file':p,'sha256':v} for p,v in inputs.items()]
name='reverse-pec-deck';s=c['exercises'][name]
s['staticMask']=json.loads((ROOT/'docs/generated-frames-v3-repairs'/name/'static-mask-spec-v2.json').read_text())
s['sourceReview']='Root visually approved V2 elevated-elbow rear-delt source and final19upper crops; independent legs owner checked19 actual composites and18 onions. Adaptive per-frame static masks preserve connected booms, opaque hands over tower, canonical head/seat/legs/tower with continuous waist handoff. Old V1/unversioned mask packets rejected.'
s['exportReady']=True
name='alternating-lunge';s=c['exercises'][name]
study=ROOT/'output/repair-animations/candidates/lunge-retime-v2'
candidate=json.loads((study/'study-config.json').read_text())['exercises'][name]
s['anchors']=candidate['anchors'];s['stepPhaseTiming']=candidate['stepPhaseTiming'];s.pop('loopCorrection',None)
s['sourceReview']='Root and independent legs reviewer approved eased72frame/6s study, all foot-transfer crops and both seams. Same inherited descent drawings; foot transfer8frames and knee descent10frames each use half cosine; returns copy forward17frames exactly. No .9 interpolation overrides.'
s['exportReady']=True
s['extraReviewedInputs']=[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in [study/'study-result.json',study/'independent-timing-review.json',study/'actual-foot-comparison.json']]
P.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Imported approved flexoraV2, reverseV2 masks and eased lunge study.')
