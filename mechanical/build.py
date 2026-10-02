#!/usr/bin/env python3
"""Parametric B-rep CAD, not AI illustration. QL-01 layout, NOT production release.
Units mm. Spring, clamp and bought-component envelopes are expressly simplified.
"""
from pathlib import Path
import json, math, csv, os
import cadquery as cq
import vtk
import ezdxf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
ROOT=Path(__file__).resolve().parents[1]
G=json.loads((ROOT/'config/geometry.json').read_text())
OUT=ROOT/'mechanical/generated';OUT.mkdir(parents=True,exist_ok=True)
STEEL=(.28,.36,.44);ARM=(.82,.59,.18);RUBBER=(.15,.17,.19);BEARING=(.72,.75,.78);PCB=(.08,.48,.29)
def box(a,b,c,x=0,y=0,z=0):return cq.Workplane('XY').box(a,b,c).translate((x,y,z)).val()
def cyl(r,h,x,y,z,axis=(0,1,0)):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(*axis))
def tube(a,b,c,axis,w=2):
    inner=[a-2*w,b-2*w,c-2*w];inner[axis]=[a,b,c][axis]+2
    return box(a,b,c).cut(box(*inner))
def ring(ro,ri,width):return cyl(ro,width,0,-width/2,0).cut(cyl(ri,width+2,0,-width/2-1,0))
def arm_blank():
    return cq.Workplane('XY').center(120,0).slot2D(260,20,0).extrude(3).faces('>Z').workplane().pushPoints([(-120,0),(120,0)]).hole(8.1).val()
def solid_mesh(shape):
    vertices,triangles=shape.tessellate(.7)
    pts=vtk.vtkPoints();cells=vtk.vtkCellArray()
    for v in vertices:pts.InsertNextPoint(v.x,v.y,v.z)
    for t in triangles:cells.InsertNextCell(3);[cells.InsertCellPoint(int(i)) for i in t]
    poly=vtk.vtkPolyData();poly.SetPoints(pts);poly.SetPolys(cells)
    norm=vtk.vtkPolyDataNormals();norm.SetInputData(poly);norm.ComputePointNormalsOn();norm.Update();return norm.GetOutput()
def render(parts,path,direction=(1.1,-1.5,1.0),size=(1700,1250)):
    renderer=vtk.vtkRenderer();renderer.SetBackground(.965,.973,.98)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(*size);window.AddRenderer(renderer)
    for _,shape,color,_,_ in parts:
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(solid_mesh(shape));actor=vtk.vtkActor();actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color);actor.GetProperty().SetSpecular(.15);actor.GetProperty().SetSpecularPower(16);renderer.AddActor(actor)
    camera=renderer.GetActiveCamera();camera.SetPosition(*[x*2500 for x in direction]);camera.SetFocalPoint(0,0,200);camera.SetViewUp(0,0,1)
    if direction==(0,0,1):camera.SetViewUp(1,0,0)
    camera.ParallelProjectionOn();renderer.ResetCamera();camera.Zoom(1.04);window.Render()
    image=vtk.vtkWindowToImageFilter();image.SetInput(window);image.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(image.GetOutputPort());writer.Write();window.Finalize()
