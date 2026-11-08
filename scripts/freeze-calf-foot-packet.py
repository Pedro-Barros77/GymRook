"""Freeze root-selected same-clock calf foot motion and body proofs in docs.

Only copies reviewed PNGs and their provenance; no inference, no media export,
no global config/report mutation. The final hardware composition is separate.
"""
from pathlib import Path
from PIL import Image
import hashlib,json
import numpy as np

ROOT=Path(__file__).resolve().parent.parent
STUDY=ROOT/'output/followup-round4/calf-two-key-inference-repair/round2-mid-key'
BODY=ROOT/'output/followup-round4/calf-two-key-study'
DEST=ROOT/'docs/generated-frames-v4-followup/standing-machine-calf-raise/foot-motion-v1'
DEST.mkdir(exist_ok=False)
for name in ['frames','body-2key','foot-estimates','ankle-guards','body-preservation-masks','keys','qa']:(DEST/name).mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def label(p):return p.resolve().relative_to(ROOT).as_posix()
def write(p,j):p.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def rgb(p):return np.asarray(Image.open(p).convert('RGB')).copy()
origins=[]
def copy(source,dest):
 dest.write_bytes(source.read_bytes());assert sha(source)==sha(dest)
 origins.append({'source':label(source),'copy':label(dest),'sha256':sha(dest)})
 return {'file':label(dest),'sha256':sha(dest)}

study_index=STUDY/'study-index.json';study=json.loads(study_index.read_text(encoding='utf-8'))
variant=next(v for v in study['variants'] if v['name']=='reverse-scale1')
body_record=json.loads((BODY/'study-result.json').read_text(encoding='utf-8'))['record']
assert len(variant['frames'])==19 and len(body_record['frames'])==36
roi=study['footROI'];assert roi==[289,370,410,447]
region=np.zeros((512,512),bool);region[370:447,289:410]=True
mid_source=ROOT/study['approvedMid']['file'];assert sha(mid_source)==study['approvedMid']['sha256']
key_records={}
for name,p in [('low',ROOT/body_record['anchors'][0]['file']),('mid',mid_source),('high',ROOT/body_record['anchors'][1]['file'])]:
 key_records[name]=copy(p,DEST/'keys'/f'{name}.png')
body_forward=[];estimate_forward=[];guard_forward=[];preservation_forward=[];checks=[]
for i,f in enumerate(variant['frames']):
 n=i+1;source=ROOT/f['file'];assert sha(source)==f['sha256']
 raw_source=ROOT/body_record['frames'][i]['file'];assert sha(raw_source)==body_record['frames'][i]['sha256']
 estimate=ROOT/f['footEstimate']['file'];assert sha(estimate)==f['footEstimate']['sha256']
 guard=ROOT/f['skinCoreMask']['file'];assert sha(guard)==f['skinCoreMask']['sha256']
 body_forward.append(copy(raw_source,DEST/'body-2key'/f'frame_{n:04d}.png'))
 estimate_forward.append(copy(estimate,DEST/'foot-estimates'/f'frame_{n:04d}.png'))
 guard_forward.append(copy(guard,DEST/'ankle-guards'/f'mask_{n:04d}.png'))
 body_mask=(~region)|(np.asarray(Image.open(guard).convert('L'))==255)
 mp=DEST/'body-preservation-masks'/f'mask_{n:04d}.png';Image.fromarray(body_mask.astype('uint8')*255).save(mp)
 preservation_forward.append({'file':label(mp),'sha256':sha(mp)})
 selected_arr=rgb(source);raw_arr=rgb(raw_source);est_arr=rgb(estimate)
 body_err=int(np.abs(selected_arr[body_mask].astype(int)-raw_arr[body_mask].astype(int)).max())
 foot_err=int(np.abs(selected_arr[~body_mask].astype(int)-est_arr[~body_mask].astype(int)).max())
 assert body_err==foot_err==0
 checks.append({'frame':n,'outsideROIPixelsExact':int((~region).sum()),'protectedBodyPixelsExact':int(body_mask.sum()),
   'protectedBodyMaxRGBError':body_err,'newFootEstimateMaxRGBError':foot_err,
   'physicalProgress':float(body_record['frames'][i]['progress'])})

