"""Assemble only image_gen's edited equipment region over approved calf poses.

This never redraws/warps the human. Production also restores every pixel outside
the equipment ROI from the already approved 36-frame source loop after RIFE.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT/'docs/generated-frames-v3-repairs/seated-plate-calf-raise'
SHEET = FOLDER/'sheet-v1.png'
PREVIOUS = ROOT/'docs/generated-frames-v2-fixes/seated-plate-calf-raise'
OLD_INPUTS = [PREVIOUS/'reference-first-pose.png', PREVIOUS/'endpoint-v5.png']
ROI = [333, 190, 499, 375]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def beam_y(array):
    crop = array[225:350, 328:339].astype(float)
    gray = crop.mean(axis=2)
    neutral = crop.max(axis=2)-crop.min(axis=2)<20
    ys, _ = np.where(neutral & (gray<180) & (gray>45))
    if len(ys)<30:
        raise ValueError('Cannot locate the exposed neutral-gray lever seam.')
    return float(np.median(ys))+225

def background_surface(array):
    """Match only the neutral studio light field, without any human retouching."""
    x0,y0,x1,y1 = ROI
    crop = array[y0:y1,x0:x1].astype(float)
    ys,xs = np.mgrid[-1:1:complex(y1-y0),-1:1:complex(x1-x0)]
    design = np.stack([np.ones_like(xs),xs,ys,xs*xs,xs*ys,ys*ys],axis=-1)
    keep = (crop.mean(axis=2)>210)&((crop.max(axis=2)-crop.min(axis=2))<20)
    for _ in range(3):
        fit = np.linalg.lstsq(design[keep],crop[keep],rcond=None)[0]
        surface = design@fit
        keep &= np.abs(surface-crop).mean(axis=2)<3
    return surface

with Image.open(SHEET) as image:
    sheet = image.convert('RGB')
records = []
contact = Image.new('RGB', (1024,512), 'white')
for index, source in enumerate(OLD_INPUTS):
    with Image.open(source) as image:
        original = image.convert('RGB')
    left = round(index*sheet.width/2)
    right = round((index+1)*sheet.width/2)
    edited = sheet.crop((left,0,right,sheet.height)).resize((512,512),Image.Resampling.LANCZOS)
    original_array, edited_array = np.asarray(original), np.asarray(edited)
    dy = round(beam_y(original_array)-beam_y(edited_array))
    if abs(dy)>12:
        raise ValueError(f'Generated machine patch drifted excessively: {dy}px')
    shifted = edited.transform((512,512),Image.Transform.AFFINE,(1,0,0,0,1,-dy),Image.Resampling.BICUBIC,fillcolor=(250,248,245))
    x0,y0,x1,y1 = ROI
    shifted_array = np.asarray(shifted).copy()
    delta = background_surface(original_array)-background_surface(shifted_array)
    shifted_array[y0:y1,x0:x1] = np.clip(shifted_array[y0:y1,x0:x1].astype(float)+delta,0,255).round().astype(np.uint8)
    shifted = Image.fromarray(shifted_array)
    alpha = Image.new('L',(512,512),0)
    mask = np.zeros((512,512),dtype=np.uint8)
    for y in range(y0,y1):
        for x in range(x0,x1):
            distance = min(x-x0,y-y0,x1-1-x,y1-1-y)
            mask[y,x] = round(255*min(1,(distance+1)/4))
    alpha = Image.fromarray(mask)
    result = original.copy()
    result.paste(shifted,(0,0),alpha)
    outside = mask==0
    if not np.array_equal(np.asarray(result)[outside],original_array[outside]):
        raise ValueError('Protected human/background pixels changed.')
    output = FOLDER/f'key-{index:02d}.png'
    result.save(output)
    edited.save(FOLDER/f'generated-normalized-{index:02d}.png')
    contact.paste(result,(index*512,0))
    records.append({'file':output.relative_to(ROOT).as_posix(),'sha256':sha(output),'progress':index,
                    'approvedHumanSource':source.relative_to(ROOT).as_posix(),'approvedHumanSourceSha256':sha(source),
                    'generatedEquipmentSheet':SHEET.relative_to(ROOT).as_posix(),'generatedEquipmentSheetSha256':sha(SHEET),
                    'mutableRectPixels':ROI,'equipmentPatchTranslationPixels':[0,dy],
                    'allPixelsOutsideEquipmentRegionPreserved':True,
                    'equipmentPatchStudioBackgroundMatch':'Robust degree-two RGB light-field correction from neutral pixels in the equipment-only rectangle; never touches human pixels.'})
contact.save(FOLDER/'source-contact.png')
(FOLDER/'source-index.json').write_text(json.dumps({'sourceKind':'image-keyframes','reviewedKeyCount':2,
    'inputs':records,'equipmentOnlyEdit':'One flat horizontal weight plate on a vertical peg; all human pixels copied exactly from approved source poses.',
    'finalFrameCompositionRequired':'Every output frame outside mutableRectPixels must be copied from the corresponding approved v2 PNG, with explicit SHA verification.'},indent=2)+'\n',encoding='utf-8')
old_loop=[]
for path in sorted((ROOT/'output/final-animations/seated-plate-calf-raise/frames').glob('frame_*.png')):
    old_loop.append({'file':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
if len(old_loop)!=36:
    raise ValueError('Approved v2 source loop is incomplete.')
(FOLDER/'preserve-approved-body.json').write_text(json.dumps({'sourceFrames':old_loop,
    'mutableRectsPixels':[ROI], 'review':'Restore all pixels outside the equipment-only rectangle from the corresponding already approved v2 loop. No human deformation or new foot trajectory.'},indent=2)+'\n')
print(json.dumps({'keys':len(records),'bodyPixelsPreserved':True,'translations':[r['equipmentPatchTranslationPixels'] for r in records]}))
