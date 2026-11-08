"""Visual-only single-DOF raster leg-raise study. Never writes dist/config.

One muscular source silhouette rotates about a fixed hip. No limb scaling,
human mesh, per-frame anatomy generation, or nonuniform body deformation.
"""
from pathlib import Path
import hashlib,json,math
import cv2 as cv
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'docs/generated-frames-v4-followup/lying-leg-raise'
OUT=BASE/'rig-v1'
SOURCE=BASE/'source-crops-v1/pose-00.png'
CLEAN=OUT/'clean-plate-generated.png'
PIVOT=np.array([263.,415.])
SOURCE_ANGLE=math.degrees(math.atan2(415-397,263-70))
SCALE=3


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def background_fit(image):
    yy,xx=np.mgrid[:512,:512]
    hsv=cv.cvtColor(image,cv.COLOR_RGB2HSV)
    valid=(hsv[:,:,1]<20)&(hsv[:,:,2]>205)&(yy<438)
    valid&=~((yy>340)&(xx>205))
    sample=valid&((xx%4)==0)&((yy%4)==0)
    x,y=xx[sample]/512,yy[sample]/512
    design=np.column_stack([np.ones_like(x),x,y,x*x,x*y,y*y])
    fit=np.linalg.lstsq(design,image[sample].astype(float),rcond=None)[0]
    X,Y=xx/512,yy/512
    full=np.stack([np.ones_like(X),X,Y,X*X,X*Y,Y*Y],axis=-1)
    return np.clip(full@fit,0,255)


def masks(source):
    hsv=cv.cvtColor(source,cv.COLOR_RGB2HSV)
    foreground=((hsv[:,:,1]>30)|(hsv[:,:,2]<170)).astype(np.uint8)*255
    roi=Image.new('L',(512,512));d=ImageDraw.Draw(roi)
    d.polygon([(0,340),(221,340),(284,372),(290,390),(290,429),(274,440),
               (218,441),(200,436),(185,427),(170,425),(140,423),(100,418),
               (75,415),(60,428),(0,428)],fill=255)
    foreground&=np.asarray(roi)
    count,labels,stats,_=cv.connectedComponentsWithStats(foreground)
    components=sorted(range(1,count),key=lambda n:stats[n,cv.CC_STAT_AREA],reverse=True)
    mask=np.zeros((512,512),np.uint8)
    for n in components:
        if stats[n,cv.CC_STAT_AREA]>100:mask[labels==n]=255
    mask=cv.morphologyEx(mask,cv.MORPH_CLOSE,np.ones((3,3),np.uint8))
    # Full fabric within the hinge disk makes the hip seam overlap naturally.
    yy,xx=np.mgrid[:512,:512]
    hinge=((xx-PIVOT[0])**2+(yy-PIVOT[1])**2<34**2)&(hsv[:,:,2]<130)&(xx<292)&(yy<438)
    mask[hinge]=255
    alpha=cv.GaussianBlur(mask.astype(np.float32)/255,(0,0),.45)
    hand=Image.new('L',(512,512));d=ImageDraw.Draw(hand)
    d.polygon([(207,451),(219,446),(244,437),(274,430),(300,430),(325,433),(334,456),(278,467),(207,467)],fill=255)
    return alpha,np.asarray(hand,dtype=np.float32)/255