frames=[];body_inputs=[];estimate_inputs=[];body_masks=[];guards=[]
for i in range(36):
 k=i if i<19 else 36-i;n=i+1
 source=ROOT/variant['frames'][k]['file']
 frames.append(copy(source,DEST/'frames'/f'frame_{n:04d}.png'))
 body_inputs.append(body_forward[k]);estimate_inputs.append(estimate_forward[k]);body_masks.append(preservation_forward[k]);guards.append(guard_forward[k])
for i in range(19,36):assert frames[i]['sha256']==frames[36-i]['sha256']
assert np.array_equal(rgb(ROOT/frames[9]['file']),rgb(mid_source))
qa_source=STUDY/'reverse-scale1'
for name in ['feet8-12-native.png','feet19-native.png','feet-onions-group-1.png','feet-onions-group-2.png','feet-onions-group-3.png']:
 copy(qa_source/name,DEST/'qa'/name)
params={'id':'standing-machine-calf-raise','fps':12,'frameCount':36,'durationSeconds':3,
 'selectedVariant':'reverse-scale1','interpolator':'Practical-RIFE4.25','scale':1,'reverseInputs':True,
 'timeline':'Original two-key cosine physical progress; third local foot key atphysical0.5. No local retiming.',
 'footROI':roi,'ankleSkinGuard':study['ankleSkinGuard'],'keys':key_records,
 'forwardTiming':variant['timing'],'sourceBodyClock':{'file':label(BODY/'study-result.json'),'sha256':sha(BODY/'study-result.json')},
 'scope':'Selected human input only; body outside foot ROI and protected ankle skin stays exact2-key raw. Canonical hardware/weight block is a separate next step.',
 'limits':'Raster foot disocclusion estimates, not a rigid3D shoe model. Slight continuous white-band width variation aroundframe12 accepted by root.'}
params_path=DEST/'parameters.json';write(params_path,params)
proof={'passed':True,'frameCount':36,'forwardFrameCount':19,'byteExactReturnCopies':17,
 'midRGBExactToRootApprovedKey':True,'outsideROIPixelsPerFrameExact':int((~region).sum()),'frames':checks,
 'rawBodySourceFrames':body_inputs,'bodyPreservationMaskFrames':body_masks,
 'footEstimateSourceFrames':estimate_inputs,'ankleMaskFrames':guards}
proof_path=DEST/'body-preservation-check.json';write(proof_path,proof)
origin_path=DEST/'relocation-proof.json';write(origin_path,{'method':'Byte-exact copies into tracked docs; no inference or PNG transform.','copies':origins})
inputs={label(params_path):sha(params_path),label(proof_path):sha(proof_path),label(origin_path):sha(origin_path)}
for r in body_forward+estimate_forward+guard_forward+preservation_forward+list(key_records.values()):inputs[r['file']]=r['sha256']
index={'id':'standing-machine-calf-raise','sourceKind':'reviewed-png-loop','fps':12,'frameCount':36,'cycle':'ping-pong',
 'status':'Root approved FOOT/HUMAN input; final canonical hardware composition and root final scene gate pending. No media export.',
 'generator':label(Path(__file__)),'generatorSha256':sha(Path(__file__)),'parameters':label(params_path),'inputs':inputs,
 'sourceFrames':frames,'preHardwareBodyPreservation':{'sourceFrames':body_inputs,'maskFrames':body_masks,'review':label(proof_path)},
 'frameDigestBin32':hashlib.sha256(b''.join(bytes.fromhex(x['sha256']) for x in frames)).hexdigest(),
 'review':{'reviewer':'root plus scott_round4 owner','observations':['One connected sole perfoot; previous loose white fragment absent.','Low to neutral to high foot position is legible, with unchanged original2-key body clock.','Slight continuous white-band width variation atframe12 is accepted; no claim of rigid3D shoes.'],
   'reviewed':'All19feet,18foot onions,full7to8 and12to13. Final hardware still requires root review.'}}
path=DEST/'source-index.json';write(path,index)
print(json.dumps({'packet':label(DEST),'indexSha256':sha(path),'frameDigestBin32':index['frameDigestBin32'],'frames':36,'outsideROIPixelsExact':int((~region).sum())}),flush=True)
