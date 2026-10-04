#!/usr/bin/env python3
"""R2 hardware: contact displacement board, protected ADC bank and isolated Pico carrier.
KiCad9 native files, one authoritative pin model, checked serialized pad coordinates.
"""
from pathlib import Path
import importlib.util,inspect,re,json,csv,sys
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'electronics/generated-r2';OUT.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(ROOT/'electronics'))
import build as b
import polish
b.OUT=OUT
native=p.PCB_IO_KICAD_SEXPR();p.FootprintSave=lambda lib,fp:native.FootprintSave(str(lib),fp)
old_layout=b.pad_layout

def layout(kind):
    kind=str(kind)
    if kind in ['SOT23','SOT23_5']:
        if kind=='SOT23':return [('1',-1.1,-.95,1,.6,0),('2',-1.1,.95,1,.6,0),('3',1.1,0,1,.6,0)]
        return [('1',-1.1,-.95,1,.6,0),('2',-1.1,0,1,.6,0),('3',-1.1,.95,1,.6,0),('4',1.1,.95,1,.6,0),('5',1.1,-.95,1,.6,0)]
    if kind=='TSSOP20':
        return [(str(i),-2.85,-2.925+(i-1)*.65,1.5,.45,0) for i in range(1,11)]+[(str(i),2.85,2.925-(i-11)*.65,1.5,.45,0) for i in range(11,21)]
    if kind.startswith('SOIC'):
        n=int(kind[4:]);half=n//2;start=(half-1)*1.27/2
        return [(str(i),-2.7,-start+(i-1)*1.27,1.5,.6,0) for i in range(1,half+1)]+[(str(i),2.7,start-(i-half-1)*1.27,1.5,.6,0) for i in range(half+1,n+1)]
    if kind=='R0603':return old_layout('C0603')
    return old_layout(kind)
b.pad_layout=layout
source=inspect.getsource(b.schematic).replace("cx=55+(index%3)*120;cy=55+(index//3)*70","cx=60+(index%4)*180;cy=55+(index//4)*65")
source=source.replace("if c['kind']=='PICO40':cx=70;cy=85","if c['kind']=='PICO40':pass").replace('(paper "A3")','(paper "A1")')
exec(source,b.__dict__)
part=b.part

def connector(ref,name,xy,nets,types=None):return part(ref,name,'H'+str(len(nets)),xy,{str(i+1):n for i,n in enumerate(nets)},types)
def cap(ref,xy,net='SENS_3V3',value='100n X7R'):return part(ref,value,'C0603',xy,{'1':net,'2':'GND'})
def resistor(ref,xy,n1,n2,value):return part(ref,value,'R0603',xy,{'1':n1,'2':n2})
def gate244(ref,xy,pairs):
    pins={'1':'OE_SENS_N','10':'GND','19':'OE_SENS_N','20':'SENS_3V3'};types={'1':'input','19':'input','10':'power_in','20':'power_in'}
    for (a,y),(inn,out) in zip([(2,18),(4,16),(6,14),(8,12),(11,9),(13,7),(15,5),(17,3)],pairs):
        pins[str(a)]=inn;pins[str(y)]=out;types[str(a)]='input';types[str(y)]='tri_state'
    return part(ref,'SN74LVC244APWR','TSSOP20',xy,dict(sorted(pins.items(),key=lambda it:int(it[0]))),types)

