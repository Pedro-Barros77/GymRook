"""Track actual rendered calf frames, not positions inferred from input timing."""
from pathlib import Path
import math,json,hashlib
import cv2,numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;R=P.parents[2];W=R/'output/final-animations/seated-plate-calf-raise'
names=['hipSurfaceProxy','kneeSurfaceProxy','ankleSurfaceProxy','forefootContactBoundary','heelOutsoleEdge','rearPivot','plateHub']
initial=np.float32([[155,315],[281,320],[266,447],[342,479],[246,474],[82,343],[422,310]])
files=[W/'frames'/('frame_%04d.png'%i) for i in range(1,37)]
gray=[cv2.imread(str(f),cv2.IMREAD_GRAYSCALE) for f in files[:19]]
poses=[initial.copy()];errors=[];fb=[]
for i in range(1,19):
 prev=poses[-1].reshape(-1,1,2)
 nxt,status,err=cv2.calcOpticalFlowPyrLK(gray[i-1],gray[i],prev,None,winSize=(25,25),maxLevel=3,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.005))
 back,st,be=cv2.calcOpticalFlowPyrLK(gray[i],gray[i-1],nxt,None,winSize=(25,25),maxLevel=3,criteria=(cv2.TERM_CRITERIA_EPS|cv2.TERM_CRITERIA_COUNT,40,.005))
 errors.append(err[:,0].tolist());fb.append(np.linalg.norm(back.reshape(-1,2)-prev.reshape(-1,2),axis=1).tolist());poses.append(nxt.reshape(-1,2))

sheet=Image.new('RGB',(1280,2500),'white');ds=ImageDraw.Draw(sheet);out=[]
for i,points in enumerate(poses):
 im=Image.open(files[i]).convert('RGB');d=ImageDraw.Draw(im)
 for j,xy in enumerate(points):
  x,y=map(float,xy);d.ellipse((x-2,y-2,x+2,y+2),fill='#00baff')
 for a,b in [(0,1),(1,2)]:d.line((tuple(points[a]),tuple(points[b])),fill='#ff5b00',width=2)
 # Small fixed contact target cross indicates whether the forefoot slides.
 d.line(((337,479),(347,479)),fill='red',width=1);d.line(((342,474),(342,484)),fill='red',width=1)
 crop=im.crop((210,265,370,500)).resize((320,470));x=i%4*320;y=i//4*500;sheet.paste(crop,(x,y));ds.text((x+6,y+476),str(i+1),fill='black')
 out.append({'frame':i+1,'sha256':hashlib.sha256(files[i].read_bytes()).hexdigest(),'landmarks':{name:points[j].astype(float).tolist() for j,name in enumerate(names)},'femurProxyPixels':float(np.linalg.norm(points[0]-points[1])),'tibiaProxyPixels':float(np.linalg.norm(points[1]-points[2])),'forefootDisplacementFromStartPixels':float(np.linalg.norm(points[3]-initial[3])),'pivotDisplacementFromStartPixels':float(np.linalg.norm(points[5]-initial[5])),'leverRadiusPixels':float(np.linalg.norm(points[5]-points[6]))})
sheet.save(P/'qa-two-key-all19-leg-tracks.png')
def stat(key):
 vals=[q[key] for q in out];return{'min':min(vals),'max':max(vals),'rangeOverMeanPercent':100*(max(vals)-min(vals))/(sum(vals)/len(vals)),'endChangeFromStartPercent':100*(vals[-1]/vals[0]-1) if vals[0] else None}
report={'sourceIndex':'docs/generated-frames-v2-fixes/seated-plate-calf-raise/source-index-two-keys-v3.json','sourceIndexSha256':hashlib.sha256((P/'source-index-two-keys-v3.json').read_bytes()).hexdigest(),'method':'Manual initial surface-proxy landmarks tracked sequentially with pyramidal Lucas-Kanade over all19actual rendered forward PNGs; forward/backward error also measured. No pose is inferred from interpolation timestep. Surface points and hidden joint proxies do not establish bone-center locations or clinical correctness. Visual crop/contact review required.','initialLandmarkUncertaintyPixels':{'hipSurfaceProxy':7,'kneeSurfaceProxy':5,'ankleSurfaceProxy':4,'forefootContactBoundary':3,'mechanicalCenter':2},'trackingMaxForwardBackwardErrorPixels':max(max(e) for e in fb),'forwardBackwardErrorPerFrame':fb,'summary':{key:stat(key) for key in ['femurProxyPixels','tibiaProxyPixels','leverRadiusPixels']},'maxForefootDisplacementPixels':max(q['forefootDisplacementFromStartPixels'] for q in out),'maxPivotDisplacementPixels':max(q['pivotDisplacementFromStartPixels'] for q in out),'limits':{'tibiaAndFemurProxyRangeOverMeanPercent':10,'forefootDisplacementPixels':5,'pivotDisplacementPixels':3,'leverRadiusRangeOverMeanPercent':5},'poses':out,'reviewStatus':'pending visual confirmation of all19actual frames; this is supporting motion tracking, not clinical validation'}
source_index=json.loads((W/'prepare.json').read_text())['source']
report['sourceIndex']=source_index
report['sourceIndexSha256']=hashlib.sha256((R/source_index).read_bytes()).hexdigest()
(P/'qa-two-key-temporal-measurements.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k in ['summary','maxForefootDisplacementPixels','maxPivotDisplacementPixels','trackingMaxForwardBackwardErrorPixels']},indent=2))
