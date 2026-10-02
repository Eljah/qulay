#!/usr/bin/env python3
"""QL-01 revision B: correct pivot-stack collisions; preserve the original beside it.
Native B-rep CAD. Design values are not released manufacturing tolerances.
"""
from pathlib import Path
import json,csv,itertools
import cadquery as cq
import build as base
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'mechanical/generated-r1';OUT.mkdir(parents=True,exist_ok=True)

def revised(mode):
    old,cut=base.build(mode)
    parts=[a for a in old if not a[0].startswith(('PB-','PS-','PM-','PE-','SP-','BR-'))]
    z=base.G['pivot_nominal_z']
    for j in range(31):
        y=(j-15)*25;tag=f'{j+1:02d}'
        def add(id,shape,color,material,note=''):
            parts.append((id+'-'+tag,shape,color,material,note))
        # Aluminium bracket touches the beam interface. Its bolted attachment is not detailed.
        bracket=cq.Workplane('XZ').polyline([(-12,-12),(12,-12),(12,30),(-15,50),(-15,10),(-12,10)]).close().extrude(5).val().translate((0,2.5,0))
        bracket=bracket.cut(base.cyl(8.025,7,0,-3.5,0))
        for x in [-6.5,6.5]:bracket=bracket.cut(base.cyl(1.1,7,x,-3.5,9))
        add('BR',bracket.translate((0,y,z)),base.BEARING,'aluminium bracket','bearing bore 16.05; retention/fasteners require review')
        add('PB',base.ring(8,4,5).translate((0,y,z)),base.BEARING,'688 bearing','centre Y=0; +/-2.5 mm')
        add('PS',base.cyl(4,16.5,0,y-11.5,z),base.BEARING,'steel shaft','Y -11.5..+5; positive arm coupling remains to detail')
        add('PC',base.ring(6,4.05,4).translate((0,y-4.5,z)),base.BEARING,'spacer','Y -6.5..-2.5')
        add('PM',base.cyl(3,3,0,y+5,z),(.72,.16,.14),'magnet','Y +5..+8; end-face attachment; no overlap with shaft')
        board=base.box(18,1.6,24,0,10.7,0)
        for x in [-6.5,6.5]:board=board.cut(base.cyl(1.1,3,x,9,9))
        add('PE',board.translate((0,y,z)),base.PCB,'PCB FR4 envelope','Y9.9..11.5; holes match encoder PCB')
        add('IC',base.box(5,1.2,6.4,0,y+9.3,z),(.12,.12,.13),'AS5048A package envelope','magnet-face to package 0.7 mm; actual sensitive-layer gap needs calibration')
        for x,suffix in [(-6.5,'L'),(6.5,'R')]:
            post=base.cyl(2,7.4,x,y+2.5,z+9).cut(base.cyl(1.1,7.6,x,y+2.4,z+9))
            add('ST'+suffix,post,base.BEARING,'nonmagnetic standoff','PCB support, unthreaded CAD bore')
        add('SP',base.ring(7.5,6.5,3.6).translate((0,y-4.5,z)),base.ARM,'torsion spring envelope','not a released spring winding or fatigue design')
    return parts,cut

def collision_report(parts):
    selected=[a for a in parts if a[0]=='C01-pivot-beam' or a[0].endswith(('-15','-16','-17','-15a','-15b','-16a','-16b','-17a','-17b'))]
    overlaps=[];tested=0
    for a,b in itertools.combinations(selected,2):
        aa,bb=a[1].BoundingBox(),b[1].BoundingBox()
        if not all(min(getattr(aa,k+'max'),getattr(bb,k+'max'))-max(getattr(aa,k+'min'),getattr(bb,k+'min'))>1e-6 for k in 'xyz'):continue
        tested+=1;volume=a[1].intersect(b[1]).Volume()
        if volume>.01:overlaps.append({'a':a[0],'b':b[0],'volume_mm3':round(volume,6)})
    return {'scope':'three adjacent measurement channels + shared pivot beam in stated static pose; not entire trolley or continuous motion','broad_phase_candidates':tested,'overlap_threshold_mm3':.01,'overlaps':overlaps,'all_selected_shapes_valid':all(a[1].isValid() for a in selected),'minimum_nominal_PCB_to_next_shaft_axial_gap_mm':2.0,'manufacturing_release':False}

