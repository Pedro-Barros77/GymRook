"""Import a frozen, explicitly reviewed native PNG loop without interpolation."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('id');p.add_argument('index');p.add_argument('--review',required=True);a=p.parse_args()
indexpath=ROOT/a.index;i=json.loads(indexpath.read_text());configpath=ROOT/'docs/generated-frames-v3-repairs/config.json'
c=json.loads(configpath.read_text(encoding='utf-8-sig'));s=c['exercises'][a.id]
assert i['id']==a.id and i['sourceKind']=='reviewed-png-loop' and i['frameCount']==36 and i['fps']==12
inputs={i['generator']:i['generatorSha256'],i['parameters']:sha(ROOT/i['parameters']),**i['inputs']}
for f in i['sourceFrames']+[{'file':k,'sha256':v} for k,v in inputs.items()]:assert sha(ROOT/f['file'])==f['sha256'],f['file']
for key in ['staticMask','preserveOutsideRectsFromFrameLoop','nativeBodyPixelPreservation']:
    s.pop(key,None)
s.update(sourceKind='reviewed-png-loop',sheet=indexpath.relative_to(ROOT).as_posix(),sheetSha256=sha(indexpath),grid=[1,1],anchors=[],sourceFrames=i['sourceFrames'],
         prepareReady=True,motionReady=True,exportReady=True,sourceReview=a.review)
s['extraReviewedInputs']=[{'file':k,'sha256':v} for k,v in inputs.items()]
if i.get('nativeBodyPixelPreservation'):s['nativeBodyPixelPreservation']=i['nativeBodyPixelPreservation']
configpath.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Imported reviewed native PNG loop; output frames not yet copied/encoded.')
