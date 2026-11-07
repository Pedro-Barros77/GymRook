"""Reproduce the reviewed old V4 near-boom mattes from local annotations.
No generated replacement geometry or image colors are used. The old silver
silhouette, original collar and short rubber shaft are traced in annotations.
Every output hash must equal the reviewed manifest. Nothing depends on cache.
"""
from pathlib import Path
import argparse,json,hashlib
from PIL import Image,ImageDraw
import numpy as np
source=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=source)
args=parser.parse_args()
annotations=json.loads((source/'annotations.json').read_text(encoding='utf-8'))
manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
traces={entry['frame']:entry for entry in annotations['traces']}
expected={entry['frame']:entry['sha256'] for entry in manifest['frames']}
frames=args.output.resolve()/'frames';frames.mkdir(parents=True,exist_ok=True)
S=6
for number in range(1,38):
 mask=Image.new('L',(512*S,512*S),0);draw=ImageDraw.Draw(mask)
 if number in traces:
  entry=traces[number];ys=entry['traceY'];left=entry['oldSilverLeft'];right=entry['oldSilverRight']
  tube=[(float(x),float(y)) for x,y in zip(left,ys)]+[(float(x),float(y)) for x,y in zip(right[::-1],ys[::-1])]
  draw.polygon([(round(x*S),round(y*S)) for x,y in tube],fill=255)
  cx,cy=entry['oldCollar']['center'];rx,ry=entry['oldCollar']['radii']
  draw.rounded_rectangle((round((cx-rx)*S),round((cy-ry)*S),round((cx+rx)*S),round((cy+ry)*S)),radius=round(2*S),fill=255)
  shaft=entry['oldUpperShaft'];top=cy+ry-1;bottom=164.;half=shaft['halfWidth'];slope=shaft['slopeDxDy']
  def xx(y):return shaft['rawAxisX164']+slope*(y-164)
  draw.polygon([(round((xx(top)-half)*S),round(top*S)),(round((xx(top)+half)*S),round(top*S)),(round((xx(bottom)+half)*S),round(bottom*S)),(round((xx(bottom)-half)*S),round(bottom*S))],fill=255)
 mask=mask.resize((512,512),Image.Resampling.LANCZOS);array=np.asarray(mask).copy();array[array<16]=0;array[:50]=0;array[164:]=0;array[:,:124]=0;array[:,180:]=0
 target=frames/f'frame_{number:04d}.png';Image.fromarray(array).save(target)
 actual=hashlib.sha256(target.read_bytes()).hexdigest()
 if actual!=expected[number]:raise RuntimeError(f'Reviewed mask did not reproduce exactly: frame{number}')
print(json.dumps({'frameCount':37,'hashesMatchReviewedManifest':True,'output':str(frames)}))
