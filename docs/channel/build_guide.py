#!/usr/bin/env python3
"""Reproducible illustrated technical note. No hardware test is implied by this build."""
from pathlib import Path
import json,math,hashlib,html,io
import fitz
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph,Table,TableStyle,Flowable,Preformatted,Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DATA=json.loads((HERE/'guide.json').read_text())
if (HERE/'appendix.json').is_file():
 DATA['pages'].insert(-1,json.loads((HERE/'appendix.json').read_text()))
FONT=Path('/usr/share/fonts/truetype/dejavu')
for name,file in [('Body','DejaVuSans.ttf'),('Bold','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Body',boldItalic='Bold')
INK=colors.HexColor('#163242');TEAL=colors.HexColor('#17656A');GRAY=colors.HexColor('#53636F');PALE=colors.HexColor('#EFF5F5');LINE=colors.HexColor('#CBD8DD');ORANGE=colors.HexColor('#A96512')
STYLE={
 'p':ParagraphStyle('p',fontName='Body',fontSize=10.5,leading=14.4,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Body',fontSize=8.2,leading=10.7,textColor=GRAY,spaceAfter=6),
 'h':ParagraphStyle('h',fontName='Bold',fontSize=12,leading=16,textColor=TEAL,spaceBefore=6,spaceAfter=6),
 'lead':ParagraphStyle('lead',fontName='Body',fontSize=15,leading=21,textColor=GRAY,spaceAfter=15),
 'cell':ParagraphStyle('cell',fontName='Body',fontSize=9.2,leading=12.1,textColor=INK),
 'th':ParagraphStyle('th',fontName='Bold',fontSize=9.2,leading=12.1,textColor=colors.white),
 'title':ParagraphStyle('title',fontName='Bold',fontSize=20,leading=25,textColor=INK),
 'code':ParagraphStyle('code',fontName='Mono',fontSize=8.1,leading=11.5,textColor=INK),
 'formula':ParagraphStyle('formula',fontName='Body',fontSize=13,leading=20,textColor=INK)
}
def para(text,style='p'):return Paragraph(html.escape(text).replace('\n','<br/>'),STYLE[style])
def label(c,x,y,text,size=9,font='Body',color=INK):c.setFillColor(color);c.setFont(font,size);c.drawString(x,y,text)
def arrow(c,x1,y1,x2,y2,color=TEAL):
 c.setStrokeColor(color);c.setFillColor(color);c.setLineWidth(1.2);c.line(x1,y1,x2,y2)
 a=math.atan2(y2-y1,x2-x1);p=c.beginPath();p.moveTo(x2,y2);p.lineTo(x2-6*math.cos(a-.43),y2-6*math.sin(a-.43));p.lineTo(x2-6*math.cos(a+.43),y2-6*math.sin(a+.43));p.close();c.drawPath(p,fill=1,stroke=0)
def boxlabel(c,x,y,w,h,text,fill=PALE,size=10):
 c.setFillColor(fill);c.setStrokeColor(LINE);c.roundRect(x,y,w,h,5,fill=1,stroke=1)
 p=Paragraph(html.escape(text).replace('\n','<br/>'),ParagraphStyle('bl',parent=STYLE['p'],fontSize=size,leading=size+3,alignment=1,spaceAfter=0));_,ph=p.wrap(w-12,h-8);p.drawOn(c,x+6,y+(h-ph)/2)
class Picture(Flowable):
 def __init__(self,path,w,h,cover=False):super().__init__();self.path=path;self.width=w;self.height=h;self.cover=cover
 def draw(self):
  c=self.canv;im=PILImage.open(self.path);iw,ih=im.size
  if not self.cover:
   scale=min(self.width/iw,self.height/ih);w,h=iw*scale,ih*scale;c.drawImage(ImageReader(im),(self.width-w)/2,(self.height-h)/2,w,h)
  else:
   scale=min(180/iw,self.height/ih);w,h=iw*scale,ih*scale;c.drawImage(ImageReader(im),25,(self.height-h)/2,w,h)
   steps=['Ролик: контакт с покрытием','Рычаг: относительный угол α','Вал и магнит: передача поворота','AS5048A: цифровой код N','Pico: опрос и сообщение Q1','Java: калибровка и геометрия']
   height=34;gap=11;x=235;top=self.height-5
   for i,text in enumerate(steps):
    y=top-(i+1)*height-i*gap;boxlabel(c,x,y,self.width-x-8,height,text,size=9.5)
    if i<5:arrow(c,x+125,y-2,x+125,y-gap+2)
class Diagram(Flowable):
 def __init__(self,name,w,h):super().__init__();self.name=name;self.width=w;self.height=h
 def draw(self):
  c=self.canv;c.saveState();c.scale(self.width/510,self.height/225)
  c.setFillColor(PALE);c.roundRect(0,0,510,225,8,fill=1,stroke=0)
  getattr(self,self.name)(c);c.restoreState()
 def motion(self,c):
  o=(82,185);scale=.61;L=240*scale;r=20*scale
  c.setStrokeColor(GRAY);c.setDash(3,3);c.line(o[0],o[1],245,o[1]);c.setDash()
  label(c,220,198,'+X',9);arrow(c,38,143,38,202,GRAY);label(c,26,209,'+Z',9)
  c.setFillColor(colors.HexColor('#87969D'));c.rect(o[0]-12,o[1]-3,24,28,fill=1,stroke=0)
  positions=[]
  for a,col,dash in [(-56.44269,ORANGE,False),(-12.02470,TEAL,True)]:
   ang=math.radians(a);x=o[0]+L*math.cos(ang);y=o[1]+L*math.sin(ang);positions.append((x,y))
   c.setStrokeColor(col);c.setLineWidth(5);c.setDash(5,3) if dash else c.setDash();c.line(*o,x,y);c.setDash();c.setFillColor(colors.white);c.setLineWidth(1.4);c.circle(x,y,r,fill=1,stroke=1)
   c.circle(x,y,2,fill=0,stroke=1)
  c.setStrokeColor(GRAY);c.setLineWidth(1);x,y=positions[0];c.line(65,y-r,245,y-r)
  c.setStrokeColor(ORANGE);c.arc(o[0]-37,o[1]-37,o[0]+37,o[1]+37,startAng=-56.44,extent=56.44);label(c,123,160,'α',12,'Bold',ORANGE)
  label(c,18,22,'Сечение X–Z; два положения одного рычага.',9)
  for yy,txt in [(193,'У верхней оси:'),(177,'магнит + неподвижный датчик'),(140,'Измеряется качание рычага α.'),(119,'Сам ролик вращается свободно.'),(86,'На каждом малом колесе'),(70,'отдельного одометра в R1 нет.')]:label(c,268,yy,txt,9.1)
 def stack(self,c):
  origin=48;scale=14.2;X=lambda y:origin+(y+12)*scale;mid=108
  c.setDash(4,3);c.setStrokeColor(GRAY);c.line(30,mid,490,mid);c.setDash()
  c.setFillColor(colors.HexColor('#9AA4AA'));c.rect(X(-11.5),mid-7,16.5*scale,14,fill=1,stroke=0)
  for yy in [mid-27,mid+7]:c.setFillColor(colors.HexColor('#687B86'));c.rect(X(-2.5),yy,5*scale,20,fill=1,stroke=0)
  c.setFillColor(colors.HexColor('#AB3D35'));c.rect(X(5),mid-10,3*scale,20,fill=1,stroke=0)
  c.setFillColor(INK);c.rect(X(8.7),mid-20,1.2*scale,40,fill=1,stroke=0)
  c.setFillColor(TEAL);c.rect(X(9.9),mid-42,1.6*scale,84,fill=1,stroke=0)
  c.setFillColor(colors.HexColor('#9AA4AA'));c.rect(X(13.5),mid-7,14,14,fill=1,stroke=0)
  for v,txt,y in [(-11.5,'−11,5',50),(-2.5,'−2,5',65),(2.5,'+2,5',50),(5,'+5,0',65),(8,'+8,0',50),(11.5,'+11,5',31),(13.5,'+13,5',65)]:
   c.setStrokeColor(GRAY);c.setLineWidth(.7);c.line(X(v),mid-10,X(v),y+12);label(c,X(v)-12,y,txt,8)
  label(c,65,168,'вал PS',10);label(c,174,168,'подшипник PB',9);label(c,295,180,'магнит PM',9)
  arrow(c,326,174,X(6.5),mid+13);label(c,352,199,'корпус IC',9);arrow(c,398,191,X(9.3),mid+23)
  label(c,434,173,'плата PE',9);arrow(c,456,167,X(10.7),mid+44)
  label(c,28,12,'Схема осевого пакета, не рабочий чертёж. Ось +Y направлена вправо.',8.6)
 def magnet(self,c):
  c.setFillColor(colors.HexColor('#AA4A40'));c.wedge(25,92,139,206,90,180,fill=1,stroke=0)
  c.setFillColor(TEAL);c.wedge(25,92,139,206,270,180,fill=1,stroke=0)
  c.setFillColor(colors.white);c.setFont('Bold',18);c.drawString(47,143,'N');c.drawString(101,143,'S')
  c.setStrokeColor(INK);c.setLineWidth(1);c.circle(82,149,57,fill=0,stroke=1)
  label(c,20,74,'Вид вдоль оси вала',9);label(c,17,54,'N/S поворачиваются',9);label(c,31,38,'вместе с рычагом',9)
  arrow(c,146,150,182,150)
  boxlabel(c,190,111,112,77,'Массив Холла\nна неподвижном\nкристалле',size=10)
  arrow(c,310,150,338,150);boxlabel(c,347,125,145,49,'Аналоговый тракт\nи АЦП',size=10)
  arrow(c,420,117,420,91);boxlabel(c,347,35,145,50,'Вычисление угла\nи регистр N',size=10)
  label(c,192,74,'Учебное представление:',8.4);label(c,199,55,'φ = atan2(S, C)',11,'Bold')
 def spi(self,c):
  boxlabel(c,38,137,190,56,'Обмен 1: MOSI 0xFFFF\nзапрос Angle',size=11)
  boxlabel(c,285,137,190,56,'Обмен 2: MOSI 0x0000\nчтение ответа',size=11)
  arrow(c,237,165,276,165);label(c,207,117,'CSn между обменами = 1',8.4)
  boxlabel(c,38,61,190,37,'MISO: предыдущий ответ',size=9.5)
  boxlabel(c,285,61,190,37,'MISO: raw, например 0xB800',size=9.5)
  arrow(c,133,130,133,105);arrow(c,380,130,380,105)
  label(c,34,21,'Сначала проверить 16 бит ответа; затем выделить 14 бит значения.',9.2)
 def chain(self,c):
  boxlabel(c,18,111,68,62,'Pico\nSPI0',size=10)
  for x,txt in [(123,'j=8'),(247,'j=14'),(374,'j=15')]:boxlabel(c,x,116,91,46,txt,size=11)
  arrow(c,86,140,120,140);arrow(c,216,140,245,140);arrow(c,340,140,372,140)
  label(c,217,166,'…',17);label(c,95,176,'DIN',8);label(c,466,142,'DOUT',7.8)
  c.setStrokeColor(TEAL);c.setLineWidth(1.2);c.line(465,137,486,137);c.line(486,137,486,60);c.line(486,60,55,60);arrow(c,55,60,55,108)
  label(c,121,41,'Возврат в MISO: сначала ответ последнего датчика.',9)
  c.setStrokeColor(GRAY);c.setDash(3,3);c.line(79,195,435,195)
  for x in [168,292,419]:c.line(x,195,x,166)
  c.setDash();label(c,125,206,'SCK и CS1 общие для банка 1',9)
 def radius(self,c):
  c.setStrokeColor(GRAY);c.setLineWidth(2);c.line(24,56,246,95)
  a=math.atan2(39,222);r=46;contact=(130,56+(130-24)*39/222);center=(contact[0]-r*math.sin(a),contact[1]+r*math.cos(a))
  c.setFillColor(colors.white);c.setStrokeColor(INK);c.circle(*center,r,fill=1,stroke=1);c.circle(*center,2,fill=1,stroke=1)
  arrow(c,*contact,center[0],center[1]);label(c,center[0]+10,center[1]-13,'r · n',11)
  label(c,32,186,'Центр ролика c',11,'Bold');arrow(c,122,178,center[0],center[1]+7)
  c.setFillColor(ORANGE);c.circle(*contact,3,fill=1,stroke=0)
  label(c,113,34,'Точка контакта p',10)
  boxlabel(c,280,111,201,67,'На наклоне:\np = c − r · n',size=14)
  label(c,278,77,'Поправка идёт по нормали,',10);label(c,278,60,'а не всегда строго по вертикали.',10)
  label(c,27,12,'Модель гладкого контакта сферической короны; грань и отрыв сюда не входят.',8.5)

def callout(title,text,w):
 inner=[para(title,'h'),para(text)]
 t=Table([[inner]],colWidths=[w]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.7,LINE),('LINEBEFORE',(0,0),(0,-1),3,TEAL),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),5)]));return t

