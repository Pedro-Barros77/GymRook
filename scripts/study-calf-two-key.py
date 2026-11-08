"""Isolated two-original-key RIFE study; never edits active config/media/core."""
from pathlib import Path
import copy,hashlib,importlib.util,json
from PIL import Image,ImageDraw
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/generated-frames-v4-followup/standing-machine-calf-raise'
STUDY=ROOT/'output/followup-round4/calf-two-key-study'
STUDY.mkdir(parents=True,exist_ok=True)
exercise='standing-machine-calf-raise'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def label(p): return p.relative_to(ROOT).as_posix()
def write(p,d): p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

orig=[BASE/'start-v2.png',BASE/'end-v1.png']
before={p:sha(p) for p in orig}
keys=[]
for i,p in enumerate(orig):
 im=Image.open(p).convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
 dest=STUDY/f'key-{i:02d}.png';im.save(dest)
 keys.append({'progress':i,'imageOverride':label(dest),'imageOverrideSha256':sha(dest)})
source_index={'id':exercise,'sourceKind':'image-keyframes','method':'Two actual original generated bottom/top poses; one shared512 normalization, no human geometry warp or new artwork.','originalSources':[{'file':label(p),'sha256':sha(p)} for p in orig],'keys':keys}
write(STUDY/'source-index.json',source_index)

config=json.loads((ROOT/'docs/generated-frames-v4-followup/config.json').read_text(encoding='utf-8'))
motion={'sourceKind':'image-keyframes','sheet':label(STUDY/'source-index.json'),'sheetSha256':sha(STUDY/'source-index.json'),
 'prepareReady':True,'motionReady':True,'exportReady':False,'sourceReview':'Root and independent source owner visually preferred the two original fullbody calf keys over the knee-bending9pose sheet. Actual intermediate frames remain a study only.',
 'reviewedKeyCount':2,'anchors':keys,'cycle':'ping-pong','frameCount':36,'phaseEasing':'cosine','referenceIndex':0,
 'registration':{'enabled':True,'regions':[[x/512 for x in r] for r in [[41,90,65,426],[78,32,140,59]]],'maxTranslationPixels':2,'minScore':.72},
 'preserveStaticRects':[],'interpolationOverrides':[]}
config['exercises']={exercise:motion}
configpath=STUDY/'study-config.json';write(configpath,config)

module_spec=importlib.util.spec_from_file_location('isolated_two_key_calf_adapter',ROOT/'scripts/build-repair-animations.py')
adapter=importlib.util.module_from_spec(module_spec);module_spec.loader.exec_module(adapter)
adapter.CONFIG,adapter.WORK,adapter.REPORT,adapter.MEDIA=configpath,STUDY,STUDY/'study-report.json',STUDY/'not-exported-media'
adapter.IDS=(exercise,)
engine,helpers=adapter.configured_engine()
record=engine.prepare(exercise,motion,config)
records={exercise:record}
engine.build_frames([exercise],config['exercises'],config,records)
frames=sorted((STUDY/exercise/'frames').glob('frame_*.png'))
assert len(frames)==36
hashes=[sha(p) for p in frames]
assert all(hashes[i]==hashes[36-i] for i in range(19,36))
assert all(sha(p)==h for p,h in before.items())
images=[Image.open(p).convert('RGB') for p in frames]

def contact(ims,titles,path,columns):
 w,h=ims[0].size;rows=(len(ims)+columns-1)//columns
 panel=Image.new('RGB',(w*columns,(h+22)*rows),'white');d=ImageDraw.Draw(panel)
 for i,(im,t) in enumerate(zip(ims,titles)):
  x=(i%columns)*w;y=(i//columns)*(h+22);d.text((x+4,y+4),t,fill='black');panel.paste(im,(x,y+22))
 panel.save(path)

contact([x.resize((320,320)) for x in images[:19]],[f'Frame {i+1}' for i in range(19)],STUDY/'full19-contact.png',5)
lower=[x.crop((270,235,420,475)).resize((300,480)) for x in images[:19]]
feet=[x.crop((280,350,420,470)).resize((350,300)) for x in images[:19]]
contact(lower,[f'Frame {i+1}' for i in range(19)],STUDY/'knees-ankles19-critical.png',5)
contact(feet,[f'Frame {i+1}' for i in range(19)],STUDY/'feet19-critical.png',5)
for start in range(0,19,5): contact(lower[start:start+5],[f'Frame {i+1}' for i in range(start,min(start+5,19))],STUDY/f'lower-group-{start//5+1}.png',3)
onions=[Image.blend(images[i],images[i+1],.5).resize((320,320)) for i in range(18)]
contact(onions,[f'{i+1}/{i+2}' for i in range(18)],STUDY/'full18-onions.png',6)
write(STUDY/'study-result.json',{'id':exercise,'studyOnly':True,'fps':12,'frameCount':36,'durationSeconds':3,'originalsUnchanged':True,
 'generator':{'file':label(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve())},'sourceIndex':{'file':label(STUDY/'source-index.json'),'sha256':sha(STUDY/'source-index.json')},
 'record':record,'frames':[{'file':label(p),'sha256':h} for p,h in zip(frames,hashes)],
 'registration':[a['registration'] for a in record['anchors']],
 'frameDigestBin32':hashlib.sha256(b''.join(bytes.fromhex(h) for h in hashes)).hexdigest(),
 'note':'Study actual head/knee/ankle/forefoot travel. No canonical machine or plate fix here, no media export and no clinical3D/anatomy certification.'})
print(json.dumps({'study':label(STUDY),'frames':36,'sourceKeys':2,'globalConfigOrMediaMutated':False,'registration':[a['registration']['translationPixels'] for a in record['anchors']]}))
