from pathlib import Path
from PIL import Image, ImageDraw

for id in ['unilateral-cable-row','machine-ab-crunch','high-cable-crossover','cable-biceps-curl','preacher-curl','floor-crunch','reverse-crunch','dumbbell-lateral-raise','reverse-pec-deck']:
    p=Path('output/final-animations')/id
    out=Image.new('RGB',(1280,1120),'white')
    d=ImageDraw.Draw(out)
    for i in range(19):
        out.paste(Image.open(p/'frames'/f'frame_{i+1:04d}.png').resize((256,256)),((i%5)*256,(i//5)*280+24))
        d.text(((i%5)*256+4,(i//5)*280+5),str(i+1),fill='black')
    out.save(p/'qa/forward19.png')