def table(block,w):
 rows=[[para(str(cell),'th' if i==0 else 'cell') for cell in row] for i,row in enumerate(block['rows'])]
 t=Table(rows,colWidths=[v*w for v in block['widths']],hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),TEAL),('VALIGN',(0,0),(-1,-1),'TOP'),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F5F8F9')]),('LINEBELOW',(0,0),(-1,0),.8,TEAL),('INNERGRID',(0,1),(-1,-1),.35,LINE),('BOX',(0,0),(-1,-1),.5,LINE),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]));return t
BASE='https://github.com/Eljah/qulay/blob/'+DATA['engineering_commit']+'/'
SOURCES=[
 ('R1','Геометрия тележки и рычага','mechanical/build.py'),
 ('R2','Узел шарнира R1; детали и осевые координаты','mechanical/revision_b.py'),
 ('R3','Плата encoder: схема, BOM, connections.csv','electronics/generated/encoder/encoder.kicad_sch'),
 ('R4','SPI-опрос Pico; проверки в include/protocol.h','firmware/src/main.c'),
 ('R5','Приём Q1; контакт и оценка наклона рамы','software/agent/src/main/java/org/qulay/agent/Wire.java'),
 ('R6','Калибровка Channel.angle; геометрия в Geometry.java','software/core/src/main/java/org/qulay/core/Model.java'),
 ('R7','Порядок каналов и соединения цепочек','electronics/generated/harness.csv'),
 ('D1','AS5048A/AS5048B, v1-11, 29.01.2018; официальный PDF','https://www.infineon.com/assets/row/public/documents/24/49/infineon-as5048a-as5048b-datasheet-en.pdf'),
 ('D2','AS5048A: официальная карточка изделия','https://www.infineon.com/part/AS5048A'),
 ('D3','Analog Devices: акселерометрический наклон при вибрации','https://www.analog.com/en/resources/analog-dialogue/raqs/raq-issue-144.html')]
