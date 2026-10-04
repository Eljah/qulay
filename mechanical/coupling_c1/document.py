"""C1 engineering note with dimensioned CAD-derived drawings and source-linked text."""
from pathlib import Path
import sys,re,math,json,hashlib
from xml.sax.saxutils import escape
import cadquery as cq
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,A3,landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Image,PageBreak,Table,TableStyle,KeepTogether
from reportlab.lib.styles import ParagraphStyle
import fitz
HERE=Path(__file__).resolve().parent;OUT=HERE/'generated'
sys.path.insert(0,str(HERE))
# File name 'build' is shared with historical mechanical code: load this module unambiguously.
import importlib.util
spec=importlib.util.spec_from_file_location('coupling_builder',HERE/'build.py');geom=importlib.util.module_from_spec(spec);spec.loader.exec_module(geom)
FONT='/usr/share/fonts/truetype/dejavu/'
pdfmetrics.registerFont(TTFont('D',FONT+'DejaVuSans.ttf'));pdfmetrics.registerFont(TTFont('DB',FONT+'DejaVuSans-Bold.ttf'))
pdfmetrics.registerFontFamily('D',normal='D',bold='DB',italic='D',boldItalic='DB')
NAVY=colors.HexColor('#18354a');TEAL=colors.HexColor('#216b76');GRAY=colors.HexColor('#53616b');LIGHT=colors.HexColor('#edf2f5')
styles={
 'body':ParagraphStyle('body',fontName='D',fontSize=10,leading=14,spaceAfter=8,textColor=NAVY),
 'heading':ParagraphStyle('heading',fontName='DB',fontSize=17,leading=22,spaceBefore=15,spaceAfter=10,textColor=TEAL,keepWithNext=True),
 'small':ParagraphStyle('small',fontName='D',fontSize=8,leading=11,spaceAfter=6,textColor=GRAY),
 'title':ParagraphStyle('title',fontName='DB',fontSize=29,leading=35,spaceAfter=20,textColor=NAVY)}

def page_foot(c,d):
 c.saveState();w,h=d.pagesize;c.setStrokeColor(TEAL);c.setLineWidth(.8);c.line(40,33,w-40,33)
 c.setFont('D',8);c.setFillColor(GRAY);c.drawString(40,21,'QULAY / C1 • Соединение рычага с валом • 04.10.2026');c.drawRightString(w-40,21,str(d.page));c.restoreState()

def para(s,style='body'):
 t=escape(s)
 t=re.sub(r'`([^`]+)`',r'<font color="#216b76">\1</font>',t)
 return Paragraph(t,styles[style])

def note_pdf():
 p=OUT/'C1-note.pdf';story=[]
 story += [para('QULAY / C1','heading'),para('Рычаг и вал:\nсоединение без проскальзывания'.replace('\n',' '),'title')]
 story.append(para('Цельный фланцевый вал · два установочных штифта · два потайных винта'))
 story.append(Image(str(OUT/'exploded.png'),width=510,height=379))
 story.append(para('Разнесённый вид из B-rep CAD. Синий — цельный вал с фланцем; жёлтый — рычаг; красный — штифты; тёмный — винты. Длинная часть рычага обрезана только на иллюстрации.','small'))
 story.append(para('Передача момента не зависит от трения торцов. Отсутствие измерительного люфта обеспечивается заданной посадкой и подтверждается отдельным контролем.','heading'))
 story.append(para('Опытный узел. Выполнены CAD и аналитический расчёт. Физические испытания и квалификация точности не проводились.','small'))
 story.append(PageBreak())
 text=(HERE/'README.md').read_text();chunks=re.split(r'\n\s*\n',text)
 for chunk in chunks:
  chunk=chunk.strip()
  if not chunk or chunk.startswith('# Qulay'):continue
  if chunk.startswith('## '):
   story.append(para(chunk[3:],'heading'))
  elif chunk.startswith('Источники:'):
   story.append(para('Первичные источники и границы заимствования','heading'))
   for line in ['[1] Геометрия R1: mechanical/build.py и mechanical/revision_b.py. Базовый коммит указан выше.',
    '[2] Bossard BN 857: hardened ground parallel pins, m6; закалённые шлифованные установочные штифты.',
    '[3] Bossard BN 616: hex socket countersunk screws; головка 90°, DIN 7991 и ISO 10642 не обозначены как полностью тождественные.',
    '[4] Würth: ограничения замены DIN 7991 на ISO 10642 из-за изменённых размеров головок.',
    'Принятые размеры C1, натяг, момент, допуски и программа проверки — проектные решения. Это не значения, якобы установленные указанными стандартами. Полные адреса источников находятся в README.md комплекта.']:
    story.append(para(line,'small'))
  elif chunk.startswith('1. '):
   for line in chunk.splitlines():story.append(para(line))
  else:story.append(para(chunk))
 story += [para('Как читать технические листы','heading'),para('Следующие три листа A3: C1-00 — сборка и осевая размерная цепь; C1-01 — цельный фланцевый вал; C1-02 — рычаг и карта обработки головки. Размеры заданы в миллиметрах. Чертежи служат вместе с требованиями к парной обработке отверстий; STEP не содержит производственного натяга и винтовой поверхности резьбы.')]
 SimpleDocTemplate(str(p),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=36,bottomMargin=47,title='Qulay C1: рычаг — вал',author='Qulay engineering project').build(story,onFirstPage=page_foot,onLaterPages=page_foot)
 return p

