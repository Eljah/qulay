"""Build EM-01: engineering manual from actual repository CAD, KiCad and Java/C sources.
ReportLab diagrams are explanatory projections; source coordinates remain inspectable.
"""
from pathlib import Path
import sys,json,math,hashlib,html
from PIL import Image as PILImage
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4,A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle,Spacer,Flowable,Frame,Preformatted
import fitz
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;OUT=HERE/'generated'
sys.path.insert(0,str(HERE/'tools'));import prepare
prepare.main()
DATA=json.loads((OUT/'engineering-data.json').read_text());PAGES=json.loads((HERE/'content.json').read_text())
FONT=Path('/usr/share/fonts/truetype/dejavu')
for name,file in [('Sans','DejaVuSans.ttf'),('SansB','DejaVuSans-Bold.ttf'),('Mono','DejaVuSansMono.ttf')]:pdfmetrics.registerFont(TTFont(name,str(FONT/file)))
pdfmetrics.registerFontFamily('Sans',normal='Sans',bold='SansB',italic='Sans',boldItalic='SansB')
INK=colors.HexColor('#173044');TEAL=colors.HexColor('#167e85');LIGHT=colors.HexColor('#edf5f6');GRID=colors.HexColor('#c5d1d8');MUTED=colors.HexColor('#516576');ORANGE=colors.HexColor('#a95120');RED=colors.HexColor('#b34038');PAD=colors.HexColor('#bd9652')
STYLE=ParagraphStyle('body',fontName='Sans',fontSize=10.35,leading=14.4,textColor=INK,spaceAfter=9)
SMALL=ParagraphStyle('small',parent=STYLE,fontSize=9.2,leading=12.1,spaceAfter=3)
CELL=ParagraphStyle('cell',parent=STYLE,fontSize=9.3,leading=12.1,spaceAfter=0)
H=ParagraphStyle('h',parent=STYLE,fontName='SansB',fontSize=12.2,leading=15.5,spaceBefore=4,spaceAfter=8)
CSTYLE=ParagraphStyle('code',fontName='Mono',fontSize=8.0,leading=11.2,textColor=INK,backColor=LIGHT,borderPadding=8,spaceBefore=4,spaceAfter=10)
NOTE=ParagraphStyle('note',parent=STYLE,fontSize=10,leading=14,backColor=LIGHT,borderPadding=10,spaceBefore=7,spaceAfter=16)

def txt(c,x,y,s,size=10,bold=False,col=INK,align='left'):
 c.setFont('SansB' if bold else 'Sans',size);c.setFillColor(col)
 {'left':c.drawString,'center':c.drawCentredString,'right':c.drawRightString}[align](x,y,str(s))
def line(c,x1,y1,x2,y2,col=INK,width=1):c.setStrokeColor(col);c.setLineWidth(width);c.line(x1,y1,x2,y2)
def arrow(c,x1,y1,x2,y2,col=TEAL,width=1.3):
 line(c,x1,y1,x2,y2,col,width);a=math.atan2(y2-y1,x2-x1);d=5
 for sign in [-1,1]:line(c,x2,y2,x2-d*math.cos(a+sign*.5),y2-d*math.sin(a+sign*.5),col,width)
def box(c,x,y,w,h,fill=LIGHT,stroke=GRID):
 c.setFillColor(fill);c.setStrokeColor(stroke);c.setLineWidth(.7);c.roundRect(x,y,w,h,4,fill=1,stroke=1)
def par(c,text,x,y,w,size=10):
 style=ParagraphStyle('f',parent=STYLE,fontSize=size,leading=size*1.32,spaceAfter=0)
 p=Paragraph(text,style);_,h=p.wrap(w,10000);p.drawOn(c,x,y-h);return h

def image(c,path,x,y,w,h):
 # Whitespace trimmed from actual CAD render, never altered geometry.
 img=PILImage.open(path).convert('RGB')
 import numpy as np
 a=np.array(img);mask=(a.max(axis=2)-a.min(axis=2)>25)|(a.mean(axis=2)<205)
 yy,xx=np.where(mask)
 if len(xx):img=img.crop((max(0,xx.min()-15),max(0,yy.min()-15),min(img.width,xx.max()+16),min(img.height,yy.max()+16)))
 from reportlab.lib.utils import ImageReader
 c.drawImage(ImageReader(img),x,y,w,h,preserveAspectRatio=True,anchor='c',mask='auto')