def source_blocks():
 out=[]
 for key,title,path in SOURCES:
  url=path if path.startswith('https:') else BASE+path
  out.append(Paragraph(f'<b>[{key}]</b> {html.escape(title)}. <link href="{html.escape(url,quote=True)}" color="#17656A">Открыть источник</link>',STYLE['small']))
 out.append(para('У D1 две вводные обложки: печатная страница 8 находится на странице 10 PDF. Ссылки «с.» в тексте используют печатную нумерацию паспорта. Для выводов см. с. 4; питания — с. 10; SPI — с. 10–17; магнита — с. 30–32.','small'))
 return out

def blocks(page,w,factor=1):
 out=[]
 for b in page['blocks']:
  kind=b['type']
  if kind in ('p','h','lead'):out.append(para(b['text'],kind))
  elif kind=='callout':out.extend([callout(b['title'],b['text'],w),Spacer(1,9)])
  elif kind=='table':out.extend([table(b,w),Spacer(1,10)])
  elif kind=='formula':out.extend([Table([[para(b['text'],'formula')]],colWidths=[w],style=[('BACKGROUND',(0,0),(-1,-1),PALE),('LEFTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]),Spacer(1,10)])
  elif kind=='code':out.extend([Preformatted(b['text'],STYLE['code']),Spacer(1,10)])
  elif kind=='image':out.append(Picture(HERE/b['path'],w,b['height']*factor,page.get('kind')=='cover'));out.extend([Spacer(1,5),para(b.get('caption',''),'small')])
  elif kind=='diagram':out.extend([Diagram(b['name'],w,b['height']*factor),Spacer(1,12)])
  elif kind=='sources':out.extend(source_blocks())
  else:raise ValueError(kind)
 return out

def calc_examples():
 values=[]
 for n in [14336,14564]:
  a=math.remainder(n*2*math.pi/16384,2*math.pi);raw=n|((n.bit_count()%2)<<15)
  assert raw.bit_count()%2==0 and (raw&0x4000)==0 and raw&0x3fff==n
  values.append({'N':n,'raw':hex(raw),'angle_deg':math.degrees(a),'center_x_mm':240*math.cos(a),'height_mm':220+240*math.sin(a)-20})
 assert abs(values[0]['angle_deg']+45)<1e-10
 assert abs(values[0]['height_mm']-30.2943725152)<1e-8
 assert abs(values[1]['height_mm']-45.7623118481)<1e-8
 levels=[]
 for h in [0,150]:
  a=math.asin((h+20-220)/240);s=240*math.cos(a)
  levels.append({'surface_height_mm':h,'angle_deg':math.degrees(a),'sensitivity_mm_per_rad':s,'one_lsb_height_mm':s*2*math.pi/16384,'height_effect_of_0p8_degree_mm':s*math.radians(.8)})
 return {'kind':'calculated_examples_not_hardware_data','zeroRad':0,'L_mm':240,'H_mm':220,'r_mm':20,'examples':values,'sensitivities':levels,'spi_payload_us_at_1MHz':31*16*4,'frame_step_mm_at_0p2_mps_and_100Hz':2.0,'grade_example_percent':5,'grade_example_degrees':math.degrees(math.atan(.05))}

def main():
 tmp=HERE/'channel-layout.pdf';target=HERE/'Qulay_One_Roller_Tilt_AS5048A_R1.pdf'
 c=canvas.Canvas(str(tmp),pagesize=A4);c.setTitle(DATA['title']);c.setAuthor('Qulay / engineering documentation');c.setSubject('Один измерительный канал QL-01.R1: кинематика, AS5048A, SPI, калибровка и ограничения')
 layout=[];overlays=[]
 for index,page in enumerate(DATA['pages']):
  W,H=landscape(A3) if page.get('kind')=='schematic' else A4;c.setPageSize((W,H));margin=40;w=W-2*margin
  c.setFillColor(TEAL);c.rect(0,H-8,W,8,fill=1,stroke=0)
  label(c,margin,H-33,'QULAY  /  ИЗМЕРИТЕЛЬНЫЙ КАНАЛ',9,'Bold',TEAL)
  c.setFont('Body',8.5);c.setFillColor(GRAY);c.drawRightString(W-margin,H-33,'К01 · QL-01.R1')
  title=Paragraph(html.escape(page['title']),STYLE['title']);_,th=title.wrap(w,80);title.drawOn(c,margin,H-51-th);top=H-65-th
  title_key='p'+str(index+1);c.bookmarkPage(title_key);c.addOutlineEntry(page['title'],title_key,0,False)
  def measure(flows):return sum(f.wrap(w,10000)[1]+getattr(f,'spaceBefore',0)+getattr(f,'spaceAfter',0) for f in flows)
  available=top-72;flows=blocks(page,w);need=measure(flows);factor=1.0
  if need>available and any(b['type'] in ['diagram','image'] for b in page['blocks']):
   flex=sum(b.get('height',0) for b in page['blocks'] if b['type'] in ['diagram','image']);factor=max(.70,1-(need-available+2)/flex);flows=blocks(page,w,factor);need=measure(flows)
  if need>available+1:raise RuntimeError(f'Page {index+1} overflows: {need:.1f} > {available:.1f}: '+page['title'])
  y=top
  for f in flows:
   y-=getattr(f,'spaceBefore',0);_,fh=f.wrap(w,10000);y-=fh;f.drawOn(c,margin,y);y-=getattr(f,'spaceAfter',0)
  if page.get('kind')=='schematic':
   rect=fitz.Rect(margin,H-y+9,W-margin,H-76);overlays.append((index,rect));c.setStrokeColor(LINE);c.rect(margin,76,w,y-85,fill=0,stroke=1)
  c.setStrokeColor(LINE);c.setLineWidth(.7);c.line(margin,60,W-margin,60)
  sf=para(page['sources'],'small');_,sh=sf.wrap(w-50,50);sf.drawOn(c,margin,55-sh)
  c.setFont('Body',8);c.setFillColor(GRAY);c.drawRightString(W-margin,30,f'{index+1} / {len(DATA["pages"])}')
  layout.append({'page':index+1,'title':page['title'],'size_pt':[W,H],'content_height_pt':need,'available_height_pt':available,'image_height_factor':factor})
  c.showPage()
 c.save()
 doc=fitz.open(tmp);sch=fitz.open(ROOT/'electronics/generated/encoder/encoder-schematic.pdf')
 # Magnified vector fragments of the same KiCad sheet; named nets remain unchanged.
 clips=[('U1 — AS5048A',fitz.Rect(75,108,261,212)),('J1 — разъём',fitz.Rect(414,120,594,202)),('C1 — 100 нФ',fitz.Rect(754,119,928,202)),('C2 — 10 мкФ',fitz.Rect(73,318,253,402))]
 for index,rect in overlays:
  page=doc[index];page.insert_font(fontname='QLNoteLabel',fontfile=str(FONT/'DejaVuSans.ttf'))
  gap=16;cw=(rect.width-gap)/2;ch=(rect.height-gap)/2
  for k,(caption,clip) in enumerate(clips):
   x=rect.x0+(k%2)*(cw+gap);y=rect.y0+(k//2)*(ch+gap)
   pane=fitz.Rect(x,y,x+cw,y+ch);page.draw_rect(pane,color=(.80,.85,.87),width=.6)
   page.insert_text((x+12,y+22),caption,fontname='QLNoteLabel',fontsize=13,color=(.09,.27,.29))
   page.show_pdf_page(fitz.Rect(x+10,y+35,x+cw-10,y+ch-10),sch,0,clip=clip,keep_proportion=True)
 if target.exists():target.unlink()
 doc.save(target,garbage=4,deflate=True);doc.close();tmp.unlink();sch.close()
 files=['config/geometry.json','mechanical/build.py','mechanical/revision_b.py','electronics/generated/encoder/connections.csv','electronics/generated/encoder/BOM.csv','electronics/generated/encoder/encoder-schematic.pdf','electronics/generated/encoder/encoder.kicad_pcb','electronics/generated/harness.csv','firmware/src/main.c','firmware/include/protocol.h','software/agent/src/main/java/org/qulay/agent/Wire.java','software/core/src/main/java/org/qulay/core/Model.java','software/core/src/main/java/org/qulay/core/Geometry.java']
 manifest={'engineering_commit':DATA['engineering_commit'],'reviewed_snapshot':DATA['reviewed_snapshot'],'files':[{'path':p,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in files],'external_references':[{'id':key,'url':url} for key,title,url in SOURCES if key.startswith('D')]}
 (HERE/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 (HERE/'examples.json').write_text(json.dumps(calc_examples(),ensure_ascii=False,indent=2))
 check={'pages':len(DATA['pages']),'a3_pages':len(overlays),'a4_pages':len(DATA['pages'])-len(overlays),'layout':layout,'numeric_examples_passed':True,'hardware_test_performed':False,'manufacturing_release':False,'document_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
 (HERE/'document-check.json').write_text(json.dumps(check,ensure_ascii=False,indent=2))
 with fitz.open(target) as d:
  assert len(d)==len(DATA['pages'])
  assert all(p.get_text().strip() for p in d)
  assert '14336' in ''.join(p.get_text() for p in d)
 print(json.dumps({'pdf':str(target),'pages':len(DATA['pages']),'layout':'PASS','numeric_examples':'PASS','hardware':'NOT_TESTED'},ensure_ascii=False))
if __name__=='__main__':main()
