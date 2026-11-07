from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib
root=Path.cwd();out=root/'.cache/old-near-tower-masks';src=Path(json.loads((out/'source.json').read_text())['directory']);maskdir=out/'frames';maskdir.mkdir(exist_ok=True)
axis=json.loads((root/'docs/generated-frames-v5/pec-deck/rigid-levers/shaft-axis-fits.json').read_text());motion=json.loads((root/'docs/generated-frames-v5/pec-deck/rigid-levers/motion-37.json').read_text());ys=np.array([50,55,60,65,70,75,80,85,90,95,100,105,110,120,130,140,143],float)
# Actual old V4 silhouette traces, read against the pixel grids. These are not
# the new rigid geometry. Only the old tube's visible outer edges are followed.
traces={
1:([190,182,174,167,160,154,148,143,139,136,134,132,131,131,131,131,131],[220,215,208,202,195,189,183,177,171,164,160,157,155,154,154,154,155]),
6:([208,201,194,186,179,171,163,156,152,149,148,147,147,147,147,147,147],[238,230,224,217,211,204,197,190,185,180,176,173,171,170,170,170,171]),
10:([216,211,205,199,192,183,175,171,168,165,163,162,162,162,162,162,163],[246,240,235,230,224,215,206,200,195,190,187,185,184,184,184,184,185]),
11:([219,214,208,202,197,187,179,175,172,170,169,169,170,172,174,177,176],[249,244,238,232,227,217,209,204,199,196,195,195,196,198,200,200,200]),
12:([222,217,212,207,202,193,184,180,177,176,175,175,175,177,179,181,179],[252,247,242,237,232,223,214,210,206,203,201,201,201,201,202,203,202])}
capx={n:axis['frames'][n-1]['hands']['near']['xAt149'] for n in range(1,13)}
for n in range(2,6):
 t=(capx[n]-capx[1])/(capx[6]-capx[1]);traces[n]=tuple((1-t)*np.asarray(a)+t*np.asarray(b) for a,b in zip(traces[1],traces[6]))
for n in range(7,10):
 t=(capx[n]-capx[6])/(capx[10]-capx[6]);traces[n]=tuple((1-t)*np.asarray(a)+t*np.asarray(b) for a,b in zip(traces[6],traces[10]))
S=6;annotations=[];manifest=[]
for n in range(1,38):
 before=Image.open(src/f'frame_{n:04d}.png').convert('RGB');mask=Image.new('L',(512*S,512*S),0);draw=ImageDraw.Draw(mask)
 if n<=12:
  left,right=map(np.asarray,traces[n]);tube=[(float(x),float(y)) for x,y in zip(left,ys)]+[(float(x),float(y)) for x,y in zip(right[::-1],ys[::-1])]
  draw.polygon([(round(x*S),round(y*S)) for x,y in tube],fill=255)
  fit=axis['frames'][n-1]['hands']['near'];handY=motion['frames'][n-1]['expectedHands']['near'][1];cy=handY-39.5;cx=fit['xAt149']+1.;rx=13.;ry=4.5
  # The original ring and upper rubber belong to the old object too.
  draw.rounded_rectangle((round((cx-rx)*S),round((cy-ry)*S),round((cx+rx)*S),round((cy+ry)*S)),radius=round(2*S),fill=255)
  top=cy+ry-1;bottom=164.;half=fit['medianBlackWidth']/2+.4;slope=fit['slopeDxDy']
  def xx(y):return fit['xAt164']+slope*(y-164)
  draw.polygon([(round((xx(top)-half)*S),round(top*S)),(round((xx(top)+half)*S),round(top*S)),(round((xx(bottom)+half)*S),round(bottom*S)),(round((xx(bottom)-half)*S),round(bottom*S))],fill=255)
  annotations.append(dict(frame=n,traceY=ys.tolist(),oldSilverLeft=left.tolist(),oldSilverRight=right.tolist(),oldCollar=dict(center=[cx,cy],radii=[rx,ry]),oldUpperShaft=dict(rawAxisX149=fit['xAt149'],rawAxisX164=fit['xAt164'],halfWidth=half,slopeDxDy=slope)))
 mask=mask.resize((512,512),Image.Resampling.LANCZOS);a=np.asarray(mask).copy();a[a<16]=0;a[:50]=0;a[164:]=0;a[:,:124]=0;a[:,180:]=0;mask=Image.fromarray(a);path=maskdir/f'frame_{n:04d}.png';mask.save(path);nonzero=np.argwhere(a>0);bounds=[int(nonzero[:,1].min()),int(nonzero[:,0].min()),int(nonzero[:,1].max()+1),int(nonzero[:,0].max()+1)] if len(nonzero) else None
 manifest.append(dict(frame=n,file=f'frames/frame_{n:04d}.png',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),sourceSha256=hashlib.sha256((src/f'frame_{n:04d}.png').read_bytes()).hexdigest(),bounds=bounds,nonzeroPixels=int(np.count_nonzero(a))))
 if n<=12:
  rgb=np.asarray(before).astype(float);alpha=a.astype(float)/255*.45;overlay=np.uint8(np.round(rgb*(1-alpha[:,:,None])+np.array([255,20,100])*alpha[:,:,None]));Image.fromarray(overlay).save(out/f'overlay-frame_{n:04d}.png')
(out/'annotations.json').write_text(json.dumps(dict(role='OLD V4 near tube silhouette only, ring and upper rubber included. New rigid equipment is not used.',roi=[124,50,180,164],traces=annotations),indent=2)+'\n');(out/'manifest.json').write_text(json.dumps(dict(status='frozen-source-reviewed-old-silhouette-candidate',frameCount=37,frameSize=[512,512],sourceDirectory=str(src),roi=[124,50,180,164],method='Source-specific old silhouette annotations plus source-fitted old collar/upper rubber. Sixfold supersampling, Lanczos ringing below16 removed; outside ROI hardzero. Frames13..37 clear after source inspection.',frames=manifest),indent=2)+'\n')
board=Image.new('RGB',(1080,1161),'#eee');d=ImageDraw.Draw(board)
for k,n in enumerate(range(1,13)):
 x=k%4*270;y=k//4*387;im=Image.open(out/f'overlay-frame_{n:04d}.png').crop((120,45,210,164)).resize((270,357));board.paste(im,(x,y+30));d.text((x+5,y+8),f'OLD silhouette mask frame{n}',fill='black')
board.save(out/'first12-overlays.png');print(json.dumps([(f['frame'],f['bounds'],f['nonzeroPixels']) for f in manifest],indent=2))
