"""Rigid raster lower-leg curl study on one generated canonical body/machine.

One fixed uniform scale and knee rotation animate a generated RGBA lower leg.
No human mesh, limb warp, frame resizing or optical-flow interpolation is used.
The posterior roller/lever share that exact rotation and invariant local offset.
This writes a comparison study only; publishing requires root review.
"""
from pathlib import Path
import hashlib,json,math,shutil
import cv2
import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent.parent
FOLDER=ROOT/'docs/generated-frames-v3-repairs/lying-leg-curl'
RIG=FOLDER/'rig'; OUT=RIG/'frames'
BASE=RIG/'clean-base-v1-512.png'; SPRITE=RIG/'lower-leg-sprite-v1.png'
SIZE=512; S=4
NEAR=(160.,274.); FAR=(156.,272.)
SRC_KNEE=(1950.,265.); SRC_ANKLE=(520.,300.)
TIBIA=100.; SCALE=TIBIA/math.dist(SRC_KNEE,SRC_ANKLE)
SOURCE_ANGLE=math.degrees(math.atan2(SRC_ANKLE[1]-SRC_KNEE[1],SRC_ANKLE[0]-SRC_KNEE[0]))
SOURCE_CORRECTION=180.-SOURCE_ANGLE
CONTACT_ALONG=90.; ROLLER_RADIUS=15.

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local(q,pivot,degrees):
 a=math.radians(degrees);c,s=math.cos(a),math.sin(a)
 return (pivot[0]+q[0]*c-q[1]*s,pivot[1]+q[0]*s+q[1]*c)
def circle(image,p,r,fill,outline=None,width=1):
 d=ImageDraw.Draw(image);x,y=p;r*=S;x*=S;y*=S
 d.ellipse((x-r,y-r,x+r,y+r),fill=fill,outline=outline,width=round(width*S))
def beam(image,a,b,width=6):
 d=ImageDraw.Draw(image);dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);nx,ny=-dy/length,dx/length
 for fraction,color in [(1.,'#393d3e'),(.79,'#777c7c'),(.48,'#b0b4b2'),(.12,'#d1d2ca')]:
  r=width*fraction/2
  d.polygon([(round((a[0]+nx*r)*S),round((a[1]+ny*r)*S)),(round((b[0]+nx*r)*S),round((b[1]+ny*r)*S)),(round((b[0]-nx*r)*S),round((b[1]-ny*r)*S)),(round((a[0]-nx*r)*S),round((a[1]-ny*r)*S))],fill=color)
def prepare_sprite():
 im=Image.open(SPRITE).convert('RGBA');a=np.array(im).copy();a[a[:,:,3]<=8,3]=0
 return Image.fromarray(a,'RGBA')
def sprite_at(sprite,pivot,degrees):
 a=math.radians(SOURCE_CORRECTION+degrees);c,s=math.cos(a),math.sin(a);ox,oy=pivot;px,py=SRC_KNEE
 coeff=(c/(S*SCALE),s/(S*SCALE),px-(c*ox+s*oy)/SCALE,-s/(S*SCALE),c/(S*SCALE),py-(-s*ox+c*oy)/SCALE)
 return sprite.transform((SIZE*S,)*2,Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC)
def circle_mask(p,r):
 out=Image.new('L',(SIZE*S,)*2,0);d=ImageDraw.Draw(out);x,y=p
 d.ellipse(((x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S),fill=255)
 return np.asarray(out)>0
def choose_posterior_offset(sprite):
 # Calibrate once from the actual generated leg. Endcap must not intersect
 # the eroded opaque limb core; this is a raster contact check, not anatomy.
 near=np.asarray(sprite_at(sprite,NEAR,0))[:,:,3]>240
 far=np.asarray(sprite_at(sprite,FAR,0))[:,:,3]>240
 core=cv2.erode((near|far).astype('uint8'),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(S*4+1,)*2))>0
 for normal in np.arange(18.,40.01,.25):
  center=local((-CONTACT_ALONG,-float(normal)),NEAR,0)
  if not np.any(circle_mask(center,ROLLER_RADIUS)&core):return float(normal)+.5
 raise ValueError('No posterior contact offset clears the generated leg core.')
def roller(image,near,far):
 # One short cylinder crosses the two ankles. Its far end is behind the near
 # circular end; opaque near cap has a constant radius/material in every frame.
 circle(image,far,ROLLER_RADIUS,'#383c3d','#202426')
 d=ImageDraw.Draw(image);r=ROLLER_RADIUS
 d.polygon([(int((near[0]-r)*S),int(near[1]*S)),(int((far[0]-r)*S),int(far[1]*S)),(int((far[0]+r)*S),int(far[1]*S)),(int((near[0]+r)*S),int(near[1]*S))],fill='#3d4142')
 circle(image,near,r,'#2c3032','#171b1d')
 circle(image,(near[0]-.6,near[1]-.7),r-1.8,'#424748','#62696a',.6)
 circle(image,near,5.3,'#a6aaa6','#d3d6cf',.7)
 circle(image,near,3.1,'#696f6d','#444a48',.5)
 circle(image,(near[0]-.45,near[1]-.5),1.4,'#d1d4ca')
