#!/usr/bin/env python3
"""Render actual R1 B-rep for an explanatory note, without changing the design."""
from pathlib import Path
import sys,json
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'mechanical'))
import revision_b as rev
import build as base
OUT=Path(__file__).resolve().parent/'assets';OUT.mkdir(exist_ok=True)
parts,_=rev.revised('crossing')
selected=[p for p in parts if p[0].endswith(('-16','-16a','-16b'))]
base.render(selected,OUT/'single-channel.png',(1.2,-1.4,.9),(1800,1500))
pivot=[p for p in selected if not p[0].startswith(('A-','R-','RB-','RA-'))]
base.render(pivot,OUT/'pivot.png',(1.2,1.4,.7),(1800,1400))
shifts={'PS':-22,'PC':-14,'SP':-14,'PB':-7,'PM':8,'IC':15,'PE':20,'STL':10,'STR':10}
exploded=[]
for name,shape,col,mat,note in pivot:
    delta=shifts.get(name.split('-')[0],0)
    exploded.append((name,shape.translate((0,delta,0)),col,mat,note))
base.render(exploded,OUT/'pivot-exploded.png',(1.2,1.5,.8),(1900,1300))
for file in OUT.glob('*.png'):
    im=Image.open(file).convert('RGB')
    bg=Image.new('RGB',im.size,im.getpixel((0,0)));mask=ImageChops.difference(im,bg).convert('L').point(lambda x:255 if x>22 else 0)
    b=mask.getbbox()
    if b:im.crop((max(0,b[0]-35),max(0,b[1]-35),min(im.width,b[2]+35),min(im.height,b[3]+35))).save(file)
(OUT/'cad-origin.json').write_text(json.dumps({'engineering_commit':'a72e3a0d45d8b01d22f80cbc825711bc627f5c7f','generator':'mechanical/revision_b.py:revised(crossing)','channel_index':15,'cad_suffix':'16','solids':[p[0] for p in selected],'exploded_offsets_mm_y':shifts,'note':'Exploded offsets are for illustration only; installed dimensions are unchanged.'},indent=2))
print('Single-channel CAD views generated')
