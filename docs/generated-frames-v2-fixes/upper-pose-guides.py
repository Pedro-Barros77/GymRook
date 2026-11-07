"""Deterministic joint guides for imagegen input only, never shipped artwork."""
import math
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).parent
SIZE = 418

def vec(a, b): return tuple(x+y for x, y in zip(a,b))
def scale(a,s): return tuple(x*s for x in a)

def render(kind):
    sheet = Image.new('RGB',(SIZE*3,SIZE*3),'#f5f2ee')
    for i in range(9):
        im = Image.new('RGB',(SIZE,SIZE),'#f5f2ee')
        d = ImageDraw.Draw(im)
        rear = kind == 'reverse-pec-deck'
        yaw = math.radians(20 if not rear else 0)
        elev = math.radians(8 if not rear else 28)
        zoom = 157 if not rear else 145
        def p(v):
            x,y,z=v
            if rear:
                a=x; b=y*math.cos(elev)+z*math.sin(elev)
            else:
                a=x*math.cos(yaw)-z*math.sin(yaw)
                b=y*math.cos(elev)-(x*math.sin(yaw)+z*math.cos(yaw))*math.sin(elev)
            return (round((160 if rear else 194)+a*zoom),round(385-b*zoom))
        def line(a,b,color,width): d.line([p(a),p(b)],fill=color,width=width)
        def joint(v,r=5,color='#db703d'):
            x,y=p(v); d.ellipse((x-r,y-r,x+r,y+r),fill=color)
        def bodyline(a,b,w): line(a,b,'#d89c75',w)
        if rear:
            # Covered tower outside the arms' entire swept circle.
            for xx in [1.42,1.66]: line((xx,0,.7),(xx,2.18,.7),'#545b61',13)
            line((1.42,2.18,.7),(1.66,2.18,.7),'#545b61',14)
            line((1.54,2.1,.7),(0,2.1,0),'#697178',11)
            # Obvious rigid fixed crossbar carries BOTH fixed pivot bearings.
            line((-.29,2.02,0),(.29,2.02,0),'#424b52',15)
            line((.29,2.02,0),(1.54,2.02,.7),'#424b52',13)
            # Fixed seat support and chest pad.
            line((0,0,-.08),(0,.69,-.08),'#545b61',16)
            line((-.26,.7,-.08),(.26,.7,-.08),'#282d32',17)
            line((0,.3,.22),(0,1.48,.22),'#545b61',14)
            line((0,1.17,.25),(0,1.55,.25),'#30363b',24)
            phi=math.radians(20+70*i/8)
            shoulder_y=1.51
            for s in [-1,1]:
                shoulder=(s*.29,shoulder_y,0)
                elbow=vec(shoulder,(s*.35*math.sin(phi),0,.35*math.cos(phi)))
                wrist=vec(elbow,(s*.30*math.sin(phi-math.radians(20)),0,.30*math.cos(phi-math.radians(20))))
                pivot=(s*.29,2.02,0)
                overhead=(wrist[0],2.02,wrist[2])
                griptop=(wrist[0],1.66,wrist[2])
                line(pivot,overhead,'#737d84',9)
                line(overhead,griptop,'#737d84',9)
                line(griptop,(wrist[0],1.36,wrist[2]),'#292e34',9)
                joint(pivot,9,'#545b61')
            # Fixed trunk and seated lower body.
            bodyline((0,.85,0),(0,1.49,0),57)
            bodyline((-.19,.77,0),(-.39,.55,.23),28)
            bodyline((.19,.77,0),(.39,.55,.23),28)
            bodyline((-.39,.55,.23),(-.40,.10,.27),21)
            bodyline((.39,.55,.23),(.40,.10,.27),21)
            line((-.4,.08,.20),(-.4,.08,.42),'#222930',21)
            line((.4,.08,.20),(.4,.08,.42),'#222930',21)
            joint((0,1.78,0),22,'#3f3531')
            for s in [-1,1]:
                shoulder=(s*.29,shoulder_y,0)
                elbow=vec(shoulder,(s*.35*math.sin(phi),0,.35*math.cos(phi)))
                wrist=vec(elbow,(s*.30*math.sin(phi-math.radians(20)),0,.30*math.cos(phi-math.radians(20))))
                bodyline(shoulder,elbow,22); bodyline(elbow,wrist,17)
                for v in [shoulder,elbow,wrist]: joint(v)
        else:
            # Torso and legs fully stationary. Elbow flexion fixed at 25 degrees.
            bodyline((0,.90,0),(0,1.52,0),60)
            bodyline((-.14,.9,0),(-.15,.53,0),28)
            bodyline((.14,.9,0),(.15,.53,0),28)
            bodyline((-.15,.53,0),(-.17,.10,0),22)
            bodyline((.15,.53,0),(.17,.10,0),22)
            for s in [-1,1]: line((s*.17,.08,-.03),(s*.17,.08,.20),'#222930',20)
            joint((0,1.78,0),22,'#3f3531')
            theta=math.radians(8+80*i/8)
            for s in [-1,1]:
                shoulder=(s*.29,1.51,0)
                upper=(s*math.sin(theta),-math.cos(theta),0)
                elbow=vec(shoulder,scale(upper,.35))
                lower=(s*math.sin(theta-math.radians(25)),-math.cos(theta-math.radians(25)),0)
                wrist=vec(elbow,scale(lower,.30))
                bodyline(shoulder,elbow,22);bodyline(elbow,wrist,17)
                for v in [shoulder,elbow,wrist]:joint(v)
                line(vec(wrist,(0,0,-.09)),vec(wrist,(0,0,.09)),'#454e56',15)
                joint(vec(wrist,(0,0,-.09)),10,'#454e56');joint(vec(wrist,(0,0,.09)),10,'#454e56')
        sheet.paste(im,((i%3)*SIZE,(i//3)*SIZE))
    target=ROOT/kind/'pose-guide.png'
    target.parent.mkdir(parents=True,exist_ok=True)
    sheet.save(target)

for kind in ['dumbbell-lateral-raise','reverse-pec-deck']: render(kind)
