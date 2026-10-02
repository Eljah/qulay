#!/usr/bin/env python3
"""Generate self-contained KiCad projects from one component/pin model.
Run with the system Python that provides pcbnew. Geometry is mm, all logic 3.3 V.
"""
from pathlib import Path
import uuid,json,csv,math
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'electronics/generated';OUT.mkdir(parents=True,exist_ok=True)
def uid(text):return str(uuid.uuid5(uuid.NAMESPACE_URL,'qulay-ql01/'+text))
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def effects(size=1.0):return f'(effects (font (size {size} {size})))'
def esc(s):return str(s).replace('\\','\\\\').replace('"','\\"')
def part(ref,value,kind,xy,pins,types=None):return dict(ref=ref,value=value,kind=kind,xy=xy,pins=pins,types=types or {})
def pad_layout(kind):
    if kind=='TSSOP14':return [(str(i),-2.85,-1.95+(i-1)*.65,1.5,.45,0) for i in range(1,8)]+[(str(i),2.85,1.95-(i-8)*.65,1.5,.45,0) for i in range(8,15)]
    if kind=='PICO40':return [(str(i),-8.89,-24.13+(i-1)*2.54,1.7,1.7,1.0) for i in range(1,21)]+[(str(i),8.89,24.13-(i-21)*2.54,1.7,1.7,1.0) for i in range(21,41)]
    if kind.startswith('H'):return [(str(i+1),i*2.0,0,1.35,1.35,.75) for i in range(int(kind[1:]))]
    if kind=='C0603':return [('1',-.8,0,.85,.95,0),('2',.8,0,.85,.95,0)]
    if kind=='F1206':return [('1',-1.6,0,1.2,1.8,0),('2',1.6,0,1.2,1.8,0)]
    raise ValueError(kind)
def layer_set(layers):
    s=p.LSET()
    for layer in layers:s.AddLayer(layer)
    return s

