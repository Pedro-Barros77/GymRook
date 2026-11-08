"""Compare same-clock RIFE direction/scales for calf-foot occlusion artefacts.

Only a new study output is written. No source, global config/report or media
is changed. Every job uses the original two registered keys and original time.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import hashlib,json,subprocess,time

ROOT=Path(__file__).resolve().parent.parent
SOURCE=ROOT/'output/followup-round4/calf-two-key-study'
OUT=ROOT/'output/followup-round4/calf-two-key-inference-repair/round1'
OUT.mkdir(parents=True,exist_ok=False)
record=json.loads((SOURCE/'study-result.json').read_text(encoding='utf-8'))['record']
plans=record['frames'][:19]
assert len(plans)==19
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def label(p):return p.relative_to(ROOT).as_posix()
def write(p,j):p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
inputs=[ROOT/a['file'] for a in record['anchors']]
input_hashes={label(p):sha(p) for p in inputs}
baseline=[ROOT/p['file'] for p in plans]
baseline_hashes={label(p):sha(p) for p in baseline}
runtime=ROOT/'.cache/qa-pec-deck-interpolation/python311/python.exe'
helper=ROOT/'scripts/rife-batch.py'
model=ROOT/'.cache/qa-pec-deck-interpolation/rife425'
variants=[('forward-scale05',False,.5),('reverse-scale05',True,.5),
          ('reverse-scale1',True,1),('forward-scale2',False,2),('reverse-scale2',True,2)]
result={'studyOnly':True,'sourceResult':{'file':label(SOURCE/'study-result.json'),'sha256':sha(SOURCE/'study-result.json')},
 'generator':{'file':label(Path(__file__)),'sha256':sha(Path(__file__))},
 'inputHashes':input_hashes,'baselineFrameHashes':baseline_hashes,
 'timePolicy':'Original physical time only. Reversed inputs use1-t, never local retiming.',
 'inferenceHelper':{'file':label(helper),'sha256':sha(helper)},
 'variants':[]}
all_paths={'baseline-scale1':baseline}
for name,reverse,scale in variants:
 folder=OUT/name;folder.mkdir();frames=folder/'frames';frames.mkdir()
 jobs=[]
 for i,p in enumerate(plans):
  path=frames/f'frame_{i+1:04d}.png'
  if i in (0,18):path.write_bytes(baseline[i].read_bytes());continue
  t=float(p['actualTimestep']);assert abs(t-float(p['timestep']))<1e-12
  jobs.append({'input0':str(inputs[1 if reverse else 0]),'input1':str(inputs[0 if reverse else 1]),
               'timestep':1-t if reverse else t,'output':str(path)})
 manifest=folder/'jobs.json';write(manifest,jobs)
 started=time.monotonic();print('Rendering '+name+' at the original17intermediate times',flush=True)
 command=[str(runtime),str(helper),'--manifest',str(manifest),'--model-dir',str(model),'--threads','8','--scale',str(scale)]
 run=subprocess.run(command,cwd=ROOT,text=True,capture_output=True)
 (folder/'inference.log').write_text(run.stdout+'\n'+run.stderr,encoding='utf-8')
 if run.returncode:raise RuntimeError(name+' inference failed; see isolated log')
 paths=sorted(frames.glob('frame_*.png'));assert len(paths)==19
 all_paths[name]=paths
 result['variants'].append({'name':name,'reverseInputs':reverse,'scale':scale,
   'seconds':time.monotonic()-started,'jobManifest':{'file':label(manifest),'sha256':sha(manifest)},
   'frames':[{'frame':i+1,'originalPhysicalTimestep':float(plans[i].get('progress',0)),
              'file':label(p),'sha256':sha(p)} for i,p in enumerate(paths)]})
 print(name+' completed19frames',flush=True)

crop=(286,338,410,466)
for name,paths in all_paths.items():
 imgs=[Image.open(p).convert('RGB') for p in paths]
 row=Image.new('RGB',(1860,410),'white');dr=ImageDraw.Draw(row)
 for col,i in enumerate(range(7,12)):
  patch=imgs[i].crop(crop).resize((372,384),Image.Resampling.NEAREST)
  row.paste(patch,(col*372,26));dr.text((col*372+6,6),name+' frame'+str(i+1),fill='black')
 row.save(OUT/f'feet8-12-native-{name}.png')
 contact=Image.new('RGB',(1750,1640),'white');dr=ImageDraw.Draw(contact)
 for i,img in enumerate(imgs):
  x,y=(i%5)*350,(i//5)*410
  patch=img.crop(crop).resize((350,361),Image.Resampling.NEAREST)
  contact.paste(patch,(x,y+24));dr.text((x+5,y+5),str(i+1),fill='black')
 contact.save(OUT/f'feet19-native-{name}.png')
 for i in range(6,13):
  # Exact source pixels at3x nearest-neighbour, with no enhancement filter.
  imgs[i].crop(crop).resize((372,384),Image.Resampling.NEAREST).save(OUT/f'foot-frame{i+1:02d}-{name}.png')
for p,h in input_hashes.items():assert sha(ROOT/p)==h
for p,h in baseline_hashes.items():assert sha(ROOT/p)==h
result['sourceAndBaselineUnchanged']=True
result['pixelCrop']=list(crop)
write(OUT/'study-index.json',result)
print(json.dumps({'study':label(OUT),'sameClockVariants':len(variants),'sourceAndBaselineUnchanged':True}),flush=True)
