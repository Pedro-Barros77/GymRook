"""Official Google FILM TFHub v1: batch dyadic midpoint interpolation.
Manifest JSON: [{input0,input1,timestep,output}]. Relative paths use manifest dir.
FILM's time input is ignored by its architecture; only midpoint recursion is used.
Model weights: https://tfhub.dev/google/film/1 (Apache-2.0).
"""
from pathlib import Path
import argparse,json,os,time
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL','2')
import numpy as np
from PIL import Image
import tensorflow as tf

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--manifest',required=True);parser.add_argument('--model-dir',default=str(Path(__file__).resolve().parent/'film-model'));parser.add_argument('--depth',type=int,default=6);parser.add_argument('--threads',type=int,default=8);parser.add_argument('--report');args=parser.parse_args()
 if not 1<=args.depth<=12:raise ValueError('depth must be within1..12')
 tf.config.threading.set_intra_op_parallelism_threads(args.threads);tf.config.threading.set_inter_op_parallelism_threads(2)
 manifest=Path(args.manifest).resolve();jobs=json.loads(manifest.read_text(encoding='utf-8-sig'));modeldir=Path(args.model_dir).resolve();model=tf.saved_model.load(str(modeldir));denom=2**args.depth
 def path(value):
  p=Path(value);return p.resolve() if p.is_absolute() else (manifest.parent/p).resolve()
 inputs={};trees={};results=[];inferences=0
 def read(p):
  key=str(p)
  if key not in inputs:inputs[key]=np.asarray(Image.open(p).convert('RGB'),np.float32)[None]/255
  return inputs[key]
 for index,job in enumerate(jobs):
  start=time.monotonic();p0,p1=path(job['input0']),path(job['input1']);dest=path(job['output']);t=float(job['timestep'])
  if not 0<=t<=1:raise ValueError('timestep must be within[0,1]')
  numerator=round(t*denom);key=(str(p0),str(p1));a,b=read(p0),read(p1)
  if a.shape!=b.shape:raise ValueError('input dimensions differ')
  h,w=a.shape[1:3];ph=(-h)%64;pw=(-w)%64
  if key not in trees:
   if ph or pw:a=np.pad(a,((0,0),(0,ph),(0,pw),(0,0)));b=np.pad(b,((0,0),(0,ph),(0,pw),(0,0)))
   trees[key]={0:a,denom:b}
  tree=trees[key];lo,hi=0,denom;used=0
  while numerator not in tree:
   mid=(lo+hi)//2
   if mid not in tree:
    res=model({'x0':tree[lo],'x1':tree[hi],'time':np.array([[.5]],np.float32)},training=False)
    tree[mid]=np.clip(res['image'].numpy(),0,1);inferences+=1;used+=1
   if numerator<mid:hi=mid
   elif numerator>mid:lo=mid
  arr=np.uint8(np.round(np.clip(tree[numerator][0,:h,:w],0,1)*255));dest.parent.mkdir(parents=True,exist_ok=True);Image.fromarray(arr).save(dest)
  actual=numerator/denom;record=dict(index=index,engine='google-film-tfhub-v1',input0=str(p0),input1=str(p1),output=str(dest),requestedTimestep=t,actualDyadicTimestep=actual,depth=args.depth,timestepError=actual-t,newMidpointInferences=used,elapsedSeconds=time.monotonic()-start);results.append(record);print(json.dumps(record),flush=True)
 report=dict(engine='google-film-tfhub-v1',modelDirectory=str(modeldir),modelSource='https://tfhub.dev/google/film/1',license='Apache-2.0',tensorflowVersion=tf.__version__,depth=args.depth,totalMidpointInferences=inferences,jobs=results)
 if args.report:
  reportpath=Path(args.report).resolve();reportpath.parent.mkdir(parents=True,exist_ok=True);reportpath.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