def table_obj(head,rows,w,widths=None,size=9.3):
 style=ParagraphStyle('tc',parent=CELL,fontSize=size,leading=size*1.30)
 hs=ParagraphStyle('th',parent=style,fontName='SansB',textColor=colors.white)
 cell=lambda s,st:Paragraph(str(s),st)
 widths=widths or [1/len(head)]*len(head)
 data=[[cell(v,hs) for v in head]]+[[cell(v,style) for v in row] for row in rows]
 t=Table(data,colWidths=[w*x for x in widths],hAlign='LEFT',repeatRows=1)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f4f7f9')]),('LINEBELOW',(0,0),(-1,0),.7,INK),('LINEBELOW',(0,1),(-1,-1),.35,GRID)]))
 return t

AS=['CSn','CLK','MISO','MOSI','TEST → GND','TEST: open','TEST: open','TEST: open','TEST: open','TEST: open','VDD5V → 3V3','VDD3V → 3V3','GND','PWM: open']
def as_pinout(c,w,h):
 cx=w/2;bh=112;by=13;bw=130;bx=cx-bw/2
 box(c,bx,by,bw,bh,colors.HexColor('#deebee'),TEAL)
 txt(c,cx,by+58,'AS5048A',11,True,align='center');txt(c,cx,by+39,'TOP VIEW',8,align='center')
 c.setFillColor(TEAL);c.circle(bx+15,by+bh-13,3,fill=1,stroke=0)
 for i in range(7):
  yy=by+bh-13-i*14
  for n,left in [(i+1,True),(14-i,False)]:
   xx=bx-18 if left else bx+bw
   c.setFillColor(PAD);c.rect(xx,yy-3,18,6,fill=1,stroke=0)
   txt(c,bx+6 if left else bx+bw-6,yy-2.5,n,7.8,align='left' if left else 'right')
   txt(c,xx-7 if left else xx+25,yy-3,AS[n-1],8.3,align='right' if left else 'left')

def encoder_view(c,x,y,scale,kind):
 enc=DATA['boards']['encoder'];boardW,boardH=18*scale,24*scale
 def tr(u,v):
  if kind=='std':return x+u*scale,y+(24-v)*scale
  if kind=='front':return x+(18-u)*scale,y+v*scale
  return x+u*scale,y+v*scale
 c.setFillColor(colors.HexColor('#eef6f0'));c.setStrokeColor(TEAL);c.rect(x,y,boardW,boardH,fill=1,stroke=1)
 for name,f in enc.items():
  for p in f['pads']:
   xx,yy=tr(p['u'],p['v']);pw,ph=p['width']*scale,p['height']*scale
   c.setFillColor(PAD if p['pin']!='1' else ORANGE)
   c.setStrokeColor(colors.white);c.setLineWidth(.3)
   if name.startswith('MH'):c.circle(xx,yy,1.1*scale,fill=0,stroke=1)
   else:c.rect(xx-pw/2,yy-ph/2,pw,ph,fill=1,stroke=1)
   if name=='J1':txt(c,xx,yy-2.4,p['pin'],8,True,colors.white,align='center')
 xx,yy=tr(9,12)
 c.setFillColor(INK if kind!='back' else colors.HexColor('#d5e2df'));c.setStrokeColor(MUTED)
 if kind=='back':c.setDash(3,2)
 c.rect(xx-2.15*scale,yy-2.5*scale,4.3*scale,5*scale,fill=1,stroke=1);c.setDash()
 txt(c,xx,yy-2,'U1',9,True,colors.white if kind!='back' else INK,align='center')
 p1=next(p for p in enc['U1']['pads'] if p['pin']=='1');xx1,yy1=tr(p1['u'],p1['v'])
 c.setFillColor(RED);c.circle(xx1,yy1,3.2,fill=1,stroke=0)
 left=xx1<xx;arrow(c,xx1+(-32 if left else 32),yy1+(-25 if kind!='std' else 25),xx1,yy1,RED)
 txt(c,xx1+(-34 if left else 34),yy1+(-27 if kind!='std' else 27),'U1.1',9,True,RED,align='right' if left else 'left')
 for u,v in [(2.5,21),(15.5,21)]:
  a,b=tr(u,v);c.setFillColor(colors.white);c.setStrokeColor(INK);c.circle(a,b,1.1*scale,fill=1,stroke=1)
 a,b=tr(4,3);txt(c,x+boardW/2,y-18,'J1: '+('1 2 3 4 5 6' if kind!='front' else '6 5 4 3 2 1'),11,True,align='center')
 a,b=tr(9,12);line(c,a-9,b,a+9,b,TEAL,.6);line(c,a,b-9,a,b+9,TEAL,.6)

