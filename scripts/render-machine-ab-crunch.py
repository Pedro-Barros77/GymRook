"""Candidate abdominal-machine repair: reviewed raster athlete, rigid native arm.

No RGB athlete warp. Original visible moving skin/hair is restored byte-for-byte
on its opaque mask core; an image_gen hardware-only edit removes the old cap.
The operating arm is a single152px radial part under the generated pad. The
column/backrest/seat/lowerbody use one canonical stationary photograph.
"""
from pathlib import Path
import hashlib,json,math
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFilter

ROOT=Path(__file__).resolve().parent.parent
ART=ROOT/'docs/generated-frames-v3-repairs/machine-ab-crunch'
RIG=ART/'rig-v3'
BODY=ART/'rig/body-source/frames'
CLEAN=ROOT/'output/repair-animations/candidates/ab-hardware-clean-v2/machine-ab-crunch/frames'
PIVOT=np.array([172.,277.])
RADIUS=152.


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def capsule(points,radius):
    mask=Image.new('L',(512,512),0);d=ImageDraw.Draw(mask)
    d.line([tuple(map(float,p)) for p in points],fill=255,width=round(radius*2),joint='curve')
    for x,y in points:d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=255)
    return mask


def skin_core(image,full_upper=False,hand_centers=None):
    arr=np.asarray(image);hsv=cv2.cvtColor(arr,cv2.COLOR_RGB2HSV)
    skin=(hsv[:,:,0]<30)&(hsv[:,:,1]>47)&(hsv[:,:,2]>35)&(arr[:,:,0].astype(float)-arr[:,:,1]>18)
    skin[:,:185]=False;skin[:,450:]=False
    upper=np.nonzero(skin[:250])[0]
    top=int(upper.min()) if len(upper) else 25
    hair=(hsv[:,:,0]<30)&(hsv[:,:,1]>15)&(hsv[:,:,2]>12)&(hsv[:,:,2]<150)
    hair[:,:185]=False;hair[:,450:]=False;hair[top+75:]=False
    skin|=hair
    # Actual hands/forearms end above282 in these reviewed sources; thighs are
    # stationary and use the master. This leaves5px clearance and prevents a
    # touching thigh component from being restored on top of the working pad.
    skin[287:]=False
    if full_upper:skin[255:]=False
    m=(skin.astype(np.uint8)*255)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    # The moving actor is head/torso/arms. Warm reflected patches below the
    # roller and static thigh components are not moving skin foreground.
    count,labels,stats,_=cv2.connectedComponentsWithStats(m,8)
    accepted=np.zeros_like(m)
    for label in range(1,count):
        x,y,w,h,area=stats[label]
        keep=y<180 and area>60
        for hx,hy in hand_centers or []:
            xx0,xx1=max(0,round(hx)-7),min(512,round(hx)+8)
            yy0,yy1=max(0,round(hy)-7),min(512,round(hy)+8)
            if np.any(labels[yy0:yy1,xx0:xx1]==label):keep=True
        if keep:accepted[labels==label]=255
    m=accepted
    # Fill small highlights/eyes, not the large empty space between arm/torso.
    inverted=255-m
    count,labels,stats,_=cv2.connectedComponentsWithStats(inverted,8)
    for label in range(1,count):
        x,y,w,h,area=stats[label]
        if area<100 and x>185 and x+w<450 and y>0 and y+h<287:m[labels==label]=255
    return Image.fromarray(m)


def old_gear_envelope(point):
    line=capsule([PIVOT,point],13)
    d=ImageDraw.Draw(line);x,y=point;d.ellipse((x-18,y-18,x+18,y+18),fill=255)
    # The fixed bearing is preserved and later drawn in front of the new arm.
    d.ellipse((150,255,194,299),fill=0)
    return line


