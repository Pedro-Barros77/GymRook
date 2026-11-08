"""Compose reviewed raster Scott key motion with safe canonical static regions.

No skin rig, arm warp or timing adjustment. One occlusion-prone RIFE estimate
uses the same physical instant with complementary input order and scale0.5.
The source inputs, mask and selected inference job are hashed in the index.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/generated-frames-v4-followup/preacher-curl'
RAW=ROOT/'output/followup-round4/preacher-curl/frames'
STUDY=ROOT/'output/followup-round4/preacher-curl/reverse-inference-study'
DEST=BASE/'static-v1'
DEST.mkdir(exist_ok=True)
(DEST/'frames').mkdir(exist_ok=True)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def label(path):return path.relative_to(ROOT).as_posix()
def write(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

raw_index=BASE/'temporal-raw-v1/raw-frames-index.json'
inputs=json.loads(raw_index.read_text(encoding='utf-8'))['frames']
assert len(inputs)==36
for item in inputs:assert sha(ROOT/item['file'])==item['sha256']
for i in range(19,36):assert inputs[i]['sha256']==inputs[36-i]['sha256']
selected=STUDY/'frame11-scale05.png'
assert (RAW/'frame_0011.png').read_bytes()==(RAW/'frame_0027.png').read_bytes()
jobs_path=STUDY/'jobs-scale05.json'
job=json.loads(jobs_path.read_text(encoding='utf-8'))[0]
assert abs(job['timestep']-(1-.6945927106677212))<1e-12

# Protect only fixed regions. The complete moving-arm/handle envelope remains
# unmasked, including the hand that comes near the lower jaw in the high pose.
hard=Image.new('L',(512,512));d=ImageDraw.Draw(hard)
rects=[(0,332,511,511),(0,272,210,511),(392,0,511,511),
       (312,0,511,88),(312,332,511,511),(0,0,74,511)]
for r in rects:d.rectangle(r,fill=255)
head=[(175,19),(188,13),(216,13),(236,18),(243,31),(243,53),
      (250,65),(244,74),(245,86),(238,105),(231,112),
      (220,111),(213,103),(204,98),(198,88),(184,85),
      (178,69),(175,47)]
head_mask=Image.new('L',(512,512));hd=ImageDraw.Draw(head_mask)
hd.polygon(head,fill=255)
# Conservative hand clearance at the end of the curl; keep its original RGB.
hd.rectangle((171,96,242,154),fill=0)
hard=Image.fromarray(np.maximum(np.asarray(hard),np.asarray(head_mask)))
mask=hard.filter(ImageFilter.GaussianBlur(1.25))
mask_path=DEST/'static-mask.png';mask.save(mask_path)
canonical=Image.open(RAW/'frame_0001.png').convert('RGB')
canonical_path=DEST/'canonical-reference.png';canonical.save(canonical_path)
mask_array=np.asarray(mask);canonical_array=np.asarray(canonical)
frames=[];max_fixed_error=0;max_unmasked_error=0
for i in range(1,37):
 source=selected if i in (11,27) else RAW/f'frame_{i:04d}.png'
 image=Image.open(source).convert('RGB')
 result=Image.composite(canonical,image,mask)
 path=DEST/'frames'/f'frame_{i:04d}.png';result.save(path)
 arr=np.asarray(result);before=np.asarray(image)
 max_fixed_error=max(max_fixed_error,int(np.abs(arr[mask_array==255].astype(int)-canonical_array[mask_array==255]).max()))
 max_unmasked_error=max(max_unmasked_error,int(np.abs(arr[mask_array==0].astype(int)-before[mask_array==0]).max()))
 frames.append({'file':label(path),'sha256':sha(path)})
assert max_fixed_error==max_unmasked_error==0
for i in range(19,36):assert frames[i]['sha256']==frames[36-i]['sha256']

imgs=[Image.open(DEST/'frames'/f'frame_{i:04d}.png').convert('RGB') for i in range(1,20)]
for group in range(4):
 out=Image.new('RGB',(1800,330),'white');dr=ImageDraw.Draw(out)
 for col,i in enumerate(range(group*5,min(group*5+5,19))):
  crop=imgs[i].crop((105,80,395,330)).resize((360,310),Image.Resampling.LANCZOS)
  out.paste(crop,(col*360,20));dr.text((col*360+5,4),str(i+1),fill='black')
 out.save(DEST/f'upper-group-{group+1}.png')
for group in range(3):
 out=Image.new('RGB',(1800,300),'white');dr=ImageDraw.Draw(out)
 for col,i in enumerate(range(group*6,min(group*6+6,18))):
  onion=Image.blend(imgs[i],imgs[i+1],.5).crop((105,80,395,330)).resize((300,258),Image.Resampling.LANCZOS)
  out.paste(onion,(col*300,22));dr.text((col*300+5,5),str(i+1)+'>'+str(i+2),fill='black')
 out.save(DEST/f'upper-onions-{group+1}.png')
out=Image.new('RGB',(1900,200),'white');dr=ImageDraw.Draw(out)
for i,img in enumerate(imgs):
 crop=img.crop((164,6,258,145)).resize((100,148),Image.Resampling.LANCZOS)
 out.paste(crop,(i*100,20));dr.text((i*100+5,4),str(i+1),fill='black')
out.save(DEST/'head-hand-clearance19.png')
out=Image.new('RGB',(1500,1200),'white');dr=ImageDraw.Draw(out)
for i,img in enumerate(imgs):
 x,y=(i%5)*300,(i//5)*300;out.paste(img.resize((280,280),Image.Resampling.LANCZOS),(x,y+20));dr.text((x+5,y+4),str(i+1),fill='black')
out.save(DEST/'forward19-contact.png')
index={'id':'preacher-curl','sourceKind':'reviewed-png-loop','frameCount':36,'fps':12,'cycle':'ping-pong',
 'scope':'Nine image_gen coloured poses plus RIFE estimates; canonical fixed scene. No body mesh, no skin rig, no arm transform, no temporal override.',
 'generator':label(Path(__file__)), 'generatorSha256':sha(Path(__file__)),
 'ninePoseSource':{'file':label(BASE/'sheet-v1.png'),'sha256':sha(BASE/'sheet-v1.png')},
 'rawInputIndex':{'file':label(raw_index),'sha256':sha(raw_index)},
 'mask':{'file':label(mask_path),'sha256':sha(mask_path)},
 'canonicalReference':{'file':label(canonical_path),'sha256':sha(canonical_path)},
 'alternateInference':{'frames':[11,27],'source':{'file':label(selected),'sha256':sha(selected)},
   'jobManifest':{'file':label(jobs_path),'sha256':sha(jobs_path)},'scale':.5,
   'physicalProgress':.6945927106677212,'reverseInputTimestep':job['timestep'],
   'reason':'Original scale1 estimate ghosts the connecting black bar; complementary input order at same physical instant with scale0.5 removes crossing ghost.'},
 'pixelChecks':{'staticOpaqueMaxRGBError':max_fixed_error,'unmaskedMovingMaxRGBError':max_unmasked_error,
   'opaqueStaticPixels':int((mask_array==255).sum()),'fullyUnmaskedPixels':int((mask_array==0).sum()),'byteExactReverseCopies':17},
 'sourceFrames':frames,'reviewStatus':'candidate for root review; not export approval'}
write(DEST/'source-index.json',index)
print(json.dumps({'frames':len(frames),'pixelChecks':index['pixelChecks'],'indexSha256':sha(DEST/'source-index.json')}))
