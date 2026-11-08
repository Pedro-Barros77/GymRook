"""Build fixed-machine plates and per-frame moving-object envelopes.

Only masks/background compositing are computed. The reviewed RIFE athlete RGB
pixels are never warped or recoloured. Alpha envelopes are conservative and
require visual inspection against all 19 actual forward frames.
"""
from pathlib import Path
import hashlib,json,math
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'output/repair-animations'
ART=ROOT/'docs/generated-frames-v3-repairs'
N=512

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def capsule(draw,points,radius):
    draw.line(points,fill=255,width=round(radius*2),joint='curve')
    for x,y in points:
        draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=255)

def skin_mask(image,name):
    data=np.asarray(image.convert('RGB'))
    hsv=cv2.cvtColor(data,cv2.COLOR_RGB2HSV)
    # Includes dark warm hair; saturation rejects the warm-white backdrop and
    # low-saturation fixed steel. Skin/hair holes are then filled by contour.
    m=(((hsv[:,:,0]<32)|(hsv[:,:,0]>174))&(hsv[:,:,1]>38)&(hsv[:,:,2]>17)).astype(np.uint8)*255
    if name=='reverse-pec-deck':
        m[:170]=0;m[313:]=0
    else:
        m[:,:185]=0;m[:,470:]=0;m[331:]=0
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8))
    contours,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    filled=np.zeros_like(m)
    for contour in contours:
        if cv2.contourArea(contour)>35:cv2.drawContours(filled,[contour],-1,255,-1)
    return Image.fromarray(cv2.dilate(filled,np.ones((7,7),np.uint8)))

def track(images,points):
    grey=[cv2.cvtColor(np.asarray(im),cv2.COLOR_RGB2GRAY) for im in images]
    current=np.asarray(points,np.float32).reshape(-1,1,2)
    values=[current[:,0].copy().tolist()];errors=[]
    for a,b in zip(grey,grey[1:]):
        nxt,status,_=cv2.calcOpticalFlowPyrLK(a,b,current,None,winSize=(35,35),maxLevel=3,
          criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.0005))
        back,_,_=cv2.calcOpticalFlowPyrLK(b,a,nxt,None,winSize=(35,35),maxLevel=3)
        error=np.linalg.norm(back-current,axis=2).ravel()
        errors.append(error.tolist());values.append(nxt[:,0].tolist());current=nxt
    return values,errors

def head_mask():
    mask=Image.new('L',(N,N),0)
    ImageDraw.Draw(mask).polygon([(239,101),(258,97),(280,105),(293,124),(287,151),(276,161),(267,183),(245,179),(234,162),(230,141),(230,119)],fill=255)
    return mask.filter(ImageFilter.GaussianBlur(.6))

def moving_mask(image,name,index,tracked):
    m=skin_mask(image,name);d=ImageDraw.Draw(m)
    if name=='machine-ab-crunch':
        hinge=tuple(tracked[index][0]);near=tuple(tracked[index][1]);far=tuple(tracked[index][2])
        capsule(d,[(172,277),hinge],15)
        capsule(d,[near,hinge],18);capsule(d,[far,(hinge[0]+35,hinge[1]-6)],18)
        cx,cy=hinge[0]+23,hinge[1]-4
        d.ellipse((cx-43,cy-26,cx+43,cy+26),fill=255)
        # Mechanical fixed bearing stays outside the operating arm.
        d.ellipse((152,257,192,297),fill=0)
        d.rectangle((0,333,512,512),fill=0)
    else:
        skin=np.asarray(m)
        yy,xx=np.nonzero(skin[170:270])
        yy=yy+170
        if len(xx)==0:raise ValueError('Missing reverse-fly skin envelope')
        left=xx.min();right=xx.max()
        ly=float(np.median(yy[xx<=left+8]));ry=float(np.median(yy[xx>=right-8]))
        lh=(float(left+6),ly);rh=(float(right-6),ry)
        p=max(0,min(1,(rh[0]-285)/147))
        lc=(lh[0]+30,83-65*p+47*p*p)
        rc=(rh[0]-23,93-80*p+68*p*p)
        for root,corner,hand in [((194,59),lc,lh),((231,59),rc,rh)]:
            bend=((root[0]+corner[0])/2,(root[1]+corner[1])/2-20)
            capsule(d,[root,bend,corner,hand],19)
            d.ellipse((hand[0]-23,hand[1]-25,hand[0]+23,hand[1]+25),fill=255)
        # True stationary top pivot cylinders, not a blanket upper rectangle
        # which would clip the rotating horizontal arms.
        d.rectangle((181,15,204,43),fill=0);d.rectangle((220,15,243,43),fill=0)
        d.rectangle((0,314,512,512),fill=0)
        h=np.asarray(head_mask());arr=np.asarray(m).copy();arr[h>20]=0;m=Image.fromarray(arr)
    # Slight feather preserves soft antialiased edges; interior255 canonical
    # pixels remain bit-for-bit fixed in the final compositor.
    m=m.filter(ImageFilter.GaussianBlur(1.0))
    return m

