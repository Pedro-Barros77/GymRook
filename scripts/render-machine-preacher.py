"""Render a raster-forearm preacher curl on a generated canonical machine/body.

The two forearms use the same generated RGBA component with fixed uniform scale
and rigid planar rotation only. No human mesh, optical-flow interpolation, limb
warp, or frame-dependent resizing is used. Hardware is a rigid native 2D rig.
"""
from pathlib import Path
import hashlib
import json
import math
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT/'docs/generated-frames-v3-repairs/preacher-curl'
RIG = FOLDER/'rig'
OUT = RIG/'frames'
S = 4
SIZE = 512
BASE = RIG/'clean-base-v1.png'
SPRITE = RIG/'forearm-sprite-v1.png'
NEAR = (291.0, 201.0)
FAR = (299.0, 194.0)
SRC_PIVOT = (150.0, 635.0)
SRC_WRIST = (955.0, 635.0)
SRC_GRIP = (1120.0, 635.0)
GRIP_RADIUS = 95.0
SCALE = GRIP_RADIUS/math.dist(SRC_PIVOT, SRC_GRIP)
START_DEGREES = 30.0
END_DEGREES = -60.0


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def circle(draw, center, radius, color, outline=None, width=1):
    x,y = [v*S for v in center]
    radius *= S
    draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=color,
                 outline=outline,width=width*S)


def polygon(draw, points, color):
    draw.polygon([(round(x*S),round(y*S)) for x,y in points],fill=color)


def beam(image, start, end, width=11):
    """Fixed-shape silver beam with a constant profile and simple light bevel."""
    draw=ImageDraw.Draw(image)
    dx,dy=end[0]-start[0],end[1]-start[1]
    length=math.hypot(dx,dy)
    normal=(-dy/length,dx/length)
    for fraction,color in [(1.0,'#35393b'),(.79,'#6b6d6c'),(.53,'#a3a4a0'),(.17,'#b8b9b6')]:
        r=width*fraction/2
        points=[(start[0]+normal[0]*r,start[1]+normal[1]*r),
                (end[0]+normal[0]*r,end[1]+normal[1]*r),
                (end[0]-normal[0]*r,end[1]-normal[1]*r),
                (start[0]-normal[0]*r,start[1]-normal[1]*r)]
        polygon(draw,points,color)


def local(point, pivot, degrees):
    a=math.radians(degrees)
    c,s=math.cos(a),math.sin(a)
    return (pivot[0]+point[0]*c-point[1]*s,pivot[1]+point[0]*s+point[1]*c)


def working_lever(image, pivot, degrees):
    # Constant bent profile: the lower edge stays just outside the forearm.
    parts=[((0,0),(9,12),11),((9,12),(GRIP_RADIUS-9,12),11),
           ((GRIP_RADIUS-9,12),(GRIP_RADIUS,0),10)]
    for start,end,width in parts:
        beam(image,local(start,pivot,degrees),local(end,pivot,degrees),width)


def sprite_at(sprite, pivot, degrees):
    """Inverse affine: one fixed scale and rotation about an immutable elbow."""
    a=math.radians(degrees)
    c,s=math.cos(a),math.sin(a)
    ox,oy=pivot
    px,py=SRC_PIVOT
    coeff=(c/(S*SCALE),s/(S*SCALE),px-(c*ox+s*oy)/SCALE,
           -s/(S*SCALE),c/(S*SCALE),py-(-s*ox+c*oy)/SCALE)
    return sprite.transform((SIZE*S,SIZE*S),Image.Transform.AFFINE,coeff,
                            Image.Resampling.BICUBIC)


def prepare_sprite():
    image=Image.open(SPRITE).convert('RGBA')
    data=np.asarray(image).copy()
    # The generation has stray alpha1..8 outside the isolated component. Drop
    # only that imperceptible alpha; RGB and the actual limb are unchanged.
    data[data[:,:,3]<=8,3]=0
    return Image.fromarray(data,'RGBA')


