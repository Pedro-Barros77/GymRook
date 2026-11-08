"""Assemble the image_gen foot-only edit onto the exact approved body midframe."""
from pathlib import Path
import hashlib,json
import cv2 as cv
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/generated-frames-v4-followup/standing-machine-calf-raise'
SOURCE=ROOT/'output/followup-round4/calf-two-key-study/standing-machine-calf-raise/frames/frame_0010.png'
EDIT=BASE/'mid-repair-v2.png'
ROI=(289,370,410,447)

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

source=np.asarray(Image.open(SOURCE).convert('RGB'))
edit=np.asarray(Image.open(EDIT).convert('RGB').resize((512,512),Image.Resampling.LANCZOS))
yy,xx=np.mgrid[:512,:512];x0,y0,x1,y1=ROI
inside=(xx>=x0)&(xx<x1)&(yy>=y0)&(yy<y1)
distance=np.minimum.reduce([xx-x0,x1-1-xx,yy-y0,y1-1-yy])
alpha=np.where(inside,np.clip(distance/6,0,1),0)
hsv=cv.cvtColor(source,cv.COLOR_RGB2HSV)
skin=((hsv[:,:,0]>=4)&(hsv[:,:,0]<=30)&(hsv[:,:,1]>45)&(hsv[:,:,2]>120)).astype(np.uint8)
edit_hsv=cv.cvtColor(edit,cv.COLOR_RGB2HSV)
edit_skin=((edit_hsv[:,:,0]>=4)&(edit_hsv[:,:,0]<=30)&(edit_hsv[:,:,1]>45)&(edit_hsv[:,:,2]>120)).astype(np.uint8)
# Preserve the full original ankle silhouette, including its antialias edge.
# A core-only mask left small notches where the generated collar met the skin.
ankle_region=(xx>=325)&(xx<=385)&(((xx<357)&(yy<398))|((xx>=357)&(yy<391)))
skin_core=cv.dilate((skin|edit_skin)*ankle_region.astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)&inside
alpha[skin_core]=0
final=np.round(source*(1-alpha[:,:,None])+edit*alpha[:,:,None]).astype(np.uint8)
assert np.array_equal(final[~inside],source[~inside])
assert np.array_equal(final[skin_core],source[skin_core])
target=BASE/'mid-repaired-key-512-v4.png';Image.fromarray(final).save(target)
mask=BASE/'mid-foot-edit-mask-v4.png';Image.fromarray(np.round(alpha*255).astype(np.uint8)).save(mask)
contact=Image.new('RGB',(1350,340),'white');d=ImageDraw.Draw(contact)
for i,(label,arr) in enumerate([('Original two-key frame10',source),('Generated sole repair only',edit),('Final foot key, original body',final)]):
    crop=Image.fromarray(arr).crop((283,360,423,453)).resize((450,299),Image.Resampling.NEAREST)
    contact.paste(crop,(i*450,30));d.text((i*450+5,7),label,fill='black')
contact.save(BASE/'mid-foot-repair-comparison-v4.png')
report={'method':'image_gen precise shoe repair; composited only in foot ROI; same-clock two-key body and core ankle skin restored exactly',
        'roiPixels':ROI,'featherPixels':6,'sourceFrame10':{'file':SOURCE.relative_to(ROOT).as_posix(),'sha256':sha(SOURCE)},
        'generatedEdit':{'file':EDIT.relative_to(ROOT).as_posix(),'sha256':sha(EDIT)},
        'repairedKey':{'file':target.relative_to(ROOT).as_posix(),'sha256':sha(target)},
        'mask':{'file':mask.relative_to(ROOT).as_posix(),'sha256':sha(mask)},
        'outsideRoiPixelsExact':int((~inside).sum()),'ankleSkinCorePixelsExact':int(skin_core.sum()),
        'status':'Prepared key, visual gate required before any interpolation/export'}
(BASE/'mid-foot-repair-assembly-v4.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'key':target.relative_to(ROOT).as_posix(),'roi':ROI,'outsideExact':report['outsideRoiPixelsExact'],'skinCoreExact':report['ankleSkinCorePixelsExact']}))