def build(mode):
    parts=[];cut=[];extra=150 if mode=='along-curb' else 200 if mode=='datum-rail' else 0
    frame_z=G['frame_z']+extra;pivot=G['pivot_nominal_z'];track=G['support_track']
    def add(name,s,color=STEEL,material='steel',note=''):parts.append((name,s,color,material,note));return s
    def member(name,a,b,c,axis,xyz,wall=2):
        shape=tube(a,b,c,axis,wall).translate(xyz);add(name,shape);cut.append((name,[a,b,c][axis],f'{[a,b,c][(axis+1)%3]}x{[a,b,c][(axis+2)%3]}x{wall}','square ends; weld fixture'))
    for y,tag in [(-387.5,'L'),(387.5,'R')]:member('F01-'+tag,840,25,25,0,(0,y,frame_z))
    for x,tag in [(-407.5,'rear'),(407.5,'front')]:member('F02-'+tag,25,750,25,1,(x,0,frame_z))
    member('F03-rear-cross',25,750,25,1,(-230,0,frame_z))
    for x,side in [(-350,'rear'),(350,'front')]:
        for y,tag in [(-track/2,'L'),(track/2,'R')]:
            base=150 if mode=='along-curb' and y>0 else 200 if mode=='datum-rail' else 0
            height=frame_z-(base+100)
            member(f'W-leg-{side}-{tag}',25,25,height,2,(x,math.copysign(387.5,y),base+100+height/2))
            add(f'W-axle-{side}-{tag}',cyl(6,62,x,(-435 if y<0 else 373),base+100),BEARING,'steel','axle envelope; retainers not detailed')
            add(f'W-wheel-{side}-{tag}',ring(100,6,35).translate((x,y,base+100)),RUBBER,'purchased wheel','rigid calibrated substitute needed on datum rails')
    for y,tag in [(-375,'L'),(375,'R')]:
        add('C-slide-'+tag,box(35,12,285,-35,y,frame_z-85),BEARING,'steel','cassette slide/clamp envelope, travel 220 mm')
    member('C01-pivot-beam',40,780,40,1,(-35,0,pivot+30))
    arm=arm_blank().rotate((0,0,0),(1,0,0),90)
    roller=cq.Solid.makeSphere(20,cq.Vector(0,0,0),angleDegrees1=-90,angleDegrees2=90).intersect(box(42,12,42)).cut(cyl(8,14,0,-7,0))
    bearing=ring(8,4,5)
    for j in range(31):
        y=(j-15)*25;h=150 if mode=='along-curb' and y>0 else 0
        alpha=math.asin((h+20-pivot)/240);deg=math.degrees(alpha);x=240*math.cos(alpha);z=pivot+240*math.sin(alpha)
        tag=f'{j+1:02d}';color=(.25+.6*j/30,.35,.85-.65*j/30)
        add('A-'+tag,arm.rotate((0,0,0),(0,1,0),-deg).translate((0,y-6.5,pivot)),color,'steel laser plate','240 mm centre distance; 3 mm; 8.1 mm holes')
        add('R-'+tag,roller.translate((x,y,z)),RUBBER,'POM/urethane crown','spherical crown R20, width12; material/hysteresis to validate')
        for offset,suffix in [(-3.5,'a'),(3.5,'b')]:add('RB-'+tag+suffix,bearing.translate((x,y+offset,z)),BEARING,'688 bearing')
        add('RA-'+tag,cyl(4,22,x,y-11,z),BEARING,'steel axle')
        add('PB-'+tag,ring(8,4,5).translate((0,y-12.5,pivot)),BEARING,'688 bearing','single-bearing envelope; stiffness and endplay need bench qualification')
        add('PS-'+tag,cyl(4,23,0,y-15,pivot),BEARING,'shaft')
        add('PM-'+tag,cyl(3,3,0,y+3.5,pivot),(.7,.12,.12),'diametrically magnetised magnet','magnet alignment and magnetic cross-talk require test')
        add('PE-'+tag,box(18,1.6,24,0,y+10,pivot),PCB,'sensor PCB envelope','mechanical envelope only; exact connector clearance not released')
        add('SP-'+tag,ring(7.5,6.5,3.6).translate((0,y-2,pivot)),ARM,'torsion spring envelope','wire/legs/preload/fatigue specification pending 3-channel rig')
        add('BR-'+tag,box(18,3,28,-11,y-12.5,pivot+13),STEEL,'bearing bracket envelope')
    add('E-enclosure',box(205,160,80,-240,0,frame_z+60),(.20,.34,.42),'purchased enclosure','Pi and acquisition carrier; sealed connectors not detailed')
    add('B-battery-envelope',box(210,120,65,-235,0,frame_z-60),(.28,.28,.30),'certified battery assembly','purchased battery+BMS; no cell-pack fabrication instructions')
    for y,tag in [(-210,'L'),(210,'R')]:member('H01-'+tag,25,25,680,2,(-407,y,frame_z+340))
    member('H02-grip',25,445,25,1,(-407,0,frame_z+680))
    if mode=='along-curb':
        add('REFERENCE-road',box(1200,1050,10,0,0,-10),(.79,.80,.80),'reference only')
        add('REFERENCE-curb',box(1200,510,150,0,267.5,75),(.66,.69,.70),'reference only','vertical face deliberately not traversed')
    if mode=='datum-rail':
        for y,tag in [(-track/2,'L'),(track/2,'R')]:
            member('D-rail-'+tag,3000,60,80,0,(0,y,160),4)
            for k,x in enumerate([-1500,-750,0,750,1500]):
                add(f'D-foot-{tag}-{k}',box(100,120,12,x,y,6),STEEL)
                add(f'D-screw-{tag}-{k}',cyl(10,114,x,y,12,(0,0,1)),BEARING,'adjustable screw envelope')
        add('REFERENCE-ramp',box(550,740,15,20,0,-12),(.83,.83,.79),'reference only','stand-in for surveyed surface, not an acceptance artifact')
    return parts,cut

