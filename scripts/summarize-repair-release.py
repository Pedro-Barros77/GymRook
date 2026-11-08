"""Persist the completed technical verification alongside tracked source docs."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=ROOT/'output/repair-animations/technical-verification.json'
report=json.loads(source.read_text());assert report['passed'] and len(report['animations'])==10
for path,key in [('dist/assets/animations-v3/manifest.json','manifestSha256'),('docs/generated-frames-v3-repairs/config.json','configSha256'),('docs/repair-animations-build.json','buildReportSha256'),('scripts/verify-repair-animations.py','verifierSha256')]:assert sha(ROOT/path)==report[key]
target=ROOT/'docs/repair-animations-technical-verification.json';shutil.copy2(source,target);assert sha(source)==sha(target)
totals={'.mp4':0,'.gif':0,'.webp':0};files=[]
for animation in report['animations']:
    for name,entry in animation['files'].items():
        path=ROOT/'dist/assets/animations-v3'/name
        assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256']
        totals[path.suffix]+=entry['bytes'];files.append({'file':path.relative_to(ROOT).as_posix(),**entry})
summary={'passed':True,'animationCount':10,'mediaFileCount':len(files),'totalFrames':sum(a['frameCount'] for a in report['animations']),
         'fps':12,'durationSecondsTotal':sum(a['durationSeconds'] for a in report['animations']),
         'normalCycleFrames':36,'lungeCycleFrames':72,'sizesBytesByFormat':totals,'totalMediaBytes':sum(totals.values()),
         'originalFilesVerifiedUnchanged':report['preservation']['verifiedOriginalFiles'],
         'technicalVerification':{'file':target.relative_to(ROOT).as_posix(),'sha256':sha(target)},
         'frozenInputs':{p:sha(ROOT/p) for p in ['docs/generated-frames-v3-repairs/config.json','docs/generated-frames-v3-repairs/final-release-review.json','docs/repair-animations-build.json','dist/assets/animations-v3/manifest.json']},
         'files':files,'limits':report['limits']}
(ROOT/'docs/repair-animations-integrity.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['files','frozenInputs','limits']},indent=2))
