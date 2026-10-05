"""Read real KiCad/CAD/code inputs; generate channel tables and a non-qualified example.
No manufacturing approval or physical test is implied by this document build.
"""
from pathlib import Path
import csv, json, re, math, hashlib
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'docs/sensors/generated';OUT.mkdir(parents=True,exist_ok=True)
BASE='097e60be99069dc5490a207dd999f34820637a1a'

def sexp(text):
    tokens=re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+',text)
    stack=[]; root=None
    for t in tokens:
        if t=='(':
            v=[]
            if stack:stack[-1].append(v)
            else:root=v
            stack.append(v)
        elif t==')':stack.pop()
        else:
            stack[-1].append(json.loads(t) if t.startswith('"') else t)
    if stack or root is None:raise ValueError('Invalid S-expression')
    return root

def child(x,key,default=None):
    return next((n for n in x if isinstance(n,list) and n and n[0]==key),default)

def pcb(rel):
    r=sexp((ROOT/rel).read_text());out={}
    for f in r:
        if not isinstance(f,list) or not f or f[0]!='footprint':continue
        ref=next((n[2] for n in f if isinstance(n,list) and n[:2]==['property','Reference']),None)
        if ref is None:
            z=next((n for n in f if isinstance(n,list) and n[:2]==['fp_text','reference']),None)
            ref=z[2] if z else '?'
        a=child(f,'at');x,y=map(float,a[1:3]);rot=float(a[3]) if len(a)>3 else 0
        pads=[]
        for pad in f:
            if not isinstance(pad,list) or not pad or pad[0]!='pad':continue
            t=child(pad,'at');dx,dy=map(float,t[1:3]);s=child(pad,'size');net=child(pad,'net')
            rr=math.radians(rot)
            pads.append({'pin':pad[1],'u':x+dx*math.cos(rr)+dy*math.sin(rr),'v':y-dx*math.sin(rr)+dy*math.cos(rr),'width':float(s[1]),'height':float(s[2]),'net':net[2] if net else ''})
        out[ref]={'u':x,'v':y,'rotation_deg':rot,'pads':pads,'library':f[1]}
    return out

def connections(rel):
    return {(r['reference'],r['pin']):r['net'] for r in csv.DictReader((ROOT/rel).open())}

