"""QL-01.R1 mechanical/installation manual, generated from pinned project files.
Run from the repository. Optional prepare_assets.py makes additional actual CAD views.
No manufactured hardware, approved tolerances or normative certification is implied.
"""
from pathlib import Path
from io import BytesIO
import csv, json, re, math, hashlib, html
import fitz
from PIL import Image, ImageChops
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import ParagraphStyle

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[1]
BASE='a72e3a0d45d8b01d22f80cbc825711bc627f5c7f'
OUTPUT=HERE/'QL01-R1-Mechanical-Installation.pdf'
INK=colors.HexColor('#193042'); ACCENT=colors.HexColor('#126978'); LIGHT=colors.HexColor('#eef4f6'); GREY=colors.HexColor('#536674'); RULE=colors.HexColor('#c6d3d9'); AMBER=colors.HexColor('#fbf2df')
for name,file in [('DV','DejaVuSans.ttf'),('DV-Bold','DejaVuSans-Bold.ttf'),('DV-Mono','DejaVuSansMono.ttf')]:
    pdfmetrics.registerFont(TTFont(name,'/usr/share/fonts/truetype/dejavu/'+file))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DV-Bold',italic='DV',boldItalic='DV-Bold')
SOURCES={
 'S1':('Геометрия и исходная компоновка','config/geometry.json','mechanical/build.py'),
 'S2':('Изменения и осевой пакет R1','mechanical/revision_b.py','docs/REVISION_R1.md'),
 'S3':('Реестр деталей и проверки R1','mechanical/generated-r1/parts-crossing.csv','mechanical/generated-r1/collision-checks.json'),
 'S4':('Наследуемые заготовки и резка','mechanical/generated/cut-list-crossing.csv','mechanical/generated/arm-240mm-3mm.dxf'),
 'S5':('Электронная сборка и платы','electronics/README.md','electronics/generated/encoder/encoder.kicad_pcb','electronics/generated/carrier/carrier.kicad_pcb'),
 'S6':('Полная таблица соединений','electronics/generated/harness.csv','electronics/generated/encoder/connections.csv','electronics/generated/carrier/connections.csv'),
 'S7':('Аппаратный интерфейс и прошивка','firmware/README.md','firmware/src/main.c'),
 'S8':('Метрология и программа работы','docs/METROLOGY.md','docs/SOFTWARE.md'),
 'S9':('Результаты цифровых проверок','electronics/generated/verification-summary.json','generated/verification/summary.json'),
 'S10':('AS5048A/B, документ v1-11; монтаж и питание','https://www.infineon.com/assets/row/public/documents/24/49/infineon-as5048a-as5048b-datasheet-en.pdf'),
 'S11':('Raspberry Pi: документация Pico','https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html')}

def rows(path):
    with (ROOT/path).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def markup(text):
    text=html.escape(text)
    text=re.sub(r'`([^`]+)`',lambda m:'<font face="DV-Mono" size="8.5">'+m[1]+'</font>',text)
    return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)

def style(size=10.4,bold=False):return ParagraphStyle('x',fontName='DV-Bold' if bold else 'DV',fontSize=size,leading=size*1.39,textColor=INK,spaceAfter=0,splitLongWords=True)
def para(text,size=10.4,bold=False,raw=False):return Paragraph(text if raw else markup(text),style(size,bold))
def table(data,width,weights=None,size=9.1):
    n=len(data[0]);ww=weights or [1]*n;ww=[width*w/sum(ww) for w in ww]
    data=[[Paragraph(markup(str(x)), ParagraphStyle('th',parent=style(size,True),textColor=colors.white)) if i==0 else para(str(x),size) for x in row] for i,row in enumerate(data)]
    t=Table(data,colWidths=ww,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,LIGHT]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.6,INK),('LINEBELOW',(0,1),(-1,-1),.25,RULE)]))
    return t

