"""Study only: ease step-out/step-back separately from knee descent.

Never writes published media or the production adapter/config. Source drawings
are the approved step-out/descending poses; both returns copy forward PNGs.
"""
from pathlib import Path
import bisect
import copy
import hashlib
import importlib.util
import json
import math

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT/'output/repair-animations/candidates/lunge-retime-v2'
STUDY.mkdir(parents=True,exist_ok=True)
CONFIG = STUDY/'study-config.json'
MODULE = ROOT/'scripts/build-repair-animations.py'
spec = importlib.util.spec_from_file_location('lunge_easing_study_adapter', MODULE)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
config = json.loads((ROOT/'docs/generated-frames-v3-repairs/config.json').read_text(encoding='utf-8-sig'))
exercise = 'alternating-lunge'
motion = copy.deepcopy(config['exercises'][exercise])
motion['exportReady'] = False
motion.pop('loopCorrection',None)
ticks = [0,8,11,14,18,22,25,28,36,44,47,50,54,58,61,64]
for entry,tick in zip(motion['anchors'],ticks):
    entry['progress'] = tick/72
motion['stepPhaseTiming'] = {'footTransferFrames':8,'kneeDescentFrames':10,
    'easing':'half cosine separately in foot-transfer and knee-descent phases',
    'reason':'Decelerate the returning foot before the standing seam instead of retaining a fast linear last step.'}
config['exercises'] = {exercise:motion}
CONFIG.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
adapter.CONFIG,adapter.WORK,adapter.MEDIA,adapter.REPORT = CONFIG,STUDY,STUDY/'preview',STUDY/'study-build.json'
adapter.IDS = (exercise,)
engine,helpers = adapter.configured_engine()

def controlled_plan(settings):
    bounds = [item['progress'] for item in settings['anchors']]
    plans=[]
    for index in range(72):
        local = index%36
        if local>18:
            plans.append({'frame':index+1,'phase':index/72,'mirroredFromFrame':37-index if index<36 else 109-index,'symmetricStepReturn':True})
            continue
        if local<=8:
            phase = (8/72)*(.5-.5*math.cos(math.pi*local/8))
            phase_name='foot transfer'
        else:
            phase = 8/72+(18/72-8/72)*(.5-.5*math.cos(math.pi*(local-8)/10))
            phase_name='knee descent'
        phase += .5 if index>=36 else 0
        a = max(0,bisect.bisect_right(bounds,phase)-1)
        b = a+1
        t = (phase-bounds[a])/(bounds[b]-bounds[a])
        plans.append({'frame':index+1,'phase':index/72,'progress':phase,'anchor0':a,'anchor1':b,
            'timestep':t,'controlledStepPhase':phase_name,'timeEasing':'half cosine'})
    return plans

engine.frame_plan = controlled_plan
record = engine.prepare(exercise,motion,config)
records={exercise:record}
result=engine.build_frames([exercise],config['exercises'],config,records)
if result is not None:
    records=result
paths=sorted((STUDY/exercise/'frames').glob('frame_*.png'))
assert len(paths)==72
hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
for output,source in list(zip(range(19,36),range(17,0,-1)))+list(zip(range(55,72),range(53,36,-1))):
    assert hashes[output]==hashes[source]
report={'id':exercise,'fps':12,'frames':72,'durationSeconds':6,'studyOnly':True,
    'sourceDrawingsUnchanged':True,'plan':controlled_plan(motion),
    'frameFiles':[{'file':p.relative_to(ROOT).as_posix(),'sha256':h} for p,h in zip(paths,hashes)],
    'timeContract':motion['stepPhaseTiming']}
(STUDY/'study-result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Study complete:72 frames, source drawings unchanged, two8-frame eased foot transfers and two10-frame eased descents; returns byte-exact.')
