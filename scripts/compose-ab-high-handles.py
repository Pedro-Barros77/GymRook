"""Compose an isolated AB high-handle candidate; never modifies dist/config/raw.

The new athlete remains the reviewed RIFE raster. Fixed machinery/lower body
uses canonical pixels, with explicit foreground occlusion protection.
"""
from pathlib import Path
import hashlib,json
import cv2 as cv
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/generated-frames-v4-followup/machine-ab-crunch'
RAW=ROOT/'output/followup-round4/machine-ab-crunch/frames'
OUT=BASE/'static-composition-v3'
OUT.mkdir(parents=True,exist_ok=True)

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def label(p): return p.relative_to(ROOT).as_posix()
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_rgb(p): return np.asarray(Image.open(p).convert('RGB')).copy()

report=json.loads((ROOT/'docs/followup-animations-build.json').read_text(encoding='utf-8'))
record=next(x for x in report['animations'] if x['id']=='machine-ab-crunch')
assert len(record['frames'])==36
raw=[read_rgb(ROOT/e['file']) for e in record['frames']]
assert all(sha(ROOT/e['file'])==e['sha256'] for e in record['frames'])
write(OUT/'raw-index.json',record)

canonical=raw[0].copy()
clean=np.asarray(Image.open(BASE/'clean-equipment-v1.png').convert('RGB').resize((512,512),Image.Resampling.LANCZOS)).copy()
canonical[90:225,190:220]=clean[90:225,190:220]
canonical[137:282,282:386]=clean[137:282,282:386]
assert np.array_equal(canonical[302:512],raw[0][302:512]),'Canonical feet/legs must stay the original reviewed RGB.'
Image.fromarray(canonical).save(OUT/'canonical-fixed-reference.png')

# Windows locate actual hair/face in each reviewed source pose. They only
# protect occluding raw pixels; no body geometry or colour is synthesized.
head_boxes=np.asarray([[272,14,347,113],[271,16,347,115],[270,18,346,117],
 [266,20,343,121],[255,27,333,136],[240,39,321,151],
 [226,52,309,163],[211,66,297,177],[200,72,290,184]],float)
head_boxes=head_boxes[[entry['cell'] for entry in record['anchors']]]
kernel=np.ones((3,3),np.uint8)
masks=[];previews=[];entries=[];opaque_body=[]
for index,(im,plan) in enumerate(zip(raw,record['frames'])):
 if index>=19:
  forward=36-index
  mask=masks[forward].copy();preview=previews[forward].copy();body=opaque_body[forward].copy()
 else:
  hsv=cv.cvtColor(im,cv.COLOR_RGB2HSV);h,s,v=cv.split(hsv)
  skin=((h<36)&(s>45)&(v>45)).astype(np.uint8)*255
  region=np.zeros((512,512),np.uint8);region[25:310,185:390]=255
  skin=cv.bitwise_and(skin,region)
  n,labels,stats,_=cv.connectedComponentsWithStats(cv.morphologyEx(skin,cv.MORPH_CLOSE,kernel),8)
  if n<2: raise ValueError('No actual torso skin component')
  component=1+int(np.argmax(stats[1:,cv.CC_STAT_AREA]));skin=(labels==component).astype(np.uint8)*255
  box=(1-plan['timestep'])*head_boxes[plan['anchor0']]+plan['timestep']*head_boxes[plan['anchor1']]
  x0,y0,x1,y1=np.rint(box).astype(int)
  hair=np.zeros((512,512),np.uint8)
  hair[y0:y1,x0:x1]=(((h[y0:y1,x0:x1]<40)&(s[y0:y1,x0:x1]>18)&(v[y0:y1,x0:x1]<155))*255).astype(np.uint8)
  points=cv.findNonZero(cv.bitwise_or(skin,hair))
  body=np.zeros((512,512),np.uint8)
  cv.fillConvexPoly(body,cv.convexHull(points),255)
  cv.rectangle(body,(239,229),(355,309),255,-1)
  body=cv.dilate(body,kernel,iterations=2)
  # Gray moving yoke pixels remain raw if they cross the fixed back-pad ROI.
  tube=np.zeros((512,512),np.uint8)
  tube[:195,225:421]=(((s[:195,225:421]<45)&(v[:195,225:421]>90)&(v[:195,225:421]<220))*255).astype(np.uint8)
  protect=cv.bitwise_or(body,cv.dilate(tube,kernel,iterations=2))
  mask=np.full((512,512),255,np.uint8)
  mask[0:302,190:435]=0
  mask[22:457,35:217]=255
  mask[137:282,282:386]=255
  mask[153:430,413:454]=255
  mask[protect>0]=0
  # The stationary bearing housing is behind the moving yoke and separate
  # from the athlete. The actual pivot centre and seat/feet stay canonical.
  cv.ellipse(mask,(403,125),(21,24),0,0,360,255,-1)
  mask[302:512,:]=255
  mask=np.asarray(Image.fromarray(mask).filter(ImageFilter.GaussianBlur(.65))).copy()
  # Opaque reviewed skin stays byte-exact, including any tower occlusion.
  body_core=cv.erode(cv.bitwise_or(skin,hair),kernel,iterations=1)>0
  mask[body_core]=0
  a=mask.astype(float)/255
  preview=np.rint(canonical*a[:,:,None]+im*(1-a[:,:,None])).clip(0,255).astype(np.uint8)
  assert np.array_equal(preview[body_core],im[body_core])
  body=(body_core.astype(np.uint8)*255)
 masks.append(mask);previews.append(preview);opaque_body.append(body)
 mp=OUT/f'static-{index+1:04d}.png';pp=OUT/f'preview-{index+1:04d}.png';bp=OUT/f'actor-core-{index+1:04d}.png'
 Image.fromarray(mask).save(mp);Image.fromarray(preview).save(pp);Image.fromarray(body).save(bp)
 entries.append({'frame':index+1,'preview':{'file':label(pp),'sha256':sha(pp)},'mask':{'file':label(mp),'sha256':sha(mp)},'actorCore':{'file':label(bp),'sha256':sha(bp)},'raw':{'file':plan['file'],'sha256':plan['sha256']}})

