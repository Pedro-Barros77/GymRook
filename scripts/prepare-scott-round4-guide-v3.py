"""Internal side-biased pose scaffold; never substituted for generated final art."""
from pathlib import Path
import math,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/'docs/generated-frames-v4-followup/preacher-curl'
near={'shoulder':(210,140),'elbow':(270,230),'gripRadius':105}
far={'shoulder':(234,129),'elbow':(294,219),'gripRadius':105}
angles=[41,28,15,2,-11,-24,-37,-50,-63]
sheet=Image.new('RGB',(1536,1536),(250,248,245));draw=ImageDraw.Draw(sheet);poses=[]
for i,angle in enumerate(angles):
 ox,oy=(i%3)*512,(i//3)*512;pose={'cell':i,'angleDegrees':angle,'arms':{}}
 for name,arm in [('far',far),('near',near)]:
  shoulder,elbow=arm['shoulder'],arm['elbow']
  grip=(elbow[0]+arm['gripRadius']*math.cos(math.radians(angle)),elbow[1]+arm['gripRadius']*math.sin(math.radians(angle)))
  points=[(x+ox,y+oy) for x,y in [shoulder,elbow,grip]]
  draw.line(points[:2],fill=(0,155,185),width=13);draw.line(points[1:],fill=(205,35,145),width=11)
  for (x,y),color in zip(points,[(0,115,155),(20,175,40),(215,25,130)]):
   draw.ellipse((x-7,y-7,x+7,y+7),fill=color)
  pose['arms'][name]={'shoulder':shoulder,'elbow':elbow,'gripCenter':grip,'projectedRadius':arm['gripRadius']}
 poses.append(pose)
sheet.save(DEST/'pose-guide-v3.png')
(DEST/'pose-guide-v3.json').write_text(json.dumps({'scope':'projection scaffold only; no3D anatomical certification','near':near,'far':far,'poses':poses},indent=2)+'\n',encoding='utf-8')