def main():
    for name in ['machine-ab-crunch','reverse-pec-deck']:
        folder=ART/name;out=folder/'static-composition';out.mkdir(exist_ok=True)
        files=[SOURCE/name/'frames'/f'frame_{i:04d}.png' for i in range(1,20)]
        images=[Image.open(p).convert('RGB') for p in files]
        points=[[310,190],[291,129],[327,130]] if name=='machine-ab-crunch' else []
        tracked,errors=track(images,points) if points else (None,[])
        masks=[moving_mask(im,name,i,tracked) for i,im in enumerate(images)]
        master=images[0]
        empty=Image.open(folder/'clean-fixed-machine-v1.png').convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
        # Preserve the original stationary pixels everywhere; use generated
        # empty-machine art only to clear the original moving-object regions.
        cleanup=masks[0].filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(1.1))
        canonical=Image.composite(empty,master,cleanup)
        if name=='reverse-pec-deck':canonical=Image.composite(master,canonical,head_mask())
        canonical_path=out/'canonical-fixed-reference.png';canonical.save(canonical_path)
        all_masks=masks+[masks[i] for i in range(17,0,-1)]
        union=np.maximum.reduce([np.asarray(mask) for mask in all_masks])
        fallback=out/'static-mask-union.png';Image.fromarray(255-union).save(fallback)
        records=[];review=[]
        preview=Image.new('RGB',(5*300,4*320),'white');d=ImageDraw.Draw(preview)
        overlay=Image.new('RGB',(5*300,4*320),'white');od=ImageDraw.Draw(overlay)
        for i,moving in enumerate(all_masks):
            static=Image.fromarray(255-np.asarray(moving));path=out/f'static-{i+1:04d}.png';static.save(path)
            records.append({'file':path.relative_to(ROOT).as_posix(),'sha256':digest(path)})
            if i<19:
                composed=Image.composite(images[i],canonical,moving)
                composed.save(out/f'preview-{i+1:04d}.png')
                rgb=np.asarray(images[i]).copy();mm=np.asarray(moving)/255
                tint=np.asarray([255,30,30]);tint=(rgb*(1-mm[:,:,None]*.25)+tint[None,None,:]*mm[:,:,None]*.25).clip(0,255).astype('uint8')
                x,y=(i%5)*300,(i//5)*320
                preview.paste(composed.resize((300,300)),(x,y+20));d.text((x+3,y+4),str(i+1),fill='black')
                overlay.paste(Image.fromarray(tint).resize((300,300)),(x,y+20));od.text((x+3,y+4),str(i+1),fill='black')
                review.append({'frame':i+1,'source':files[i].relative_to(ROOT).as_posix(),'sourceSha256':digest(files[i]),'dynamicFraction':float((np.asarray(moving)>0).mean()),'previewSha256':digest(out/f'preview-{i+1:04d}.png')})
        preview.save(out/'composed-forward19.png');overlay.save(out/'mask-forward19.png')
        spec={'enabled':True,'file':fallback.relative_to(ROOT).as_posix(),'sha256':digest(fallback),'referenceIndex':0,'referenceImage':{'file':canonical_path.relative_to(ROOT).as_posix(),'sha256':digest(canonical_path)},'frameMasks':records,'review':'Candidate per-frame envelopes, actual raster-skin segmentation and mechanical capsules. Canonical fixed apparatus/lower body; reverse head fixed. No athlete RGB warp/recolour. All19composed frames/edges must be visually reviewed before motion/export release.'}
        (folder/'static-mask-spec.json').write_text(json.dumps(spec,indent=2)+'\n')
        report={'id':name,'method':'Actual final-RIFE pixel segmentation and conservative mechanical capsules; alpha only, not image warp. The reference uses an image_gen empty-machine plate only where original moving parts need clearing.','scope':'candidate: inspect all19composed frames and overlaps before release','reverseDepth':'Hands and drop arms are foreground of the tower when silhouettes overlap. Their current masks retain actual source foreground pixels over the canonical tower.','trackerPoints':points,'trackedPoints':tracked,'trackForwardBackwardErrors':errors,'maximumForwardBackwardError':max([v for row in errors for v in row],default=None),'frames':review,'staticSpecSha256':digest(folder/'static-mask-spec.json')}
        (folder/'static-composition-review.json').write_text(json.dumps(report,indent=2)+'\n')
        print(name,'candidate masks36 ready; maximumFB',report['maximumForwardBackwardError'])

if __name__=='__main__':main()
