from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np, json, hashlib
R=Path(__file__).resolve().parents[2]
W=R/'output/leg-animations/alternating-lunge'
O=Path(__file__).resolve().parent/'alternating-lunge'
O.mkdir(parents=True,exist_ok=True)
names=['anchors/anchor_14.png','anchors/anchor_15.png','frames/frame_0046.png','frames/frame_0047.png','frames/frame_0048.png','frames/frame_0001.png','frames/frame_0002.png','frames/frame_0003.png','anchors/anchor_00.png','anchors/anchor_08.png']
sheet=Image.new('RGB',(512*5,548*2),'white');d=ImageDraw.Draw(sheet)
for i,n in enumerate(names):
    im=Image.open(W/n).convert('RGB');x=(i%5)*512;y=(i//5)*548
    sheet.paste(im,(x,y));d.text((x+8,y+518),n,fill='black')
sheet.save(O/'loop-contact.png')
arr=[np.asarray(Image.open(W/f'frames/frame_{i:04d}.png').convert('RGB'),dtype=float) for i in range(1,49)]
diffs=[float(np.abs(arr[i]-arr[(i+1)%48]).mean()) for i in range(48)]
first=Image.open(W/'anchors/anchor_00.png').convert('RGB');last=Image.open(W/'anchors/anchor_15.png').convert('RGB')
Image.blend(first,last,0.5).save(O/'standing-00-vs-15-onion.png')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
report={'readOnlyAnalysis':True,'source':'output/leg-animations/alternating-lunge','frameMAEToNextInOrder':diffs,'seam48to1MAE':diffs[-1],'preceding47to48MAE':diffs[-2],'following1to2MAE':diffs[0],'anchor00Equals08':sha(W/'anchors/anchor_00.png')==sha(W/'anchors/anchor_08.png'),'anchor00Equals15':sha(W/'anchors/anchor_00.png')==sha(W/'anchors/anchor_15.png'),'anchor00to15MAE':float(np.abs(np.asarray(first,dtype=float)-np.asarray(last,dtype=float)).mean()),'proposal':'Set anchor index 15 at progress .9375 to source cell 0, as index 8 already does at .5. Regenerate periodic frames; inspect interval 14->15 for stepping occlusion. This changes return into a canonical planted standing pose then holds through seam. No mirroring, scaling, native geometry or fake pixel jitter. Keep 48 MP4 frames at 12 fps. GIF encoder may legitimately merge identical standing holds while preserving 4000ms.'}
(O/'loop-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='frameMAEToNextInOrder'},indent=2))