def schematic(name,components,directory):
    root=uid(name+'/root');lib=[];instances=[];connections=[]
    for index,c in enumerate(components):
        ref=c['ref'];key=name+'_'+ref;sid=uid(name+'/'+ref);keys=list(c['pins']);n=len(keys);half=(n+1)//2;h=max(6.35,(half+1)*2.54/2)
        cx=55+(index%3)*120;cy=55+(index//3)*70
        if c['kind']=='PICO40':cx=70;cy=85
        elif name=='carrier':cx=190+((index-1)%2)*105;cy=40+((index-1)//2)*44
        pins=[];local=[]
        for i,k in enumerate(keys):
            right=i>=half;j=i-half if right else i;px=20.32 if right else -20.32;py=h-3.81-j*2.54;angle=180 if right else 0
            net=c['pins'][k];label=net if net else 'NC';typ=c['types'].get(k,'passive')
            pins.append(f'(pin {typ} line (at {px} {py} {angle}) (length 5.08) (name "{esc(label)}" {effects(.9)}) (number "{k}" {effects(.9)}))')
            wx=cx+px;wy=cy-py;endx=wx+(5.08 if right else -5.08)
            if net:
                connections.append(f'(wire (pts (xy {wx} {wy}) (xy {endx} {wy})) (stroke (width 0) (type default)) (uuid {uid(key+"/wire/"+k)}))')
                connections.append(f'(label "{esc(net)}" (at {endx} {wy} {0 if right else 180}) (effects (font (size 1 1)) (justify left bottom)) (uuid {uid(key+"/label/"+k)}))')
            else:connections.append(f'(no_connect (at {wx} {wy}) (uuid {uid(key+"/nc/"+k)}))')
            local.append(f'(pin "{k}" (uuid {uid(key+"/pin/"+k)}))')
        lib.append(f'''(symbol "QL:{key}" (pin_names (offset 1)) (in_bom yes) (on_board yes)
          (property "Reference" "{ref}" (at 0 {h+2.54} 0) {effects()})
          (property "Value" "{esc(c['value'])}" (at 0 {-h-2.54} 0) {effects()})
          (symbol "{key}_0_1" (rectangle (start -15.24 {h}) (end 15.24 {-h}) (stroke (width .254) (type default)) (fill (type background))))
          (symbol "{key}_1_1" {''.join(pins)}))''')
        instances.append(f'''(symbol (lib_id "QL:{key}") (at {cx} {cy} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid {sid})
          (property "Reference" "{ref}" (at {cx} {cy-h-3} 0) {effects(1.2)})
          (property "Value" "{esc(c['value'])}" (at {cx} {cy+h+3} 0) {effects(1)})
          (property "Footprint" "QL:{c['kind']}" (at {cx} {cy+h+6} 0) {effects(.8)})
          {''.join(local)} (instances (project "{name}" (path "/{root}" (reference "{ref}") (unit 1)))))''')
    text=f'''(kicad_sch (version 20231120) (generator "eeschema") (uuid {root}) (paper "A3")
      (title_block (title "QULAY QL-01 {name}") (date "2026-10-02") (rev "0.1 PROTOTYPE") (comment 1 "NOT FOR FABRICATION UNTIL DRC/ERC AND HARDWARE REVIEW"))
      (lib_symbols {''.join(lib)}) {''.join(instances)} {''.join(connections)})'''
    (directory/f'{name}.kicad_sch').write_text(text)
    return root

def board(name,components,size,directory,root):
    b=p.BOARD();net_names=sorted({net for c in components for net in c['pins'].values() if net});nets={}
    for net in net_names:n=p.NETINFO_ITEM(b,net);b.Add(n);nets[net]=n
    for c in components:
        x,y=c['xy'];f=p.FOOTPRINT(b);f.SetReference(c['ref']);f.SetValue(c['value']);f.SetFPID(p.LIB_ID('QL',c['kind']));b.Add(f);f.SetPosition(vec(x,y))
        try:
            path=p.KIID_PATH();path.push_back(p.KIID(root));path.push_back(p.KIID(uid(name+'/'+c['ref'])));f.SetPath(path)
        except (AttributeError,TypeError):pass
        for number,dx,dy,sx,sy,drill in pad_layout(c['kind']):
            pad=p.PAD(f);pad.SetNumber(number);pad.SetSize(vec(sx,sy));pad.SetPosition(vec(x+dx,y+dy))
            pad.SetShape(p.PAD_SHAPE_RECT if not drill or number=='1' else p.PAD_SHAPE_CIRCLE)
            if drill:pad.SetAttribute(p.PAD_ATTRIB_PTH);pad.SetDrillSize(vec(drill,drill));pad.SetLayerSet(layer_set([p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask]))
            else:pad.SetAttribute(p.PAD_ATTRIB_SMD);pad.SetLayerSet(layer_set([p.F_Cu,p.F_Paste,p.F_Mask]))
            net=c['pins'].get(number)
            if net:pad.SetNet(nets[net])
            f.Add(pad)
        f.Reference().SetPosition(vec(x,y-3));f.Reference().SetTextSize(vec(.8,.8));f.Reference().SetTextThickness(p.FromMM(.12))
        f.Value().SetVisible(False)
        library=directory/'QL.pretty';library.mkdir(exist_ok=True);p.FootprintSave(str(library),f)
    outline=p.PCB_SHAPE(b);outline.SetShape(p.SHAPE_T_RECT);outline.SetStart(vec(0,0));outline.SetEnd(vec(*size));outline.SetLayer(p.Edge_Cuts);outline.SetWidth(p.FromMM(.05));b.Add(outline)
    # Non-plated alignment/mount holes away from the magnet centre.
    holes=[(2.5,21),(15.5,21)] if name=='encoder' else [(4,4),(76,4),(4,96),(76,96)]
    for i,(x,y) in enumerate(holes):
        f=p.FOOTPRINT(b);f.SetReference('MH'+str(i+1));b.Add(f);f.SetPosition(vec(x,y));pad=p.PAD(f);pad.SetAttribute(p.PAD_ATTRIB_NPTH);pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(vec(2.2,2.2));pad.SetDrillSize(vec(2.2,2.2));pad.SetPosition(vec(x,y));pad.SetLayerSet(layer_set([p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask]));f.Add(pad);f.Reference().SetVisible(False)
    b.BuildConnectivity();p.SaveBoard(str(directory/f'{name}.kicad_pcb'),b)
    p.ExportSpecctraDSN(b,str(directory/f'{name}.dsn'))
    (directory/'fp-lib-table').write_text('(fp_lib_table (lib (name "QL") (type "KiCad") (uri "${KIPRJMOD}/QL.pretty") (options "") (descr "Embedded prototype footprints")))')
    project={'meta':{'filename':name+'.kicad_pro','version':1},'net_settings':{'classes':[{'name':'Default','clearance':.15,'track_width':.2,'via_diameter':.6,'via_drill':.3,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.2,'diff_pair_gap':.25,'diff_pair_via_gap':.25,'bus_width':12,'wire_width':6}],'meta':{'version':3}},'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_hole_clearance':.2,'min_copper_edge_clearance':.25}}}}
    (directory/f'{name}.kicad_pro').write_text(json.dumps(project,indent=2))