def contact(ims,labels,path,columns=5):
 side=ims[0].width;height=ims[0].height;rows=(len(ims)+columns-1)//columns
 canvas=Image.new('RGB',(side*columns,(height+22)*rows),'white');d=ImageDraw.Draw(canvas)
 for i,(im,title) in enumerate(zip(ims,labels)):
  x=(i%columns)*side;y=(i//columns)*(height+22);d.text((x+5,y+4),title,fill='black');canvas.paste(im,(x,y+22))
 canvas.save(path)

contact([Image.fromarray(x).resize((320,320)) for x in previews[:19]], [f'Frame {i+1}' for i in range(19)],OUT/'forward19-contact.png')
upper=[Image.fromarray(x).crop((188,0,438,305)).resize((400,488)) for x in previews[:19]]
contact(upper, [f'Frame {i+1}' for i in range(19)],OUT/'upper19-critical.png',5)
for start in range(0,19,5):
 contact(upper[start:start+5],[f'Frame {i+1}' for i in range(start,min(start+5,19))],OUT/f'upper-group-{start//5+1}.png',3)
onions=[Image.blend(Image.fromarray(previews[i]),Image.fromarray(previews[i+1]),.5).crop((188,0,438,305)).resize((350,427)) for i in range(18)]
contact(onions,[f'{i+1}/{i+2}' for i in range(18)],OUT/'upper18-onions.png',6)
for start in range(0,18,6):
 contact(onions[start:start+6],[f'{i+1}/{i+2}' for i in range(start,start+6)],OUT/f'onions-group-{start//6+1}.png',3)
constant=np.all(np.stack(masks)==255,axis=0)
assert all(np.array_equal(x[constant],canonical[constant]) for x in previews)
assert all(np.array_equal(x[305:512],raw[0][305:512]) for x in previews),'Lowerbody/feet source RGB must be unchanged.'
assert all(np.array_equal(previews[i],previews[36-i]) for i in range(19,36))
metadata={'id':'machine-ab-crunch','status':'Canonical candidate; root final visual gate pending. No export.',
 'generator':{'file':label(Path(__file__).resolve()),'sha256':sha(Path(__file__).resolve())},
 'method':'Raw reviewed RIFE human and moving yoke kept, fixed equipment/lowerbody canonical. Skin core is exact raw RGB; no human warping.',
 'sourceSha256':record['sourceSha256'],'rawIndex':{'file':label(OUT/'raw-index.json'),'sha256':sha(OUT/'raw-index.json')},
 'canonical':{'file':label(OUT/'canonical-fixed-reference.png'),'sha256':sha(OUT/'canonical-fixed-reference.png')},
 'canonicalEquipmentEdit':{'file':label(BASE/'clean-equipment-v1.png'),'sha256':sha(BASE/'clean-equipment-v1.png'),'selectedPatchPixels':[[190,90,220,225],[282,137,386,282]]},
 'entries':entries,'identicalProtectedPixelsAcross36':int(constant.sum()),'bodyCoreChangedRGBPixels':0,'lowerBodyExactBelowY':305,'returnCopiesByteExact':True,
 'limitations':['Protected pixels measure stability, not exercise accuracy.','Moving overhead yoke remains generated raster perspective, not a complete3D rigid rig.','Masks and pad/skin boundaries require actual visual inspection at all19poses.']}
write(OUT/'composition-index.json',metadata)
print(json.dumps({'candidate':label(OUT),'frames':len(entries),'protectedPixels':int(constant.sum()),'bodyRGBError':0}))
