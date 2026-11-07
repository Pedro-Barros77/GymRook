"""Audit of frozen rejected v2 artwork, with manually estimated surface landmarks."""
from pathlib import Path
from PIL import Image,ImageDraw
import math,json,hashlib
P=Path(__file__).resolve().parent;R=P.parents[2]
W=R/'output/final-animations/candidates/calf-v2/seated-plate-calf-raise'
K=[[281,320],[281,319],[281,317],[282,314],[282,313],[282,310],[282,307],[282,304],[282,301]]
A=[[266,447],[267,445],[268,442],[270,439],[272,435],[276,430],[280,424],[285,417],[291,410]]
HEEL=[[245,485],[245,483],[245,481],[246,478],[246,475],[247,468],[250,460],[256,449],[263,438]]
PAD=[[254,277],[254,276],[254,275],[254,275],[254,274],[253,272],[252,270],[251,267],[250,264]]
PLATE=[[422,310],[422,302],[422,295],[422,290],[422,283],[421,276],[421,269],[421,260],[421,250]]
poses=[];sheet=Image.new('RGB',(1536,1620),'white');d=ImageDraw.Draw(sheet)
for i in range(9):
 path=W/'anchors'/('anchor_%02d.png'%i);im=Image.open(path).convert('RGB');dd=ImageDraw.Draw(im)
 q={'hip':[155,315],'knee':K[i],'ankle':A[i],'ballContact':[344,479],'heel':HEEL[i],'rearPivot':[82,343],'padCenter':PAD[i],'plateCenter':PLATE[i]}
 for label,xy in q.items():
  dd.ellipse((xy[0]-3,xy[1]-3,xy[0]+3,xy[1]+3),fill='#00c3ff');dd.text((xy[0]+4,xy[1]-8),label,fill='#005d9b')
 for a,b in [('hip','knee'),('knee','ankle')]:dd.line((tuple(q[a]),tuple(q[b])),fill='#ff5d00',width=2)
 x=i%3*512;y=i//3*540;sheet.paste(im,(x,y));d.text((x+8,y+518),str(i),fill='black')
 q.update({'index':i,'file':str(path.relative_to(R)).replace('\\','/'),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'femurPixels':math.dist(q['hip'],q['knee']),'tibiaPixels':math.dist(q['knee'],q['ankle']),'leverRadiusPixels':math.dist(q['rearPivot'],q['plateCenter'])});poses.append(q)
sheet.save(P/'qa-calf-v2-landmarks.png')
report={'source':'docs/generated-frames-v2-fixes/seated-plate-calf-raise/sheet-v2.png','sourceSHA256':'aec2de7037686bba557b65defc5ec2cda6c790d8f94a58e1193f6427f5fbfa50','method':'Manual surface estimates on all9 actual frozen512px anchors. Hip/knee centers are hidden anatomical proxies, uncertainty~5-7px; ankle/contact/plate~3-4px. Not inferred from the IK guide.','result':'rejected','uncertaintyPixels':{'hip':7,'knee':5,'ankle':4,'contact':3,'mechanicalCenter':3},'poses':poses,'summary':{'tibiaStart':poses[0]['tibiaPixels'],'tibiaEnd':poses[-1]['tibiaPixels'],'tibiaEndChangePercent':100*(poses[-1]['tibiaPixels']/poses[0]['tibiaPixels']-1),'heelRisePixels':HEEL[0][1]-HEEL[-1][1],'kneeRisePixels':K[0][1]-K[-1][1],'ankleRisePixels':A[0][1]-A[-1][1],'padRisePixels':PAD[0][1]-PAD[-1][1],'plateRisePixels':PLATE[0][1]-PLATE[-1][1]},'reason':'Ankle rise exceeds knee rise by18px, estimated shin shortens~14%; excessive heel lift and pad lift inconsistent with rear-pivot lever. This supersedes an earlier rough visual estimate of28% shortening.','replacementStrategy':'Two imagegen endpoints with a much smaller heel rise and constant shin, RIFE19halfcycle; verify forefoot contact and all19 actual interpolated tibia lengths.'}
(P/'qa-calf-v2-geometry.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['summary'],indent=2))
