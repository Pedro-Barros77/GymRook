"""Reference geometry only. Final artwork is produced with builtin imagegen."""
from pathlib import Path
import math, json
from PIL import Image, ImageDraw

BASE = Path(__file__).resolve().parent
CELL = 418
BG = (249, 247, 243)
SKIN = (190, 111, 72)
INK = (42, 45, 48)

def add(p, q): return (p[0]+q[0], p[1]+q[1])
def v(length, deg):
    a=math.radians(deg)
    return (length*math.cos(a), length*math.sin(a))
def circle(d,p,r,fill): d.ellipse((p[0]-r,p[1]-r,p[0]+r,p[1]+r),fill=fill)
def limb(d,a,b,width=14): d.line((a,b),fill=SKIN,width=width);circle(d,a,width/2,SKIN);circle(d,b,width/2,SKIN)
def sheet_out(exercise, cells, poses):
    out=BASE/exercise;out.mkdir(parents=True,exist_ok=True)
    sheet=Image.new('RGB',(CELL*3,CELL*3),BG)
    for i,c in enumerate(cells):sheet.paste(c,((i%3)*CELL,(i//3)*CELL))
    sheet.save(out/'reference-geometry.png')
    (out/'reference-geometry.json').write_text(json.dumps({'cellSize':CELL,'grid':[3,3],'purpose':'Geometric support for imagegen, not final art or measurements of final art','poses':poses},indent=2)+'\n')

def curl():
    cells=[];poses=[]
    for i in range(9):
        c=Image.new('RGB',(CELL,CELL),BG);d=ImageDraw.Draw(c)
        k=(140,235);h=(228,228);s=(315,218);a=add(k,v(86,180+i*12.5))
        foot=add(a,v(25,125+i*12.5));roller=add(k,v(75,180+i*12.5))
        # Stable profile apparatus, transparent geometry purpose only.
        d.rectangle((242,50,290,340),outline=(110,113,115),width=8)
        d.rectangle((252,55,280,334),outline=(110,113,115),width=3)
        for y in range(270-i*3,318-i*3,6):d.rectangle((254,y,278,y+4),fill=INK)
        d.line(((128,255),(352,255)),fill=INK,width=20)
        d.line(((135,265),(118,350),(355,350),(345,265)),fill=(110,113,115),width=9)
        d.line((k,roller),fill=(110,113,115),width=6)
        limb(d,h,k,24);limb(d,k,a,17);d.line((a,foot),fill=INK,width=17)
        limb(d,h,s,33);d.line((h,(201,230)),fill=INK,width=38)
        limb(d,s,(338,250),20);limb(d,(338,250),(376,238),15)
        circle(d,(347,197),18,SKIN);d.line((s,(336,206)),fill=SKIN,width=24)
        circle(d,roller,12,(59,60,61));circle(d,k,4,(225,150,0))
        poses.append({'pose':i,'kneeAngleFlexionDegrees':i*12.5,'hip':h,'shoulder':s,'knee':k,'ankle':a,'footTip':foot,'roller':roller,'expectedLengthsPixels':{'femur':math.dist(h,k),'tibia':86,'foot':25,'torso':math.dist(h,s)}})
        cells.append(c)
    sheet_out('lying-leg-curl',cells,poses)

def stiff():
    cells=[];poses=[]
    for i in range(9):
        c=Image.new('RGB',(CELL,CELL),BG);d=ImageDraw.Draw(c)
        t=i/8;a=(190,376);k=add(a,v(80,-80-22*t));h=add(k,v(80,-95-22*t));s=add(h,v(110,-90+65*t))
        hand=(211,s[1]+math.sqrt(146**2-(s[0]-211)**2));elbow=((s[0]+hand[0])/2,(s[1]+hand[1])/2)
        neck=add(s,v(14,-90+65*t));head=add(neck,v(20,-90+65*t))
        # Near and far shoes remain planted. Skeleton lengths do not change.
        d.ellipse((158,378,242,391),fill=(225,223,220))
        d.line(((199,376),(232,380)),fill=(110,110,110),width=16)
        limb(d,a,k,21);limb(d,k,h,28);limb(d,h,s,37)
        d.line((h,add(h,v(34,85-22*t))),fill=INK,width=40)
        limb(d,s,hand,17);limb(d,s,neck,22);circle(d,head,18,SKIN)
        d.line((a,(221,380)),fill=INK,width=17)
        d.rectangle((hand[0]-23,hand[1]-10,hand[0]+23,hand[1]+10),fill=INK)
        circle(d,k,3,(225,150,0));circle(d,h,3,(225,150,0))
        poses.append({'pose':i,'ankle':a,'knee':k,'hip':h,'shoulder':s,'elbow':elbow,'hand':hand,'head':head,'expectedLengthsPixels':{'femur':80,'tibia':80,'torso':110,'arm':146},'kneeInteriorDegrees':165,'torsoAngleFromHorizontalDegrees':90-65*t})
        cells.append(c)
    sheet_out('dumbbell-stiff-leg-deadlift',cells,poses)

if __name__=='__main__':curl();stiff()
