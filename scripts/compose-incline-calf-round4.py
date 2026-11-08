"""Candidate-only canonical inclined calf machine and rigid selected weights.

Keeps the chosen raw athlete/carrying assembly pixels. No skin mesh/warp,
joint deformation, or fixed head overlay. Never writes global config/dist.
"""
from pathlib import Path
import hashlib,json,math
import cv2 as cv
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/generated-frames-v4-followup/standing-machine-calf-raise'
RAW=BASE/'temporal-two-key-v1'
OUT=BASE/'static-two-key-v1'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def poly(points):
    image=Image.new('L',(512,512));ImageDraw.Draw(image).polygon(points,fill=255)
    return np.asarray(image).copy()


def athlete_mask(raw,canonical,phase):
    hsv=cv.cvtColor(raw,cv.COLOR_RGB2HSV)
    rough=poly([(83,86),(141,50),(152,2),(219,2),(231,77),(267,117),
                (311,217),(351,302),(399,431),(386,454),(341,455),
                (307,404),(263,337),(215,288),(168,229),(102,170),(83,128)])
    skin=((hsv[:,:,0]<36)&(hsv[:,:,1]>42)&(hsv[:,:,2]>65)&(rough>0)).astype(np.uint8)*255
    # Skin, hair and garments are selected semantically. A difference image
    # would also select displaced rail edges from the equipment cleanup.
    moving=skin.copy()
    hair_region=poly([(151,2),(215,2),(228,34),(223,81),(181,98),(150,73)])
    moving[(hair_region>0)&(hsv[:,:,2]<175)]=255
    clothes_region=poly([(205,158),(275,174),(311,223),(337,283),
                         (298,305),(250,288),(224,257)])
    moving[(clothes_region>0)&(hsv[:,:,2]<190)]=255
    # Explicit moving-carriage ROI follows the keyframe carriage direction;
    # it selects original pixels only and never transforms the human image.
    shift=np.array([-14*phase,-25*phase])
    carriage=np.array([(91,105),(142,72),(243,76),(259,132),(260,262),
                       (238,286),(194,281),(143,205),(102,169),(88,129)])+shift
    carriage=poly([tuple(x) for x in carriage])
    moving=np.maximum(moving,carriage)
    moving=np.maximum(moving,cv.dilate(skin,np.ones((3,3),np.uint8)))
    # Feet are segmented independently so the exposed steel step can remain
    # canonical rather than moving with a broad rectangular foot patch.
    foot_region=poly([(289,398),(318,348),(389,345),(406,408),(402,459),
                      (337,459),(294,432)])
    low=np.array([(305,404),(332,393),(359,402),(368,393),(395,415),
                  (397,440),(387,448),(344,451),(310,425)],float)
    mid=np.array([(303,400),(332,383),(349,389),(369,377),(385,398),
                  (374,422),(342,434),(317,422),(303,416)],float)
    high=np.array([(299,407),(315,375),(342,363),(369,355),(386,373),
                   (378,396),(347,414),(311,421),(299,415)],float)
    points=low+(mid-low)*(phase*2) if phase<=.5 else mid+(high-mid)*((phase-.5)*2)
    shoe=poly([tuple(p) for p in points])
    shoe=cv.dilate(shoe,np.ones((5,5),np.uint8))
    moving[foot_region>0]=np.maximum(shoe[foot_region>0],skin[foot_region>0])
    moving=cv.morphologyEx(moving,cv.MORPH_CLOSE,np.ones((3,3),np.uint8))
    alpha=cv.GaussianBlur(moving.astype(np.float32)/255,(0,0),.45)
    return alpha,skin,shoe


def weight_sprite(first):
    mask=poly([(72,280),(123,279),(126,284),(137,284),(137,413),(76,418),(71,414)])
    mask=np.maximum(mask,poly([(84,261),(111,261),(112,285),(83,285)]))
    mask=np.maximum(mask,poly([(101,246),(106,246),(110,263),(99,263)]))
    alpha=cv.GaussianBlur(mask.astype(np.float32)/255,(0,0),.35)
    return np.dstack([first.astype(np.float32)/255*alpha[:,:,None],alpha])


def contact(images,labels,path,crop=None,size=250):
    columns=5;rows=math.ceil(len(images)/columns)
    sheet=Image.new('RGB',(columns*size,rows*(size+22)),(250,249,247));draw=ImageDraw.Draw(sheet)
    for i,(a,label) in enumerate(zip(images,labels)):
        x,y=i%columns*size,i//columns*(size+22);im=Image.fromarray(a)
        if crop:im=im.crop(crop)
        sheet.paste(im.resize((size,size),Image.Resampling.LANCZOS),(x,y+22));draw.text((x+4,y+4),label,fill='black')
    sheet.save(path)


