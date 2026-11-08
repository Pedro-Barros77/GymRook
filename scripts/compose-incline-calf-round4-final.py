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
RAW=BASE/'final-composition-v1'
OUT=BASE/'final-composition-v1'
CLEAN=BASE/'static-two-key-v1/clean-machine-generated.png'
ALPHA_SOURCE=BASE/'static-two-key-v1/foreground-matte-generated-0.png'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def poly(points):
    image=Image.new('L',(512,512));ImageDraw.Draw(image).polygon(points,fill=255)
    return np.asarray(image).copy()


def tracked_mattes(raws):
    generated=np.asarray(Image.open(ALPHA_SOURCE).convert('RGBA').resize((512,512),Image.Resampling.LANCZOS))
    base=generated[:,:,3].astype(np.float32)/255
    feature=cv.SIFT_create(nfeatures=3000)
    g=cv.cvtColor(generated[:,:,:3],cv.COLOR_RGB2GRAY);target=cv.cvtColor(raws[0],cv.COLOR_RGB2GRAY)
    kg,dg=feature.detectAndCompute(g,(base>.8).astype(np.uint8)*255)
    kt,dt=feature.detectAndCompute(target,None)
    pairs=cv.BFMatcher().knnMatch(dg,dt,k=2);good=[a for a,b in pairs if a.distance<.72*b.distance]
    assert len(good)>=8,'Insufficient exact source texture matches to position alpha reference.'
    matrix,inliers=cv.estimateAffinePartial2D(np.array([kg[m.queryIdx].pt for m in good]),np.array([kt[m.trainIdx].pt for m in good]),method=cv.RANSAC,ransacReprojThreshold=2.)
    scale=float(np.linalg.norm(matrix[0,:2]));assert .9<scale<1.1 and np.max(np.abs(matrix[:,2]))<20
    alpha=cv.warpAffine(base,matrix,(512,512),flags=cv.INTER_LINEAR,borderMode=cv.BORDER_CONSTANT)
    alpha=cv.GaussianBlur(cv.dilate((alpha>.5).astype(np.float32),np.ones((3,3),np.uint8)),(0,0),.4)
    Image.fromarray(np.round(alpha*255).astype(np.uint8)).save(OUT/'aligned-initial-alpha.png')
    dis=cv.DISOpticalFlow_create(cv.DISOPTICAL_FLOW_PRESET_MEDIUM)
    dis.setFinestScale(0);dis.setVariationalRefinementIterations(20)
    yy,xx=np.mgrid[:512,:512];maps=[];previous=target
    rough=poly([(83,86),(141,50),(152,2),(219,2),(231,77),(267,117),(311,217),(351,302),(399,431),(386,454),(341,455),(307,404),(263,337),(215,288),(168,229),(102,170),(83,128)])
    flow_records=[]
    for index,raw in enumerate(raws[:19]):
        gray=cv.cvtColor(raw,cv.COLOR_RGB2GRAY)
        if index:
            # Backward image motion transports alpha labels only. The RGB
            # source athlete is never transformed, stretched or synthesized.
            flow=dis.calc(gray,previous,None)
            alpha=cv.remap(alpha,(xx+flow[:,:,0]).astype(np.float32),(yy+flow[:,:,1]).astype(np.float32),cv.INTER_LINEAR,borderMode=cv.BORDER_CONSTANT)
        hsv=cv.cvtColor(raw,cv.COLOR_RGB2HSV)
        skin=((hsv[:,:,0]>5)&(hsv[:,:,0]<30)&(hsv[:,:,1]>70)&(hsv[:,:,2]>70)&
              ((raw[:,:,0].astype(int)-raw[:,:,2].astype(int))>35)&(rough>0)).astype(np.uint8)*255
        core=cv.dilate(skin,np.ones((3,3),np.uint8)).astype(np.float32)/255
        alpha=np.maximum(alpha,core)
        # Warm white soles are real shoe material, not studio background.
        # Do not color-key them away. Only discard negligible alpha noise.
        alpha[alpha<.01]=0
        alpha=np.clip(alpha,0,1)
        maps.append((alpha.copy(),skin,np.zeros_like(skin)))
        flow_records.append({'frame':index+1,'method':'DIS backward transport of alpha only; source RGB untouched','skinPixels':int((skin>0).sum())})
        previous=gray
    write(OUT/'alpha-tracking-parameters.json',{'initialReference':ALPHA_SOURCE.relative_to(ROOT).as_posix(),'initialReferenceSha256':sha(ALPHA_SOURCE),'sourceTextureMatches':len(good),'inlierMatches':int(inliers.sum()),'initialSimilarityMatrix':matrix.tolist(),'scale':scale,'frames':flow_records,'limits':'Masks only are transported by image motion; no body RGB transform.'})
    return maps


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
    plate=np.asarray(Image.open(CLEAN).convert('RGB').resize((512,512),Image.Resampling.LANCZOS))
    # This whole image is the one fixed clean machine; its tower/chassis,
    # empty rails and step are identical in every candidate frame.
    Image.fromarray(plate).save(OUT/'canonical-clean-machine.png')
    sprite=weight_sprite(raws[0]);Image.fromarray(np.round(np.clip(sprite,0,1)*255).astype(np.uint8),'RGBA').save(OUT/'weight-premultiplied-reference.png')
    frames=[];parameters=[]
    masks=tracked_mattes(raws)
    for index,raw in enumerate(raws[:19]):
        phase=.5-.5*math.cos(math.pi*index/18)
        alpha,skin,shoe=masks[index]
        # Quantize the actual blend matte before rendering so mask255 has
        # exactly the same meaning in the raster and preservation verifier.
        alpha8=np.round(alpha*255).astype(np.uint8)
        alpha=alpha8.astype(np.float32)/255
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
        maskpath=OUT/'actor-masks'/f'actor-{index+1:04d}.png';Image.fromarray(alpha8).save(maskpath)
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
    contact([np.round((a.astype(float)+b.astype(float))/2).astype(np.uint8) for a,b in zip(frames,frames[1:])],
            [f'{i}/{i+1}' for i in range(1,19)],OUT/'full18-onions.png')
    write(OUT/'candidate-index.json',{'id':'standing-machine-calf-raise','status':'Final candidate: ROOT-approved reverse-scale1 local3key feet, unchanged2key body, canonical machine and rigid selected weights; awaiting final composite gate',
        'generator':'scripts/compose-incline-calf-round4-final.py','generatorSha256':sha(Path(__file__)),
        'rawIndex':{'file':(RAW/'raw-index.json').relative_to(ROOT).as_posix(),'sha256':sha(RAW/'raw-index.json')},
        'cleanPlate':{'file':CLEAN.relative_to(ROOT).as_posix(),'sha256':sha(CLEAN)},
        'forwardParameters':parameters,'sourceFrames':[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sorted((OUT/'frames').glob('frame_*.png'))],
        'limits':'Skin is copied from actual chosen raw sources. Pixel stability does not approve execution, machine physics, or shoe shape. No global config or active assets written.'})
    print('Calf canonical machine/rigidweights candidate36PNG prepared, not promoted.')


if __name__=='__main__':main()