def generated(name,width,scale):
    size=9.0*scale; weights=None
    if name=='dimensions':
        data=[['Параметр','Номинал CAD'],['Рама / база / колея','840 × 800 / 700 / 825 мм'],['Ширина по колёсам / концам осей','860 / 870 мм'],['Крайние оси датчиков / шаг','750 / 25 мм'],['Опорное колесо / измерительный ролик','Ø200 × 35 / Ø40 × 12 мм'],['Рычаг: длина между осями','240 мм'],['Ось шарнира / ось трубы рамы','Z = 220 / 260 мм (обычный режим)'],['Рабочий диапазон угла','−70…+20°'],['Габаритная перестановка кассеты','До 220 мм; механизм не разработан']];weights=[1.05,1]
    elif name=='bom_base':
        data=[['ID в CAD','Наименование и размер, мм','Кол.'],['F01-L/R','Продольная труба 25 × 25 × 2, L840','2'],['F02-rear/front','Торцевая труба 25 × 25 × 2, L750','2'],['F03-rear-cross','Промежуточная труба 25 × 25 × 2, L750','1'],['W-leg-*','Опоры: габарит трубы 25 × 25 × 2, L160','4'],['W-axle-*','Оси основных колёс Ø12 × 62, габарит','4'],['W-wheel-*','Основное колесо Ø200 × 35, отверстие Ø12','4'],['C-slide-L/R','Габарит направляющей кассеты 35 × 12 × 285','2'],['C01-pivot-beam','Измерительная труба 40 × 40 × 2, L780','1'],['H01-L/R; H02-grip','Рукоять: 2 × L680 и 1 × L445, труба 25 × 25 × 2','3'],['E-enclosure','Габарит ящика электроники 205 × 160 × 80','1'],['B-battery-envelope','Габарит батарейной сборки 210 × 120 × 65','1']];weights=[1.05,2.4,.25]
    elif name=='bom_channel':
        data=[['ID','Деталь / номинал, мм','На канал / всего'],['A-NN','Рычаг 260 × 20 × 3, оси 240; 2 × Ø8,1','1 / 31'],['R-NN','Корона R20; ширина 12; отверстие Ø16','1 / 31'],['RB-NNa/b','Два подшипника Ø16/Ø8 × 5','2 / 62'],['RA-NN','Ось ролика Ø8 × 22','1 / 31'],['BR-NN','Алюминиевый кронштейн, толщина 5; контур А06','1 / 31'],['PB-NN','Подшипник шарнира Ø16/Ø8 × 5','1 / 31'],['PS-NN','Вал шарнира Ø8 × 16,5','1 / 31'],['PC-NN','Проставка Ø12/Ø8,1 × 4','1 / 31'],['PM-NN','Магнит Ø6 × 3, диаметральный','1 / 31'],['PE-NN; IC-NN','FR4 18 × 24 × 1,6; габарит IC 5 × 6,4 × 1,2','1 + 1 / 31 + 31'],['STL/STR-NN','Стойки: Ø4, отверстие Ø2,2; длина 7,4','2 / 62'],['SP-NN','Габарит пружины: Ø15/Ø13 × 3,6','1 / 31']];weights=[.7,2.15,.85]
    elif name=='cuts':
        data=[['Идентификатор','Профиль, мм','Длина, мм']]+[[x['id'],x['section_mm'].replace('x',' × '),x['length_mm']] for x in rows('mechanical/generated/cut-list-crossing.csv')];weights=[1.2,1,.65]
    elif name=='power':
        data=[['Сеть / ввод','Монтажное правило'],['carrier.J1.1 / J1.2','EXT_3V3 / GND; вход только стабилизированных 3,3 В'],['F1 → SENS_3V3','Питание 31 платы encoder через проектный PTC'],['PICO_3V3','Другая сеть: вывод 36 Pico → J6.1 и J7.1'],['USB SBC → Pico','Питание и данные CDC; фиксация кабеля обязательна'],['GND','Общая сигнальная земля; не заменять стальной рамой']];weights=[1,1.9]
    elif name=='pinout':
        data=[['Разъём','Контакт → сеть'],['carrier.J1','1 → EXT_3V3; 2 → GND'],['carrier.J2 (ветвь 0)','1 → SENS_3V3; 2 → GND; 3 → CS0; 4 → SCK0; 5 → MOSI0; 6 → MISO0'],['carrier.J3 (ветвь 1)','1 → SENS_3V3; 2 → GND; 3 → CS1; 4 → SCK0; 5 → MOSI0; 6 → MISO0'],['carrier.J4 (ветвь 2)','1 → SENS_3V3; 2 → GND; 3 → CS2; 4 → SCK0; 5 → MOSI0; 6 → MISO0'],['carrier.J5 (ветвь 3)','1 → SENS_3V3; 2 → GND; 3 → CS3; 4 → SCK0; 5 → MOSI0; 6 → MISO0'],['carrier.J6 (ADXL355)','1 → PICO_3V3; 2 → GND; 3 → SCK1; 4 → MOSI1; 5 → MISO1; 6 → CS_ADXL; 7 → DRDY_ADXL'],['carrier.J7 (одометр)','1 → PICO_3V3; 2 → GND; 3 → ODO_A; 4 → ODO_B'],['encoder.J1 (каждый)','1 → SENS_3V3; 2 → GND; 3 → CS; 4 → SCK; 5 → DIN; 6 → DOUT']];weights=[1,2.25]
    elif name in ('channels_first','channels_second'):
        data=[['CAD / j','Y, мм','Ветвь','Вход J1.5','Выход J1.6']]
        h=rows('electronics/generated/harness.csv');group={}
        for x in h:group.setdefault(int(x['channel']),{})[int(x['sensor_pin'])]=x
        def compact(s):return s.replace('carrier.','C.').replace('encoder','E')
        for j in (range(16) if name=='channels_first' else range(16,31)):
            d=group[j];b=int(d[5]['bank']);data.append([f'{j+1:02d} / {j}',str((j-15)*25),f'{b} / J{b+2}',compact(d[5]['connect_to']),compact(d[6]['connect_to'])])
        weights=[.8,.7,.85,1.5,1.5]
    elif name=='channel_check':
        data=[['CAD/j','Индекс\nпроверен','Диагн.','Замечание','CAD/j','Индекс\nпроверен','Диагн.','Замечание']]
        for j in range(16):
            k=j+16;data.append([f'{j+1:02d}/{j}','____','____','________',f'{k+1:02d}/{k}' if k<31 else '—','____' if k<31 else '','____' if k<31 else '','________' if k<31 else ''])
        weights=[.7,.95,.65,1.1]*2;size=8.1*scale
    elif name=='sources_table':
        data=[['Код','Источник / путь в проекте']]
        for key,(title,*paths) in SOURCES.items():
            path=paths[0];label=title+'\n'+path
            if path.startswith('http'):label=title+'\nВнешний документ; просмотрен 03.10.2026'
            data.append([key,label])
        weights=[.3,3.2];size=8.25*scale
    else:raise ValueError(name)
    return table(data,width,weights,size)