def main():
    OUT.mkdir(exist_ok=True);(OUT/'frames').mkdir(exist_ok=True)
    (OUT/'actor-masks').mkdir(exist_ok=True)
    records=read(RAW/'raw-index.json')['sourceFrames']
    raws=[]
    for entry in records:
        path=ROOT/entry['file'];assert sha(path)==entry['sha256'];raws.append(np.asarray(Image.open(path).convert('RGB')))
    plate=np.asarray(Image.open(OUT/'clean-machine-generated.png').convert('RGB').resize((512,512),Image.Resampling.LANCZOS))
    # This whole image is the one fixed clean machine; its tower/chassis,
    # empty rails and step are identical in every candidate frame.
    Image.fromarray(plate).save(OUT/'canonical-clean-machine.png')
    sprite=weight_sprite(raws[0]);Image.fromarray(np.round(np.clip(sprite,0,1)*255).astype(np.uint8),'RGBA').save(OUT/'weight-premultiplied-reference.png')
    frames=[];parameters=[]
    for index,raw in enumerate(raws[:19]):
        phase=.5-.5*math.cos(math.pi*index/18)
        alpha,skin,shoe=athlete_mask(raw,plate,phase)
        # A single unit of unchanged plates travels vertically25pixels, as
        # in the two original keyframes, instead of changing plate count.
        dy=-25*phase
        matrix=np.float32([[1,0,0],[0,1,dy]])
        moved=cv.warpAffine(sprite,matrix,(512,512),flags=cv.INTER_LINEAR,borderMode=cv.BORDER_CONSTANT)
        stage=plate.astype(np.float32)/255
        # Continuous cable from fixed upper tower into the moving eye.
        cable=Image.fromarray(np.round(stage*255).astype(np.uint8));d=ImageDraw.Draw(cable)
        d.line([(104,173),(104,round(248+dy))],fill=(135,134,131),width=1)
        stage=np.asarray(cable).astype(np.float32)/255
        stage=moved[:,:,:3]+stage*(1-moved[:,:,3:4])
        final=np.round(np.clip(raw.astype(np.float32)/255*alpha[:,:,None]+stage*(1-alpha[:,:,None]),0,1)*255).astype(np.uint8)
        path=OUT/'frames'/f'frame_{index+1:04d}.png';Image.fromarray(final).save(path)
        maskpath=OUT/'actor-masks'/f'actor-{index+1:04d}.png';Image.fromarray(np.round(alpha*255).astype(np.uint8)).save(maskpath)
        core=(skin==255)&(alpha>.999)
        error=int(np.abs(final[core].astype(int)-raw[core].astype(int)).max()) if core.any() else 0
        assert error==0
        parameters.append({'frame':index+1,'phase':phase,'weightTranslationPixels':[0,dy],
                           'actorMask':{'file':maskpath.relative_to(ROOT).as_posix(),'sha256':sha(maskpath)},
                           'skinCorePixels':int(core.sum()),'skinCoreMaxRGBDifference':error})
        frames.append(final)
    for target,origin in zip(range(20,37),range(18,1,-1)):
        (OUT/'frames'/f'frame_{target:04d}.png').write_bytes((OUT/'frames'/f'frame_{origin:04d}.png').read_bytes())
        (OUT/'actor-masks'/f'actor-{target:04d}.png').write_bytes((OUT/'actor-masks'/f'actor-{origin:04d}.png').read_bytes())
    contact(frames,[str(i) for i in range(1,20)],OUT/'forward19-contact.png')
    contact(frames,[str(i) for i in range(1,20)],OUT/'feet19-critical.png',(285,350,405,455))
    contact(frames,[str(i) for i in range(1,20)],OUT/'weights19-critical.png',(55,225,146,430))
    contact([np.round((a.astype(float)+b.astype(float))/2).astype(np.uint8) for a,b in zip(frames,frames[1:])],
            [f'{i}/{i+1}' for i in range(1,19)],OUT/'feet18-onions.png',(285,350,405,455))
    write(OUT/'candidate-index.json',{'id':'standing-machine-calf-raise','status':'Candidate only; original2key foot inference and foreground/step contours still need full visual review',
        'generator':'scripts/compose-incline-calf-round4.py','generatorSha256':sha(Path(__file__)),
        'rawIndex':{'file':(RAW/'raw-index.json').relative_to(ROOT).as_posix(),'sha256':sha(RAW/'raw-index.json')},
        'cleanPlate':{'file':(OUT/'clean-machine-generated.png').relative_to(ROOT).as_posix(),'sha256':sha(OUT/'clean-machine-generated.png')},
        'forwardParameters':parameters,'sourceFrames':[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sorted((OUT/'frames').glob('frame_*.png'))],
        'limits':'Skin is copied from actual chosen raw sources. Pixel stability does not approve execution, machine physics, or shoe shape. No global config or active assets written.'})
    print('Calf canonical machine/rigidweights candidate36PNG prepared, not promoted.')


if __name__=='__main__':main()