def encoder_views(c,w,h):
 gap=22;panel=(w-2*gap)/3
 for i,(title,kind,desc) in enumerate([('1. KiCad / пайка','std','Вид на F.Cu. Разъём сверху, отверстия снизу.'),('2. Установка: от магнита','front','Взгляд вдоль +Y. Вверх +Z, вправо +X.'),('3. Тыльная сторона','back','Взгляд вдоль −Y. IC показан на просвет.')]):
  x=i*(panel+gap);box(c,x,15,panel,h-22,colors.white)
  txt(c,x+panel/2,h-30,title,12,True,align='center')
  par(c,desc,x+15,h-45,panel-30,9.5)
  sc=10.6;bw=18*sc;encoder_view(c,x+(panel-bw)/2,100,sc,kind)
  par(c,('Припаять IC к его площадкам; dot корпуса к U1.1.' if kind=='std' else 'Pin 1 не меняет номер. Жгут сверить прозвонкой.'),x+18,65,panel-36,10)
 txt(c,w/2,0,'Установочная связь: X=9−u; Z=H+v−12. Поворачивается вся плата, не IC на плате.',11,True,TEAL,'center')

def axial_stack(c,w,h):
 x0=245;scale=(w-285)/28.5
 def xx(y):return x0+(y+13)*scale
 base=26
 line(c,xx(-13),base,xx(15),base,INK)
 for q in [-12.5,-9.5,-6.5,-2.5,0,2.5,5,8,9.9,11.5]:
  line(c,xx(q),base-3,xx(q),h-18,GRID,.45)
  txt(c,xx(q),base-15,str(q).replace('.',','),8.5,align='center')
 parts=[('Фланец C1',-12.5,-9.5,TEAL),('Рычаг',-9.5,-6.5,ORANGE),('Вал Ø8',-9.5,5,INK),('Подшипник',-2.5,2.5,MUTED),('Магнит',5,8,RED),('Корпус IC',8.7,9.9,INK),('FR4 платы',9.9,11.5,TEAL)]
 for i,(name,a,b,col) in enumerate(parts):
  yy=h-28-i*23
  txt(c,2,yy,name,10.5,True,col)
  txt(c,150,yy,f'{a:g} … {b:g}',9,col=MUTED)
  c.setFillColor(col);c.roundRect(xx(a),yy-3,xx(b)-xx(a),12,2,fill=1,stroke=0)
 txt(c,2,base-13,'Y от центра подшипника, мм',9,True)

def banks(c,w,h):
 left=115;box(c,8,22,93,h-45,INK,INK);txt(c,55,h-65,'CARRIER',11,True,colors.white,'center')
 for b,n in enumerate([8,8,8,7]):
  yy=h-108-b*68;txt(c,55,yy+19,f'J{b+2}',14,True,colors.white,'center')
  txt(c,55,yy+3,f'CS GP{b+5}',8,False,colors.white,'center')
  x=160;ww=(w-245)/8;last=None
  arrow(c,101,yy+20,x,yy+20,TEAL)
  for k in range(n):
   j=8*b+k;xx=x+k*ww;box(c,xx,yy,ww-14,44,LIGHT,TEAL)
   txt(c,xx+(ww-14)/2,yy+25,f'encoder{j:02d}',9.5,True,align='center');txt(c,xx+(ww-14)/2,yy+9,f'j={j}',8.5,align='center')
   if k<n-1:arrow(c,xx+ww-14,yy+20,xx+ww,yy+20)
   last=xx+ww-14
  line(c,last,yy+20,last+10,yy+20,TEAL);line(c,last+10,yy+20,last+10,yy-12,TEAL);arrow(c,last+10,yy-12,103,yy-12,TEAL)
  txt(c,w-3,yy+23,'G'+str(b),13,True,TEAL,'right')
 txt(c,160,h-28,'MOSI → первый DIN → … → последний DOUT → MISO',12,True)
 txt(c,160,h-48,'Четыре общие цепи внутри банка: SENS_3V3, GND, CSn, SCK',10)