def export(mode):
    parts,cut=build(mode);assembly=cq.Assembly(name='Qulay_QL01_'+mode)
    for name,s,col,mat,note in parts:assembly.add(s,name=name,color=cq.Color(*col))
    assembly.save(str(OUT/f'qulay-{mode}.step'))
    with (OUT/f'parts-{mode}.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['id','material','solid_volume_mm3','note']);w.writerows((n,m,round(s.Volume(),2),note) for n,s,c,m,note in parts)
    with (OUT/f'cut-list-{mode}.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['id','length_mm','section_mm','cut']);w.writerows(cut)
    checks={'mode':mode,'parts':len(parts),'all_shapes_valid':all(s.isValid() for _,s,_,_,_ in parts),'coordinate_units':'mm','release':'CONCEPT_LAYOUT_NOT_FOR_PRODUCTION','not_verified':['full assembly interference','spring fatigue','fits and retainers','sealing','loaded frame and rail deformation','metrological accuracy']}
    (OUT/f'validation-{mode}.json').write_text(json.dumps(checks,indent=2))
    if not checks['all_shapes_valid']:raise ValueError('invalid CAD solid')
    render(parts,OUT/f'{mode}-iso.png')
    if mode=='crossing':
        render(parts,OUT/'crossing-front.png',(0,-1,0));render(parts,OUT/'crossing-top.png',(0,0,1));render(parts,OUT/'crossing-side.png',(1,0,0))
    return parts,cut

def drawings():
    d=ezdxf.new('R2010');d.units=4;m=d.modelspace()
    m.add_line((0,-10),(240,-10));m.add_arc((240,0),10,270,90);m.add_line((240,10),(0,10));m.add_arc((0,0),10,90,270)
    m.add_circle((0,0),4.05);m.add_circle((240,0),4.05);d.saveas(OUT/'arm-240mm-3mm.dxf')
    cq.exporters.export(arm_blank(),str(OUT/'arm-240mm-3mm.step'))
    font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';pdfmetrics.registerFont(TTFont('DejaVu',font))
    pdf=canvas.Canvas(str(OUT/'QL01-CAD-album.pdf'),pagesize=landscape(A3));W,H=landscape(A3)
    pages=[('crossing-iso.png','Общий вид QL-01','31 канал; шаг 25 мм; база крайних осей 750 мм; рычаг 240 мм.'),('crossing-top.png','Вид сверху','Габарит рамы 840 × 800 мм. Колея опор 825 мм; наружный габарит колёс 860 мм.'),('crossing-front.png','Боковая проекция X–Z','Высота оси измерительного рычага 220 мм; опорные колёса Ø200; ролики Ø40.'),('crossing-side.png','Фронтальная проекция Y–Z','Полоса измерения не равна полной ширине съезда. Требуются привязанные перекрывающиеся проходы.'),('along-curb-iso.png','Проход вдоль бордюра','Слева/справа разные уровни 0/150 мм; рама поднята, кассета опущена на 150 мм.'),('datum-rail-iso.png','Независимая высотная база: направляющие','Направляющие 3000 × 60 × 80 × 4 мм, 5 опор на каждую. Поверенная геометрия ещё не подтверждена.')]
    for page,(image,title,caption) in enumerate(pages,1):
        pdf.setFont('DejaVu',20);pdf.drawString(35,H-42,'QULAY / '+title)
        pdf.setFont('DejaVu',10);pdf.drawString(35,H-65,caption)
        pdf.drawImage(str(OUT/image),35,70,width=W-70,height=H-155,preserveAspectRatio=True,anchor='c')
        pdf.setFont('DejaVu',10);pdf.drawString(35,48,'QL-01 • Компоновочный CAD. НЕ рабочая документация для изготовления. Размеры — мм.')
        pdf.drawString(35,30,'Изображения отрендерены из тех же B-rep тел, которые экспортированы в STEP. Упрощения указаны в реестре деталей.')
        pdf.drawRightString(W-35,30,f'{page}/{len(pages)+1}');pdf.showPage()
    pdf.setFont('DejaVu',20);pdf.drawString(35,H-42,'Измерительная кассета — исходные размеры и ограничения')
    lines=['Рычаг: расстояние осей 240 мм; ширина 20 мм; сталь 3 мм; отверстия Ø8.1 мм.', 'Ролик: сферическая корона R20, ширина 12 мм, отверстие Ø16 мм под два подшипника 688.', '31 независимый канал с шагом 25 мм; шарниры, магниты, платы и пружины показаны отдельными телами.', 'Приведён DXF 1:1 контура рычага и STEP заготовки; перед заказом согласовать посадки и технологию.', 'Пружина и крепёжные кронштейны показаны габаритно. Рабочие чертежи пружин, стопоров,', 'грязезащиты и замков высоты требуют проверки на трёхканальном стенде.', 'Не утверждается отсутствие взаимных пересечений всех сборочных деталей: выполнена проверка валидности', 'отдельных B-rep тел. Полная проверка зазоров, нагрузок и прогибов должна предшествовать производству.', 'Калибровка включает: угловую LUT каждого канала, положение магнита, длину рычага, радиус и биение', 'ролика, ориентацию инклинометра, масштаб одометра и высотную базу под нагрузкой.', 'Целевая погрешность не является достигнутой характеристикой. Реальные датчики ещё не испытаны.']
    pdf.setFont('DejaVu',13);y=H-90
    for line in lines:pdf.drawString(35,y,line);y-=29
    pdf.drawString(35,y-20,'Реестры резки и деталей выгружены в CSV отдельно для каждого положения сборки.');pdf.save()

if __name__=='__main__':
    for mode in ['crossing','along-curb','datum-rail']:export(mode)
    drawings();print('CAD, STEP, DXF, solid-validity reports, views and PDF generated:',OUT)