def generate(name,components,size,holes):
    b.generate(name,components,size);d=OUT/name;pcb=d/f'{name}.kicad_pcb';board=p.LoadBoard(str(pcb));checks=[]
    for fp in list(board.GetFootprints()):
        if str(fp.GetReference()).startswith('MH'):board.Remove(fp);continue
        expected={v[0]:v[1:] for v in layout(fp.GetFPID().GetLibItemName())}
        for pad in fp.Pads():
            dx,dy,*_=expected[str(pad.GetNumber())];pad.SetFPRelativePosition(b.vec(dx,dy))
        fp.Reference().SetLayer(p.F_Fab);fp.Reference().SetVisible(True)
        p.FootprintSave(d/'QL.pretty',fp)
    for idx,(x,y) in enumerate(holes):
        fp=p.FOOTPRINT(board);fp.SetReference('MH'+str(idx+1));fp.SetFPID(p.LIB_ID('QL','MountingHole_2.2mm'));board.Add(fp);fp.SetPosition(b.vec(x,y))
        pad=p.PAD(fp);pad.SetAttribute(p.PAD_ATTRIB_NPTH);pad.SetShape(p.PAD_SHAPE_CIRCLE);pad.SetSize(b.vec(2.2,2.2));pad.SetDrillSize(b.vec(2.2,2.2));pad.SetLayerSet(b.layer_set([p.F_Cu,p.B_Cu,p.F_Mask,p.B_Mask]));fp.Add(pad);pad.SetFPRelativePosition(b.vec(0,0));fp.Reference().SetVisible(False);p.FootprintSave(d/'QL.pretty',fp)
    txt=p.PCB_TEXT(board);txt.SetText('QULAY R2');txt.SetPosition(b.vec(size[0]/2,size[1]-2));txt.SetTextSize(b.vec(.7,.7));txt.SetTextThickness(p.FromMM(.12));txt.SetLayer(p.F_SilkS);board.Add(txt)
    board.BuildConnectivity();p.SaveBoard(str(pcb),board);board=p.LoadBoard(str(pcb))
    for fp in board.GetFootprints():
        if str(fp.GetReference()).startswith('MH'):continue
        positions={(pad.GetPosition().x,pad.GetPosition().y) for pad in fp.Pads()}
        assert len(positions)==len(list(fp.Pads())),str(fp.GetReference())
        checks.append({'reference':str(fp.GetReference()),'distinct_pads':len(positions)})
    p.ExportSpecctraDSN(board,str(d/f'{name}.dsn'))
    path=d/f'{name}.dsn';dsn=path.read_text();start=dsn.index('(class kicad_default');end=polish.matching(dsn,start);expr=dsn[start:end+1]
    powers=[n for n in ['GND','SENS_3V3','PICO_3V3'] if re.search(r'\b'+n+r'\b',expr)]
    at=expr.index('(circuit');head=expr[:at]
    for net in powers:head=re.sub(r'\b'+net+r'\b','',head)
    expr=head+expr[at:];expr=expr.replace('(clearance 200)','(clearance 150)')
    power='(class QL_POWER '+ ' '.join(powers)+' (circuit (use_via "Via[0-1]_600:300_um")) (rule (width 400) (clearance 150)))'
    dsn=dsn[:start]+expr+'\n'+power+dsn[end+1:];dsn=dsn.replace('(clearance 200.1','(clearance 150.1');path.write_text(dsn)
    polish.finish(d,name)
    (d/'pad-coordinate-checks.json').write_text(json.dumps(checks,indent=2))
    (d/'placement.json').write_text(json.dumps({'board_mm':size,'mount_holes_mm':holes,'components':[{'ref':c['ref'],'xy_mm':c['xy'],'footprint':c['kind'],'value':c['value']} for c in components]},indent=2))