def parse_pages():
    pages=[]
    for chunk in (HERE/'manual.md').read_text(encoding='utf8').split('\n# '):
        chunk=chunk.removeprefix('# '); lines=chunk.strip().splitlines();title=lines.pop(0)
        sources=lines.pop(0).replace('@sources ','').strip() if lines and lines[0].startswith('@sources ') else ''
        blocks=[];i=0
        while i<len(lines):
            s=lines[i].strip();i+=1
            if not s:continue
            if s.startswith('## '):blocks.append(('h',s[3:]));continue
            if s.startswith('@'):blocks.append(('g',s[1:]));continue
            if s.startswith('|'):
                data=[s]
                while i<len(lines) and lines[i].strip().startswith('|'):data.append(lines[i].strip());i+=1
                cells=[[x.strip() for x in row.strip('|').split('|')] for row in data if not re.match(r'^\|?\s*:?-{2,}',row)]
                blocks.append(('t',cells));continue
            kind='q' if s.startswith('> ') else 'p';text=s[2:] if kind=='q' else s
            while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','@','|','>')):
                text+=' '+lines[i].strip();i+=1
            blocks.append((kind,text))
        pages.append((title,sources,blocks))
    return pages

def flowables(blocks,width,scale=1):
    out=[]
    for kind,data in blocks:
        if kind=='h':out.extend([Spacer(1,7),para(data,12.0*scale,True),Spacer(1,5)])
        elif kind=='p':out.extend([para(data,10.4*scale),Spacer(1,9*scale)])
        elif kind=='g':out.extend([generated(data,width,scale),Spacer(1,9*scale)])
        elif kind=='t':out.extend([table(data,width,None,8.8*scale),Spacer(1,9*scale)])
        elif kind=='q':
            t=Table([[para(data,9.7*scale)]],colWidths=[width]);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),AMBER),('BOX',(0,0),(-1,-1),.3,colors.HexColor('#ddc68f')),('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]));out.extend([t,Spacer(1,9*scale)])
    return out

CACHE={}
def cropped(path):
    path=str(path)
    if path not in CACHE:
        im=Image.open(path).convert('RGB');bg=Image.new('RGB',im.size,im.getpixel((0,0)))
        diff=ImageChops.difference(im,bg).convert('L').point(lambda v:255 if v>16 else 0)
        box=diff.getbbox() or (0,0,*im.size);box=(max(0,box[0]-25),max(0,box[1]-25),min(im.width,box[2]+25),min(im.height,box[3]+25));CACHE[path]=(im.crop(box),box)
    return CACHE[path]

def picture(c,path,x,y,w,h):
    im,box=cropped(path);scale=min(w/im.width,h/im.height);ww=im.width*scale;hh=im.height*scale;xx=x+(w-ww)/2;yy=y+(h-hh)/2
    c.drawImage(ImageReader(im),xx,yy,ww,hh,mask='auto');return (xx,yy,scale,box,im.height)

def label(c,text,x,y,w=250,size=10):
    p=para(text,size);_,h=p.wrap(w,1000);p.drawOn(c,x,y-h);return h

def heading(c,title,sources,land=False):
    W,H=landscape(A3) if land else A4;c.setPageSize((W,H))
    c.setFillColor(ACCENT);c.rect(0,H-12,W,12,fill=1,stroke=0)
    c.setFillColor(GREY);c.setFont('DV',8);c.drawString(42,H-34,'QULAY  /  МЕХАНИКА И МОНТАЖ  /  QL-01.R1-ММ • D1')
    h=label(c,title,42,H-52,W-84,21 if land else 19)
    c.setStrokeColor(RULE);c.line(42,H-68-h,W-42,H-68-h)
    c.setFillColor(GREY);c.setFont('DV',7.6);c.drawString(42,39,'Предварительная монтажная документация • 03.10.2026')
    c.drawString(42,26,'Источники: '+sources+'   |   База: '+BASE[:12])
    return W,H,H-82-h

def text_page(c,title,sources,blocks):
    W,H,y=heading(c,title,sources);width=W-84;available=y-61
    chosen=None
    for scale in [1,.98,.96,.94,.92]:
        ff=flowables(blocks,width,scale);height=sum(f.wrap(width,10000)[1] for f in ff)
        if height<=available:chosen=ff;break
    if chosen is None:raise ValueError(f'Page too full: {title}: {height:.1f} > {available:.1f}')
    for f in chosen:
        _,h=f.wrap(width,10000);f.drawOn(c,42,y-h);y-=h
    c.showPage()

PLATES=[
 ('А01. Общая компоновка R1','S1, S2, S3','iso'),
 ('А02. Вид сверху и идентификация узлов','S1, S2, S3','top'),
 ('А03. Вид сбоку и установочные координаты','S1, S2, S3','side'),
 ('А04. Шарнир: разнесённый вид','S2, S3','exploded'),
 ('А05. Осевой разрез и размерная цепь','S2, S3','stack'),
 ('А06. Кронштейн BR: номинальная заготовка','S2, S3','bracket'),
 ('А07. Рычаг A: номинальная заготовка','S1, S4','arm'),
 ('А08. Carrier: монтажные координаты платы','S5, S6','carrier'),
 ('А09. Encoder: установка платы на шарнир','S2, S5, S6','encoder'),
 ('А10. Положение вдоль бордюра','S1, S2, S8','curb'),
 ('А11. Положение на направляющих','S1, S2, S8','rail'),
 ('А12. Принципиальная схема encoder','S5, S6','schematic-encoder'),
 ('А13. Принципиальная схема carrier','S5, S6','schematic-carrier')]

def dimension(c,a,b,offset,text,horizontal=True):
    c.setStrokeColor(INK);c.setFillColor(INK);c.setLineWidth(.6)
    if horizontal:
        x1,y1=a;x2,y2=b;y=offset;c.line(x1,y1,x1,y+4);c.line(x2,y2,x2,y+4);c.line(x1,y,x2,y)
        for x,sgn in [(x1,1),(x2,-1)]:c.line(x,y,x+sgn*5,y+2);c.line(x,y,x+sgn*5,y-2)
        c.setFont('DV',10);c.drawCentredString((x1+x2)/2,y+5,text)
    else:
        x1,y1=a;x2,y2=b;x=offset;c.line(x1,y1,x-4,y1);c.line(x2,y2,x-4,y2);c.line(x,y1,x,y2)
        for y,sgn in [(y1,1),(y2,-1)]:c.line(x,y,x-2,y+sgn*5);c.line(x,y,x+2,y+sgn*5)
        c.saveState();c.translate(x-6,(y1+y2)/2);c.rotate(90);c.setFont('DV',10);c.drawCentredString(0,0,text);c.restoreState()

# Minimal S-expression reader: extracts existing board coordinates; does not invent nets.
def sexpr(path):
    tokens=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',Path(path).read_text());stack=[];root=None
    for t in tokens:
        if t=='(':
            v=[]
            if stack:stack[-1].append(v)
            stack.append(v)
        elif t==')':
            root=stack.pop()
        else:stack[-1].append(json.loads(t) if t.startswith('"') else t)
    return root

def children(node,key):return [x for x in node if isinstance(x,list) and x and x[0]==key]
def one(node,key,default=None):return next(iter(children(node,key)),default)

def pcb_plate(c,name,y):
    board=sexpr(ROOT/f'electronics/generated/{name}/{name}.kicad_pcb');bw,bh=(18,24) if name=='encoder' else (80,100)
    scale=18 if name=='encoder' else 5.5;ox=135;oy=145
    def pt(x,v):return ox+float(x)*scale,oy+(bh-float(v))*scale
    c.setFillColor(colors.HexColor('#f5f9f7'));c.setStrokeColor(INK);c.setLineWidth(1);c.rect(ox,oy,bw*scale,bh*scale,fill=1)
    for seg in children(board,'segment'):
        layer=one(seg,'layer')[1];c.setStrokeColor(colors.HexColor('#3b8789') if layer=='F.Cu' else colors.HexColor('#c3cdd2'))
        c.setLineWidth(max(.35,float(one(seg,'width')[1])*scale));c.line(*pt(*one(seg,'start')[1:3]),*pt(*one(seg,'end')[1:3]))
    for via in children(board,'via'):
        x,v=one(via,'at')[1:3];diam=float(one(via,'size')[1]);c.setStrokeColor(GREY);c.setFillColor(colors.white);c.circle(*pt(x,v),diam*scale/2,stroke=1,fill=1)
    refs=[]
    for fp in children(board,'footprint'):
        at=one(fp,'at');fx,fy=map(float,at[1:3]);angle=float(at[3]) if len(at)>3 else 0
        if angle:raise ValueError('Unexpected rotated footprint; update PCB drawing transform')
        ref=next((v[2] for v in children(fp,'property') if v[1]=='Reference'),'?')
        refs.append((ref,fx,fy))
        for pad in children(fp,'pad'):
            dx,dy=map(float,one(pad,'at')[1:3]);sx,sy=map(float,one(pad,'size')[1:3]);x,v=pt(fx+dx,fy+dy)
            c.setFillColor(colors.HexColor('#e4bc6f'));c.setStrokeColor(INK);c.setLineWidth(.5)
            if pad[3]=='circle':c.circle(x,v,sx*scale/2,fill=1)
            else:c.rect(x-sx*scale/2,v-sy*scale/2,sx*scale,sy*scale,fill=1)
            dr=one(pad,'drill')
            if dr:
                c.setFillColor(colors.white);c.circle(x,v,float(dr[1])*scale/2,fill=1)
            if pad[1] and not ref.startswith('MH'):
                c.setFillColor(INK);c.setFont('DV',7 if name=='carrier' else 9)
                c.drawCentredString(x,v+sy*scale/2+2,pad[1])
        if not ref.startswith('MH'):
            c.setFillColor(INK);c.setFont('DV-Bold',10 if name=='carrier' else 12);xx,yy=pt(fx,fy);c.drawString(xx-8,yy-18 if ref.startswith('J') else yy+22,ref)
    dimension(c,(ox,oy),(ox+bw*scale,oy),oy-35,f'{bw} мм')
    dimension(c,(ox,oy),(ox,oy+bh*scale),ox-45,f'{bh} мм',False)
    textx=690;tw=440
    label(c,'Вид со стороны компонентов (F.Cu). Координаты u вправо, v вниз. Номера площадок перенесены из сохранённого PCB; корпуса ответных разъёмов здесь не показаны.',textx,y,tw,12)
    if name=='encoder':
        data=[['Элемент','Координаты u;v, мм'],['Центр U1','9;12'],['MH1 / MH2','2,5;21 / 15,5;21; Ø2,2'],['J1, контакт 1','4;3; затем шаг 2,0 по +u'],['C1 / C2','14;15 / 14;18'],['Толщина FR4','1,6 мм (габарит модели)']]
        tx='На шарнире: X = u − 9; Z = v − 12. Отверстия на Z = +9; разъём на Z = −9. Сторона U1 обращена к магниту (−Y). Габарит компонентов, пайки и проводов проверить отдельно.'
    else:
        data=[['Элемент','Координаты u;v, мм'],['MH1…MH4','4;4 / 76;4 / 4;96 / 76;96; Ø2,2'],['Pico, центр footprint','25;47; междурядье 17,78'],['J1 / F1','57;12 / 60;18'],['J2 / J3 / J4 / J5','54;30 / 54;41 / 54;52 / 54;63'],['J6 / J7','52;80 / 14;85'],['C1 / C2','67;18 / 67;22']]
        tx='Крепёжный прямоугольник 72 × 92 мм. Carrier не содержит питания SBC. J1 принимает 3,3 В для encoder; J6/J7 используют PICO_3V3. Номера разъёмов не являются номерами физических выводов Pico.'
    t=table(data,tw,[1,2.15],11);_,h=t.wrap(tw,1000);t.drawOn(c,textx,y-110-h)
    label(c,tx,textx,y-140-h,tw,11)
    label(c,'Монтажный план по PCB, не замена Gerber. Масштаб изображения не использовать для сверления: применять координаты и исходный файл платы.',42,95,1100,10)


def dxf_plate(c,kind,y):
    import ezdxf
    path=ROOT/('mechanical/generated-r1/pivot-bracket-5mm.dxf' if kind=='bracket' else 'mechanical/generated/arm-240mm-3mm.dxf')
    doc=ezdxf.readfile(path);scale=8.5 if kind=='bracket' else 2.834645669;ox=285 if kind=='bracket' else 160;oy=220 if kind=='bracket' else 390
    def pt(x,z):return ox+x*scale,oy+z*scale
    c.setStrokeColor(INK);c.setLineWidth(1.4)
    for ent in doc.modelspace():
        typ=ent.dxftype()
        if typ=='LINE':c.line(*pt(ent.dxf.start.x,ent.dxf.start.y),*pt(ent.dxf.end.x,ent.dxf.end.y))
        elif typ=='CIRCLE':c.circle(*pt(ent.dxf.center.x,ent.dxf.center.y),ent.dxf.radius*scale,stroke=1)
        elif typ=='ARC':
            x,z=ent.dxf.center.x,ent.dxf.center.y;r=ent.dxf.radius
            c.arc(*pt(x-r,z-r),*pt(x+r,z+r),startAng=ent.dxf.start_angle,extent=(ent.dxf.end_angle-ent.dxf.start_angle)%360)
        elif typ=='LWPOLYLINE':
            points=[pt(a,b) for a,b,*_ in ent.get_points()];p=c.beginPath();p.moveTo(*points[0]);[p.lineTo(*v) for v in points[1:]]
            if ent.closed:p.close()
            c.drawPath(p)
        else:raise ValueError('Unexpected DXF entity '+typ)
    if kind=='bracket':
        dimension(c,pt(-15,50),pt(12,50),oy+50*scale+35,'27')
        dimension(c,pt(-15,-12),pt(-15,50),ox-15*scale-40,'62',False)
        c.setDash(4,3);c.line(*pt(-18,0),*pt(16,0));c.line(*pt(0,-15),*pt(0,53));c.setDash()
        label(c,'BR-NN • пластина 5 мм\nМатериал в CAD: алюминий.\nПоказан контур DXF, не чертёж посадки.',630,y,490,13)
        data=[['Точка контура','X;Z, мм'],['1','−12;−12'],['2','+12;−12'],['3','+12;+30'],['4','−15;+50'],['5','−15;+10'],['6','−12;+10'],['Отверстие PB','X0;Z0; Ø16,05'],['2 отверстия стоек','X = ±6,5; Z = +9; Ø2,2']]
        t=table(data,450,[1,1.5],11);_,h=t.wrap(450,1000);t.drawOn(c,630,y-85-h)
        label(c,'Не заданы: посадка/удержание подшипника, способ соединения BR с C01, винты и резьбы. Резку и отверстия согласовать с технологом до заказа.',630,y-110-h,450,11)
    else:
        dimension(c,pt(0,0),pt(240,0),oy+85,'240 между осями')
        dimension(c,pt(-10,-10),pt(250,-10),oy-85,'260 габарит')
        dimension(c,pt(-10,-10),pt(-10,10),ox-75,'20',False)
        c.setDash(5,3);c.line(*pt(-18,0),*pt(258,0));c.setDash()
        label(c,'A-NN • стальная пластина толщиной 3 мм; 2 отверстия Ø8,1; концевые дуги R10.',70,y,1000,13)
        label(c,'Номинальный контур 1:1 при печати листа A3 без масштабирования. Приоритет у чисел и исходного DXF. Проверочная линия ниже — 100 мм.',70,215,1020,12)
        c.setLineWidth(1);c.line(70,160,70+100*2.834645669,160);c.line(70,153,70,167);c.line(70+100*2.834645669,153,70+100*2.834645669,167);c.setFont('DV',10);c.drawString(70,136,'100 мм')
        label(c,'КО-4: гладкий вал Ø8 в отверстии Ø8,1 не задаёт передачу момента. Узел фиксации рычага должен быть выпущен отдельно.',460,165,600,12)
    label(c,'Все размеры номинальные, мм. Допуски, шероховатости, припуски и покрытия не назначены. Не измерять размер по растру.',42,85,1100,10)


def plate(c,title,sources,kind):
    W,H,y=heading(c,title,sources,True)
    if kind in ('encoder','carrier'):pcb_plate(c,kind,y);c.showPage();return
    if kind in ('bracket','arm'):dxf_plate(c,kind,y);c.showPage();return
    if kind=='stack':
        picture(c,ROOT/'mechanical/generated-r1/pivot-section.png',90,370,980,325)
        label(c,'Реальный разрез B-rep по плоскости оси шарнира. Ниже — справочная размерная цепь по локальной Y, не дополнительный разрез.',50,355,1090,11)
        x0=310;factor=18.5
        lanes=[('A: рычаг',-9.5,-6.5),('PC: проставка',-6.5,-2.5),('PB / BR',-2.5,2.5),('PS: вал',-11.5,5),('PM: магнит',5,8),('IC: корпус',8.7,9.9),('PE: FR4',9.9,11.5),('Следующий PS',13.5,30)]
        palette=[colors.HexColor(x) for x in ['#b38631','#87949a','#74818a','#576b78','#b64b43','#333333','#267450','#b8c2c6']]
        for k,(name,a,b) in enumerate(lanes):
            yy=300-k*23;c.setFillColor(palette[k]);c.rect(x0+a*factor,yy,(b-a)*factor,13,fill=1,stroke=0);c.setFillColor(INK);c.setFont('DV',9);c.drawString(52,yy+2,name);c.drawString(x0+b*factor+9,yy+2,f'{a:g}…{b:g} мм')
        label(c,'0,7 мм — зазор PM–корпус IC. 2,0 мм — номинал между PE и началом соседнего PS. Корпус разъёма, пайка, винты и люфт в этот номинал не включены.',50,94,1080,10)
        c.showPage();return
    image,desc={
      'iso':(ROOT/'mechanical/generated-r1/crossing-iso.png','31 независимый канал. Цвета рычагов сохранены из CAD. Ящик и батарея показаны габаритными телами; внутренний монтаж не разработан.'),
      'top':(HERE/'assets/r1-top.png','Ортогональная проекция R1: +X вверх, +Y влево. 01 — сторона −Y, 31 — сторона +Y. Рама 840 × 800; крайние оси каналов 750; шаг 25 мм.'),
      'side':(HERE/'assets/r1-side.png','Ортогональная проекция X–Z: +X вправо, +Z вверх. Ось шарниров Z220; оси рамы Z260; база колёс 700 мм. Габаритные трубы не задают сварные узлы.'),
      'exploded':(HERE/'assets/r1-pivot-exploded.png','Разнесённый вид одного шарнира из CAD R1. Детали искусственно смещены для чтения; реальные монтажные координаты — на листе А05.'),
      'curb':(ROOT/'mechanical/generated-r1/along-curb-iso.png','Модель уровней 0/150 мм. Верхняя площадка со стороны +Y. Рама Z410, шарниры Z220. Перед переналадкой разгрузить кассету; замки высоты требуют разработки.'),
      'rail':(ROOT/'mechanical/generated-r1/datum-rail-iso.png','Две направляющие 3000 × 60 × 80 × 4 мм; 5 опор на каждую. Верх Z200, рама Z460, шарниры Z220. Прогиб и устойчивость под нагрузкой не проверены.')
    }[kind]
    label(c,desc,42,y,W-84,12)
    place=picture(c,image,260 if kind in ('top','side','exploded') else 50,130,W-310 if kind in ('top','side','exploded') else W-100,H-310)
    if kind in ('top','side','exploded'):
        codes={'top':['F02-front','W-wheel-front-R','A-01','A-31','C01-pivot-beam','E-enclosure'], 'side':['H02-grip','E-enclosure','C01-pivot-beam','A-16','W-wheel-front-L'], 'exploded':['PS-16','PC-16','SP-16','PB-16','BR-16','PM-16','IC-16','PE-16','STL-16']}[kind]
        coords=json.loads(image.with_suffix('.json').read_text());codes.sort(key=lambda n:coords[n][1]);xx,yy,sc,box,imh=place
        for k,code in enumerate(codes):
            tx,ty=coords[code];px=xx+(tx-box[0])*sc;py=yy+(box[3]-ty)*sc;ly=y-95-k*(46 if kind=='exploded' else 60)
            c.setFillColor(INK);c.setFont('DV-Bold',10);c.drawString(48,ly,code);c.setStrokeColor(GREY);c.setLineWidth(.55);c.line(160,ly+3,212,ly+3);c.line(212,ly+3,px,py);c.circle(px,py,2,fill=0,stroke=1)
    label(c,'Изображение построено из существующих CAD-тел. Не использовать масштаб растра для изготовления. Крепёж, пружины и рабочие посадки уточняются по реестру КО.',42,95,W-84,10)
    c.showPage()


def cover(c,total):
    W,H=A4;c.setPageSize(A4);c.setFillColor(INK);c.rect(0,H-168,W,168,fill=1,stroke=0)
    c.setFillColor(colors.white);c.setFont('DV-Bold',35);c.drawString(42,H-70,'QULAY');c.setFont('DV',12);c.drawString(44,H-103,'КОНТАКТНЫЙ ПРОФИЛОМЕТР ДОРОЖНОГО ПЕРЕХОДА')
    label(c,'Механическая часть\nи монтаж',42,H-206,W-84,29)
    label(c,'Руководство по сборке стендового образца, установке электроники и контролю монтажа',44,H-293,W-88,13)
    picture(c,ROOT/'mechanical/generated-r1/crossing-iso.png',30,202,W-60,290)
    c.setStrokeColor(RULE);c.line(42,185,W-42,185)
    label(c,'QL-01.R1-ММ • редакция документа D1\n03 октября 2026 • '+str(total)+' страниц • текст A4, чертежи A3',44,163,W-88,10)
    label(c,'Основание: CAD R1, KiCad и таблицы соединений из Eljah/qulay.\nБазовый коммит: '+BASE,44,119,W-88,8.5)
    label(c,'ПРЕДВАРИТЕЛЬНЫЙ КОМПЛЕКТ. Номинальные размеры не являются производственными допусками. Контрольные остановки перед изготовлением указаны в тексте.',44,72,W-88,9)
    c.showPage()

def toc_page(c,pages):
    W,H,y=heading(c,'Содержание и навигация','Переходы по оглавлению доступны в PDF')
    y-=3;left=42;right=315;colw=235
    label(c,'ТЕКСТОВАЯ ЧАСТЬ',left,y,colw,11);label(c,'ЧЕРТЕЖИ И СХЕМЫ A3',right,y,colw,11)
    yy=y-26
    for i,(title,_,_) in enumerate(pages):
        p=para(title,8.8);_,h=p.wrap(colw-28,1000);p.drawOn(c,left,yy-h);c.setFont('DV',8.8);c.drawRightString(left+colw,yy-9,str(i+3));yy-=h+7
    yy=y-26
    for i,(title,_,_) in enumerate(PLATES):
        p=para(title,8.8);_,h=p.wrap(colw-28,1000);p.drawOn(c,right,yy-h);c.setFont('DV',8.8);c.drawRightString(right+colw,yy-9,str(len(pages)+3+i));yy-=h+10
    label(c,'Печатать текст на A4. Листы А01–А13 — A3. Для заготовки рычага лист А07 печатать 100%, без «вписать в страницу»; проверить контрольную линию 100 мм.',right,yy-15,colw,9)
    c.showPage()


def manifest():
    paths=set()
    for _,*sources in SOURCES.values():paths.update(x for x in sources if not x.startswith('http'))
    paths.update(['mechanical/generated-r1/pivot-bracket-5mm.dxf','electronics/generated/encoder/encoder-schematic.pdf','electronics/generated/carrier/carrier-schematic.pdf'])
    for d in ['mechanical/generated-r1']:
        paths.update(str(p.relative_to(ROOT)) for p in (ROOT/d).glob('*.png'))
    data={'source_commit':BASE,'document_revision':'D1','created_date':'2026-10-03','source_files':[{'path':x,'sha256':hashlib.sha256((ROOT/x).read_bytes()).hexdigest()} for x in sorted(paths)],'external_sources':[s for v in SOURCES.values() for s in v[1:] if s.startswith('http')]}
    (HERE/'source-manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8');return data

def main():
    for f in ['r1-top.png','r1-side.png','r1-pivot-exploded.png']:
        if not (HERE/'assets'/f).is_file():raise SystemExit('Run docs/manual/prepare_assets.py first')
    pages=parse_pages();total=2+len(pages)+len(PLATES)
    raw=BytesIO();c=canvas.Canvas(raw,pagesize=A4,pageCompression=1);c.setTitle('Qulay QL-01.R1 — механическая часть и монтаж');c.setAuthor('Qulay project');c.setSubject('CAD-based mechanical assembly and electronics installation; preliminary prototype documentation')
    cover(c,total);toc_page(c,pages)
    for title,sources,blocks in pages:text_page(c,title,sources,blocks)
    for title,sources,kind in PLATES:
        if kind.startswith('schematic'):continue
        plate(c,title,sources,kind)
    c.save();doc=fitz.open(stream=raw.getvalue(),filetype='pdf')
    for title,sources,kind in PLATES[-2:]:
        name=kind.split('-')[1];src=fitz.open(ROOT/f'electronics/generated/{name}/{name}-schematic.pdf')
        pg=doc.new_page(width=landscape(A3)[0],height=landscape(A3)[1]);pg.show_pdf_page(fitz.Rect(20,64,pg.rect.width-20,pg.rect.height-54),src,0)
        buf=BytesIO();o=canvas.Canvas(buf,pagesize=landscape(A3));o.setFillColor(INK);o.setFont('DV-Bold',17);o.drawString(42,landscape(A3)[1]-32,title);o.setFont('DV',9);o.drawString(42,landscape(A3)[1]-50,'Исходная векторная схема KiCad. Источники: '+sources+'. Обозначения контактов — по разделу 12.');o.setFont('DV',8);o.drawString(42,25,'QULAY • QL-01.R1-ММ • D1 • Схема включена без изменения электрических связей.');o.save();over=fitz.open(stream=buf.getvalue(),filetype='pdf');pg.show_pdf_page(pg.rect,over,0)
    assert len(doc)==total,(len(doc),total)
    outline=[[1,'Титульный лист',1],[1,'Содержание',2]]+[[1,t,i+3] for i,(t,_,_) in enumerate(pages)]+[[1,t,3+len(pages)+i] for i,(t,_,_) in enumerate(PLATES)]
    doc.set_toc(outline)
    # Link the source codes/paths and the contents entries without altering source engineering files.
    for i,pg in enumerate(doc):
        pg.insert_text(fitz.Point(pg.rect.width-68,pg.rect.height-27),f'{i+1} / {total}',fontsize=9,color=(.20,.29,.34))
    tp=doc[1]
    for level,title,page in outline[2:]:
        hits=tp.search_for(title)
        for r in hits:tp.insert_link({'kind':fitz.LINK_GOTO,'from':r,'page':page-1})
    registry=doc[23]
    for code,(title,*paths) in SOURCES.items():
        url=paths[0] if paths[0].startswith('http') else 'https://github.com/Eljah/qulay/blob/'+BASE+'/'+paths[0]
        for r in registry.search_for(title):registry.insert_link({'kind':fitz.LINK_URI,'from':r,'uri':url})
    doc.set_metadata({'title':'Qulay QL-01.R1 — механическая часть и монтаж','author':'Qulay project','subject':'Предварительная монтажная документация D1 по CAD R1 и KiCad','keywords':'Qulay, QL-01, CAD, монтаж, механика, KiCad','creator':'ReportLab + PyMuPDF; source commit '+BASE})
    doc.save(OUTPUT,garbage=4,deflate=True)
    manifest();check={'pages':len(doc),'a4_pages':24,'a3_pages':13,'source_commit':BASE,'document_sha256':hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),'note':'Layout and source traceability check; not hardware validation'}
    (HERE/'document-check.json').write_text(json.dumps(check,indent=2),encoding='utf8')
    print(OUTPUT);print(json.dumps(check,indent=2))
if __name__=='__main__':main()