W,H=landscape(A3);MM=72/25.4

def text(c,x,y,s,size=11,bold=False):c.setFont('DB' if bold else 'D',size);c.setFillColor(NAVY);c.drawString(x,y,s)
def wrap(c,x,y,s,w=490,size=11):
 p=Paragraph(escape(s),ParagraphStyle('draw',fontName='D',fontSize=size,leading=size*1.35,textColor=NAVY));_,hh=p.wrap(w,1000);p.drawOn(c,x,y-hh);return y-hh-8

def arrow(c,x,y,dx,dy):
 n=math.hypot(dx,dy);ux,uy=dx/n,dy/n
 path=c.beginPath();path.moveTo(x,y);path.lineTo(x+5*ux+2*uy,y+5*uy-2*ux);path.lineTo(x+5*ux-2*uy,y+5*uy+2*ux);path.close();c.drawPath(path,fill=1,stroke=0)
def dimh(c,x1,x2,y,fromy,label):
 c.setStrokeColor(NAVY);c.setFillColor(NAVY);c.setLineWidth(.45)
 for x in [x1,x2]:c.line(x,fromy,x,y+4)
 c.line(x1,y,x2,y);arrow(c,x1,y,1,0);arrow(c,x2,y,-1,0)
 c.setFont('D',10);c.drawCentredString((x1+x2)/2,y+5,label)
def dimv(c,y1,y2,x,fromx,label):
 c.setStrokeColor(NAVY);c.setFillColor(NAVY);c.setLineWidth(.45)
 for y in [y1,y2]:c.line(fromx,y,x-4,y)
 c.line(x,y1,x,y2);arrow(c,x,y1,0,1);arrow(c,x,y2,0,-1)
 c.saveState();c.translate(x-6,(y1+y2)/2);c.rotate(90);c.setFont('D',10);c.drawCentredString(0,0,label);c.restoreState()

def title(c,num,name):
 c.setPageSize((W,H));c.setStrokeColor(NAVY);c.setLineWidth(.8);c.rect(24,24,W-48,H-48)
 text(c,42,H-53,'QULAY / '+num+'   '+name,21,True)
 text(c,42,H-76,'Единицы: мм. Проект опытного узла C1. Не является подтверждением ресурса или точности.',10)
 c.line(24,66,W-24,66);text(c,40,46,'C1 • Номинальная геометрия из CAD; посадки и допуски — по документу',10)
 text(c,W-236,46,'04.10.2026   |   Лист '+num[-2:],10)

def hole_map(c,x,y,s,flange=True):
 c.setLineWidth(1);c.setStrokeColor(NAVY);c.circle(x,y,12*s)
 c.setLineWidth(.4);c.setDash(4,3);c.line(x-15*s,y,x+15*s,y);c.line(x,y-15*s,x,y+15*s);c.circle(x,y,4.025*s);c.setDash()
 for i,(a,b) in enumerate(geom.PINS,1):
  c.setLineWidth(.9);c.circle(x+a*s,y+b*s,1.5*s);text(c,x+a*s+1.8*s,y+b*s,'P'+str(i),9)
 for i,(a,b) in enumerate(geom.SCREWS,1):
  c.circle(x+a*s,y+b*s,(1.5 if flange else 1.7)*s)
  if not flange:c.circle(x+a*s,y+b*s,3.1*s)
  text(c,x+a*s-1.8*s,y+b*s+3.6*s,'S'+str(i),9)
 text(c,x-60,y-17*s,'Карта координат (X, Z)',10)

