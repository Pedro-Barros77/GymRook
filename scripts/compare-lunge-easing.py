"""Compare actual timed raster foot trajectories; never infer them from a clock."""
from pathlib import Path
import hashlib
import json
import shutil
import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
STUDY = ROOT/'output/repair-animations/candidates/lunge-retime-v2'
OLD = STUDY/'reference-linear/frames'
OLD.mkdir(parents=True,exist_ok=True)
for source in sorted((ROOT/'output/repair-animations/alternating-lunge/frames').glob('frame_*.png')):
    destination = OLD/source.name
    if destination.exists() and destination.read_bytes()!=source.read_bytes():
        raise ValueError('The comparison baseline changed; create a new study directory.')
    shutil.copyfile(source,destination)
NEW = STUDY/'alternating-lunge/frames'

def audit(folder):
    paths=sorted(folder.glob('frame_*.png'))
    if len(paths)!=72:raise ValueError('Need a complete72-frame loop.')
    hashes=[hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    for end,start in list(zip(range(19,36),range(17,0,-1)))+list(zip(range(55,72),range(53,36,-1))):
        assert hashes[end]==hashes[start]
    tracks=np.zeros((72,2,2),float)
    errors=[]
    for base in [0,36]:
        current=np.array([[[206.,450.]],[[299.,450.]]],np.float32)
        tracks[base]=current[:,0,:]
        previous=cv2.imread(str(paths[base]),cv2.IMREAD_GRAYSCALE)
        for offset in range(1,19):
            following=cv2.imread(str(paths[base+offset]),cv2.IMREAD_GRAYSCALE)
            points,status,_=cv2.calcOpticalFlowPyrLK(previous,following,current,None,winSize=(25,25),maxLevel=3,criteria=(3,50,.001))
            back,back_status,_=cv2.calcOpticalFlowPyrLK(following,previous,points,None,winSize=(25,25),maxLevel=3,criteria=(3,50,.001))
            if not bool(status.all() and back_status.all()):raise ValueError('A surface point could not be tracked.')
            errors.extend(np.linalg.norm(back-current,axis=2).ravel().tolist())
            tracks[base+offset]=points[:,0,:]
            current,previous=points,following
        for offset in range(19,36):tracks[base+offset]=tracks[base+36-offset]
    speeds=np.linalg.norm(np.roll(tracks,-1,axis=0)-tracks,axis=2)*12
    return {'folder':folder.relative_to(ROOT).as_posix(),'sourceFiles':[{'file':p.relative_to(ROOT).as_posix(),'sha256':h} for p,h in zip(paths,hashes)],
        'manualInitialSurfacePoints':[[206,450],[299,450]],'tracksPixels':tracks.tolist(),'speedsPixelsPerSecond':speeds.tolist(),
        'trackingMaxForwardBackwardErrorPixels':max(errors),'standingSeam35to36Speed':speeds[35].tolist(),
        'standingSeam71to0Speed':speeds[71].tolist(),'lastThreeTransitionsMaximumSpeed':float(speeds[-3:].max())}

old,new=audit(OLD),audit(NEW)
report={'fps':12,'frameCount':72,'durationSeconds':6,'method':'Manual ankle/shoe-collar surface points tracked by LK on actual19forward RGB frames per leg; returns derived only after byte-equality verification.',
    'limits':'Projected surface points, not anatomical joints or a biomechanical assessment. No native-player playback is claimed.',
    'baseline':old,'candidate':new}
(STUDY/'actual-foot-comparison.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:{'maxFB':v['trackingMaxForwardBackwardErrorPixels'],'seamMid':v['standingSeam35to36Speed'],'seamLoop':v['standingSeam71to0Speed'],'lastThreeMax':v['lastThreeTransitionsMaximumSpeed']} for k,v in [('old',old),('new',new)]}))
