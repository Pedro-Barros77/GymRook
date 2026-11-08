"""Comparison with the extracted original-volume calf/shoe, no local scaling.

The V1 renderer and frames remain untouched. Only one global uniform texture
scale maps the newly generated original-leg cutout onto the fixed knee rig.
"""
from pathlib import Path
import importlib.util,json,math,hashlib

ROOT=Path(__file__).resolve().parent.parent
PATH=ROOT/'scripts/render-lying-leg-curl-rig.py'
spec=importlib.util.spec_from_file_location('leg_rig_core',PATH)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
FOLDER=ROOT/'docs/generated-frames-v3-repairs/lying-leg-curl'
m.BASE=FOLDER/'rig/clean-base-v1-512.png'
m.SPRITE=FOLDER/'rig/original-leg-sprite-v2.png'
m.RIG=FOLDER/'rig-v2';m.OUT=m.RIG/'frames';m.FOLDER=m.RIG
m.SRC_KNEE=(535.,652.);m.SRC_ANKLE=(187.,658.)
m.SCALE=m.TIBIA/math.dist(m.SRC_KNEE,m.SRC_ANKLE)
m.SOURCE_ANGLE=math.degrees(math.atan2(m.SRC_ANKLE[1]-m.SRC_KNEE[1],m.SRC_ANKLE[0]-m.SRC_KNEE[0]))
m.SOURCE_CORRECTION=180.-m.SOURCE_ANGLE
m.FAR=(156.,273.)

if __name__=='__main__':
 m.main()
 path=m.RIG/'source-index-rig.json'
 data=json.loads(path.read_text());data['generator']=Path(__file__).relative_to(ROOT).as_posix();data['generatorSha256']=m.digest(Path(__file__));data['inputs'][PATH.relative_to(ROOT).as_posix()]=m.digest(PATH)
 data['sourceAssetNote']='Generated extraction/restoration of the original approved calf/shoe, fixed uniform scale only. No foot or calf local resizing.'
 path.write_text(json.dumps(data,indent=2)+'\n')
