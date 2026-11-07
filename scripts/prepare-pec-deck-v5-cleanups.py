"""Reuse one clean plate only where old equipment must be removed.

Neighboring v4 human/background pixels remain untouched. The shared clean
plate is matched to each frame's unobstructed background and visible skin,
avoiding a pasted rectangular head/background exposure boundary.
"""
from pathlib import Path
import hashlib
import json
import cv2
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT/'docs/generated-frames-v5/pec-deck'
BASE = ROOT/'backups/pec-deck-v4-before-structure-20261107/output/pec-deck-v4/frames'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def warm(rgb):
    a=rgb.astype(np.float32)
    return (a[:,:,0]-a[:,:,2]>32)&(a[:,:,0]-a[:,:,1]>8)&(a.mean(2)>85)


def main():
    plate_path=ASSETS/'upper-clean-canonical.png'
    plate=np.asarray(Image.open(plate_path).convert('RGB'))
    g=plate.astype(np.float32)
    h,w=g.shape[:2]
    out=ASSETS/'cleanup-frames'
    out.mkdir(exist_ok=True)
    yy,xx=np.mgrid[:h,:w].astype(np.float32)
    x,y=(xx-256)/256,(yy-90)/128
    basis=np.stack([np.ones_like(x),x,y,x*x,x*y,y*y],axis=2)
    clean_neutral=g.max(2)-g.min(2)<28
    clean_bright=(g.min(2)>200)&clean_neutral
    face_region=(xx>=230)&(xx<294)&(yy>=69)&(yy<148)
    upper=yy<155
    records=[]
    motion=json.loads((ROOT/'backups/pec-deck-v4-before-structure-20261107/docs/pec-deck-v4-build.json').read_text(encoding='utf-8'))['frames']
    matte_dir=ASSETS/'old-near-tower-masks'
    matte_manifest=json.loads((matte_dir/'manifest.json').read_text(encoding='utf-8'))
    sources=[np.asarray(Image.open(BASE/f'frame_{n:04d}.png').convert('RGB')).astype(np.float32) for n in range(1,38)]
    tower_masks=[]
    for n,record in enumerate(matte_manifest['frames'],start=1):
        mask_path=matte_dir/record['file']
        if record['frame']!=n or sha(mask_path)!=record['sha256']:
            raise ValueError('Old equipment matte index/hash mismatch.')
        mask=np.asarray(Image.open(mask_path).convert('L'))
        if mask.shape!=(512,512) or np.any(mask[:50]) or np.any(mask[164:]) or np.any(mask[:,:124]) or np.any(mask[:,180:]):
            raise ValueError('Old equipment matte crossed its reviewed tower scope.')
        tower_masks.append(mask)
    # Reviewed silhouettes are coverage mattes, not full removal masks. Their
    # antialiased fringe still contains old steel. Remove that contamination
    # within two pixels only in the independently inspected fixed brace area.
    effective_dir=ASSETS/'effective-tower-masks'
    effective_frames=effective_dir/'frames'
    effective_frames.mkdir(parents=True,exist_ok=True)
    brace_scope=(xx>=145)&(xx<180)&(yy>=45)&(yy<86)
    effective_records=[]
    for i,mask in enumerate(tower_masks):
        expanded=cv2.dilate((mask>0).astype(np.uint8),np.ones((5,5),np.uint8))>0
        effective=mask.copy()
        effective[brace_scope&expanded]=255
        path=effective_frames/f'frame_{i+1:04d}.png'
        Image.fromarray(effective).save(path)
        effective_records.append({'frame':i+1,'file':'frames/'+path.name,'sha256':sha(path),
                                  'originalMatteSha256':matte_manifest['frames'][i]['sha256'],
                                  'additionalFringePixels':int(np.count_nonzero((effective>0)&(mask==0)))})
        tower_masks[i]=effective
    effective_manifest_path=effective_dir/'manifest.json'
    effective_manifest_path.write_text(json.dumps({
        'sourceManifest':str((matte_dir/'manifest.json').relative_to(ROOT)),
        'sourceManifestSha256':sha(matte_dir/'manifest.json'),
        'rule':'Original reviewed matte, plus binary two-pixel Chebyshev dilation only inside [145,45,180,86]; removes confirmed old antialiased steel fringe.',
        'frameCount':37,'frameSize':[w,h],'frames':effective_records},indent=2)+'\n',encoding='utf-8')
    tower_masks=np.asarray(tower_masks)
    tower_slice=np.s_[:164,124:180]
    donor_bias_cache={}

    def donor_bias(i,j,column):
        key=(i,j,column)
        if key not in donor_bias_cache:
            a,c=sources[i][:164,column],sources[j][:164,column]
            visible=(tower_masks[i,:164,column]==0)&(tower_masks[j,:164,column]==0)
            visible[:50]=False
            visible&=(a.max(1)-a.min(1)<35)&(c.max(1)-c.min(1)<35)
            if np.count_nonzero(visible)>=8:
                bias=np.median((a-c)[visible],axis=0)
            else:
                a,c=sources[i][tower_slice],sources[j][tower_slice]
                visible=(tower_masks[i][tower_slice]==0)&(tower_masks[j][tower_slice]==0)
                bias=np.median((a-c)[visible],axis=0) if np.any(visible) else np.zeros(3)
            donor_bias_cache[key]=np.clip(bias,-32,32)
        return donor_bias_cache[key]

    def restore_tower(i,fill,alpha):
        old=tower_masks[i]
        remaining=old[tower_slice]>0
        donor_counts={}
        alpha[tower_slice]=old[tower_slice].astype(np.float32)/255
        # Prefer the preceding frame on equal temporal distance; use the next
        # when the same point was still hidden in the previous one.
        neighbors=[j for d in range(1,37) for j in [i-d,i+d] if 0<=j<37]
        for j in neighbors:
            available=remaining&(tower_masks[j][tower_slice]==0)
            if not np.any(available):
                continue
            rows,cols=np.nonzero(available)
            for local_x in np.unique(cols):
                selected=cols==local_x
                source_x=int(local_x)+124
                source_y=rows[selected]
                values=sources[j][source_y,source_x]+donor_bias(i,j,source_x)
                fill[source_y,source_x]=np.clip(values,0,255)
            donor_counts[str(j+1)]=int(np.count_nonzero(available))
            remaining[available]=False
            if not np.any(remaining):
                break
        if np.any(remaining):
            raise ValueError('No unobstructed neighboring v4 frame could fill an old tower occluder.')
        # The fixed diagonal brace/hood must not be assembled from different
        # donor pixels: small optical-flow residues look like a comb there.
        # Reuse its one clean canonical photograph, strictly inside the old
        # occluder matte; all visible original tower pixels remain untouched.
        brace=(old>0)&(xx>=145)&(xx<180)&(yy>=45)&(yy<86)
        fill[brace]=g[brace]
        # The old image already contains antialiased foreground pixels. Using
        # its coverage a second time would retain a moving fringe of steel.
        # Replace these contaminated edge pixels with the clean fixed brace.
        alpha[brace]=1
        return {'originalMaskSha256':matte_manifest['frames'][i]['sha256'],
                'effectiveMaskSha256':effective_records[i]['sha256'],
                'method':'Nearest unoccluded previous/next v4 pixel, RGB offset from mutually visible samples; fixed brace reuses canonical RGB with full old-fringe removal. No pixel outside effective matte changes.',
                'donorFramePixelCounts':donor_counts,'maximumRgbOffset':32,
                'fixedBraceCanonicalPixels':int(np.count_nonzero(brace)),
                'unoccludedTowerAlphaMaximum':int(np.max(alpha[tower_slice][old[tower_slice]==0])) if np.any(old[tower_slice]==0) else 0}
    for n in range(1,38):
        source=BASE/f'frame_{n:04d}.png'
        before=np.asarray(Image.open(source).convert('RGB'))
        b=before.astype(np.float32)
        spread=b.max(2)-b.min(2)
        mean=b.mean(2)
        shared_bg=clean_bright&(b.min(2)>200)&(spread<28)&upper
        a,target=basis[shared_bg],(b-g)[shared_bg]
        keep=np.ones(len(a),bool)
        for _ in range(4):
            coefficient=np.linalg.lstsq(a[keep],target[keep],rcond=None)[0]
            error=np.max(np.abs(a@coefficient-target),axis=1)
            keep=error<max(4.,float(np.percentile(error,90)))
        fill=g.copy()
        matched_background=np.clip(g+basis@coefficient,0,255)
        fill[clean_bright]=matched_background[clean_bright]
        tower=(xx>=105)&(xx<170)&(yy>=70)&(yy<164)
        shared_tower=tower&clean_bright&(b.min(2)>195)&(spread<28)
        if np.count_nonzero(shared_tower)>50:
            tower_bias=np.median((b-g)[shared_tower],axis=0)
            fill[tower&clean_bright]=np.clip(g[tower&clean_bright]+tower_bias,0,255)
        steel_samples=(xx>=82)&(xx<108)&(yy>=60)&(yy<164)&(g.mean(2)>55)&(g.mean(2)<200)&clean_neutral&(spread<28)
        steel_bias=np.median((b-g)[steel_samples],axis=0)
        tower_steel=(xx<180)&clean_neutral&(g.mean(2)>55)&(g.mean(2)<200)
        fill[tower_steel]=np.clip(g[tower_steel]+steel_bias,0,255)
        visible_skin=face_region&warm(plate)&warm(before)
        skin_offset=np.median((b-g)[visible_skin],axis=0) if np.count_nonzero(visible_skin)>=30 else np.zeros(3)
        skin_offset=np.clip(skin_offset,-35,35)
        fill[warm(plate)]=np.clip(g[warm(plate)]+skin_offset,0,255)
        # Old steel is neutral and substantially darker than the background.
        # Warm skin and dark hair do not seed removal. Within the head, only
        # neutral metal occluding skin/hair is a candidate (not eye whites).
        # The old profiles have AI-dependent shapes; a guessed centerline can
        # leave their far edge behind as a second outline. Select neutral
        # equipment in its actual upper image area, protecting the left tower
        # facade and retaining the head/skin exclusions below.
        seed=(spread<18)&(mean>20)&(mean<232)&upper&(xx>=124)&(xx<476)
        head_candidate=(spread<40)&(mean>50)&(mean<232)&(warm(plate)|(g.mean(2)<90))
        seed[face_region]=head_candidate[face_region]
        for hand in ['near','far']:
            center=float(motion[n-1]['expectedHands'][hand][0])
            collar=(np.abs(xx-center)<20)&(yy>=140)&(yy<164)
            seed|=collar&(spread<40)&(mean>15)&(mean<238)
        expanded=cv2.dilate(seed.astype(np.uint8),np.ones((5,5),np.uint8))
        expanded[164:]=0
        distance=cv2.distanceTransform(expanded,cv2.DIST_L2,3)
        alpha=np.clip(distance/1.5,0,1)
        alpha[:1]=0
        tower_restoration=restore_tower(n-1,fill,alpha)
        rgba=np.zeros((h,w,4),np.uint8)
        rgba[:,:,:3]=np.where((alpha>0)[:,:,None],np.clip(np.rint(fill),0,255).astype(np.uint8),0)
        rgba[:,:,3]=np.rint(alpha*255).astype(np.uint8)
        path=out/f'frame_{n:04d}.png'
        Image.fromarray(rgba).save(path)
        records.append({'frame':n,'file':path.name,'sha256':sha(path),'baseSha256':sha(source),
                        'maskPixels':int(np.count_nonzero(alpha)),'visibleSkinSampleCount':int(np.count_nonzero(visible_skin)),
                        'towerRestoration':tower_restoration,
                        'skinExposureOffsetRGB':skin_offset.tolist(),'backgroundBiasCoefficients':coefficient.tolist(),
                        'protectedRows164To511AlphaMaximum':int(rgba[164:,:,3].max())})
    # The support column is a separate fixed, opaque canonical layer.
    mask=Image.new('L',(w,h),0)
    ImageDraw.Draw(mask).polygon([(209,57),(234,57),(234,88),(210,91)],fill=255)
    mask.save(ASSETS/'column-mask.png')
    manifest={'engine':'selective-shared-generated-plate-composition','frameCount':37,'frameSize':[w,h],
              'sourcePlate':str(plate_path.relative_to(ROOT)),'sourcePlateSha256':sha(plate_path),
              'strategy':'One shared clean plate, selective old-neutral-metal removal, RGB exposure fits to existing v4 pixels; no per-frame image generation or human deformation.',
              'towerOldMatteManifest':str((matte_dir/'manifest.json').relative_to(ROOT)),
              'towerOldMatteManifestSha256':sha(matte_dir/'manifest.json'),
              'towerEffectiveMatteManifest':str(effective_manifest_path.relative_to(ROOT)),
              'towerEffectiveMatteManifestSha256':sha(effective_manifest_path),
              'alphaProtectedBelowY':164,'frames':records}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print('Prepared 37 selective cleanups; alpha is zero at/below y=164. Human/background outside each mask remain original v4 pixels.')


if __name__=='__main__':
    main()