def make_drawing():
    import ezdxf
    d=ezdxf.new('R2010');d.units=4;m=d.modelspace()
    m.add_lwpolyline([(-12,-12),(12,-12),(12,30),(-15,50),(-15,10),(-12,10)],close=True)
    m.add_circle((0,0),8.025)
    for x in [-6.5,6.5]:m.add_circle((x,9),1.1)
    d.saveas(OUT/'pivot-bracket-5mm.dxf')

def pdf_album():
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A3,landscape
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle
    pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    W,H=landscape(A3);c=canvas.Canvas(str(OUT/'QL01-R1-review.pdf'),pagesize=(W,H))
    pages=[('crossing-iso.png','Обновлённая компоновка','Ревизия B / 31 канал с шагом 25 мм. Исходная ревизия сохранена в mechanical/generated.'),('pivot-detail.png','Два соседних шарнира — крупно','Перенесены подшипники и платы. Магнит установлен на торце, а не внутри объёма вала.'),('pivot-section.png','Шарнир: осевой разрез','Разрез CAD по Z оси. Зелёный — плата; чёрный — корпус датчика; красный — магнит; жёлтый — габарит пружины.'),('along-curb-iso.png','Режим вдоль бордюра','Два уровня 0/150 мм. Необходимо отдельно ограничивать ошибку от смещения контактов по X.'),('datum-rail-iso.png','Режим на независимых направляющих','Только компоновка: прямолинейность и прогиб направляющих под нагрузкой ещё не измерены.')]
    style=ParagraphStyle('p',fontName='DejaVu',fontSize=11,leading=15)
    for i,(image,title,caption) in enumerate(pages,1):
        c.setFont('DejaVu',23);c.drawString(32,H-40,'QULAY / '+title)
        p=Paragraph(caption,style);p.wrap(W-64,50);p.drawOn(c,32,H-72)
        c.drawImage(str(OUT/image),32,75,width=W-64,height=H-162,preserveAspectRatio=True,anchor='c')
        c.setFont('DejaVu',10);c.drawString(32,49,'QL-01.R1 · Компоновочный CAD. НЕ разрешение на изготовление и НЕ подтверждение точности.')
        c.drawString(32,32,'Номинальные размеры, мм. Пружины, замки высоты, уплотнения и соединение рычага с валом требуют деталировки.')
        c.drawRightString(W-32,49,f'{i}/{len(pages)}');c.showPage()
    c.save()

if __name__=='__main__':
    summaries={}
    # Preserve quantified evidence of the old interference; do not rewrite history.
    original=collision_report(base.build('crossing')[0])
    original.pop('minimum_nominal_PCB_to_next_shaft_axial_gap_mm')
    (OUT/'original-interference.json').write_text(json.dumps(original,indent=2))
    for mode in ['crossing','along-curb','datum-rail']:
        parts,cut=revised(mode);a=cq.Assembly(name='Qulay_R1_'+mode)
        for name,s,color,material,note in parts:a.add(s,name=name,color=cq.Color(*color))
        a.save(str(OUT/f'qulay-r1-{mode}.step'))
        base.render(parts,OUT/f'{mode}-iso.png')
        with (OUT/f'parts-{mode}.csv').open('w',newline='') as f:
            w=csv.writer(f);w.writerow(['id','material','volume_mm3','note']);w.writerows((n,m,round(s.Volume(),3),note) for n,s,col,m,note in parts)
        summaries[mode]=collision_report(parts)
        if mode=='crossing':
            close=[a for a in parts if a[0].endswith(('-15','-16')) and not a[0].startswith(('A-','R-','RB-','RA-'))]
            base.render(close,OUT/'pivot-detail.png',(1.2,1.4,.8))
            plane=base.box(200,100,100,0,-12.5,170)
            section=[(n,s.intersect(plane),col,m,note) for n,s,col,m,note in close if not s.intersect(plane).isNull()]
            section=[a for a in section if a[1].Volume()>1e-6]
            base.render(section,OUT/'pivot-section.png',(0,0,1))
    (OUT/'collision-checks.json').write_text(json.dumps(summaries,indent=2))
    make_drawing();pdf_album()
    if any(v['overlaps'] or not v['all_selected_shapes_valid'] for v in summaries.values()):raise RuntimeError('Interference or invalid shape in checked channels; inspect collision-checks.json')
    print('Revision B: three adjacent channels in three poses have no >0.01 mm3 solid overlaps')
