"""Image-generation composition guide only; never an app demonstration."""
from pathlib import Path
from PIL import Image, ImageDraw
import math, json

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT/'docs/generated-frames-v4-followup/lying-leg-raise'
OUT.mkdir(parents=True, exist_ok=True)
sheet = Image.new('RGB', (1536,1536), '#faf9f5')
records=[]
for i in range(9):
    im=Image.new('RGB',(512,512),'#faf9f5'); d=ImageDraw.Draw(im)
    hip=(267.,419.); angle=12+i*8.5
    def segment(p,length,theta):
        a=math.radians(theta)
        return (p[0]-length*math.cos(a),p[1]-length*math.sin(a))
    knee=segment(hip,115,angle)
    ankle=segment(knee,103,angle+8)
    d.rounded_rectangle((18,445,498,460),radius=4,fill='#44474b')
    d.line([(267,419),(340,415),(405,412),(438,411)],fill='#9ba5b0',width=45)
    d.ellipse((440,375,494,430),fill='#9ba5b0')
    d.line([(406,424),(355,441),(262,448)],fill='#9ba5b0',width=16)
    d.line([hip,knee,ankle],fill='#d9463e',width=24)
    for p in [hip,knee,ankle]:
        d.ellipse((p[0]-5,p[1]-5,p[0]+5,p[1]+5),fill='#263c54')
    # Shoe points up relative to the shin, with the same size in every cell.
    theta=math.radians(angle+8)
    toe=(ankle[0]-29*math.sin(theta),ankle[1]+29*math.cos(theta))
    d.line([ankle,toe],fill='#263c54',width=19)
    sheet.paste(im,((i%3)*512,(i//3)*512))
    records.append({'cell':i,'hip':hip,'knee':knee,'ankle':ankle,
                    'femurPixels':115,'tibiaPixels':103,'softKneeBendDegrees':8,
                    'angleAboveFloorDegrees':angle})
sheet.save(OUT/'pose-guide-v2.png')
(OUT/'pose-guide-v2.json').write_text(json.dumps({'purpose':'composition/bone-length guide only; no clinical3D angle claim','poses':records},indent=2)+'\n',encoding='utf-8')