if __name__=='__main__':
    force=[part('U1','DRV5055A3DBZR','SOT23',(9,6),{'1':'SENS_3V3','2':'HALL_RAW','3':'GND'},{'1':'power_in','2':'output','3':'power_in'}),connector('J1','HALL_3V3_GND_OUT',(5,9.5),['SENS_3V3','GND','FORCE_OUT'],{'1':'power_out','2':'power_out','3':'input'}),cap('C1',(4.8,5.5)),resistor('R1',(12.7,5.5),'HALL_RAW','FORCE_OUT','3k3 1%'),cap('C2',(13,8),'FORCE_OUT','1u X7R 6.3V')]
    generate('force',force,(18,12),[(2,2),(16,10)])
    pins={str(i+1):'A'+str(i) for i in range(8)};pins.update({'9':'GND','10':'ADC_CS','11':'ADC_MOSI','12':'ADC_OUT_RAW','13':'ADC_SCK','14':'GND','15':'SENS_3V3','16':'SENS_3V3'})
    types={'9':'power_in','10':'input','11':'input','12':'tri_state','13':'input','14':'power_in','15':'power_in','16':'power_in'}
    adc=[part('U1','MCP3208-BI/SL','SOIC16',(28,27),pins,types),connector('J1','SPI_POWER',(57,29),['SENS_3V3','GND','ADC_SCK','ADC_MOSI','ADC_MISO','ADC_CS'],{'1':'power_out','2':'power_out','3':'output','4':'output','5':'input','6':'output'}),connector('J2','8X_HALL_3V3_GND_SIGNAL',(12,10),[n for j in range(8) for n in ['SENS_3V3','GND','IN7' if j==7 else 'A'+str(j)]])]
    adc.extend([cap('C1',(34,23)),cap('C2',(34,27),value='10u X7R 6.3V'),part('U2','SN74LVC1G125DBVR_IOFF','SOT23_5',(60,38),{'1':'ADC_CS','2':'ADC_OUT_RAW','3':'GND','4':'ADC_MISO','5':'SENS_3V3'},{'1':'input','2':'input','3':'power_in','4':'tri_state','5':'power_in'}),cap('C3',(55,38))])
    for j in range(8):adc.append(resistor('R'+str(j+1),(14 if j<4 else 43,20+(j%4)*5),'A'+str(j),'GND','100k 1% cable-open pull-down'))
    adc.extend([resistor('R9',(67,18),'SENS_3V3','MID','10k 1%'),resistor('R10',(67,22),'MID','GND','10k 1%'),connector('JP1','CH7_1-2_SENSOR_2-3_TEST',(57,18),['IN7','A7','MID'])])
    generate('adc',adc,(80,50),[(4,4),(76,4),(4,46),(76,46)])
    pico={str(i):None for i in range(1,41)}
    for pin in [3,8,13,18,23,28,33,38]:pico[str(pin)]='GND'
    pico.update({'1':'ODO_A','2':'ODO_B','4':'P_SCK0','5':'P_MOSI0','6':'MISO0','7':'P_CS0','9':'P_CS1','10':'P_CS2','11':'P_CS3','14':'P_SCK1','15':'P_MOSI1','16':'MISO1','17':'CS_ADXL','19':'DRDY_ADXL','21':'P_ADC_CS0','22':'P_ADC_CS1','24':'P_ADC_CS2','25':'P_ADC_CS3','26':'LIFT_STOWED_N','27':'POWER_GOOD','29':'SENSOR_ENABLE','36':'PICO_3V3'})
    carrier=[part('U1','Raspberry_Pi_Pico_USB_powered','PICO40',(24,44),pico,{'36':'power_out'}),connector('J1','EXTERNAL_3V3_FUSED_1A',(79,12),['SENS_3V3','GND'],{'1':'power_out','2':'power_out'})]
    carrier.append(gate244('U2',(53,37),[(a,b) for a,b in [('P_SCK0','SCK0_BUF'),('P_MOSI0','MOSI0_BUF'),('P_CS0','CS0'),('P_CS1','CS1'),('P_CS2','CS2'),('P_CS3','CS3'),('P_SCK1','ADC_SCK_BUF'),('P_MOSI1','ADC_MOSI_BUF')]]))
    carrier.append(gate244('U3',(53,68),[('P_ADC_CS'+str(j),'ADC_CS'+str(j)) for j in range(4)]+[('GND',None)]*4))
    carrier.extend([part('U4','SN74LVC125AD_IOFF','SOIC14',(53,104),{'1':'GND','2':'MISO0_RAW','3':'MISO0','4':'GND','5':'MISO1_RAW','6':'MISO1','7':'GND','8':None,'9':'GND','10':'PICO_3V3','11':None,'12':'GND','13':'PICO_3V3','14':'PICO_3V3'},{'1':'input','2':'input','3':'tri_state','4':'input','5':'input','6':'tri_state','7':'power_in','10':'input','13':'input','14':'power_in'}),cap('C1',(61,37)),cap('C2',(61,68)),cap('C3',(61,104),'PICO_3V3'),cap('C4',(88,17),value='10u X7R 6.3V')])
    for bank in range(4):carrier.append(connector('J'+str(bank+2),'ENCODER_BANK_'+str(bank),(76,29+11*bank),['SENS_3V3','GND','CS'+str(bank),'SCK0','MOSI0','MISO0_RAW']))
    carrier.extend([connector('J6','ADXL355_MODULE',(76,81),['PICO_3V3','GND','P_SCK1','P_MOSI1','MISO1_RAW','CS_ADXL','DRDY_ADXL']),connector('J7','ODOMETER_3V3_ONLY',(15,83),['PICO_3V3','GND','ODO_A','ODO_B']),connector('J8','ADC_BANK_FANOUT',(72,96),['SENS_3V3','GND','ADC_SCK','ADC_MOSI','MISO1_RAW','ADC_CS0','ADC_CS1','ADC_CS2','ADC_CS3','GND']),connector('J9','INTERLOCK_GND_LIFT_PG_REMOTE_PULLUP',(74,124),['GND','LIFT_STOWED_N','POWER_GOOD','PICO_3V3'])])
    for j,net in enumerate(['CS0','CS1','CS2','CS3','ADC_CS0','ADC_CS1','ADC_CS2','ADC_CS3']):carrier.append(resistor('R'+str(j+1),(40,16+j*9),'SENS_3V3',net,'10k default-CS-high'))
    carrier.extend([part('Q1','MMBT3904','SOT23',(25,114),{'1':'Q_BASE','2':'GND','3':'OE_SENS_N'},{'1':'passive','2':'passive','3':'open_collector'}),resistor('R9',(18,110),'SENSOR_ENABLE','Q_BASE','10k'),resistor('R10',(18,116),'Q_BASE','GND','100k'),resistor('R11',(32,114),'SENS_3V3','OE_SENS_N','10k'),resistor('R12',(64,125),'POWER_GOOD','GND','100k wire-open-low')])
    carrier.extend([resistor('R13',(53,115),'MISO0_RAW','GND','100k'),resistor('R14',(53,120),'MISO1_RAW','GND','100k')])
    for j,(inn,out,xy) in enumerate([('SCK0_BUF','SCK0',(64,29)),('MOSI0_BUF','MOSI0',(64,33)),('ADC_SCK_BUF','ADC_SCK',(64,45)),('ADC_MOSI_BUF','ADC_MOSI',(64,49))]):carrier.append(resistor('R'+str(j+15),xy,inn,out,'47R source termination'))
    generate('carrier_r2',carrier,(100,140),[(4,4),(96,4),(4,136),(96,136)])
    with (OUT/'contact-harness.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['index','mechanical_id','bank','adc_channel','force_pin1_to','force_pin2_to','force_pin3_to'])
        for j in range(31):w.writerow([j,f'FORCE-BOARD-{j+1:02d}',j//8,j%8,f'ADC{j//8}.J2.{3*(j%8)+1}',f'ADC{j//8}.J2.{3*(j%8)+2}',f'ADC{j//8}.J2.{3*(j%8)+3}'])
    print('R2 contact/ADC/carrier projects generated. Unqualified hardware remains blocked.')