def chain8(c,w,h):
 xs=[105+i*(w-165)/8 for i in range(8)];bw=(w-165)/8-15;by=95;bh=78
 cols=[RED,INK,TEAL,ORANGE]
 for a,(sig,col) in enumerate(zip(['3V3 / P1','GND / P2','CS / P3','SCK / P4'],cols)):
  yy=h-40-a*22;txt(c,2,yy-3,sig,9,True,col);line(c,100,yy,w-10,yy,col,.9)
  for x in xs:
   xx=x+10+a*12;line(c,xx,yy,xx,by+bh,col,.6);c.setFillColor(col);c.circle(xx,yy,1.7,fill=1,stroke=0)
 for k,x in enumerate(xs):
  box(c,x,by,bw,bh,colors.white,GRID);txt(c,x+bw/2,by+52,f'encoder{8+k:02d}',10,True,align='center')
  txt(c,x+5,by+30,'P5',9);txt(c,x+bw-5,by+30,'P6',9,align='right');txt(c,x+bw/2,by+11,'DIN  →  DOUT',8,align='center')
  if k<7:arrow(c,x+bw,by+28,xs[k+1],by+28)
 txt(c,3,by+48,'J3.5',10,True);arrow(c,5,by+28,xs[0],by+28)
 right=xs[-1]+bw;line(c,right,by+28,right+8,by+28,TEAL);line(c,right+8,by+28,right+8,45,TEAL);arrow(c,right+8,45,5,45,TEAL)
 txt(c,5,27,'Возврат → carrier.J3.6 (MISO)',10,True,TEAL)
 txt(c,w/2,3,'Соединять P6 предыдущей платы с P5 следующей. Общие шины сверху не соединены между собой.',10,True,align='center')

def channel_table(c,w,h):
 rows=[]
 for r in DATA['channels']:
  j=r['java_index'];rows.append([j,r['cad_suffix'],r['encoder_label'],r['Y_mm'],f"{r['bank']} / {r['slot']}",r['carrier_connector'],f"GP{r['CS_gpio']} / {r['CS_physical_pin']}",f"ADC{j//8}.CH{j%8}"])
 t=table_obj(['j (Java)','Суффикс CAD','Жгут','Y, мм','Банк / слот','carrier','CS GPIO / pin','R2 контакт'],rows,w,[.07,.12,.17,.09,.12,.1,.13,.2],9.0)
 t.setStyle(TableStyle([('TOPPADDING',(0,0),(-1,-1),2.8),('BOTTOMPADDING',(0,0),(-1,-1),2.8)]))
 _,hh=t.wrap(w,h);t.drawOn(c,0,h-hh)
 if hh>h:raise ValueError('channel table too tall '+str(hh))

def carrier_views(c,w,h):
 for i,(key,title,dims) in enumerate([('r1','carrier / R1',(80,100)),('r2','carrier_r2 / R2',(100,140))]):
  pw=w/2-15;x=i*(w/2+15);box(c,x,5,pw,h-12,colors.white)
  txt(c,x+pw/2,h-30,title,15,True,align='center')
  sc=min((pw-100)/dims[0],(h-100)/dims[1]);ox=x+(pw-dims[0]*sc)/2;oy=40
  c.setFillColor(colors.HexColor('#eef6f0'));c.setStrokeColor(TEAL);c.rect(ox,oy,dims[0]*sc,dims[1]*sc,fill=1,stroke=1)
  for ref,f in DATA['boards'][key].items():
   for p in f['pads']:
    xx=ox+p['u']*sc;yy=oy+(dims[1]-p['v'])*sc
    c.setFillColor(ORANGE if p['pin']=='1' else PAD);c.rect(xx-p['width']*sc/2,yy-p['height']*sc/2,p['width']*sc,p['height']*sc,fill=1,stroke=0)
   if ref.startswith('J'):
    xj=ox+f['u']*sc;yj=oy+(dims[1]-f['v'])*sc;txt(c,xj-8,yj+10,ref,10,True,TEAL)
    p1=next((p for p in f['pads'] if p['pin']=='1'),None)
    if p1:txt(c,ox+p1['u']*sc,oy+(dims[1]-p1['v'])*sc-2,'1',5.7,True,colors.white,'center')
   elif ref=='U1':txt(c,ox+f['u']*sc,oy+(dims[1]-f['v'])*sc,'PICO',11,True,align='center')
  txt(c,x+pw/2,18,f'{dims[0]} × {dims[1]} мм  •  F.Cu сверху',10,align='center')