def render(degrees,sprite,normal):
 image=Image.open(BASE).convert('RGBA').resize((SIZE*S,)*2,Image.Resampling.LANCZOS)
 # A small fixed bearing bracket joins the knee axle to the existing bench.
 beam(image,(159,294),NEAR,8)
 image=Image.alpha_composite(image,sprite_at(sprite,FAR,degrees))
 image=Image.alpha_composite(image,sprite_at(sprite,NEAR,degrees))
 q=(-CONTACT_ALONG,-normal);near=local(q,NEAR,degrees);far=local(q,FAR,degrees)
 # Constant dog-leg profile routes the beam outside the posterior calf,
 # instead of drawing a straight arm through the shin/foot silhouette.
 elbow=local((0,-normal),NEAR,degrees)
 beam(image,NEAR,elbow,6);beam(image,elbow,near,6)
 roller(image,near,far)
 circle(image,NEAR,9.3,'#42494a','#202729')
 circle(image,NEAR,7.1,'#a1a7a2','#d7d9ce',.7)
 circle(image,NEAR,4.5,'#666e69','#39423b',.7)
 circle(image,NEAR,2.,'#d3d8cb')
 return image.convert('RGB').resize((SIZE,)*2,Image.Resampling.LANCZOS),near,far
def main():
 OUT.mkdir(parents=True,exist_ok=True);sprite=prepare_sprite();normal=choose_posterior_offset(sprite)
 records=[];forward=[];contact_checks=[]
 for i in range(19):
  phase=(1-math.cos(math.pi*i/18))/2;degrees=95.*phase
  image,near,far=render(degrees,sprite,normal);path=OUT/f'frame_{i+1:04d}.png';image.save(path);forward.append(path)
  near_leg=np.asarray(sprite_at(sprite,NEAR,degrees))[:,:,3]>240
  near_core=cv2.erode(near_leg.astype('uint8'),cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(S*4+1,)*2))>0
  overlap=int((circle_mask(near,ROLLER_RADIUS)&near_core).sum())
  contact_checks.append({'frame':i+1,'nearCapLegCoreOverlapSupersamplePixels':overlap})
  records.append({'frame':i+1,'file':path.relative_to(ROOT).as_posix(),'sha256':digest(path),'phase':phase,'degrees':degrees,'nearKnee':NEAR,'farKnee':FAR,'nearAnkle':local((-TIBIA,0),NEAR,degrees),'farAnkle':local((-TIBIA,0),FAR,degrees),'nearRoller':near,'farRoller':far,'rollerLeverRadius':math.hypot(CONTACT_ALONG,normal),'tibiaRadius':TIBIA})
 for j,index in enumerate(range(17,0,-1),start=20):
  path=OUT/f'frame_{j:04d}.png';shutil.copyfile(forward[index],path);r=dict(records[index]);r.update(frame=j,file=path.relative_to(ROOT).as_posix(),sha256=digest(path),copyOfFrame=index+1);records.append(r)
 params={'method':'Generated canonical body/machine plus rigidly rotated generated RGBA lower-leg raster; exactly invariant tibia, shoe and roller/lever geometry.','authorization':'Root explicitly requested planar one-DOF raster-leg study, no human mesh or limb warp.','base':BASE.relative_to(ROOT).as_posix(),'baseSha256':digest(BASE),'sprite':SPRITE.relative_to(ROOT).as_posix(),'spriteSha256':digest(SPRITE),'sourceKnee':SRC_KNEE,'sourceAnkle':SRC_ANKLE,'fixedUniformScale':SCALE,'sourceAxisCorrectionDegrees':SOURCE_CORRECTION,'nearKnee':NEAR,'farKnee':FAR,'tibiaRadius':TIBIA,'posteriorRollerOffset':[CONTACT_ALONG,normal],'rollerRadius':ROLLER_RADIUS,'leverRadius':math.hypot(CONTACT_ALONG,normal),'kneeFlexionRangeDegrees':[0,95],'fps':12,'frameCount':36,'supersampling':S,'contactChecks':contact_checks,'limits':['Planar side-profile illustration, not a biomechanical certification.','Muscle texture is fixed raster art and does not bulge dynamically.','The generated near-leg texture is duplicated for the mostly hidden far leg with fixed knee offset.']}
 (RIG/'parameters.json').write_text(json.dumps(params,indent=2)+'\n')
 index={'id':'lying-leg-curl','sourceKind':'reviewed-png-loop','frameCount':36,'fps':12,'cycle':'ping-pong','generator':Path(__file__).relative_to(ROOT).as_posix(),'generatorSha256':digest(Path(__file__)),'parameters':(RIG/'parameters.json').relative_to(ROOT).as_posix(),'inputs':{p.relative_to(ROOT).as_posix():digest(p) for p in [BASE,SPRITE]},'sourceFrames':[{'file':r['file'],'sha256':r['sha256']} for r in records],'frames':records,'reviewStatus':'comparison study only; body seam/contact/full motion requires independent root approval'}
 (FOLDER/'source-index-rig.json').write_text(json.dumps(index,indent=2)+'\n')
 contact=Image.new('RGB',(5*320,4*340),'white');d=ImageDraw.Draw(contact)
 for i,p in enumerate(forward):
  x,y=(i%5)*320,(i//5)*340;contact.paste(Image.open(p).resize((320,320)),(x,y+20));d.text((x+4,y+4),f'{i+1:02d}',fill='black')
 contact.save(RIG/'forward19-contact.png')
 print(f'Rendered36comparison frames; tibia={TIBIA:.3f}, lever={params["leverRadius"]:.3f}, posteriorOffset={normal:.2f}, maximumNearCoreOverlap={max(c["nearCapLegCoreOverlapSupersamplePixels"] for c in contact_checks)}')

if __name__=='__main__':main()
