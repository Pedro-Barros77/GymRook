"""Verify the 10 round-3 repair media sets, their exact inputs and reviewed PNGs.

Default checks the complete production set, never a partial manifest. A focused
--exercise ID check is available during staged export. Decoding/integrity checks
do not approve exercise mechanics, anatomy, or equipment geometry.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MEDIA = ROOT/'dist/assets/animations-v3'
WORK = ROOT/'output/repair-animations'
CONFIG = ROOT/'docs/generated-frames-v3-repairs/config.json'
BUILD = ROOT/'docs/repair-animations-build.json'


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def exact_file(path, expected):
    require(path.is_file() and digest(path) == expected, f'Exact reviewed file hash changed: {path}')


def rgb(path):
    with Image.open(path) as image:
        require(image.size == (512,512), f'Expected 512-square PNG: {path}')
        return np.asarray(image.convert('RGB')).copy()


def normalized_source(path):
    with Image.open(path) as image:
        image = image.convert('RGB')
        if image.size != (512,512):
            image = image.resize((512,512), Image.Resampling.LANCZOS)
        return np.asarray(image).copy()


def verify_inputs(exercise, spec, record):
    for entry in spec.get('extraReviewedInputs',[]):
        exact_file(ROOT/entry['file'],entry['sha256'])
    source = ROOT/spec['sheet']
    exact_file(source, spec['sheetSha256'])
    require(record['sourceSha256'] == spec['sheetSha256'], f'{exercise}: recorded source differs from current reviewed source.')
    require(record['source'] == spec['sheet'], f'{exercise}: unexpected source path.')
    anchors = []
    for i, anchor in enumerate(record['anchors']):
        path, raw = ROOT/anchor['file'], ROOT/anchor['raw']
        require(path.resolve() == (WORK/exercise/'anchors'/f'anchor_{i:02d}.png').resolve(), f'{exercise}: wrong active anchor mapping.')
        exact_file(path, anchor['sha256'])
        exact_file(raw, anchor['rawSha256'])
        anchors.append(rgb(path))
    kind = spec.get('sourceKind', 'pose-sheet')
    if kind == 'reviewed-png-loop':
        require(len(spec['sourceFrames'])==len(anchors)==36,f'{exercise}: invalid reviewed native input loop length.')
        for anchor,item in zip(anchors,spec['sourceFrames']):
            exact_file(ROOT/item['file'],item['sha256'])
            require(np.array_equal(anchor,rgb(ROOT/item['file'])),f'{exercise}: reviewed native raster input was transformed or interpolated.')
    elif kind == 'isometric-hold':
        require(len(anchors) == 1 and np.array_equal(anchors[0], normalized_source(source)), f'{exercise}: isometric anchor is not the approved single source.')
    elif kind == 'decimated-png-loop':
        require(len(spec['sourceFrames']) == len(anchors) == 36, f'{exercise}: invalid decimation input count.')
        require([f['sourceFrame'] for f in spec['sourceFrames']] == list(range(1,72,2)), f'{exercise}: must sample source 1,3,...,71.')
        for anchor, item in zip(anchors, spec['sourceFrames']):
            path = ROOT/item['file']
            exact_file(path, item['sha256'])
            require(np.array_equal(anchor, normalized_source(path)), f'{exercise}: a sampled input changed during normalization.')
    elif kind == 'image-keyframes':
        require(len(anchors) == len(spec['anchors']) == spec['reviewedKeyCount'], f'{exercise}: invalid reviewed individual-key count.')
        for selected,anchor in zip(spec['anchors'],record['anchors']):
            path=ROOT/selected['imageOverride']
            exact_file(path,selected['imageOverrideSha256'])
            require(anchor['progress']==selected['progress'] and anchor['imageOverride']['sha256']==selected['imageOverrideSha256'],
                    f'{exercise}: individual-key mapping/provenance changed.')
            require(np.array_equal(rgb(ROOT/anchor['raw']),normalized_source(path)), f'{exercise}: individual raw key was altered.')
    else:
        require(len(anchors) == len(spec['anchors']), f'{exercise}: active source count differs from reviewed selection.')
        with Image.open(source) as opened:
            sheet = opened.convert('RGB')
            cols, rows = spec['grid']
            trim = spec['cellTrimPixels']
            for i, (selected, anchor) in enumerate(zip(spec['anchors'], record['anchors'])):
                require(anchor['cell'] == selected['cell'] and anchor['progress'] == selected['progress'], f'{exercise}: source cell/progress mapping changed.')
                if 'imageOverride' in selected:
                    path = ROOT/selected['imageOverride']
                    exact_file(path, selected['imageOverrideSha256'])
                    expected = normalized_source(path)
                else:
                    cx, cy = selected['cell'] % cols, selected['cell']//cols
                    box = [round(cx*sheet.width/cols)+trim, round(cy*sheet.height/rows)+trim,
                           round((cx+1)*sheet.width/cols)-trim, round((cy+1)*sheet.height/rows)-trim]
                    require(anchor['cropPixels'] == box, f'{exercise}: extraction crop changed.')
                    expected = np.asarray(sheet.crop(box).resize((512,512),Image.Resampling.LANCZOS))
                require(np.array_equal(rgb(ROOT/anchor['raw']),expected), f'{exercise}: raw active anchor does not match its exact reviewed raster input.')
        if exercise == 'alternating-lunge':
            require(len(anchors) == 16 and spec['anchors'][0]['cell'] == spec['anchors'][8]['cell'] == 0 and spec.get('symmetricStepReturn') and not spec.get('interpolationOverrides'),
                    'Lunge must use the same standing cell at keys0,8 and symmetric unretimed step returns.')
            require(record['anchors'][0]['sha256'] == record['anchors'][8]['sha256'],
                    'Lunge standing anchors must be byte-identical.')
    return anchors


def verify_frames(exercise, spec, record, anchors):
    count = spec['frameCount']
    paths = sorted((WORK/exercise/'frames').glob('frame_*.png'))
    require([p.name for p in paths] == [f'frame_{i:04d}.png' for i in range(1,count+1)], f'{exercise}: incomplete or extra source PNGs.')
    require(len(record['frames']) == count, f'{exercise}: incomplete recorded frame plan.')
    hashes, frames = [], []
    for path, entry in zip(paths, record['frames']):
        require(path.resolve() == (ROOT/entry['file']).resolve(), f'{exercise}: recorded PNG sequence is out of order.')
        exact_file(path,entry['sha256'])
        if entry.get('preComposite'):
            exact_file(ROOT/entry['preComposite']['file'],entry['preComposite']['sha256'])
        hashes.append(entry['sha256'])
        frames.append(rgb(path))
    patch_spec = spec.get('preserveOutsideRectsFromFrameLoop')
    actor_spec=spec.get('nativeBodyPixelPreservation')
    if actor_spec:
        require(len(actor_spec['sourceFrames'])==len(actor_spec['maskFrames'])==count and bool(actor_spec.get('review')),f'{exercise}: incomplete native athlete preservation contract.')
        for frame,source,matte in zip(frames,actor_spec['sourceFrames'],actor_spec['maskFrames']):
            exact_file(ROOT/source['file'],source['sha256'])
            exact_file(ROOT/matte['file'],matte['sha256'])
            mask=np.asarray(Image.open(ROOT/matte['file']).convert('L'))
            require(mask.shape==(512,512),f'{exercise}: wrong native actor-mask coordinate space.')
            require(np.array_equal(frame[mask==255],rgb(ROOT/source['file'])[mask==255]),f'{exercise}: reviewed athlete RGB was changed by the native equipment renderer.')
    if patch_spec:
        require(len(patch_spec['sourceFrames'])==count and bool(patch_spec.get('review')), f'{exercise}: missing reviewed immutable-body input sequence.')
        mutable=np.zeros((512,512),dtype=bool)
        for x0,y0,x1,y1 in patch_spec['mutableRectsPixels']:
            mutable[y0:y1,x0:x1]=True
        for frame,plan,source in zip(frames,record['frames'],patch_spec['sourceFrames']):
            exact_file(ROOT/source['file'],source['sha256'])
            require(plan.get('outsidePatchSource')==source, f'{exercise}: protected-body source mapping changed.')
            original=rgb(ROOT/source['file'])
            require(np.array_equal(frame[~mutable],original[~mutable]),f'{exercise}: a protected original pixel outside the equipment patch changed.')
    static_spec=spec.get('staticMask')
    if static_spec:
        exact_file(ROOT/static_spec['file'],static_spec['sha256'])
        mask=np.asarray(Image.open(ROOT/static_spec['file']).convert('L'))
        canonical=anchors[static_spec.get('referenceIndex',spec.get('referenceIndex',0))]
        if static_spec.get('referenceImage'):
            entry=static_spec['referenceImage']
            exact_file(ROOT/entry['file'],entry['sha256'])
            canonical=rgb(ROOT/entry['file'])
        require(mask.shape==(512,512) and bool(static_spec.get('review')),f'{exercise}: invalid unreviewed static mask.')
        if static_spec.get('frameMasks'):
            require(len(static_spec['frameMasks'])==len(frames),f'{exercise}: incomplete per-frame static masks.')
            for frame,entry,plan in zip(frames,static_spec['frameMasks'],record['frames']):
                exact_file(ROOT/entry['file'],entry['sha256'])
                dynamic=np.asarray(Image.open(ROOT/entry['file']).convert('L'))
                require(plan['staticMask']==entry and dynamic.shape==(512,512),f'{exercise}: changed per-frame static mask mapping.')
                require(np.array_equal(frame[dynamic==255],canonical[dynamic==255]),f'{exercise}: per-frame static pixels differ from canonical plate.')
        else:
            require(all(np.array_equal(frame[mask==255],canonical[mask==255]) for frame in frames),f'{exercise}: canonical static pixels jittered or changed.')
    kind = spec.get('sourceKind', 'pose-sheet')
    if kind == 'reviewed-png-loop':
        require(all(np.array_equal(f,a) for f,a in zip(frames,anchors)),f'{exercise}: native reviewed output differs from producer PNGs.')
        for i,item in enumerate(spec['sourceFrames']):
            require(hashes[i]==item['sha256'],f'{exercise}: producer native PNGs were rewritten instead of copied exactly.')
        for returned,forward in zip(range(19,36),range(17,0,-1)):
            require(hashes[returned]==hashes[forward],f'{exercise}: native return PNG differs from the reviewed forward image.')
    elif kind == 'isometric-hold':
        require(len(set(hashes)) == 1 and np.array_equal(frames[0],anchors[0]), f'{exercise}: fabricated movement or changed isometric PNG detected.')
    elif kind == 'decimated-png-loop':
        require(all(np.array_equal(f,a) for f,a in zip(frames,anchors)), f'{exercise}: output differs from sampled reviewed input.')
        for i, item in enumerate(spec['sourceFrames']):
            with Image.open(ROOT/item['file']) as original:
                if original.mode == 'RGB' and original.size == (512,512):
                    require(hashes[i] == item['sha256'], f'{exercise}: unnecessary PNG rewriting during exact decimation.')
        for returned, forward in zip(range(19,36),range(17,0,-1)):
            require(hashes[returned] == hashes[forward], f'{exercise}: sampled return PNG bytes differ from the forward frame.')
    elif spec['cycle'] == 'ping-pong':
        for returned, forward in zip(range(19,36),range(17,0,-1)):
            require(hashes[returned] == hashes[forward], f'{exercise}: return PNG bytes differ from the approved forward frame.')
    else:
        require(exercise == 'alternating-lunge' and count == 72, 'Only the declared full alternating-leg cycle uses this periodic motion contract.')
        require(hashes[0] == hashes[36], 'Lunge standing PNGs must be identical.')
        for i in list(range(19,36))+list(range(55,72)):
            source = 36-i if i<36 else 108-i
            require(hashes[i]==hashes[source], 'Lunge step-back must copy the opposite-time step-out frame exactly.')
        require(not spec.get('interpolationOverrides'), 'Artificial local retiming is not permitted for the repaired step.')
    steps = [float(np.abs(b.astype(float)-a.astype(float)).mean()) for a,b in zip(frames,frames[1:])]
    seam = float(np.abs(frames[-1].astype(float)-frames[0].astype(float)).mean())
    return frames, {'frameDigestBin32': hashlib.sha256(b''.join(bytes.fromhex(h) for h in hashes)).hexdigest(),
                    'frameDigestHexConcat': hashlib.sha256(''.join(hashes).encode()).hexdigest(),
                    'seamMAE': seam, 'largestAdjacentMAE': max(steps,default=0),
                    'interpretation': 'Pixel continuity diagnostics only; no anatomical or mechanical approval inferred.'}


def verify_gif_and_poster(exercise, spec, record, frames):
    count, duration = spec['frameCount'], round(spec['frameCount']*1000/12)
    with Image.open(MEDIA/record['gif']) as image:
        require(image.format == 'GIF' and image.size == (512,512) and image.info.get('loop') == 0, f'{exercise}: invalid looping GIF.')
        gif_count = image.n_frames
        if spec.get('sourceKind') == 'isometric-hold':
            require(gif_count == 1, f'{exercise}: isometric GIF must be a single stable pose.')
        elif exercise == 'alternating-lunge':
            require(1 <= gif_count <= count, f'{exercise}: invalid GIF count for periodic hold.')
        else:
            require(gif_count == count, f'{exercise}: unexpected merged GIF frames.')
        require(gif_count == record['gifFrames'], f'{exercise}: GIF count differs from manifest.')
        palette = image.copy().convert('P')
        decoded, delays = [], []
        for i in range(gif_count):
            image.seek(i)
            delays.append(image.info.get('duration',0))
            decoded.append(np.asarray(image.convert('RGB')).copy())
        require(all(isinstance(d,int) and d>0 for d in delays), f'{exercise}: GIF has nonpositive delays.')
        require(delays == record['gifFrameDelaysMilliseconds'] and sum(delays) == record['gifDurationMilliseconds'] == duration,
                f'{exercise}: GIF frame delays/total duration differ from declared exact time.')
        source_bounds = [round(i*100/12)*10 for i in range(count+1)]
        elapsed = 0
        for i,(image,delay) in enumerate(zip(decoded,delays)):
            end = elapsed+delay
            contributing = [j for j in range(count) if source_bounds[j]<end and source_bounds[j+1]>elapsed]
            require(contributing, f'{exercise}: GIF timing is outside source timeline.')
            for j in contributing:
                error = float(np.abs(image.astype(float)-frames[j].astype(float)).mean())
                require(error <= 25, f'{exercise}: GIF image {i+1} differs excessively from source {j+1} ({error:.3f}).')
            if len(contributing)>1:
                # A held/coalesced frame must really be identical after the
                # declared shared-palette quantization, not skipped movement.
                indexed = [np.asarray(Image.fromarray(frames[j]).quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB')) for j in contributing]
                require(all(np.array_equal(indexed[0],p) for p in indexed), f'{exercise}: GIF merged actual changing poses instead of an identical palette hold.')
            elapsed=end
    with Image.open(MEDIA/record['poster']) as poster:
        require(poster.format == 'WEBP' and poster.size == (512,512), f'{exercise}: invalid poster.')
        error = float(np.abs(np.asarray(poster.convert('RGB')).astype(float)-frames[0].astype(float)).mean())
        require(error <= 25, f'{exercise}: poster does not represent the first pose.')


def verify_preserved_originals():
    backup = ROOT/'backups/visual-v2-before-repairs-20261107/manifest.json'
    require(backup.is_file(), 'Required pre-correction backup manifest is missing.')
    snapshot = json.loads(backup.read_text(encoding='utf-8'))
    prefixes = ['dist/assets/', 'docs/generated-frames/', 'docs/generated-frames-v2/',
                'docs/generated-frames-v3/', 'docs/generated-frames-v4/', 'docs/generated-frames-v5/',
                'docs/generated-frames-d-v1/', 'docs/generated-frames-bc-v1/', 'docs/generated-frames-v2-fixes/',
                'output/leg-animations/', 'output/bc-animations/', 'output/final-animations/',
                'output/pec-deck-v5/frames/', 'output/generated-motion/reverse-cable-curl/frames/']
    names = {'scripts/build-leg-animations.py','scripts/build-bc-animations.py','scripts/build-final-animations.py','scripts/encode-3d.py','scripts/rife-batch.py'}
    selected = [r for r in snapshot['files'] if r['file'] in names or any(r['file'].startswith(p) for p in prefixes)]
    for item in selected:
        exact_file(ROOT/item['file'],item['sha256'])
    return {'manifest':str(backup.relative_to(ROOT)).replace('\\','/'), 'manifestSha256':digest(backup),
            'verifiedOriginalFiles':len(selected), 'passed':True}


def main():
    builder = module('final_animation_builder_verifier',ROOT/'scripts/build-repair-animations.py')
    shared = module('final_animation_codec_verifier',ROOT/'scripts/verify-leg-animations.py')
    shared.MEDIA, shared.SOURCES = MEDIA, WORK
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exercise', choices=['all',*builder.IDS],default='all')
    args=parser.parse_args()
    config=json.loads(CONFIG.read_text(encoding='utf-8'))
    build=json.loads(BUILD.read_text(encoding='utf-8'))
    manifest=json.loads((MEDIA/'manifest.json').read_text(encoding='utf-8'))
    require(manifest['preferredFormat']=='MP4' and manifest['fps']==12, 'Final manifest must declare MP4/12 fps.')
    by_id={r['id']:r for r in manifest['animations']}
    require(len(by_id)==len(manifest['animations']), 'Duplicate animation IDs in final manifest.')
    coverage=manifest['coverage']
    require(coverage['expectedAnimationCount']==len(builder.IDS) and coverage['encodedAnimationCount']==len(by_id), 'Incorrect coverage counts.')
    require(coverage['pendingIds']==[i for i in builder.IDS if i not in by_id] and coverage['complete']==(len(by_id)==len(builder.IDS)), 'Coverage pending/completion status is stale.')
    if args.exercise=='all':
        require(set(by_id)==set(builder.IDS) and coverage['complete'], 'Production verification requires all 10 round-3 repair animations, without a partial override.')
        require(manifest.get('publicationStage')==build.get('publicationStage')=='complete' and build.get('coverage')==coverage,
                'Final manifest/build publication stage must be complete and consistent.')
        reference=manifest.get('visualReview',{})
        require(reference==build.get('visualReview') and reference.get('reviewedAnimationCount')==10,
                'Final manifest/build must link the complete matching visual-review index.')
        exact_file(ROOT/reference['file'],reference['sha256'])
        review=json.loads((ROOT/reference['file']).read_text(encoding='utf-8'))
        require(review.get('complete') and {a['id'] for a in review['animations']}==set(builder.IDS),
                'Final review index must cover all10 exact guides.')
        reviewed={a['id']:a for a in review['animations']}
        for verdict in reviewed.values():
            for evidence in verdict.get('reviewEvidence',[]):
                exact_file(ROOT/evidence['file'],evidence['sha256'])
    selected=builder.IDS if args.exercise=='all' else [args.exercise]
    records={r['id']:r for r in build['animations']}
    results=[]
    for exercise in selected:
        require(exercise in by_id and exercise in records, f'{exercise}: missing encoded build.')
        spec,record,media=config['exercises'][exercise],records[exercise],by_id[exercise]
        if args.exercise=='all':
            verdict=reviewed[exercise]
            frame_digest=hashlib.sha256(b''.join(bytes.fromhex(f['sha256']) for f in record['frames'])).hexdigest()
            require(verdict['verdict']=='PASS' and verdict['sourceSha256']==record['sourceSha256'] and verdict['frameDigestBin32']==frame_digest,
                    f'{exercise}: final review no longer matches actual source and PNG timeline.')
        count=72 if exercise=='alternating-lunge' else 36
        require(spec['frameCount']==count and spec.get('motionReady') and spec.get('exportReady'), f'{exercise}: invalid count or source/motion/export review not released.')
        require((media['frameCount'],media['fps'],media['durationSeconds'],media['width'],media['height'])==(count,12,count/12,512,512), f'{exercise}: invalid video contract.')
        require(media['fpsNumerator']==12 and media['fpsDenominator']==1, f'{exercise}: invalid rational video frame rate.')
        expected_render='generated-static-hold' if spec.get('sourceKind')=='isometric-hold' else 'generated-interpolated'
        require(media['render']==expected_render, f'{exercise}: wrong render provenance.')
        require(record['frameSpecSha256']==builder.frame_spec_digest(spec), f'{exercise}: frame-producing specification changed after frame build.')
        shared.verify_files(media,exercise)
        anchors=verify_inputs(exercise,spec,record)
        frames,diagnostics=verify_frames(exercise,spec,record,anchors)
        shared.verify_video(exercise,media,frames,count)
        verify_gif_and_poster(exercise,spec,media,frames)
        results.append({'id':exercise,'fps':12,'frameCount':count,'durationSeconds':count/12,
                        'gifFrames':media['gifFrames'],'gifDurationMilliseconds':media['gifDurationMilliseconds'],
                        'sourceSha256':record['sourceSha256'],'files':media['files'],**diagnostics})
        print(f"{exercise}: PASS; GIF {media['gifFrames']} frames / {media['gifDurationMilliseconds']} ms; exact reviewed inputs and PNGs retained.")
    preservation=verify_preserved_originals()
    result={'passed':True,'scope':'all 10 production animations' if args.exercise=='all' else f'focused staged verification: {args.exercise}',
            'manifestSha256':digest(MEDIA/'manifest.json'),'configSha256':digest(CONFIG),'buildReportSha256':digest(BUILD),
            'verifierSha256':digest(Path(__file__)),'preservation':preservation,'animations':results,
            'limits':'Technical integrity, encoding and continuity only. Source anatomy, execution and equipment geometry have separate visual reviews.'}
    path=WORK/('technical-verification.json' if args.exercise=='all' else f'technical-verification-{args.exercise}.json')
    path.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'PASS: {len(results)} final-version media sets; {preservation["verifiedOriginalFiles"]} original files unchanged. Report {path}')


if __name__=='__main__':
    main()
