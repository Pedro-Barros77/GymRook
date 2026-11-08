"""Bind completed root/owner visual gates to exact source and PNG hashes.

Run only after all ten explicit exportReady gates have been authorized.
This records completed reviews; technical pixel checks cannot grant approval.
"""
from pathlib import Path
import hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('release_adapter',ROOT/'scripts/build-repair-animations.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads(adapter.CONFIG.read_text(encoding='utf-8-sig'))
build=json.loads(adapter.REPORT.read_text())
records={r['id']:r for r in build['animations']}
notes={
 'incline-dumbbell-press':('Head contour remains canonical; side camera keeps passing dumbbells outside supported face. Root reviewed19 head crops and18 onions.',['incline-dumbbell-press/canonical-head-temporal-review.json']),
 'preacher-curl':('Machine Scott uses generated muscular raster forearms rotating rigidly around fixed elbows; body/pad/head stay canonical. Root reviewed actual36PNG source and19 contacts.',['preacher-curl/rig/parameters.json']),
 'reverse-pec-deck':('Integrated machine V2 with raised elbows; both shoulders open together. Root/independent owner reviewed19 composites and18 onions, foreground opaque hands and continuous waist.',['reverse-pec-deck/qa-reviewed-mask-v2.json','reverse-pec-deck/independent-final-composition-review.json']),
 'seated-plate-calf-raise':('Horizontal plate hardware patch only; all approved human RGB outside the equipment rectangle preserved exactly over36frames.',['seated-plate-calf-raise/immutable-body-review.json']),
 'machine-ab-crunch':('Native rigid152px arm with tapered6px terminal fits behind the continuous pad, avoiding a wide metal lip on the thigh. Reviewed athlete upper-body RGB remains exact on opaque masks; seat/feet/back structure canonical. Root and machine owner reviewed19 native composites and18 transitions.',['machine-ab-crunch/rig-v3/junction-review.json','machine-ab-crunch/rig-v3/machines-owner-qa/review.json']),
 'leg-extension':('Foot follows a gradual neutral-ankle profile without abrupt front flip. Root/legs owner reviewed all19 foot crops and18 onions.',['leg-extension/temporal-review.json']),
 'hack-squat':('Heel and forefoot stay planted and aligned on platform throughout19poses; root and legs owner reviewed actualsole crops/onions.',['hack-squat/temporal-review.json']),
 'lying-leg-curl':('Native V2 keeps original raster calf girth, fixed knee/tibia and rigid lever; tangent pad stays outside both lower-leg opaque cores. Original RIFE candidate archived.',['lying-leg-curl/rig-v2/freeze-verification.json','lying-leg-curl/rig-v2/contact-clearance-independent.json']),
 'dumbbell-stiff-leg-deadlift':('New continuous hip-hinge source and gradual timeline; root/legs owner reviewed19 actualbody/hip crops and18 onions. This is visual continuity review, not a skeletal motion-capture measurement.',['dumbbell-stiff-leg-deadlift/temporal-review.json']),
 'alternating-lunge':('Same inherited source drawings, eased8frame foot transfer then10frame knee descent per leg; both17frame returns exact reverse copies. Root/independent legs owner reviewed both seams and36foot-transfer crops.',['alternating-lunge/independent-feet-review.json'])
}
animations=[]
for name in adapter.IDS:
    settings=c['exercises'][name];r=records[name]
    assert settings.get('exportReady') and settings.get('motionReady'),name+' lacks final root/owner export gate'
    assert r['frameSpecSha256']==adapter.frame_spec_digest(settings),name+' spec differs'
    assert r['sourceSha256']==sha(ROOT/settings['sheet']),name+' source differs'
    for frame in r['frames']:assert sha(ROOT/frame['file'])==frame['sha256']
    note,paths=notes[name]
    paths=[ROOT/'docs/generated-frames-v3-repairs'/p for p in paths]
    if name=='alternating-lunge':paths += [ROOT/'docs/generated-frames-v3-repairs/alternating-lunge/timing-v2/independent-timing-review.json',ROOT/'docs/generated-frames-v3-repairs/alternating-lunge/timing-v2/actual-foot-comparison.json',ROOT/'docs/generated-frames-v3-repairs/alternating-lunge/timing-v2/relocation-proof.json']
    missing=[str(p) for p in paths if not p.is_file()]
    assert not missing,missing
    animations.append({'id':name,'verdict':'PASS','sourceSha256':r['sourceSha256'],
       'frameDigestBin32':hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in r['frames'])).hexdigest(),
       'sourceReview':settings['sourceReview'],'notes':[note],
       'reviewEvidence':[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths]})
review={'complete':True,'scope':'Ten round3 repairs: root plus owner visual checks of actual forward frames/critical contacts and transitions; approved source timeline and static body preservation. No claim of certified biomechanics from pixel metrics.',
 'fps':12,'animations':animations}
path=ROOT/'docs/generated-frames-v3-repairs/final-release-review.json'
path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Frozen final visual-review index10/10; source and actual PNG hash bindings verified.')