def adxl_pins(c,w,h):
 bx=200;by=55;bw=165;bh=155;box(c,bx,by,bw,bh,colors.HexColor('#e4edf0'),TEAL)
 txt(c,bx+bw/2,by+bh/2+6,'ADXL355',13,True,align='center');txt(c,bx+bw/2,by+bh/2-14,'TOP VIEW',9,align='center')
 c.setFillColor(RED);c.circle(bx+10,by+bh-20,3,fill=1,stroke=0)
 for i,(num,name) in enumerate([(1,'CS / SCL'),(2,'SCLK / VSSIO'),(3,'MOSI / SDA'),(4,'MISO / ASEL')]):
  yy=by+bh-22-i*36;line(c,bx-17,yy,bx,yy,PAD,6);txt(c,bx-23,yy-3,f'{num}  {name}',10,align='right')
 for i,(num,name) in enumerate([(11,'VSUPPLY'),(10,'V1P8ANA'),(9,'VSS'),(8,'V1P8DIG')]):
  yy=by+bh-22-i*36;line(c,bx+bw,yy,bx+bw+17,yy,PAD,6);txt(c,bx+bw+23,yy-3,f'{num}  {name}',10)
 for i,(num,name) in enumerate([(14,'DRDY'),(13,'INT2'),(12,'INT1')]):
  xx=bx+35+i*47;line(c,xx,by+bh,xx,by+bh+12,PAD,6);txt(c,xx,by+bh+27,f'{num}',9,True,align='center');txt(c,xx,by+bh+13,name,7.5,align='center')
 for i,(num,name) in enumerate([(5,'VDDIO'),(6,'VSSIO'),(7,'RESERVED')]):
  xx=bx+35+i*47;line(c,xx,by,xx,by-12,PAD,6);txt(c,xx,by-25,f'{num}',9,True,align='center');txt(c,xx,by-39,name,7.3,align='center')
 box(c,650,45,w-665,h-70,colors.white)
 par(c,'<b>Корпус IC ≠ разъём готового модуля</b><br/><br/>Кабель к carrier.J6 имеет свой порядок 1…7. Выводы питания и развязки IC остаются на модуле. Перед покупкой проверьте его схему, а не только надпись «ADXL355».',670,h-40,w-705,12)

def hall(c,w,h):
 bx=95;by=30;bw=70;bh=95;box(c,bx,by,bw,bh,colors.white,TEAL)
 for n,yy,side,lab in [(1,by+75,'L','VCC'),(2,by+20,'L','OUT'),(3,by+47,'R','GND')]:
  xx=bx-15 if side=='L' else bx+bw;line(c,xx,yy,xx+15,yy,PAD,5)
  txt(c,xx-5 if side=='L' else xx+20,yy-3,f'{n} {lab}',10,True,align='right' if side=='L' else 'left')
 txt(c,130,3,'SOT-23, сверху',9,align='center');txt(c,130,by+50,'DRV',9,True,align='center')
 box(c,300,35,175,90,LIGHT)
 txt(c,310,105,'force.J1',11,True)
 for k,sig in [(1,'3V3'),(2,'GND'),(3,'OUT после R/C')]:txt(c,310,105-20*k,f'{k}   {sig}',9.5)
 txt(c,300,13,'U1.2 ≠ J1.2',11,True,RED)

def source_table(c,w,h):
 pairs=[('S1 / S2','electronics/generated/encoder: connections.csv; encoder.kicad_pcb'),('S3','electronics/generated/carrier: connections.csv; carrier.kicad_pcb'),('S4','electronics/generated-r2/carrier_r2: connections.csv; carrier_r2.kicad_pcb'),('S5 / S7','electronics/generated-r2/{force,adc}/connections.csv'),('S6','electronics/generated/harness.csv'),('S8','mechanical/revision_b.py'),('S9','mechanical/coupling_c1/{build.py,README.md,generated/*}'),('S10 / S11','firmware/src/main.c; firmware/r2/main.c'),('S12','firmware/include/protocol.h'),('S13','core/Model.java: Channel.angle(), validate()'),('S14','agent/Wire.java; agent/WireV2.java: parse()'),('S15 / S16','core/ContactModel.java; core/Geometry.java'),('S17 / S18','agent/Agent.java; core/Json.java'),('S19','desktop/DesktopApp.java')]
 t=table_obj(['Код','Путь / ключевой участок'],pairs,w,[.16,.84],8.8);_,hh=t.wrap(w,h);t.drawOn(c,0,h-hh)
 par(c,'Сокращённые пути Java: <b>core/</b> = software/core/src/main/java/org/qulay/core/; <b>agent/</b> = software/agent/src/main/java/org/qulay/agent/; <b>desktop/</b> — аналогично в модуле desktop. Полные пути и хеши приведены в source-manifest.json.',0,h-hh-12,w,9)