def render(degrees, sprite):
    image=Image.open(BASE).convert('RGBA').resize((SIZE*S,)*2,Image.Resampling.LANCZOS)
    draw=ImageDraw.Draw(image)
    polygon(draw,[(137,258),(160,261),(160,286),(137,282)],'#656965')
    beam(image,(150,272),NEAR,15)
    draw=ImageDraw.Draw(image)
    for point in [(143,265),(154,267),(143,277),(154,279)]:
        circle(draw,point,1.7,'#b8bcb6','#454844')
    # Both handgrips belong to one rigid cross-bar. Their separation remains
    # equal to the fixed separation of the two elbow axes.
    near_grip=local((GRIP_RADIUS,0),NEAR,degrees)
    far_grip=local((GRIP_RADIUS,0),FAR,degrees)
    working_lever(image,NEAR,degrees)
    beam(image,far_grip,near_grip,6)
    image=Image.alpha_composite(image,sprite_at(sprite,FAR,degrees))
    image=Image.alpha_composite(image,sprite_at(sprite,NEAR,degrees))
    draw=ImageDraw.Draw(image)
    circle(draw,NEAR,10.0,'#4f5453','#2f3433')
    circle(draw,NEAR,8.2,'#a1a49e','#c0c1ba')
    circle(draw,NEAR,5.8,'#656b67','#383f3b')
    circle(draw,NEAR,2.8,'#b4b7b0','#e1e0d7')
    return image.convert('RGB').resize((SIZE,)*2,Image.Resampling.LANCZOS),near_grip,far_grip


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    sprite=prepare_sprite()
    records=[]
    forward=[]
    for i in range(19):
        phase=(1-math.cos(math.pi*i/18))/2
        degrees=START_DEGREES+(END_DEGREES-START_DEGREES)*phase
        image,near,far=render(degrees,sprite)
        path=OUT/f'frame_{i+1:04d}.png'
        image.save(path)
        forward.append(path)
        records.append({'frame':i+1,'file':path.relative_to(ROOT).as_posix(),
                        'sha256':digest(path),'degrees':degrees,'phase':phase,
                        'nearElbow':NEAR,'farElbow':FAR,'nearGrip':near,'farGrip':far})
    for j,source_index in enumerate(range(17,0,-1),start=20):
        path=OUT/f'frame_{j:04d}.png'
        shutil.copyfile(forward[source_index],path)
        item=dict(records[source_index]);item.update(frame=j,file=path.relative_to(ROOT).as_posix(),sha256=digest(path),copyOfFrame=source_index+1)
        records.append(item)
    params={'method':'Generated canonical body and RGBA forearm; exactly rigid 2D raster rotation and constant-profile native equipment.','scope':'Root explicitly authorized planar raster-limb rig for this single-degree-of-freedom exercise. No human mesh or limb warping.','nativeSize':512,'antialiasSupersampling':S,'base':BASE.relative_to(ROOT).as_posix(),'baseSha256':digest(BASE),'sprite':SPRITE.relative_to(ROOT).as_posix(),'spriteSha256':digest(SPRITE),'sourceSpritePivot':SRC_PIVOT,'sourceSpriteWrist':SRC_WRIST,'sourceSpriteGrip':SRC_GRIP,'fixedUniformSpriteScale':SCALE,'nearElbow':NEAR,'farElbow':FAR,'gripRadiusPixels':GRIP_RADIUS,'forearmBoneRadiusPixels':math.dist(SRC_PIVOT,SRC_WRIST)*SCALE,'upperArmApproxDirectionDegrees':50,'elbowFlexionDegrees':[20,110],'rotationDegrees':[START_DEGREES,END_DEGREES],'frameCount':36,'fps':12,'durationSeconds':3,'limits':['Planar side-view representation; not a biomechanical certification.','Forearm muscles are stable raster art and do not dynamically bulge.','Source sprite shows a rotating machine grip; exact grip design varies by machine.']}
    (RIG/'parameters.json').write_text(json.dumps(params,indent=2)+'\n')
    index={'id':'preacher-curl','sourceKind':'reviewed-png-loop','frameCount':36,'fps':12,'cycle':'ping-pong','generator':Path(__file__).relative_to(ROOT).as_posix(),'generatorSha256':digest(Path(__file__)),'parameters':(RIG/'parameters.json').relative_to(ROOT).as_posix(),'inputs':{str(p.relative_to(ROOT).as_posix()):digest(p) for p in [BASE,SPRITE]},'sourceFrames':[{'file':r['file'],'sha256':r['sha256']} for r in records],'frames':records,'reviewStatus':'candidate; full-frame anatomical/mechanical and seam review required before release'}
    (FOLDER/'source-index.json').write_text(json.dumps(index,indent=2)+'\n')
    cols=5;contact=Image.new('RGB',(cols*320,4*340),'white');draw=ImageDraw.Draw(contact)
    for i,path in enumerate(forward):
        x,y=(i%cols)*320,(i//cols)*340
        contact.paste(Image.open(path).resize((320,320)),(x,y+20));draw.text((x+5,y+4),f'{i+1:02d}',fill='black')
    contact.save(RIG/'forward19-contact.png')
    print(f'Rendered {len(records)} rigid raster source PNGs in {OUT}')


if __name__=='__main__':
    main()
