"""Batch inference with official Practical-RIFE model, isolated local runtime.
JSON manifest: [{"input0":"...png","input1":"...png","timestep":0.5,"output":"...png"}]
All manifest paths may be absolute or relative to the manifest directory.
"""
from pathlib import Path
import argparse,json,sys,time
import numpy as np
from PIL import Image
import torch
p=argparse.ArgumentParser();p.add_argument('--manifest',required=True);p.add_argument('--model-dir',default=str(Path(__file__).resolve().parent/'rife425'));p.add_argument('--threads',type=int,default=8);p.add_argument('--scale',type=float,default=1);args=p.parse_args()
manifest=Path(args.manifest).resolve();modeldir=Path(args.model_dir).resolve();sys.path.insert(0,str(modeldir))
from train_log.IFNet_HDv3 import IFNet
torch.set_num_threads(args.threads);model=IFNet().eval();state=torch.load(modeldir/'train_log/flownet.pkl',map_location='cpu',weights_only=True);state={k.removeprefix('module.'):v for k,v in state.items()};state={k:v for k,v in state.items() if not k.startswith(('teacher.','caltime.'))};model.load_state_dict(state)
cache={}
def read(path):
 path=Path(path);path=path if path.is_absolute() else manifest.parent/path
 if str(path) not in cache:
  arr=np.asarray(Image.open(path).convert('RGB'),np.float32)/255
  cache[str(path)]=torch.from_numpy(arr.copy()).permute(2,0,1).unsqueeze(0)
 return cache[str(path)]
for i,job in enumerate(json.loads(manifest.read_text(encoding='utf-8-sig'))):
 a,b=read(job['input0']),read(job['input1']);t=float(job['timestep']);dest=Path(job['output']);dest=dest if dest.is_absolute() else manifest.parent/dest;dest.parent.mkdir(parents=True,exist_ok=True)
 if not 0<=t<=1:raise ValueError('timestep must be in [0,1]')
 if a.shape!=b.shape:raise ValueError('input dimensions differ')
 # Model pyramids need dimensions divisible by 64 at default scale.
 h,w=a.shape[-2:];s=args.scale;align=max(64,round(64/s));ph=(align-h%align)%align;pw=(align-w%align)%align
 if ph or pw:
  a=torch.nn.functional.pad(a,(0,pw,0,ph));b=torch.nn.functional.pad(b,(0,pw,0,ph))
 with torch.inference_mode():
  if t==0:r=a
  elif t==1:r=b
  else:_,_,merged=model(torch.cat((a,b),1),t,[16/s,8/s,4/s,2/s,1/s]);r=merged[-1]
 arr=(r[0,:,:h,:w].clamp(0,1).permute(1,2,0).numpy()*255).round().astype('uint8');Image.fromarray(arr).save(dest)
 print(json.dumps({'index':i,'output':str(dest),'timestep':t}),flush=True)