def generate(name,components,size):
    d=OUT/name;d.mkdir(parents=True,exist_ok=True);root=schematic(name,components,d);board(name,components,size,d,root)
    with (d/'connections.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['reference','pin','net','pin_type']);w.writerows((c['ref'],pin,net or 'NC',c['types'].get(pin,'passive')) for c in components for pin,net in c['pins'].items())
    with (d/'BOM.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['reference','value','footprint','quantity_per_board']);w.writerows((c['ref'],c['value'],c['kind'],1) for c in components)
    (d/'design-status.json').write_text(json.dumps({'stage':'prototype schematic and PCB; review DRC and router output before manufacture','hardware_validated':False,'analogue_simulated':False,'rated_accuracy_claimed':False,'board_mm':size,'notes':['PCB geometry and circuit do not prove EMC or metrological performance','Carrier is a Pico acquisition adapter; Raspberry Pi Linux SBC is connected through USB','Manufacturing release blocked until pinout, power, routing and harness bench checks']},indent=2))

if __name__=='__main__':
    enc={'1':'CS','2':'SCK','3':'DOUT','4':'DIN','5':'GND','6':None,'7':None,'8':None,'9':None,'10':None,'11':'SENS_3V3','12':'SENS_3V3','13':'GND','14':None}
    generate('encoder',[
        part('U1','AS5048A','TSSOP14',(9,12),enc,{'1':'input','2':'input','3':'tri_state','4':'input','5':'power_in','11':'power_in','12':'power_in','13':'power_in'}),
        part('J1','CHAIN_3V3_ONLY','H6',(4,3),dict(zip(map(str,range(1,7)),['SENS_3V3','GND','CS','SCK','DIN','DOUT'])),{'1':'power_out','2':'power_out','3':'output','4':'output','5':'output','6':'input'}),
        part('C1','100n X7R','C0603',(14,15),{'1':'SENS_3V3','2':'GND'}),
        part('C2','10u 6.3V X7R','C0603',(14,18),{'1':'SENS_3V3','2':'GND'})],(18,24))
    pico={str(i):None for i in range(1,41)}
    for pin in [3,8,13,18,23,28,33,38]:pico[str(pin)]='GND'
    pico.update({'1':'ODO_A','2':'ODO_B','4':'SCK0','5':'MOSI0','6':'MISO0','7':'CS0','9':'CS1','10':'CS2','11':'CS3','14':'SCK1','15':'MOSI1','16':'MISO1','17':'CS_ADXL','19':'DRDY_ADXL','36':'PICO_3V3'})
    components=[part('U1','Raspberry_Pi_Pico_USB_powered','PICO40',(25,47),pico,{'36':'power_out'}),part('J1','EXTERNAL_3V3_CURRENT_LIMITED','H2',(57,12),{'1':'EXT_3V3','2':'GND'},{'1':'power_out','2':'power_out'}),part('F1','PTC_hold_0.75A_review_derating','F1206',(60,18),{'1':'EXT_3V3','2':'SENS_3V3'})]
    for bank in range(4):components.append(part('J'+str(bank+2),'SPI_BANK_'+str(bank),'H6',(54,30+bank*11),dict(zip(map(str,range(1,7)),['SENS_3V3','GND','CS'+str(bank),'SCK0','MOSI0','MISO0']))))
    components.extend([part('J6','ADXL355_3V3_MODULE','H7',(52,80),dict(zip(map(str,range(1,8)),['PICO_3V3','GND','SCK1','MOSI1','MISO1','CS_ADXL','DRDY_ADXL']))),part('J7','ODOMETER_3V3_ONLY','H4',(14,85),{'1':'PICO_3V3','2':'GND','3':'ODO_A','4':'ODO_B'}),part('C1','100n','C0603',(67,18),{'1':'SENS_3V3','2':'GND'}),part('C2','10u 6.3V','C0603',(67,22),{'1':'SENS_3V3','2':'GND'})])
    generate('carrier',components,(80,100))
    with (OUT/'harness.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['channel','bank','sensor_pin','signal','connect_to']);offset=0
        for bank,n in enumerate([8,8,8,7]):
            for k in range(n):
                j=offset+k
                for pin,sig,target in [(1,'3V3',f'carrier.J{bank+2}.1'),(2,'GND',f'carrier.J{bank+2}.2'),(3,'CS',f'carrier.J{bank+2}.3'),(4,'SCK',f'carrier.J{bank+2}.4'),(5,'DIN',f'encoder{j-1:02d}.J1.6' if k else f'carrier.J{bank+2}.5'),(6,'DOUT',f'encoder{j+1:02d}.J1.5' if k<n-1 else f'carrier.J{bank+2}.6')]:w.writerow([j,bank,pin,sig,target])
            offset+=n
    print('KiCad projects generated',OUT)
