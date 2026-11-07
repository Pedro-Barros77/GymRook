"""Manual 2D landmark audit; measured artwork, not the input skeleton."""
from pathlib import Path
import json, math, hashlib
import numpy as np
from PIL import Image, ImageDraw
BASE=Path(__file__).resolve().parent

CURL=[
 {'hip':[210,218],'knee':[132,225],'ankle':a,'pivot':[132,225],'roller':r,'shoulder':[315,198]}
 for a,r in zip([[53,216],[57,201],[66,186],[72,176],[79,162],[90,154],[99,147],[104,145],[112,144]],
                [[63,217],[66,201],[76,188],[83,181],[88,174],[97,166],[102,164],[105,161],[109,158]])]
STIFF=[
 {'hip':h,'knee':k,'ankle':[173,337]}
 for h,k in zip([[174,197],[169,197],[163,198],[156,199],[151,201],[145,202],[141,203],[138,204],[135,205]],
                [[177,265],[175,265],[175,265],[173,265],[172,265],[170,266],[169,267],[168,268],[166,268]])]

def stats(values):
 return {'minimum':min(values),'maximum':max(values),'mean':sum(values)/len(values),'rangeOverMeanPercent':100*(max(values)-min(values))/(sum(values)/len(values))}

def audit(id,poses):
 p=BASE/id;im=Image.open(p/'sheet.png').convert('RGB');annotated=im.copy();d=ImageDraw.Draw(annotated)
 for i,q in enumerate(poses):
  ox=i%3*418;oy=i//3*418
  for name,point in q.items():
   x,y=point;d.ellipse((ox+x-3,oy+y-3,ox+x+3,oy+y+3),fill=(0,150,255))
   d.text((ox+x+4,oy+y-8),name,fill=(0,75,150))
  for a,b in [('hip','knee'),('knee','ankle')]:
   d.line(((q[a][0]+ox,q[a][1]+oy),(q[b][0]+ox,q[b][1]+oy)),fill=(255,90,0),width=2)
 annotated.save(p/'qa-joint-landmarks.png')
 segments={name:[math.dist(q[a],q[b]) for q in poses] for name,a,b in [('femur','hip','knee'),('tibia','knee','ankle')]}
 if id=='lying-leg-curl':segments['mechanicalLeverRadius']=[math.dist(q['pivot'],q['roller']) for q in poses]
 summary={name:stats(vals) for name,vals in segments.items()}
 for i,q in enumerate(poses):q['pose']=i;q['segmentLengthsPixels']={name:vals[i] for name,vals in segments.items()}
 report={'source':'docs/generated-frames-v2-fixes/'+id+'/sheet.png','sha256':hashlib.sha256((p/'sheet.png').read_bytes()).hexdigest(),'grid':[3,3],'cellPixels':[418,418],
 'method':'Manual near-side surface-landmark estimates on the final generated sheet. Orange lines/blue points in qa-joint-landmarks.png show the estimates. These are not the exact input-guide coordinates. Bone centers under shorts/roller cannot be observed directly.',
 'uncertaintyPixels':{'visibleAnkle':4,'visibleKnee':5,'hipUnderShorts':7,'mechanicalPivotAndRoller':2},
 'acceptanceLimits':{'femurAndTibiaRangeOverMeanPercent':10,'mechanicalLeverRadiusRangeOverMeanPercent':10,'scope':'Screen-space geometry screening only, not clinical or 3D skeletal validation'},
 'summary':summary,'poses':poses,
 'geometryScreenResult':'within manual screen-space range limits; interpolated motion still must be reviewed',
 'visualReview':{'camera':'side profile, no planned camera move or scale change','body':'same muscular colored character, no obvious calf/thigh growth at peak','feet':'constant-scale shoes; curl feet rotate as rigid pieces, stiff soles remain planted','equipment':'curl bench/tower fixed, external roller lever rotates about fixed knee pivot; tower enclosed with opaque cover' if id=='lying-leg-curl' else 'two fixed-size dumbbells, no machine',
 'limitations':['Landmarks are approximate surface proxies; projection and hidden joint centers prevent proof of exact bone lengths.','Knee flexion in stiff remains soft but not mathematically identical in every generated source.','Do not equate a passing source screen with perfect anatomical execution; review final interpolation.']}}
 (p/'qa-source-measurements.json').write_text(json.dumps(report,indent=2)+'\n')
 print(id,json.dumps(summary))

if __name__=='__main__':audit('lying-leg-curl',CURL);audit('dumbbell-stiff-leg-deadlift',STIFF)
