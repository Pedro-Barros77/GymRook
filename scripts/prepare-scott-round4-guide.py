"""Internal pose scaffold: fixed shoulders/elbows and equal projected forearm arcs.

This guide is not a delivered exercise illustration or a biomechanical model.
It constrains generated art so that upper arms cannot shorten as the curl rises.
"""
from pathlib import Path
import math,json
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parent.parent
DEST=ROOT/'docs/generated-frames-v4-followup/preacher-curl'
NEAR={'shoulder':(166,144),'elbow':(211,226),'gripRadius':105}
FAR={'shoulder':(254,143),'elbow':(293,207),'gripRadius':100}
angles=[45,32,19,6,-7,-20,-33,-46,-59]
sheet=Image.new('RGB',(1536,1536),(250,248,245))
draw=ImageDraw.Draw(sheet)
poses=[]
for i,angle in enumerate(angles):
 ox,oy=(i%3)*512,(i//3)*512
 pose={'cell':i,'angleDegrees':angle,'arms':{}}
 for name,arm in [('far',FAR),('near',NEAR)]:
  shoulder,elbow=arm['shoulder'],arm['elbow']
  grip=(elbow[0]+arm['gripRadius']*math.cos(math.radians(angle)),elbow[1]+arm['gripRadius']*math.sin(math.radians(angle)))
  points=[(x+ox,y+oy) for x,y in [shoulder,elbow,grip]]
  draw.line(points[:2],fill=(0,155,185),width=13)
  draw.line(points[1:],fill=(205,35,145),width=11)
  for point,color in zip(points,[(0,115,155),(20,175,40),(215,25,130)]):
   x,y=point;draw.ellipse((x-7,y-7,x+7,y+7),fill=color)
  pose['arms'][name]={'shoulder':shoulder,'elbow':elbow,'gripCenter':grip,'projectedRadius':arm['gripRadius']}
 poses.append(pose)
 for x,y in [(0,0),(511,0),(0,511),(511,511)]:
  draw.ellipse((ox+x-2,oy+y-2,ox+x+2,oy+y+2),fill=(175,175,175))
sheet.save(DEST/'pose-guide-v2.png')
(DEST/'pose-guide-v2.json').write_text(json.dumps({'scope':'projected drawing scaffold only; no exact3D anatomy certificate','near':NEAR,'far':FAR,'poses':poses},indent=2)+'\n',encoding='utf-8')