def main():
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'frames').mkdir(exist_ok=True)
    source=np.asarray(Image.open(SOURCE).convert('RGB'))
    clean=np.asarray(Image.open(CLEAN).convert('RGB').resize((512,512),Image.Resampling.LANCZOS))
    # The generated clean plate establishes an empty-leg background. Refit
    # its smooth studio field to the original exposure, preserving the exact
    # original source color at all regions surrounding the extraction.
    bg=background_fit(source)
    alpha,hand=masks(source)
    canonical=source.copy()
    # Replace the old leg area with a studio clean plate, then retain the
    # existing torso/waist/near hand/mat as fixed foreground pixels.
    erase=cv.dilate((alpha>.05).astype(np.uint8),np.ones((11,11),np.uint8)).astype(float)
    erase=cv.GaussianBlur(erase,(0,0),2.)
    erase[:,270:]=0
    erase[438:]=0
    canonical=np.round(source*(1-erase[:,:,None])+bg*erase[:,:,None]).astype(np.uint8)
    canonical=np.round(canonical*(1-hand[:,:,None])+source*hand[:,:,None]).astype(np.uint8)
    canonical[438:]=source[438:]
    # Keep every core leg pixel from the source. Premultiplied alpha avoids
    # white halos during the rigid rotation at the raster edge.
    rgb=source.astype(np.float32)/255
    packed=np.dstack([rgb*alpha[:,:,None],alpha])
    packed=cv.resize(packed,(512*SCALE,512*SCALE),interpolation=cv.INTER_CUBIC)
    fixed=canonical.astype(np.float32)/255
    foreground=np.zeros((512,512),np.float32)
    foreground[:,296:]=1
    foreground[438:]=1
    foreground=np.maximum(foreground,hand)
    parameters=[];frames=[]
    landmarks={'hip':PIVOT.tolist(),'knee':[156.,397.],'ankle':[70.,397.],'toe':[22.,374.]}
    for i in range(19):
        progress=.5-.5*math.cos(math.pi*i/18)
        angle=12+68*progress
        delta=angle-SOURCE_ANGLE
        matrix=cv.getRotationMatrix2D(tuple(PIVOT*SCALE),-delta,1.)
        transformed=cv.warpAffine(packed,matrix,(512*SCALE,512*SCALE),flags=cv.INTER_CUBIC,borderMode=cv.BORDER_CONSTANT)
        transformed=cv.resize(transformed,(512,512),interpolation=cv.INTER_AREA)
        moving_alpha=np.clip(transformed[:,:,3:4],0,1)
        combined=transformed[:,:,:3]+fixed*(1-moving_alpha)
        combined=combined*(1-foreground[:,:,None])+rgb*foreground[:,:,None]
        image=np.round(np.clip(combined,0,1)*255).astype(np.uint8)
        path=OUT/'frames'/f'frame_{i+1:04d}.png';Image.fromarray(image).save(path)
        m=cv.getRotationMatrix2D(tuple(PIVOT),-delta,1.)
        joints={name:(m@np.array([*point,1.])).tolist() for name,point in landmarks.items()}
        parameters.append({'frame':i+1,'angleDegrees':angle,'scale':1.,'joints':joints,
                           'projectedFemurPixels':float(np.linalg.norm(np.array(joints['hip'])-joints['knee'])),
                           'projectedTibiaPixels':float(np.linalg.norm(np.array(joints['knee'])-joints['ankle']))})
        frames.append(image)
    for target,origin in zip(range(20,37),range(18,1,-1)):
        dst=OUT/'frames'/f'frame_{target:04d}.png';src=OUT/'frames'/f'frame_{origin:04d}.png';dst.write_bytes(src.read_bytes())
    Image.fromarray(canonical).save(OUT/'canonical-body-and-mat.png')
    Image.fromarray(np.round(alpha*255).astype(np.uint8)).save(OUT/'leg-alpha.png')
    rgba=np.dstack([source,np.round(alpha*255).astype(np.uint8)])
    Image.fromarray(rgba).save(OUT/'source-leg-sprite.png')
    Image.fromarray(np.round(foreground*255).astype(np.uint8)).save(OUT/'fixed-foreground-mask.png')
    def contact(images,labels,target,crop=None,size=250,columns=5):
        rows=math.ceil(len(images)/columns);sheet=Image.new('RGB',(columns*size,rows*(size+22)),(250,249,247));d=ImageDraw.Draw(sheet)
        for k,(arr,label) in enumerate(zip(images,labels)):
            im=Image.fromarray(arr)
            if crop:im=im.crop(crop)
            im=im.resize((size,size),Image.Resampling.LANCZOS)
            x,y=k%columns*size,k//columns*(size+22);sheet.paste(im,(x,y+22));d.text((x+4,y+4),label,fill='black')
        sheet.save(target)
    contact(frames,[f'{i+1}: {p["angleDegrees"]:.1f}deg' for i,p in enumerate(parameters)],OUT/'forward19-contact.png')
    contact(frames,[str(i+1) for i in range(19)],OUT/'hip19-critical.png',crop=(195,350,310,465),size=250)
    overlays=[np.round((a.astype(float)+b.astype(float))/2).astype(np.uint8) for a,b in zip(frames,frames[1:])]
    contact(overlays,[f'{i+1}/{i+2}' for i in range(18)],OUT/'forward18-onions.png')
    index={'id':'lying-leg-raise','status':'VISUAL STUDY ONLY; not approved or promoted','method':'single constant-shape raster leg pair rotates at one fixed hip; static canonical torso/hand/mat; no mesh or nonuniform warp','generator':'scripts/study-native-leg-raise.py','generatorSha256':sha(Path(__file__)),
           'sources':{str(SOURCE.relative_to(ROOT)).replace('\\','/'):sha(SOURCE),str(CLEAN.relative_to(ROOT)).replace('\\','/'):sha(CLEAN)},
           'pivotPixels':PIVOT.tolist(),'sourceAngleDegrees':SOURCE_ANGLE,'angleRangeDegrees':[12,80],
           'frameCount':36,'fps':12,'forwardParameters':parameters,
           'sourceFrames':[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in sorted((OUT/'frames').glob('frame_*.png'))],
           'limits':['The2D source landmarks are approximate visible landmarks, not certified skeletal positions.','One profile raster pair can conceal the far leg; no fabricated scaling or new limb geometry.','Hip cloth handoff and muscle appearance require full-size visual review before any media integration.']}
    save_json(OUT/'study-index.json',index)
    print(json.dumps({'studyOnly':True,'frames':36,'angleRange':[12,80],'output':str(OUT)}))


if __name__=='__main__':main()