def sheets_pdf():
 c=canvas.Canvas(str(OUT/'C1-drawings.pdf'),pagesize=(W,H))
 # Sheet 00: actual CAD plus explicit source-coordinate stack.
 title(c,'C1-00','Сборка и осевая размерная цепь')
 c.drawImage(str(OUT/'joint.png'),40,345,width=545,height=390,preserveAspectRatio=True,anchor='c')
 c.drawImage(str(OUT/'section.png'),615,440,width=510,height=240,preserveAspectRatio=True,anchor='c')
 wrap(c,625,413,'Осевой CAD-разрез по Z=0. Потайные головки расположены со стороны +Y. Магнит и электронная плата не показаны на разрезе изменяемой пары.',460)
 x0=90;y0=215;s=27
 # axis is Y along page; markers intentionally include retained references.
 items=[('Плата соседа',-15.1,-13.5,colors.HexColor('#598674')),('Фланец',-12.5,-9.5,colors.HexColor('#9aafbd')),('Рычаг',-9.5,-6.5,colors.HexColor('#d2b272')),('Втулка R1',-6.5,-2.5,colors.HexColor('#c9d3d9')),('Подшипник R1',-2.5,2.5,colors.HexColor('#b8c2ca')),('Торец вала',2.5,5,colors.HexColor('#9aafbd')),('Магнит R1',5,8,colors.HexColor('#c57b72'))]
 for name,a,b,col in items:
  xx=x0+(a+16)*s;c.setFillColor(col);c.setStrokeColor(NAVY);c.rect(xx,y0,(b-a)*s,65,fill=1)
  c.saveState();c.translate(xx+(b-a)*s/2,y0+5);c.rotate(90);text(c,0,0,name,8);c.restoreState()
  text(c,xx-9,y0-17,str(a).replace('.',','),9)
 text(c,x0+(8+16)*s-5,y0-17,'8',9)
 dimh(c,x0+(3.5)*s,x0+(6.5)*s,y0+88,y0+65,'3,00 ±0,02')
 dimh(c,x0+(6.5)*s,x0+(9.5)*s,y0+122,y0+65,'3,00 ±0,02')
 wrap(c,845,330,'Ось схемы — Y относительно центра подшипника. Шейка Ø8 проходит сквозь рычаг, втулку и подшипник. Изменяемые детали: фланцевый вал и головка рычага.',290)
 wrap(c,845,225,'Зазор фланец–плата соседнего канала: 1,00 номинально. Расчётный минимум 0,70 при выделенном бюджете отклонений 0,30. Проверять щупом и при полном ходе.',290)
 text(c,75,105,'Штифты: 2 × Ø3 × 5,80. Винты: 2 × M3; окончательная длина 5,70 включая головку.',12,True)
 c.showPage()
 # Shaft sheet.
 title(c,'C1-01','Цельный фланцевый вал')
 ox=410;oy=455;s=13
 coords=[(-12.5,-12),(-9.5,-12),(-9.5,-4),(5,-4),(5,4),(-9.5,4),(-9.5,12),(-12.5,12)]
 path=c.beginPath();path.moveTo(ox+coords[0][0]*s,oy+coords[0][1]*s)
 for a,b in coords[1:]:path.lineTo(ox+a*s,oy+b*s)
 path.close();c.setFillColor(LIGHT);c.setStrokeColor(NAVY);c.drawPath(path,fill=1)
 c.setDash(5,3);c.line(200,oy,525,oy);c.setDash()
 dimh(c,ox-12.5*s,ox-9.5*s,655,oy+12*s,'3,00 ±0,02')
 dimh(c,ox-9.5*s,ox+5*s,689,oy+4*s,'14,50 ±0,02')
 dimh(c,ox-12.5*s,ox+5*s,310,oy-12*s,'17,50 справ.')
 dimv(c,oy-12*s,oy+12*s,205,ox-12.5*s,'Ø24 ±0,05')
 dimv(c,oy-4*s,oy+4*s,515,ox+5*s,'Ø8: 7,994…8,000')
 text(c,240,268,'Продольный профиль Y–Z; галтель R0,20 у фланца.',10)
 hole_map(c,780,505,10,True)
 rows=[['Отверстие','X','Z','Обработка'],['P1','0','+8','Совместно под свой штифт'],['P2','+1','−8','Совместно под свой штифт'],['S1','−8','0','M3×0,5-6H сквозное'],['S2','+8','0','M3×0,5-6H сквозное']]
 t=Table(rows,colWidths=[88,43,43,210]);t.setStyle(TableStyle([('FONTNAME',(0,0),(-1,-1),'D'),('FONTSIZE',(0,0),(-1,-1),10),('BACKGROUND',(0,0),(-1,0),LIGHT),('GRID',(0,0),(-1,-1),.4,GRAY),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]));t.wrap(500,300);t.drawOn(c,660,145)
 yy=215
 for txt in ['Материал: C45 / сталь 45; сертификат Rp0,2 ≥300 МПа.', 'Вал и фланец — одна заготовка. Не приваривать шайбу.', 'Шейка: Ra ≤0,8 мкм. Торец фланца: плоскостность 0,02;', 'его биение относительно шейки ≤0,02. Задиры не допускаются.']:
  text(c,65,yy,txt,11);yy-=22
 c.showPage()
 # Actual face edges, dimensional notes.
 title(c,'C1-02','Рычаг и обработка головки')
 x0=105;y0=657;s=MM
 face=cq.Workplane(obj=geom.arm_xy()).faces('>Z').val()
 c.setStrokeColor(NAVY);c.setLineWidth(.8)
 for e in face.Edges():
  vv,_=e.sample(max(2,int(e.Length()*3)));p=c.beginPath();p.moveTo(x0+vv[0].x*s,y0+vv[0].y*s)
  for v in vv[1:]:p.lineTo(x0+v.x*s,y0+v.y*s)
  c.drawPath(p)
 dimh(c,x0,x0+240*s,y0+58,y0,'240,00 ±0,10')
 dimv(c,y0-10*s,y0+10*s,x0+265*s,x0+250*s,'20,00 ±0,10')
 text(c,65,587,'Общий вид 1:1: линии получены с плоской грани CAD. Головка R12; роликовое отверстие Ø8,10.',11)
 hole_map(c,260,350,10,False)
 yy=490
 for txt in [
  'Головка рычага: толщина 3,00 ±0,02; сталь Rp0,2 ≥300 МПа.',
  'Центральное отверстие Ø8,05 ±0,01. Со стороны фланца',
  'фаска 0,4×45° для галтели. Плоскостность торца ≤0,02.',
  'S1 / S2: Ø3,4 сквозные; зенковка Ø6,2 +0,05/0, угол 90°.',
  'Головка винта ≤Ø6,0; утапливание 0…0,10. Подрезанный',
  'винт длиной 5,70 ±0,05 включая головку; не выступать сзади.',
  'P1 / P2: координаты как на листе C1-01. Финиш отверстий',
  'только совместно в стянутой паре. Dотв = Dштифта − 0,002…0,004.',
  'Натяг измерять; обозначение H7/m6 не является заменой.',
  'Серийный номер пары нанести до запрессовки. Не смешивать пары.',
  'Рабочее цилиндрическое зацепление штифта ≥2,4 в каждой детали.',
  'DXF — геометрия готовой грани, не программа лазера: отверстия',
  'с натягом, фаски и зенковки требуют механической обработки.'
 ]:
  text(c,520,yy,txt,11);yy-=24
 c.setLineWidth(1);c.line(90,112,90+100*MM,112);c.line(90,108,90,116);c.line(90+100*MM,108,90+100*MM,116);text(c,90,91,'Контроль печати: 100 мм. Печатать A3, 100%, без вписывания.',10)
 c.showPage();c.save();return OUT/'C1-drawings.pdf'

if __name__=='__main__':
 note=note_pdf();draw=sheets_pdf();merged=fitz.open()
 for p in [note,draw]:
  with fitz.open(p) as d:merged.insert_pdf(d)
 dest=OUT/'Qulay_C1_Lever_Shaft_Coupling.pdf';merged.save(dest,garbage=4,deflate=True)
 info={'pages':len(merged),'a3_drawing_pages':3,'physical_tests':False,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'source_baseline':'3d26a5449f2bf5eea4555df82f0002fc7f63131f'}
 (OUT/'document-check.json').write_text(json.dumps(info,indent=2));print(info)
