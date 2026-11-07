"""Assemble the generated clean plate with the unchanged canonical scene.

The image_gen edit supplies the removed-boom background and pivot housings.
Canonical face/post/frame pixels are reused directly; background-only color
matching prevents a rectangular exposure seam. No per-frame art is generated.
"""
from pathlib import Path
import hashlib
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'docs/generated-frames-v5/pec-deck'
CANONICAL = ROOT / 'backups/pec-deck-v4-before-structure-20261107/output/pec-deck-v4/frames/frame_0037.png'
GENERATED = OUT / 'upper-clean-plate.png'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = np.asarray(Image.open(CANONICAL).convert('RGB'))
    generated = np.asarray(Image.open(GENERATED).convert('RGB'))
    height, width = original.shape[:2]
    if original.shape != generated.shape or (width, height) != (512, 512):
        raise ValueError('Both plates must already be aligned at 512 square.')
    stroke = np.zeros((height, width), np.uint8)
    curves = [np.array([[240,40],[275,63],[327,91],[348,112],[356,136],[359,150]], np.int32),
              np.array([[340,48],[369,73],[385,100],[389,127],[389,150]], np.int32)]
    for curve in curves:
        cv2.polylines(stroke, [curve], False, 255, 32, cv2.LINE_AA)
    for center in [(359,151),(390,149)]:
        cv2.ellipse(stroke, center, (14,6), 0, 0, 360, 255, -1)
    o = original.astype(np.float32)
    g = generated.astype(np.float32)
    neutral = o.max(2) - o.min(2) < 30
    clear = (g.min(2) > 198) & (g.max(2) - g.min(2) < 32)
    changed = np.max(np.abs(o - g), axis=2) > 14
    search = np.zeros((height,width),bool)
    search[35:155,235:465] = True
    removed = (search & neutral & clear & changed & (o.mean(2) < 237)).astype(np.uint8)
    removed = cv2.dilate(removed, np.ones((5,5),np.uint8))
    removed[:35] = 0
    removed[155:] = 0
    # The closed reference reveals the complete face. Preserve its warm skin,
    # dark hair and eye pixels while clearing the old metal beside the head.
    head=np.zeros((height,width),bool)
    head[65:148,230:295]=True
    protected_head=head & (((o[:,:,0]-o[:,:,2])>32) | ((o.mean(2)<100)&(g.mean(2)<100)))
    removed[protected_head]=0
    removed[96:103,267:281]=0
    # Match the generated plain background to the canonical exposure, using
    # only bright, neutral, unobstructed pixels shared by both references.
    yy, xx = np.mgrid[:height,:width].astype(np.float32)
    x, y = (xx - 256)/256, (yy - 100)/128
    basis = np.stack([np.ones_like(x), x, y, x*x, x*y, y*y], axis=2)
    samples = ((o.min(2)>200) & neutral & clear & (stroke==0) & (yy>=35) & (yy<155) & (xx>=125) & (xx<465))
    a, b = basis[samples], (o-g)[samples]
    keep = np.ones(len(a), bool)
    for _ in range(4):
        coefficients = np.linalg.lstsq(a[keep],b[keep],rcond=None)[0]
        residual = np.max(np.abs(a @ coefficients-b),axis=1)
        keep = residual < max(4.,float(np.percentile(residual,90)))
    harmonized = np.clip(np.rint(g + basis @ coefficients),0,255).astype(np.uint8)
    result = original.copy()
    result[removed>0] = harmonized[removed>0]
    # No closed-pose grip placeholders may remain in this shared upper plate.
    # Reuse the adjacent generated plain-background strip (no human pixels)
    # above each former collar, rather than leaving floating dark cap dots.
    for left,right in [(341,378),(376,406)]:
        result[150:164,left:right]=harmonized[130:144,left:right]
        removed[150:164,left:right]=1
    # The static pivot drums from the generated edit contain no leftover lever
    # roots. These same drums are also a foreground matte over the rigid gear.
    cap_polygons = [[(211,31),(258,31),(258,51),(251,57),(221,58),(211,53)],
                    [(317,36),(355,36),(355,55),(348,62),(323,62),(317,57)]]
    cap_mask = Image.new('L',(width,height),0)
    draw = ImageDraw.Draw(cap_mask)
    for polygon in cap_polygons:
        draw.polygon(polygon,fill=255)
    caps = np.asarray(cap_mask).copy()
    caps[(g.min(2)>212) & (g.max(2)-g.min(2)<30)] = 0
    caps[:35] = 0
    caps[57:87,212:231] = 0
    result[caps>0] = generated[caps>0]
    output = OUT / 'upper-clean-canonical.png'
    Image.fromarray(result).save(output)
    cap_rgba = np.dstack((generated,caps))
    Image.fromarray(cap_rgba).save(OUT / 'fixed-pivot-caps.png')
    Image.fromarray(caps).save(OUT / 'fixed-pivot-caps-mask.png')
    Image.fromarray(removed*255).save(OUT / 'removed-booms-mask.png')
    before_after = Image.new('RGB',(1024,512),'white')
    before_after.paste(Image.fromarray(original),(0,0))
    before_after.paste(Image.fromarray(result),(512,0))
    before_after.save(OUT / 'clean-plate-comparison.png')
    post = np.s_[57:87,212:231]
    if np.max(np.abs(result[post].astype(int)-original[post].astype(int))):
        raise RuntimeError('Protected canonical support post changed during plate assembly.')
    report = {'canonical':str(CANONICAL.relative_to(ROOT)), 'canonicalSha256':sha(CANONICAL),
              'generatedEdit':str(GENERATED.relative_to(ROOT)), 'generatedSha256':sha(GENERATED),
              'output':str(output.relative_to(ROOT)), 'outputSha256':sha(output),
              'removedBoomPixels':int(np.count_nonzero(removed)), 'foregroundCapPixels':int(np.count_nonzero(caps)),
              'colorMatch':'Second-order RGB exposure bias fitted only to shared unobstructed neutral background.',
              'canonicalPostMaximumPixelError':0,
              'canonicalSceneRule':'All original pixels are preserved outside old boom removal and fixed pivot drum masks; no human is regenerated per frame.'}
    (OUT/'plate-assembly.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
