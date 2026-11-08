"""Round-3 raster repairs at 12 fps; previous source/media builders stay read-only.

Use --prepare-only, review real sources, then --no-encode. Export only the
reviewed PNG hashes with --encode-only. Periodic lunge timing is deliberately
6 seconds, with ascent/step-back copies of the corresponding descent/step-out.
"""
from pathlib import Path
import argparse
import bisect
import hashlib
import importlib.util
import json
import math
import shutil

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT/'docs/generated-frames-v3-repairs/config.json'
WORK = ROOT/'output/repair-animations'
MEDIA = ROOT/'dist/assets/animations-v3'
REPORT = ROOT/'docs/repair-animations-build.json'
IDS = ('incline-dumbbell-press', 'preacher-curl', 'reverse-pec-deck',
       'seated-plate-calf-raise', 'machine-ab-crunch', 'leg-extension',
       'hack-squat', 'lying-leg-curl', 'dumbbell-stiff-leg-deadlift',
       'alternating-lunge')
SHARED = ROOT/'scripts/build-final-animations.py'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_spec_digest(spec):
    administrative = {'prepareReady', 'motionReady', 'exportReady', 'sourceReview', 'pendingReason', 'geometryReview', 'reviewStatus'}
    payload = {k:v for k,v in spec.items() if k not in administrative}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def configured_engine():
    helper = module('repair_final_helpers', SHARED)
    helper.CONFIG, helper.WORK, helper.MEDIA, helper.REPORT = CONFIG, WORK, MEDIA, REPORT
    helper.IDS = IDS
    helper.frame_spec_digest = frame_spec_digest
    helper.__file__ = str(Path(__file__).resolve())
    engine = helper.configured_engine()
    shared_plan, shared_build, shared_prepare = engine.frame_plan, engine.build_frames, engine.prepare
    shared_translation = engine.translation_only

    def translation_only(reference,current,settings,anchor,identity=False):
        limit=float(settings.get('maxTranslationPixels',10))
        if limit<=10:
            return shared_translation(reference,current,settings,anchor,identity)
        if limit>35 or not settings.get('recenterReview'):
            raise ValueError('Extended translation requires explicit source-recentering review and a limit<=35pixels.')
        cv,np=engine.cv2,engine.np
        side=current.shape[0]
        regions=[engine.rect_pixels(r,side) for r in settings.get('regions',[])]
        ref=cv.cvtColor(reference,cv.COLOR_RGB2GRAY)
        gray=cv.cvtColor(current,cv.COLOR_RGB2GRAY)
        before=engine.region_error(ref,gray,regions)
        candidates=[];shift=np.zeros(2)
        if not identity and settings.get('enabled',True):
            radius=int(engine.math.ceil(limit))
            for x0,y0,x1,y1 in regions:
                patch=ref[y0:y1,x0:x1]
                sx,sy=max(0,x0-radius),max(0,y0-radius)
                ex,ey=min(side,x1+radius),min(side,y1+radius)
                scores=cv.matchTemplate(gray[sy:ey,sx:ex],patch,cv.TM_CCOEFF_NORMED)
                _,score,_,point=cv.minMaxLoc(scores)
                px,py=point;peak=np.array([float(px),float(py)])
                for axis,coord in enumerate([px,py]):
                    if 0<coord<scores.shape[1-axis]-1:
                        a,b,c=scores[py,px-1:px+2] if axis==0 else scores[py-1:py+2,px]
                        denominator=float(a-2*b+c)
                        if denominator < -1e-8:
                            peak[axis]+=float(np.clip(.5*(a-c)/denominator,-.5,.5))
                candidate=np.array([x0-sx,y0-sy])-peak
                usable=bool(score>=settings.get('minScore',.55) and np.max(np.abs(candidate))<=limit)
                candidates.append({'regionPixels':[x0,y0,x1,y1],'score':float(score),'translationPixels':candidate.tolist(),'usable':usable})
            usable=[c['translationPixels'] for c in candidates if c['usable']]
            if usable:shift=np.median(np.asarray(usable),axis=0)
        matrix=np.array([[1,0,shift[0]],[0,1,shift[1]]],dtype=np.float32)
        aligned=current.copy() if not np.any(shift) else cv.warpAffine(current,matrix,(side,side),flags=cv.INTER_LANCZOS4,borderMode=cv.BORDER_REPLICATE)
        after=engine.region_error(ref,cv.cvtColor(aligned,cv.COLOR_RGB2GRAY),regions)
        accepted=True
        if not identity and before is not None and after>before+.25:
            shift[:]=0;matrix[:,2]=0;aligned=current.copy();after=before;accepted=False
        return aligned,{'method':'source-recentering translation only; no human geometry warp','accepted':accepted,
                        'translationPixels':shift.tolist(),'matrix':matrix.tolist(),'maxTranslationPixels':limit,
                        'candidates':candidates,'staticRegionMAEBefore':before,'staticRegionMAEAfter':after,
                        'recenterReview':settings['recenterReview']}

    engine.translation_only=translation_only

    def prepare(exercise,spec,config):
        if spec.get('sourceKind')!='reviewed-png-loop':
            return shared_prepare(exercise,spec,config)
        entries=spec['sourceFrames']
        if len(entries)!=spec['frameCount'] or len(entries)!=36:
            raise ValueError('Reviewed native raster loop requires36explicit final input PNGs.')
        folder=WORK/exercise
        for directory in [folder/'anchors',folder/'anchors/raw',folder/'qa']:
            directory.mkdir(parents=True,exist_ok=True)
        records=[];images=[]
        for i,entry in enumerate(entries):
            source=ROOT/entry['file']
            if digest(source)!=entry['sha256']:
                raise ValueError('Reviewed native raster PNG changed.')
            opened=engine.Image.open(source)
            if opened.mode!='RGB' or opened.size!=(512,512):
                raise ValueError('Reviewed native raster inputs must already be RGB512, no conversion.')
            raw,path=folder/'anchors/raw'/f'anchor_{i:02d}.png',folder/'anchors'/f'anchor_{i:02d}.png'
            raw.write_bytes(source.read_bytes());path.write_bytes(source.read_bytes())
            images.append(engine.np.asarray(opened).copy())
            records.append({'index':i,'cell':None,'progress':i/36,'cropPixels':None,
                            'raw':engine.label(raw),'rawSha256':digest(raw),'file':engine.label(path),'sha256':digest(path),
                            'registration':{'method':'exact reviewed PNG copy; no interpolation or transform','translationPixels':[0,0]},
                            'reviewedInput':entry})
        engine.contact(images,[f'Reviewed input {i+1}' for i in range(36)],folder/'qa/anchors-contact.png',columns=6)
        record={'id':exercise,'status':'exact native raster loop inputs prepared; source and actual motion review required',
                'sourceKind':'reviewed-png-loop','sourceReview':spec['sourceReview'],'render':'generated-interpolated',
                'source':spec['sheet'],'sourceSha256':digest(ROOT/spec['sheet']),'sourceSize':[512,512],
                'width':512,'height':512,'fps':12,'cycle':spec['cycle'],'frameCount':36,
                'phaseEasing':'reviewed input timeline preserved','registration':{'enabled':False},
                'anchors':records,'qa':{'anchorsContact':engine.label(folder/'qa/anchors-contact.png')}}
        engine.write_json(folder/'prepare.json',record)
        return record

    def frame_plan(spec):
        if spec.get('sourceKind')=='reviewed-png-loop':
            return [{'frame':i+1,'phase':i/36,'progress':i/36,'anchor0':i,'anchor1':i,'timestep':0.,'reviewedInputCopy':True} for i in range(36)]
        if spec.get('stepPhaseTiming'):
            timing=spec['stepPhaseTiming']
            if (spec['frameCount'],spec['cycle'],timing['footTransferFrames'],timing['kneeDescentFrames'])!=(72,'periodic',8,10):
                raise ValueError('Reviewed two-phase lunge timing is8+10frames per descent,72periodicframes.')
            bounds=[item['progress'] for item in spec['anchors']]
            plans=[]
            for index in range(72):
                local=index%36
                if local>18:
                    plans.append({'frame':index+1,'phase':index/72,'mirroredFromFrame':37-index if index<36 else 109-index,'symmetricStepReturn':True})
                    continue
                if local<=8:
                    phase=(8/72)*(.5-.5*math.cos(math.pi*local/8));phase_name='foot transfer'
                else:
                    phase=8/72+(18/72-8/72)*(.5-.5*math.cos(math.pi*(local-8)/10));phase_name='knee descent'
                phase+=.5 if index>=36 else 0
                a=max(0,bisect.bisect_right(bounds,phase)-1);b=a+1
                t=(phase-bounds[a])/(bounds[b]-bounds[a])
                plans.append({'frame':index+1,'phase':index/72,'progress':phase,'anchor0':a,'anchor1':b,
                              'timestep':t,'controlledStepPhase':phase_name,'timeEasing':'half cosine'})
            return plans
        plans = shared_plan(spec)
        if spec.get('symmetricStepReturn'):
            if spec['cycle'] != 'periodic' or spec['frameCount'] != 72:
                raise ValueError('Symmetric alternating step return is exactly 72 periodic frames.')
            for index, plan in enumerate(plans):
                if 18 < index < 36:
                    plan.clear()
                    plan.update({'frame':index+1, 'mirroredFromFrame':37-index,
                                 'symmetricStepReturn':True, 'phase':index/72})
                elif 54 < index < 72:
                    plan.clear()
                    plan.update({'frame':index+1, 'mirroredFromFrame':109-index,
                                 'symmetricStepReturn':True, 'phase':index/72})
        return plans

    def build_frames(selected, specs, config, records, patch_overrides=False):
        result = shared_build(selected, specs, config, records, patch_overrides)
        for exercise in selected:
            spec, record = specs[exercise], records[exercise]
            mask_spec = spec.get('staticMask')
            preserved_loop = spec.get('preserveOutsideRectsFromFrameLoop')
            if not mask_spec and not preserved_loop:
                continue
            if mask_spec:
                if not mask_spec.get('review'):
                    raise ValueError('A static compositing mask requires an explicit per-pose occlusion review.')
                mask_path = ROOT/mask_spec['file']
                if digest(mask_path) != mask_spec['sha256']:
                    raise ValueError('Static mask changed after source review.')
                mask = engine.Image.open(mask_path).convert('L')
                if mask.size != (512,512):
                    raise ValueError('Static mask must use the exact 512-pixel source coordinate space.')
                ref_index = mask_spec.get('referenceIndex', spec.get('referenceIndex',0))
                ref = engine.Image.open(WORK/exercise/'anchors'/f'anchor_{ref_index:02d}.png').convert('RGB')
                if mask_spec.get('referenceImage'):
                    entry=mask_spec['referenceImage']
                    if digest(ROOT/entry['file'])!=entry['sha256']:
                        raise ValueError('External canonical static plate changed.')
                    ref=engine.Image.open(ROOT/entry['file']).convert('RGB')
                    if ref.size!=(512,512):
                        raise ValueError('Canonical static plate must be512RGB.')
                if mask_spec.get('frameMasks'):
                    if len(mask_spec['frameMasks'])!=len(record['frames']):
                        raise ValueError('Per-frame static masks must cover the exact output timeline.')
                    for entry in mask_spec['frameMasks']:
                        if digest(ROOT/entry['file'])!=entry['sha256']:
                            raise ValueError('Per-frame static mask changed.')
            if preserved_loop:
                entries = preserved_loop['sourceFrames']
                if not preserved_loop.get('review') or len(entries)!=len(record['frames']):
                    raise ValueError('Frame-preserving patch composition requires matching reviewed frame inputs.')
                for entry in entries:
                    if digest(ROOT/entry['file'])!=entry['sha256']:
                        raise ValueError('Preserved original per-frame body input changed.')
                rects = preserved_loop['mutableRectsPixels']
                if any(len(r)!=4 or not(0<=r[0]<r[2]<=512 and 0<=r[1]<r[3]<=512) for r in rects):
                    raise ValueError('Mutable patch rectangles must be inside the exact512 canvas.')
            for index,plan in enumerate(record['frames']):
                path = ROOT/plan['file']
                raw_before=WORK/exercise/'qa/pre-composite'/path.name
                raw_before.parent.mkdir(parents=True,exist_ok=True)
                raw_before.write_bytes(path.read_bytes())
                plan['preComposite']={'file':engine.label(raw_before),'sha256':digest(raw_before)}
                image = engine.Image.open(path).convert('RGB')
                if preserved_loop:
                    original = engine.Image.open(ROOT/entries[index]['file']).convert('RGB')
                    for rect in rects:
                        original.paste(image.crop(tuple(rect)),tuple(rect[:2]))
                    image = original
                    plan['outsidePatchSource'] = entries[index]
                if mask_spec:
                    selected_mask=mask
                    mask_entry={'file':mask_spec['file'],'sha256':mask_spec['sha256']}
                    if mask_spec.get('frameMasks'):
                        mask_entry=mask_spec['frameMasks'][index]
                        selected_mask=engine.Image.open(ROOT/mask_entry['file']).convert('L')
                        if selected_mask.size!=(512,512):
                            raise ValueError('Per-frame static mask must have exact512coordinates.')
                    image = engine.Image.composite(ref,image,selected_mask)
                    plan['staticMask'] = mask_entry
                image.save(path)
                plan['sha256'] = digest(path)
            if mask_spec:
                record['staticMask'] = mask_spec
            if preserved_loop:
                record['preserveOutsideRectsFromFrameLoop'] = preserved_loop
            # Regenerate diagnostic contacts from the exact composited PNGs.
            images = [engine.np.asarray(engine.Image.open(ROOT/p['file']).convert('RGB')) for p in record['frames']]
            sample = [round(i*(len(images)-1)/11) for i in range(12)]
            qa = WORK/exercise/'qa'
            engine.contact([images[i] for i in sample], [f'Frame {i+1:02d}' for i in sample], qa/'frames-contact.png', columns=4)
            last = len(images) if spec['cycle']=='periodic' else len(images)//2
            overlays = [engine.np.asarray(engine.Image.blend(engine.Image.fromarray(images[i]),engine.Image.fromarray(images[(i+1)%len(images)]),.5)) for i in range(last)]
            engine.contact(overlays,[f'{i+1:02d}/{(i+1)%len(images)+1:02d} overlay' for i in range(last)],qa/'transitions-onions.png',columns=6)
            differences=[float(engine.np.mean(engine.np.abs(images[(i+1)%len(images)].astype(float)-im))) for i,im in enumerate(images)]
            record['seamMAE'],record['adjacentFrameMAE']=differences[-1],differences
        return result

    engine.prepare, engine.frame_plan, engine.build_frames = prepare, frame_plan, build_frames
    return engine, helper


