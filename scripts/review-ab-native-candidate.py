"""Inspect the actual raster/native pad junction and preserve a hash-bound study."""
from pathlib import Path
import hashlib,json,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
ART=ROOT/'docs/generated-frames-v3-repairs/machine-ab-crunch'
RIG=ART/'rig-v3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
params=json.loads((RIG/'parameters.json').read_text())
frames=[Image.open(RIG/'frames'/f'frame_{i:04d}.png').convert('RGB') for i in range(1,20)]
contact=Image.new('RGB',(1500,1600),'white');d=ImageDraw.Draw(contact)
onions=Image.new('RGB',(1500,1280),'white');od=ImageDraw.Draw(onions)
entries=[]
for i,(image,entry) in enumerate(zip(frames,params['review'])):
    x,y=entry['endpointPixels'];cx,cy=round(x),round(y)
    rgb=np.asarray(image)[cy-1:cy+2,cx-1:cx+2]
    theta=math.radians(entry['angleDegrees']);normal=np.array([-math.sin(theta),math.cos(theta)])
    lower=[]
    for offset in [0,1,2,3]:
        px,py=np.rint(np.array([x,y])+normal*offset).astype(int)
        lower.append(np.asarray(image)[py,px].tolist())
    assert max(max(p) for p in lower)<145,(i+1,lower)
    record={'frame':i+1,'endpointPixels':[x,y],'endpoint3x3MaxRGB':int(rgb.max()),'radiusPixels':entry['radiusPixels'],
            'terminalLowerNormalOffsets0to3RGB':lower,'rigidTerminalWidthPixels':6}
    assert rgb.max()<145,record
    crop=image.crop((220,100,420,330)).resize((300,345))
    px,py=(i%5)*300,(i//5)*400
    contact.paste(crop,(px,py+25));d.text((px+4,py+4),f'{i+1} | R152 endpoint max {rgb.max()}',fill='black')
    if i<18:
        blend=Image.blend(image,frames[i+1],.5).crop((220,100,420,330)).resize((250,288))
        ox,oy=(i%6)*250,(i//6)*320;onions.paste(blend,(ox,oy+20));od.text((ox+4,oy+4),f'{i+1}/{i+2}',fill='black')
    entries.append(record)
contact.save(RIG/'hardware19-critical.png');onions.save(RIG/'hardware18-onions.png')
review={'status':'candidate: actual junction images require independent/root review','radiusPixels':152,
        'endpointInsideDarkCushionAll19':True,'endpointSampling':'3x3 actual final RGB neighborhood max<145; supplemented by visual pad-silhouette review',
        'sourceIndex':{'file':(ART/'source-index-native-v3.json').relative_to(ROOT).as_posix(),'sha256':sha(ART/'source-index-native-v3.json')},
        'frames':[{'file':(RIG/'frames'/f'frame_{i:04d}.png').relative_to(ROOT).as_posix(),'sha256':sha(RIG/'frames'/f'frame_{i:04d}.png')} for i in range(1,37)],'samples':entries}
(RIG/'junction-review.json').write_text(json.dumps(review,indent=2)+'\n')
print('All19 actual endpoints inside dark cushion; candidate not released by metrics alone.')
