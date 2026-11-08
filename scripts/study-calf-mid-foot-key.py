"""Isolated3-key foot estimates composed onto the unchanged2-key body clock.

Do not run until root approves the repaired midpoint image and exact foot ROI.
No source/config/media is changed. Source times are never locally retimed.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import argparse,hashlib,json,subprocess,time
import cv2
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'output/followup-round4/calf-two-key-study'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mid',type=Path,required=True)
parser.add_argument('--roi',type=int,nargs=4,required=True,metavar=('X0','Y0','X1','Y1'))
parser.add_argument('--output',type=Path,default=ROOT/'output/followup-round4/calf-two-key-inference-repair/round2-mid-key')
args=parser.parse_args()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def label(p):return p.resolve().relative_to(ROOT).as_posix()
def write(p,j):p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def rgb(p):
 im=Image.open(p)
 if im.size!=(512,512):raise ValueError('Approved source must already be512square: '+str(p))
 return np.asarray(im.convert('RGB')).copy()

mid=args.mid.resolve();out=args.output.resolve()
if ROOT not in out.parents:raise ValueError('Study output must remain in workspace.')
if not mid.is_file():raise ValueError('Approved midpoint file is required before running.')
record=json.loads((SOURCE/'study-result.json').read_text(encoding='utf-8'))['record']
plans=record['frames'][:19];keys=[ROOT/a['file'] for a in record['anchors']]
baseline=[ROOT/f['file'] for f in plans];before={label(p):sha(p) for p in keys+baseline+[mid]}
raw=[rgb(p) for p in baseline];m=rgb(mid)
x0,y0,x1,y1=args.roi
if not(0<=x0<x1<=512 and 0<=y0<y1<=512):raise ValueError('Invalid ROI.')
region=np.zeros((512,512),dtype=bool);region[y0:y1,x0:x1]=True
if np.any(m[~region]!=raw[9][~region]):raise ValueError('Mid image differs from actual rawframe10 outside approved foot ROI.')
out.mkdir(parents=True,exist_ok=False)
runtime=ROOT/'.cache/qa-pec-deck-interpolation/python311/python.exe'
helper=ROOT/'scripts/rife-batch.py';model=ROOT/'.cache/qa-pec-deck-interpolation/rife425'
variants=[('forward-scale1',False,1),('reverse-scale1',True,1),
          ('forward-scale05',False,.5),('reverse-scale05',True,.5)]
report={'studyOnly':True,'physicalClock':'Original2-key cosine progress. Midkey atphysical.5; no retiming.',
 'generator':{'file':label(Path(__file__)),'sha256':sha(Path(__file__))},
 'approvedMid':{'file':label(mid),'sha256':sha(mid)},'footROI':args.roi,
 'sourceAndBaselineHashes':before,
 'ankleSkinGuard':{'method':'Baseline hue4..30/S>45/V>120, per-frame anatomical calf corridor, dilated1pixel. No dark-shoe or sole colour recovery.',
   'midpointPolicy':'Atphysical.5 this matches root V4 anatomical bounds x325..385, nearx<357/y<398, farx>=357/y<391.',
   'dynamicBounds':'xMin334-18t;xMax394-18t;nearFarSplit366-18t;nearMaxY420-44t;farMaxY412-42t'},
 'variants':[]}
crop=(286,338,410,466)
for name,reverse,scale in variants:
 folder=out/name;folder.mkdir();est=folder/'estimates';est.mkdir();dest=folder/'frames';dest.mkdir();masks=folder/'skin-core';masks.mkdir()
 jobs=[];timing=[]
 for i,plan in enumerate(plans):
  t=float(plan.get('progress',0));path=est/f'frame_{i+1:04d}.png'
  if i in (0,18):path.write_bytes(baseline[i].read_bytes());timing.append({'frame':i+1,'physicalT':t,'copiedEndpoint':True});continue
  if abs(t-.5)<1e-10:path.write_bytes(mid.read_bytes());timing.append({'frame':i+1,'physicalT':t,'copiedMidKey':True});continue
  a,b,local=(keys[0],mid,2*t) if t<.5 else(mid,keys[1],2*t-1)
  jobs.append({'input0':str(b if reverse else a),'input1':str(a if reverse else b),
               'timestep':1-local if reverse else local,'output':str(path)})
  timing.append({'frame':i+1,'physicalT':t,'segmentT':local,'actualInferenceT':1-local if reverse else local,'reversed':reverse})
 manifest=folder/'jobs.json';write(manifest,jobs);started=time.monotonic()
 print('Rendering3-key foot estimate '+name+' with original physical times',flush=True)
 run=subprocess.run([str(runtime),str(helper),'--manifest',str(manifest),'--model-dir',str(model),'--threads','8','--scale',str(scale)],cwd=ROOT,text=True,capture_output=True)
 (folder/'inference.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
 if run.returncode:raise RuntimeError(name+' inference failed; see study log.')
 composed=[];records=[];outside_error=0;skin_error=0
 for i,p in enumerate(sorted(est.glob('frame_*.png'))):
  estimate=rgb(p);body=raw[i]
  t=float(plans[i].get('progress',0));yy,xx=np.mgrid[:512,:512]
  hsv=cv2.cvtColor(body,cv2.COLOR_RGB2HSV)
  hue_skin=(hsv[:,:,0]>=4)&(hsv[:,:,0]<=30)&(hsv[:,:,1]>45)&(hsv[:,:,2]>120)
  split=366-18*t
  anatomical=(xx>=334-18*t)&(xx<=394-18*t)&(((xx<split)&(yy<420-44*t))|((xx>=split)&(yy<412-42*t)))
  skin=cv2.dilate((hue_skin&anatomical).astype('uint8'),np.ones((3,3),dtype='uint8'))
  core=skin.astype(bool)&region
  final=body.copy();final[region]=estimate[region];final[core]=body[core]
  if i==9 and np.any(final!=m):raise ValueError('Ankle guard changed the approved middle foot key; inspect before continuing.')
  outside_error=max(outside_error,int(np.abs(final[~region].astype(int)-body[~region].astype(int)).max()))
  if np.any(core):skin_error=max(skin_error,int(np.abs(final[core].astype(int)-body[core].astype(int)).max()))
  q=dest/f'frame_{i+1:04d}.png';Image.fromarray(final).save(q)
  mp=masks/f'mask_{i+1:04d}.png';Image.fromarray(core.astype('uint8')*255).save(mp)
  records.append({'frame':i+1,'file':label(q),'sha256':sha(q),'footEstimate':{'file':label(p),'sha256':sha(p)},'skinCoreMask':{'file':label(mp),'sha256':sha(mp)},'protectedSkinPixels':int(core.sum())})
  composed.append(Image.fromarray(final))
 assert len(composed)==19 and outside_error==skin_error==0
 row=Image.new('RGB',(1860,410),'white');dr=ImageDraw.Draw(row)
 for col,i in enumerate(range(7,12)):
  row.paste(composed[i].crop(crop).resize((372,384),Image.Resampling.NEAREST),(col*372,26));dr.text((col*372+6,6),name+' frame'+str(i+1),fill='black')
 row.save(folder/'feet8-12-native.png')
 contact=Image.new('RGB',(1750,1640),'white');dr=ImageDraw.Draw(contact)
 for i,img in enumerate(composed):
  x,y=(i%5)*350,(i//5)*410;contact.paste(img.crop(crop).resize((350,361),Image.Resampling.NEAREST),(x,y+24));dr.text((x+5,y+5),str(i+1),fill='black')
 contact.save(folder/'feet19-native.png')
 report['variants'].append({'name':name,'scale':scale,'reverseInputs':reverse,'seconds':time.monotonic()-started,
   'outsideROIMaxRGBError':outside_error,'protectedSkinCoreMaxRGBError':skin_error,'timing':timing,'frames':records})
for p,h in before.items():assert sha(ROOT/p)==h
report['sourcesAndBodyUnchanged']=True
write(out/'study-index.json',report)
print(json.dumps({'study':label(out),'sameClockVariants':len(variants),'sourcesAndBodyUnchanged':True}),flush=True)