FUNCS={'as_pinout':as_pinout,'encoder_views':encoder_views,'axial_stack':axial_stack,'banks':banks,'chain8':chain8,'channel_table':channel_table,'carrier_views':carrier_views,'adxl_pins':adxl_pins,'hall':hall,'source_table':source_table}
class Figure(Flowable):
 def __init__(self,name,w,h):super().__init__();self.name=name;self.width=w;self.height=h
 def draw(self):
  if self.name in ['cover','coupling']:
   path=ROOT/('docs/channel/assets/single-channel.png' if self.name=='cover' else 'mechanical/coupling_c1/generated/exploded.png');image(self.canv,path,0,10,self.width,self.height-20)
  else:FUNCS[self.name](self.canv,self.width,self.height)

PDF=OUT/'Qulay_Tilt_Sensors_Mounting_Wiring_Channels.pdf'
c=canvas.Canvas(str(PDF),pagesize=A4,pageCompression=1,invariant=1)
c.setTitle('Qulay ЭМ-01 — датчики наклона: монтаж, цоколёвка, жгуты и код')
c.setAuthor('Qulay engineering documentation')
layout=[]
for num,page in enumerate(PAGES,1):
 W,HH=landscape(A3) if page['size']=='A3' else A4;c.setPageSize((W,HH))
 margin=36 if page['size']=='A3' else 40;ww=W-2*margin
 c.bookmarkPage('p'+str(num));c.addOutlineEntry(page['title'],'p'+str(num),level=0)
 c.setFillColor(TEAL);c.rect(0,HH-7,W,7,fill=1,stroke=0)
 txt(c,margin,HH-31,page['kicker'],8.5,True,TEAL)
 title=Paragraph(page['title'],ParagraphStyle('title',fontName='SansB',fontSize=23,leading=28,textColor=INK));_,th=title.wrap(ww,100)
 title.drawOn(c,margin,HH-44-th)
 ytop=HH-58-th
 story=[]
 for b in page['blocks']:
  if b['type']=='p':story.append(Paragraph(b['text'],STYLE))
  elif b['type']=='h':story.append(Paragraph(b['text'],H))
  elif b['type']=='note':story.extend([Spacer(1,3),Paragraph(b['text'],NOTE)])
  elif b['type']=='code':story.append(Preformatted(b['text'],CSTYLE,dedent=0,maxLineLength=90))
  elif b['type']=='figure':story.extend([Figure(b['name'],ww-2,b['height']),Spacer(1,8)])
  elif b['type']=='table':story.extend([table_obj(b['head'],b['rows'],ww-2,b.get('widths')),Spacer(1,10)])
  else:raise ValueError(b)
 frame=Frame(margin,65,ww,ytop-65,leftPadding=0,bottomPadding=0,rightPadding=0,topPadding=0,showBoundary=0)
 frame.addFromList(story,c)
 if story:raise ValueError(f'Page {num} overflow ({page["title"]}): {len(story)} flowables remain, first={type(story[0])}')
 line(c,margin,53,W-margin,53,GRID,.6)
 footer=Paragraph(page['source'],ParagraphStyle('ft',fontName='Sans',fontSize=7.3,leading=9.2,textColor=MUTED));_,fh=footer.wrap(ww-52,35);footer.drawOn(c,margin,45-fh)
 txt(c,W-margin,28,f'{num:02d} / {len(PAGES)}',8.5,True,MUTED,'right')
 layout.append({'page':num,'title':page['title'],'size':page['size']});c.showPage()
c.save()
doc=fitz.open(PDF)
for page in doc:
 text=page.get_text();assert len(text.strip())>100
 for b in page.get_text('dict')['blocks']:
  if b['type']==0:
   for ln in b['lines']:
    for s in ln['spans']:
     x0,y0,x1,y1=s['bbox']
     if x0<1 or y0<1 or x1>page.rect.width+1 or y1>page.rect.height+1:raise ValueError(('text outside page',page.number+1,s['text']))
report={'pages':len(doc),'a3_pages':sum(p['size']=='A3' for p in PAGES),'a4_pages':sum(p['size']=='A4' for p in PAGES),'source_commit':prepare.BASE,'document_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest(),'layout':layout,'hardware_tested':False,'automatic_checks':'all story content fits; text inside page bounds; actual CAD/PCB source inputs used'}
(OUT/'document-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(PDF,len(doc),'pages',PDF.stat().st_size,'bytes')
