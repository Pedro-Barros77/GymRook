"""Source-pixel plate/masks for the native far-lever midpoint; no generated anatomy."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import hashlib, json

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

v6_path = SOURCE / 'sheet-v6-annotated-repair-candidate.png'
v7_path = SOURCE / 'midpoint-v7-candidate.png'
closed = Image.open(v6_path).convert('RGB').crop((0, 0, 418, 418)).resize((512, 512), Image.Resampling.LANCZOS)
base = Image.open(v7_path).convert('RGB').resize((512, 512), Image.Resampling.LANCZOS)

# Copy the closed reference only over the unwanted opened far branch/limb.
# Neither original near arm nor the right-side cleared area is inside this mask.
removal_polygon = [(245,43),(255,45),(255,63),(224,85),(215,106),(212,130),
                   (212,149),(218,162),(218,184),(215,211),(209,227),
                   (191,228),(180,207),(178,179),(178,153),(181,127),
                   (176,110),(181,90),(197,72),(219,54),(236,45)]
removal = Image.new('L', (512,512), 0)
ImageDraw.Draw(removal).polygon(removal_polygon, fill=255)
# A one-pixel source-source transition, contained inside the declared polygon.
soft = removal.filter(ImageFilter.GaussianBlur(0.6))
soft = Image.fromarray(np.minimum(np.asarray(soft), np.asarray(removal)))
plate = Image.composite(closed, base, soft)
plate.save(HERE / 'clean-plate.png')
removal.save(HERE / 'removal-region-mask.png')
soft.save(HERE / 'source-blend-mask.png')

# Actual human silhouette, foreground only. Machine, grips, and backrest excluded.
# The lower edge lies inside the torso, below the new far gear's complete extent.
human_polygon = [(213,95),(217,85),(226,78),(237,73),(247,71),
                 (259,73),(267,76),(271,80),(270,87),(265,91),
                 (267,98),(269,101),(270,106),(267,111),(270,119),
                 (270,123),(266,126),(265,136),(260,140),(254,140),
                 (253,153),(264,155),(278,160),(289,169),(306,173),
                 (340,174),(357,171),(361,164),(366,163),(369,165),
                 (374,163),(380,164),(385,163),(389,166),(390,173),
                 (387,181),(389,187),(386,193),(378,197),(366,195),
                 (351,193),(330,200),(309,205),(292,207),(279,203),
                 (271,220),(201,220),(193,206),(189,192),(188,176),
                 (192,166),(199,159),(209,151),(220,140),(224,130),
                 (218,120),(214,111),(212,102)]
human = Image.new('L',(512,512),0)
ImageDraw.Draw(human).polygon(human_polygon, fill=255)
human.save(HERE / 'foreground-human-mask.png')
rgba = plate.convert('RGBA'); rgba.putalpha(human)
rgba.save(HERE / 'foreground-human.png')

# Far hand/wrist skin copied from closed cell 0. Excludes the near forearm below
# y175 and the black grip. Translation only by downstream renderer.
hand_polygon = [(309,172),(313,166),(318,162),(324,161),(330,162),
                (335,161),(340,163),(343,167),(342,171),(338,174),
                (332,174),(326,171),(322,171),(318,174),(312,175)]
hand_mask = Image.new('L',(512,512),0)
ImageDraw.Draw(hand_mask).polygon(hand_polygon, fill=255)
rgb = np.asarray(closed).astype(np.int16)
skin = (rgb[:,:,0] > 130) & (rgb[:,:,0]-rgb[:,:,1] > 15) & (rgb[:,:,0]-rgb[:,:,2] > 25)
hand_mask = Image.fromarray((np.asarray(hand_mask).astype(bool) & skin).astype('uint8')*255)
hand_bbox = hand_mask.getbbox()
hand = closed.convert('RGBA'); hand.putalpha(hand_mask)
hand.crop(hand_bbox).save(HERE / 'hand-far-source.png')
hand_mask.save(HERE / 'hand-far-source-mask-full.png')

# Side-by-side diagnostics, including the exact source blend mask overlay.
contact = Image.new('RGB',(1536,512),'white')
contact.paste(base,(0,0)); contact.paste(plate,(512,0)); contact.paste(rgba,(1024,0),human)
contact.save(HERE / 'qa' / 'clean-plate-comparison.png')
overlay = Image.blend(plate, Image.composite(Image.new('RGB',(512,512),(245,50,50)),plate,human),0.35)
overlay.save(HERE / 'qa' / 'foreground-human-overlay.png')
hand_crop = hand.crop(hand_bbox)
enlarged = hand_crop.resize((hand_crop.width*12, hand_crop.height*12),Image.Resampling.NEAREST)
checker = Image.new('RGBA',enlarged.size,'white'); checker.alpha_composite(enlarged)
checker.convert('RGB').save(HERE / 'qa' / 'hand-source-enlarged.png')

changed = np.any(np.asarray(plate) != np.asarray(base), axis=2)
outside = np.asarray(removal)==0
assert not np.any(changed & outside), 'Pixels changed outside the declared source-copy polygon'
meta = {
 'purpose':'Clean source-pixel human plate for native far metal midpoint; no generated/drawn anatomy',
 'sources': [{'path':str(v6_path.relative_to(SOURCE.parent.parent.parent)), 'sha256':sha(v6_path), 'crop':[0,0,418,418]},
             {'path':str(v7_path.relative_to(SOURCE.parent.parent.parent)), 'sha256':sha(v7_path)}],
 'normalization':{'size':[512,512],'resize':'Pillow LANCZOS, RGB','translation_xy':[0,0],
                  'registration':'fixed base NCC 0.9937604 at ROI [40,405,265,505]; integer shift [0,0]'},
 'plate':{'base':'normalized V7', 'replacement':'normalized V6 closed cell0', 'polygon_xy':removal_polygon,
          'boundary':'Gaussian sigma0.6, clamped inside binary replacement polygon',
          'changed_pixels':int(changed.sum()),'outside_polygon_identical_to_v7':True},
 'foreground':{'mask':'foreground-human-mask.png','reference_rgb':'clean-plate.png','format':'L, binary0/255',
               'polygon_xy':human_polygon,'scope':'head, hair, neck, upper torso and near arm/hand; no machine/backrest/metal',
               'lower_edge_y':220},
 'hand':{'rgba':'hand-far-source.png','source':'normalized V6 closed cell0','crop_xyxy':hand_bbox,
         'contact_center_full512':[329,169],'contact_center_in_crop':[329-hand_bbox[0],169-hand_bbox[1]],
         'polygon_full_xy':hand_polygon,'skin_threshold':'R>130,R-G>15,R-B>25 within polygon',
         'transform_allowed':'translation only; renderer occludes using foreground-human-mask.png'},
 'suggested_new_far_grip_center_full512':[252.3,167],
 'suggested_far_pivot_full512':[240.1,24.5],
 'fixed_cap':'Overlay original cap from qa/canonical-closed-512.png or qa/v7-base-512.png last; cap excluded from human mask',
 'layer_order':['clean-plate','native far lever and black grip','translated source hand','foreground-human','original fixed cap'],
 'outputs':{}
}
for name in ['clean-plate.png','removal-region-mask.png','source-blend-mask.png','foreground-human-mask.png',
             'foreground-human.png','hand-far-source.png','hand-far-source-mask-full.png']:
    p=HERE/name; meta['outputs'][name]={'sha256':sha(p),'bytes':p.stat().st_size,'size':Image.open(p).size}
(HERE/'composition.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'changed_pixels':int(changed.sum()),'hand_bbox':hand_bbox,'outputs':meta['outputs']},indent=2))
