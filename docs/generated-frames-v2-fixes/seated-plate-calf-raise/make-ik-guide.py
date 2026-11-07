"""Reference guide only: closed rigid leg chain and rigid rear-pivot machine lever."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent
SIZE=512
def add(a,b):return(a[0]+b[0],a[1]+b[1])
def rot(a,deg):
 t=math.radians(deg);return(a[0]*math.cos(t)-a[1]*math.sin(t),a[0]*math.sin(t)+a[1]*math.cos(t))
def sub(a,b):return(a[0]-b[0],a[1]-b[1])
def ik(h,a,lf,lt):
 dx,dy=sub(a,h);dist=math.hypot(dx,dy);along=(lf*lf-lt*lt+dist*dist)/(2*dist);perp=math.sqrt(lf*lf-along*along)
 base=(h[0]+along*dx/dist,h[1]+along*dy/dist)
 choices=[(base[0]+sign*perp*-dy/dist,base[1]+sign*perp*dx/dist) for sign in [-1,1]]
 return max(choices,key=lambda q:q[0])
H=(155,315);K=(280,322);A=(265,447);T=(345,475);HEEL=(244,483)
LF=math.dist(H,K);LT=math.dist(K,A);R=(82,343);PLATE=(422,310);PAD=(255,277);GRIP=(255,231)
sheet=Image.new('RGB',(SIZE*3,SIZE*3),(249,247,243));poses=[]
for i in range(9):
 f=i/8;ang=12*f;ankle=add(T,rot(sub(A,T),ang));heel=add(T,rot(sub(HEEL,T),ang));knee=ik(H,ankle,LF,LT)
 plate=add(R,rot(sub(PLATE,R),-6*f));pad=add(R,rot(sub(PAD,R),-6*f));grip=add(R,rot(sub(GRIP,R),-6*f))
 c=Image.new('RGB',(SIZE,SIZE),(249,247,243));d=ImageDraw.Draw(c)
 d.line(((40,484),(208,484)),fill='#626467',width=16);d.line(((82,346),(48,484)),fill='#626467',width=12);d.line(((166,350),(166,484)),fill='#626467',width=12)
 d.line(((83,354),(201,354)),fill='#27292c',width=23);d.polygon(((315,475),(354,441),(405,441),(405,498),(315,498)),fill='#626467')
 d.line((R,plate),fill='#777b80',width=17);d.ellipse((plate[0]-55,plate[1]-55,plate[0]+55,plate[1]+55),fill='#343638',outline='#777b80',width=5)
 d.line((H,knee,ankle),fill='#bd774f',width=24);d.line((heel,T),fill='#25282b',width=22)
 d.line((H,(148,153)),fill='#bd774f',width=43);d.ellipse((123,48,185,114),fill='#bd774f')
 d.line(((148,153),(174,244),grip),fill='#bd774f',width=22)
 d.line(((140,311),(194,320)),fill='#27292c',width=44)
 d.rounded_rectangle((pad[0]-34,pad[1]-13,pad[0]+34,pad[1]+13),radius=9,fill='#17191a');d.line((pad,grip),fill='#343638',width=7)
 for q,col in [(H,'#00b5ff'),(knee,'#00b5ff'),(ankle,'#00b5ff'),(T,'#00b5ff'),(R,'#ffad00')]:d.ellipse((q[0]-4,q[1]-4,q[0]+4,q[1]+4),fill=col)
 sheet.paste(c,((i%3)*SIZE,(i//3)*SIZE))
 poses.append({'index':i,'hip':H,'knee':knee,'ankle':ankle,'ballContact':T,'heel':heel,'pad':pad,'handGrip':grip,'rearPivot':R,'plateCenter':plate,'femurLength':LF,'tibiaLength':LT,'plateRadius':55,'leverLength':math.dist(R,plate),'footRotationDegrees':ang,'leverRotationDegrees':-6*f})
sheet.resize((1254,1254)).save(P/'reference-ik-v3.png')
(P/'reference-ik-v3.json').write_text(json.dumps({'purpose':'REFERENCE ONLY; positions computed with exact two-link IK and constant foot/lever lengths; this is not measurement of generated image','coordinateCellSize':512,'sheetSavedCellSize':418,'poses':poses},indent=2)+'\n')
print(json.dumps({'femur':LF,'tibia':LT,'initial':poses[0],'final':poses[-1]},indent=2))