def release_metadata(report, engine):
    manifest_path = MEDIA/'manifest.json'
    if not manifest_path.exists():
        return
    manifest = engine.read_json(manifest_path)
    coverage = manifest['coverage']
    report['coverage'] = coverage
    if report['stage'] != 'encoded':
        report['publicationStage'] = 'source-or-motion-review'
        return
    report['publicationStage'] = 'complete' if coverage['complete'] else 'partial-export'
    manifest['publicationStage'] = report['publicationStage']
    if coverage['complete']:
        review_path = ROOT/'docs/generated-frames-v3-repairs/final-release-review.json'
        review = engine.read_json(review_path)
        reviewed = {a['id']:a for a in review['animations']}
        records = {a['id']:a for a in report['animations']}
        if set(reviewed) != set(IDS) or not review.get('complete'):
            raise ValueError('Complete repair release requires all ten matching visual review records.')
        for exercise in IDS:
            record, verdict = records[exercise], reviewed[exercise]
            frame_hash = hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in record['frames'])).hexdigest()
            if verdict['verdict']!='PASS' or verdict['frameDigestBin32']!=frame_hash or verdict['sourceSha256']!=record['sourceSha256']:
                raise ValueError('Final visual review index differs from the actual reviewed frames: '+exercise)
        reference = {'file':engine.label(review_path),'sha256':digest(review_path),'reviewedAnimationCount':len(reviewed),'scope':review['scope']}
        manifest['visualReview'] = report['visualReview'] = reference
    engine.write_json(manifest_path, manifest)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise',choices=['all',*IDS],default='all')
    parser.add_argument('--config',type=Path,default=CONFIG)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--prepare-only',action='store_true')
    modes.add_argument('--no-encode',action='store_true')
    modes.add_argument('--encode-only',action='store_true')
    args=parser.parse_args()
    engine,helper=configured_engine()
    config=engine.read_json(args.config)
    config_hash=digest(args.config)
    if (config['fps'],config['size']) != (12,512):
        raise ValueError('Repair media is defined at RGB512 and12fps.')
    specs=config['exercises']
    requested=list(IDS) if args.exercise=='all' else [args.exercise]
    selected=[i for i in requested if specs[i].get('prepareReady',False)]
    if not selected:
        raise ValueError('No source released for preparation.')
    for exercise in selected:
        if specs[exercise]['frameCount'] != (72 if exercise=='alternating-lunge' else 36):
            raise ValueError('Incorrect cycle duration: '+exercise)
    preserved=helper.reviewed_inputs(config,selected)
    preserved.update({p:digest(p) for folder in (ROOT/'dist/assets').glob('animations*') if folder.is_dir() and folder!=MEDIA for p in folder.rglob('*') if p.is_file()})
    preserved.update({ROOT/'scripts'/name:digest(ROOT/'scripts'/name) for name in ['build-leg-animations.py','build-bc-animations.py','build-final-animations.py','rife-batch.py','encode-3d.py']})
    preserved[args.config]=config_hash
    for exercise in selected:
        source=ROOT/specs[exercise]['sheet']
        preserved[source]=digest(source)
        for entry in specs[exercise].get('extraReviewedInputs',[]):
            preserved[ROOT/entry['file']]=entry['sha256']
        if specs[exercise].get('staticMask'):
            mask=specs[exercise]['staticMask']
            preserved[ROOT/mask['file']]=mask['sha256']
            for entry in mask.get('frameMasks',[])+([mask['referenceImage']] if mask.get('referenceImage') else []):
                preserved[ROOT/entry['file']]=entry['sha256']
        for entry in specs[exercise].get('preserveOutsideRectsFromFrameLoop',{}).get('sourceFrames',[]):
            preserved[ROOT/entry['file']]=entry['sha256']
    prior=engine.read_json(REPORT) if REPORT.exists() else{}
    records={r['id']:r for r in prior.get('animations',[])}
    batch=None
    if args.encode_only:
        for exercise in selected:
            if not specs[exercise].get('motionReady',False):
                raise ValueError('Source/motion release was withdrawn: '+exercise)
            if not specs[exercise].get('exportReady',False):
                raise ValueError('Actual final temporal/contact review has not released encoding: '+exercise)
            record=records.get(exercise,{})
            if record.get('frameSpecSha256') != helper.frame_spec_digest(specs[exercise]):
                raise ValueError('Frame-producing spec changed after review: '+exercise)
            if record.get('sourceSha256')!=digest(ROOT/specs[exercise]['sheet']) or len(record.get('frames',[]))!=specs[exercise]['frameCount']:
                raise ValueError('Incomplete or changed reviewed source/frame set: '+exercise)
            for frame in record['frames']:
                path=ROOT/frame['file']
                if digest(path)!=frame['sha256']:
                    raise ValueError('Reviewed PNG changed: '+str(path))
                preserved[path]=frame['sha256']
        print('Encoding exact reviewed PNGs; no inference or source preparation.',flush=True)
        engine.encode_media(selected,config,records)
    else:
        for exercise in selected:
            records[exercise]=engine.prepare(exercise,specs[exercise],config)
            records[exercise]['configSha256']=config_hash
            engine.write_json(WORK/exercise/'prepare.json',records[exercise])
            print(f'{exercise}: prepared {len(records[exercise]["anchors"])} keys',flush=True)
        if not args.prepare_only:
            batch=engine.build_frames(selected,specs,config,records)
            if not args.no_encode:
                raise ValueError('Review actual PNGs first, then explicitly export with --encode-only.')
    for path,sha in preserved.items():
        if not path.is_file() or digest(path)!=sha:
            raise RuntimeError('Preserved input/source/media changed: '+str(path))
    for record in records.values():
        if 'frames' in record:
            record['generatedFrameTimesteps']=engine.generated_frame_timesteps(record['frames'])
    stage='encoded' if args.encode_only else 'prepared' if args.prepare_only else 'frames'
    report={'pipeline':'generated-interpolated','stage':stage,'fps':12,'size':[512,512],
            'config':engine.label(args.config),'configSha256':config_hash,
            'generator':engine.label(Path(__file__)),'generatorSha256':digest(Path(__file__)),
            'interpolation':engine.model_provenance(config),'batch':batch,
            'method':{'normal':'19 forward frames and17 byte-exact return frames; 3s at12fps',
                      'lunge':'72 frames/6s; two controlled18-frame descents and byte-exact reversed step-back trajectories; no local .9 retiming override',
                      'qaLimit':'Review actual playback, feet/rollers/pads and rigid structure; pixel metrics do not validate mechanics.'},
            'preservationVerified':True,'preservedSourceAndMediaFiles':len(preserved),
            'animations':[records[i] for i in IDS if i in records]}
    release_metadata(report,engine)
    write(REPORT,report)
    print(f'{stage}: {len(selected)} selected; {REPORT}',flush=True)


if __name__=='__main__':
    main()