def writecsv(name,fields,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

paths={
 'encoder_pcb':'electronics/generated/encoder/encoder.kicad_pcb',
 'encoder_nets':'electronics/generated/encoder/connections.csv',
 'r1_pcb':'electronics/generated/carrier/carrier.kicad_pcb',
 'r1_nets':'electronics/generated/carrier/connections.csv',
 'r2_pcb':'electronics/generated-r2/carrier_r2/carrier_r2.kicad_pcb',
 'r2_nets':'electronics/generated-r2/carrier_r2/connections.csv',
 'force_nets':'electronics/generated-r2/force/connections.csv',
 'adc_nets':'electronics/generated-r2/adc/connections.csv',
 'harness':'electronics/generated/harness.csv',
 'cad':'mechanical/revision_b.py','coupling':'mechanical/coupling_c1/build.py',
 'coupling_note':'mechanical/coupling_c1/README.md',
 'image':'mechanical/coupling_c1/generated/exploded.png',
 'channel_image':'docs/channel/assets/single-channel.png',
 'q1':'firmware/src/main.c','q2':'firmware/r2/main.c','protocol':'firmware/include/protocol.h',
 'model':'software/core/src/main/java/org/qulay/core/Model.java',
 'geometry':'software/core/src/main/java/org/qulay/core/Geometry.java',
 'contact':'software/core/src/main/java/org/qulay/core/ContactModel.java',
 'wire':'software/agent/src/main/java/org/qulay/agent/Wire.java',
 'wire2':'software/agent/src/main/java/org/qulay/agent/WireV2.java',
 'agent':'software/agent/src/main/java/org/qulay/agent/Agent.java',
 'json':'software/core/src/main/java/org/qulay/core/Json.java',
 'desktop':'software/desktop/src/main/java/org/qulay/desktop/DesktopApp.java'
}

def main():
    manifest={k:{'path':v,'sha256':hashlib.sha256((ROOT/v).read_bytes()).hexdigest(),'git_blob':hashlib.sha1(b'blob '+str((ROOT/v).stat().st_size).encode()+b'\0'+(ROOT/v).read_bytes()).hexdigest()} for k,v in paths.items()}
    boards={key:pcb(paths[key+'_pcb']) for key in ['encoder','r1','r2']}
    ns=connections(paths['encoder_nets'])
    expected={'1':'CS','2':'SCK','3':'DOUT','4':'DIN','5':'GND','6':'NC','7':'NC','8':'NC','9':'NC','10':'NC','11':'SENS_3V3','12':'SENS_3V3','13':'GND','14':'NC'}
    assert all(ns['U1',k]==v for k,v in expected.items())
    assert all(ns['J1',str(i)]==v for i,v in enumerate(['SENS_3V3','GND','CS','SCK','DIN','DOUT'],1))
    pin1=next(p for p in boards['encoder']['U1']['pads'] if p['pin']=='1')
    assert abs(pin1['u']-6.15)<1e-5 and abs(pin1['v']-10.05)<1e-5
    j1=boards['encoder']['J1']['pads'];assert len(j1)==6
    for p in j1:assert abs(p['u']-(4+2*(int(p['pin'])-1)))<1e-5 and abs(p['v']-3)<1e-5
    maps=[];wire=[]
    source_harness=list(csv.DictReader((ROOT/paths['harness']).open()))
    original={(int(x['channel']),int(x['sensor_pin'])):x['connect_to'] for x in source_harness}
    for j in range(31):
        b,k=divmod(j,8);n=[8,8,8,7][b];cs=[5,6,7,8][b];physical=[7,9,10,11][b]
        row={'java_index':j,'cad_suffix':f'{j+1:02d}','encoder_label':f'encoder{j:02d}','Y_mm':(j-15)*25,'bank':b,'slot':k,'bank_size':n,'carrier_connector':f'J{b+2}','CS_gpio':cs,'CS_physical_pin':physical,'r2_adc_bank':b,'r2_adc_channel':k,'r2_adc_J2_OUT_pin':3*k+3}
        maps.append(row)
        dest=[f'carrier.J{b+2}.1',f'carrier.J{b+2}.2',f'carrier.J{b+2}.3',f'carrier.J{b+2}.4',f'carrier.J{b+2}.5' if k==0 else f'encoder{j-1:02d}.J1.6',f'carrier.J{b+2}.6' if k==n-1 else f'encoder{j+1:02d}.J1.5']
        for pin,(signal,to) in enumerate(zip(['SENS_3V3','GND','CSn','SCK','DIN','DOUT'],dest),1):
            assert original[j,pin]==to,(j,pin,to,original[j,pin])
            wire.append({'label':f'G{b}-E{j:02d}-P{pin}','from':f'encoder{j:02d}.J1.{pin}','signal':signal,'to':to,'note':'4 common conductors; data is daisy-chained, not parallel'})
    assert len(maps)==31 and len(wire)==186
    for key in ['r1','r2']:
        net=connections(paths[key+'_nets'])
        for b in range(4):
            for pin,sig in [(1,'SENS_3V3'),(2,'GND'),(3,f'CS{b}')]:assert net[f'J{b+2}',str(pin)]==sig
        assert net['J6','1']=='PICO_3V3' and net['J6','2']=='GND'
    orientation={'standard_top_U1_pin1_uv_mm':[pin1['u'],pin1['v']], 'front_transform':'X=9-u; Z-H=v-12; F.Cu faces -Y', 'mounted_front_J1_left_to_right':[6,5,4,3,2,1], 'mounted_back_J1_left_to_right':[1,2,3,4,5,6], 'scope':'Derived coordinate placement; actual connector body and lead dress require mechanical clearance check.'}
    writecsv('channel-map.csv',list(maps[0]),maps);writecsv('encoder-harness.csv',list(wire[0]),wire)
    blank=[dict(j=j,bank=j//8,slot=j%8,cad=f'{j+1:02d}',serial='',sign_checked='',raw_reference='',reference_angle_deg='',zero_rad='',lut_id='',operator='',date='') for j in range(31)]
    writecsv('commissioning-31-channels.csv',list(blank[0]),blank)
    cal={'id':'SENSOR-GUIDE-DEMO-NOT-FOR-HARDWARE','traceable':False,'odometerMmPerTick':0.1,'expandedHeightUncertaintyMm':2.0,'expandedGradeUncertainty':0.005,'channels':[]}
    for j in range(31):
        ch={'pivotXmm':0,'pivotYmm':(j-15)*25,'pivotZmm':0,'lengthMm':240,'radiusMm':20,'zeroRad':0,'measuredRad':[],'correctedRad':[],'contact':None}
        if j==8:
            ch['zeroRad']=-math.pi/2
            ch['measuredRad']=[x*2*math.pi/16384-math.pi/2 for x in [1365,2048,2731]]
            ch['correctedRad']=[math.radians(x) for x in [-60,-45,-30]]
        cal['channels'].append(ch)
    (OUT/'calibration-DEMO.json').write_text(json.dumps(cal,ensure_ascii=False,indent=2)+'\n')
    data={'engineering_baseline':BASE,'paths':paths,'manifest':manifest,'boards':boards,'channels':maps,'orientation':orientation,'checks':{'AS5048_pin_to_net':True,'encoder_pad_positions':True,'31_channels':True,'186_harness_endpoints_match_repository':True,'r1_r2_connector_pin_functions':True,'physical_test':False}}
    (OUT/'engineering-data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    (OUT/'source-manifest.json').write_text(json.dumps({'baseline':BASE,'files':manifest,'physical_tests':False},indent=2))
    print(json.dumps(data['checks'],indent=2))
if __name__=='__main__':main()