def raw_hardware_mask(raw,point,tips):
    env=Image.new('L',(512,512),0);d=ImageDraw.Draw(env)
    cx,cy=point+[23,-4]
    d.ellipse((cx-43,cy-30,cx+43,cy+30),fill=255)
    for tip,end in [(tips[0],point),(tips[1],point+[35,-6])]:
        lower=tip+(end-tip)*.72
        env=Image.fromarray(np.maximum(np.asarray(env),np.asarray(capsule([tip,lower],10))))
    a=np.asarray(raw);hsv=cv2.cvtColor(a,cv2.COLOR_RGB2HSV)
    # Leather shadow is warm brown, so a saturation-only "neutral metal"
    # threshold cuts holes through the lower cylinder. Retain dark material
    # of any hue, plus the brighter neutral metal of the grip hardware.
    neutral=(hsv[:,:,2]<175)|((hsv[:,:,1]<72)&(hsv[:,:,2]<220))
    mask=np.asarray(env).copy();mask[~neutral]=0
    mask=cv2.morphologyEx(mask,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
    return Image.fromarray(mask).filter(ImageFilter.BoxBlur(.5))


def clean_alignment(raw,clean,tips):
    a=cv2.cvtColor(np.asarray(raw),cv2.COLOR_RGB2GRAY)
    b=cv2.cvtColor(np.asarray(clean),cv2.COLOR_RGB2GRAY)
    shifts=[];scores=[]
    for x,y in tips:
        x,y=round(x),round(y);r=6;search=6
        patch=a[y-r:y+r+1,x-r:x+r+1]
        window=b[y-r-search:y+r+search+1,x-r-search:x+r+search+1]
        result=cv2.matchTemplate(window,patch,cv2.TM_CCOEFF_NORMED)
        _,score,_,pos=cv2.minMaxLoc(result)
        if score>.72:
            shifts.append([search-pos[0],search-pos[1]]);scores.append(score)
    shift=np.median(shifts,axis=0) if shifts else np.zeros(2)
    if np.max(np.abs(shift))>4:shift[:]=0
    aligned=cv2.warpAffine(np.asarray(clean),np.array([[1,0,shift[0]],[0,1,shift[1]]],np.float32),(512,512),flags=cv2.INTER_LANCZOS4,borderMode=cv2.BORDER_REPLICATE)
    return Image.fromarray(aligned),{'translationPixels':shift.tolist(),'scores':scores,'scope':'equipment cleanup only; never applied to athlete RGB'}


def operating_arm(angle):
    size=4;out=Image.new('RGBA',(512*size,512*size),(0,0,0,0));d=ImageDraw.Draw(out)
    u=np.array([math.cos(angle),math.sin(angle)]);n=np.array([-u[1],u[0]])
    end=PIVOT+RADIUS*u
    # One rigid monoblock shape:24px main beam toR125, taper to a6px tab atR145,
    # then a7px-long tab entering the cushion. A24px terminal would protrude
    # under the cushion into the stationary thigh at deep contraction.
    radii=[0.,125.,145.,RADIUS]
    for width,color in [(24,(69,73,71,255)),(21,(122,127,124,255)),(16,(150,155,151,255))]:
        widths=[width,width,width*.25,width*.25]
        left=[PIVOT+u*r-n*w/2 for r,w in zip(radii,widths)]
        right=[PIVOT+u*r+n*w/2 for r,w in zip(radii,widths)]
        d.polygon([tuple(p*size) for p in left+right[::-1]],fill=color)
    for sign,color in [(-1,(202,207,202,255)),(1,(88,92,89,255))]:
        offsets=[8.,8.,1.5,1.5]
        points=[tuple((PIVOT+u*r+n*sign*off)*size) for r,off in zip(radii,offsets)]
        d.line(points,fill=color,width=2*size,joint='curve')
    return out.resize((512,512),Image.Resampling.LANCZOS),end


def main():
    RIG.mkdir(parents=True,exist_ok=True);(RIG/'frames').mkdir(exist_ok=True);(RIG/'actor-masks').mkdir(exist_ok=True)
    frozen_body=json.loads((BODY.parent/'index.json').read_text())['frames']
    for item in frozen_body:
        if digest(ROOT/item['file'])!=item['sha256']:
            raise ValueError('Reviewed original athlete motion changed before native equipment composition.')
    source=json.loads((ART/'static-composition-review.json').read_text())
    tracked=np.asarray(source['trackedPoints'])
    raws=[Image.open(BODY/f'frame_{i:04d}.png').convert('RGB') for i in range(1,20)]
    cleans=[Image.open(CLEAN/f'frame_{i:04d}.png').convert('RGB') for i in range(1,20)]
    empty=Image.open(ART/'clean-lowerbody-machine-v2.png').convert('RGB').resize((512,512),Image.Resampling.LANCZOS)
    master=raws[0]
    # Clear original moving torso/head above waist using generated background.
    body_cleanup=skin_core(master,True)
    hardware_cleanup=raw_hardware_mask(master,tracked[0,0],tracked[0,1:])
    cleanup=Image.fromarray(np.maximum(np.asarray(body_cleanup),np.asarray(hardware_cleanup)))
    cleanup=cleanup.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.BoxBlur(.5))
    # Remove the faint original standing-head antialias halo as background,
    # before placing the actual moving head. No fixed hardware occupies this
    # isolated upper region; this is not a rectangle pasted over the athlete.
    head_clear=Image.new('L',(512,512),0)
    ImageDraw.Draw(head_clear).ellipse((194,2,306,126),fill=255)
    cleanup=Image.fromarray(np.maximum(np.asarray(cleanup),np.asarray(head_clear)))
    cleanup_arr=np.asarray(cleanup).copy();cleanup_arr[255:]=0;cleanup=Image.fromarray(cleanup_arr)
    canonical=Image.composite(empty,master,cleanup)
    gear=old_gear_envelope(tracked[0,0]);geararr=np.asarray(gear).copy()
    geararr[np.asarray(skin_core(master))>128]=0
    upper=geararr.copy();upper[255:]=0
    canonical=Image.composite(empty,canonical,Image.fromarray(upper).filter(ImageFilter.BoxBlur(.5)))
    # Tool-generated cleanup fills only the occluded strip of old shaft below
    # the waist. All visible canonical hips/legs/seat pixels remain the master.
    clean0,alignment0=clean_alignment(master,cleans[0],tracked[0,1:])
    lower=geararr.copy();lower[:255]=0
    canonical=Image.composite(clean0,canonical,Image.fromarray(lower).filter(ImageFilter.BoxBlur(.5)))
    canonical.save(RIG/'canonical-machine-lowerbody.png')
    bearing_mask=Image.new('L',(512,512),0);ImageDraw.Draw(bearing_mask).ellipse((150,255,194,299),fill=255)
    bearing_mask=bearing_mask.filter(ImageFilter.BoxBlur(.5))
    outputs=[];reviews=[];actor_masks=[]
    for i,(raw,clean) in enumerate(zip(raws,cleans)):
        point=tracked[i,0];tips=tracked[i,1:]
        hand_centers=[tips[0]+(point-tips[0])*.5,tips[1]+(point+[35,-6]-tips[1])*.5]
        angle=math.atan2(point[1]-PIVOT[1],point[0]-PIVOT[0])
        image=canonical.convert('RGBA');arm,end=operating_arm(angle);image=Image.alpha_composite(image,arm).convert('RGB')
        # Original visible pad/grips survive; only old cap pixels are replaced
        # by the image_gen hardware-only cleanup, never generated athlete skin.
        aligned,alignment=clean_alignment(raw,clean,tips)
        # Use the tool-cleaned pad/handles as one continuous hardware object,
        # rather than welding a small circular cap patch into the old roller.
        hardware=raw_hardware_mask(aligned,point,tips)
        image=Image.composite(aligned,image,hardware)
        # Restore exact original upper-body skin/hair core; no RGB warp.
        actor=skin_core(raw,hand_centers=hand_centers).filter(ImageFilter.BoxBlur(.5))
        image=Image.composite(raw,image,actor)
        image=Image.composite(master,image,bearing_mask)
        apath=RIG/'actor-masks'/f'actor_{i+1:04d}.png';actor.save(apath)
        current=np.asarray(image);a=np.asarray(actor);original=np.asarray(raw)
        assert np.array_equal(current[a==255],original[a==255])
        outputs.append(image);actor_masks.append(actor)
        reviews.append({'frame':i+1,'angleDegrees':math.degrees(angle),'pivotPixels':PIVOT.tolist(),'endpointPixels':end.tolist(),
                        'radiusPixels':float(np.linalg.norm(end-PIVOT)),'bodySource':(BODY/f'frame_{i+1:04d}.png').relative_to(ROOT).as_posix(),
                        'bodySourceSha256':digest(BODY/f'frame_{i+1:04d}.png'),'changedOpaqueActorRGBPixels':0,
                        'cleanupAlignment':alignment,'actorMask':{'file':apath.relative_to(ROOT).as_posix(),'sha256':digest(apath)}})
    images=outputs+[outputs[j] for j in range(17,0,-1)]
    masks=actor_masks+[actor_masks[j] for j in range(17,0,-1)]
    frames=[]
    for i,image in enumerate(images):
        path=RIG/'frames'/f'frame_{i+1:04d}.png';image.save(path)
        frames.append({'file':path.relative_to(ROOT).as_posix(),'sha256':digest(path)})
    contact=Image.new('RGB',(1500,1280),'white');d=ImageDraw.Draw(contact)
    for i,image in enumerate(outputs):
        x,y=(i%5)*300,(i//5)*320;contact.paste(image.resize((300,300)),(x,y+20));d.text((x+4,y+4),str(i+1),fill='black')
    contact.save(RIG/'forward19-contact.png')
    parameters={'pivotPixels':PIVOT.tolist(),'operatingArmRadiusPixels':RADIUS,'operatingArmMaximumWidthPixels':24,
                'rigidArmCrossSection':{'radiusStationsPixels':[0,125,145,152],'widthPixels':[24,24,6,6],'reason':'Narrow rigid terminal tab fits fully inside actual cushion; no wide gray terminal across the thigh.'},
                'angleSource':'atan2 of actual old pad side-cap material point relative to fixed pivot; source point is not treated as a3D joint certificate',
                'canonicalMachine':(RIG/'canonical-machine-lowerbody.png').relative_to(ROOT).as_posix(),
                'rawBodySourceIndex':(BODY.parent/'index.json').relative_to(ROOT).as_posix(),'review':reviews,
                'radiusSelection':'Actual dark-cushion silhouette has common radial interior149..156px across19poses; R152 keeps the fixed-length endpoint in the roller instead of extending R165 into the stationary thigh.',
                'scope':'Candidate native equipment repair. Original visible upper-body skin/hair RGB preserved on opaque mask; static lowerbody restored from a single master. Tool cleanup only restores old gray cap/shaft regions, not new full athlete poses.'}
    (RIG/'parameters.json').write_text(json.dumps(parameters,indent=2)+'\n')
    input_paths=[ART/'sheet-hardware-clean-v2.png',ART/'clean-lowerbody-machine-v2.png',ART/'static-composition-review.json',BODY.parent/'index.json',RIG/'canonical-machine-lowerbody.png']
    input_paths += [ROOT/item['file'] for item in frozen_body]
    input_paths += [CLEAN/f'frame_{i:04d}.png' for i in range(1,20)]
    input_paths += [RIG/'actor-masks'/f'actor_{i:04d}.png' for i in range(1,20)]
    inputs={str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in input_paths}
    actor_entries=[r['actorMask'] for r in reviews]
    actor_entries += [actor_entries[j] for j in range(17,0,-1)]
    index={'id':'machine-ab-crunch','sourceKind':'reviewed-png-loop','frameCount':36,'fps':12,'cycle':'ping-pong',
           'generator':Path(__file__).relative_to(ROOT).as_posix(),'generatorSha256':digest(Path(__file__)),
           'parameters':(RIG/'parameters.json').relative_to(ROOT).as_posix(),'inputs':inputs,'sourceFrames':frames,
           'nativeBodyPixelPreservation':{'sourceFrames':frozen_body,'maskFrames':actor_entries,
             'review':'Opaque moving upper-body skin/hair core pixels are identical to each corresponding reviewed raw athlete frame. Lowerbody/seat use one stationary canonical master. No human RGB warp.'},
           'reviewStatus':'candidate: inspect all19actual composites, old shaft/cap disappearance, actor edges and pants before release'}
    (ART/'source-index-native-v3.json').write_text(json.dumps(index,indent=2)+'\n')
    print('Candidate Ab native36; actor RGB core exact; rigid arm152px with6px terminal; review required.')


if __name__=='__main__':main()
