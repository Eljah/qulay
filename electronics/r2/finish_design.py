#!/usr/bin/env python3
"""Final R2 EDA entrypoint. 0.20 mm rules; no DRC exclusions. TPS3808 pinout from TI DBV datasheet."""
from pathlib import Path
import sys,re,json
import pcbnew as p
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
# Preserve the historical generator; canonical builds apply the verified orderable part name.
text=(HERE/'build.py').read_text().replace('DRV5055A3DBZR','DRV5055A3QDBZR')
ns={'__file__':str(HERE/'build.py'),'__name__':'__main__'}
exec(compile(text,str(HERE/'build.py'),'exec'),ns)
old_layout=ns['layout'];base=ns['b']
def final_layout(kind):
 if str(kind)=='SOT23_6':
  return [('1',-1.1,-.95,1,.6,0),('2',-1.1,0,1,.6,0),('3',-1.1,.95,1,.6,0),('4',1.1,.95,1,.6,0),('5',1.1,0,1,.6,0),('6',1.1,-.95,1,.6,0)]
 return old_layout(kind)
ns['layout']=final_layout;base.pad_layout=final_layout
part=ns['part'];connector=ns['connector'];cap=ns['cap'];resistor=ns['resistor']
components=[part('U1','TPS3808G33DBVR','SOT23_6',(10,9),{'1':'POWER_GOOD','2':'GND','3':'PICO_3V3','4':None,'5':'SENS_3V3','6':'PICO_3V3'},{'1':'open_collector','2':'power_in','3':'input','5':'input','6':'power_in'}),connector('J1','PICO3V3_GND_SENSE3V3_PG',(7,15),['PICO_3V3','GND','SENS_3V3','POWER_GOOD'],{'1':'power_out','2':'power_out','3':'power_out','4':'input'}),cap('C1',(14,7),'PICO_3V3'),resistor('R1',(10,4.5),'SENS_3V3','POWER_GOOD','10k fail-low pull-up')]
ns['generate']('power_good',components,(20,20),[(2.5,2.5),(17.5,17.5)])
for name in ['force','adc','carrier_r2','power_good']:
 d=ROOT/'electronics/generated-r2'/name;pcb=d/f'{name}.kicad_pcb';board=p.LoadBoard(str(pcb))
 for item in board.GetDrawings():
  if isinstance(item,p.PCB_TEXT):
   item.SetTextSize(p.VECTOR2I(p.FromMM(.9),p.FromMM(.9)))
   if name in ['force','power_good']:item.SetLayer(p.F_Fab)
 if name=='carrier_r2':
  net=board.GetNetsByName()['MOSI0_BUF'];points=[(55.85,36.675),(57.5,36.675),(61.175,33),(63.2,33)]
  for a,z in zip(points,points[1:]):
   tr=p.PCB_TRACK(board);tr.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));tr.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));tr.SetWidth(p.FromMM(.2));tr.SetLayer(p.F_Cu);tr.SetNet(net);board.Add(tr)
 board.BuildConnectivity();p.SaveBoard(str(pcb),board)
 project=d/f'{name}.kicad_pro';j=json.loads(project.read_text())
 for cl in j['net_settings']['classes']:cl['clearance']=.2
 j['board']['design_settings']['rules']['min_clearance']=.2;project.write_text(json.dumps(j,indent=2))
 p.ExportSpecctraDSN(board,str(d/f'{name}.dsn'))
 path=d/f'{name}.dsn';s=path.read_text();s=re.sub(r'\(clearance\s+150(?:\.1)?(?=[ )])','(clearance 200.1',s);s=re.sub(r'\(clearance\s+200(?=[ )])','(clearance 200.1',s);path.write_text(s)
 (d/'routing-policy.json').write_text(json.dumps({'minimum_clearance_mm':.2,'router_clearance_mm':.2001,'violations_excluded':False,'pre_routed_net':'MOSI0_BUF' if name=='carrier_r2' else None},indent=2))
(ROOT/'electronics/generated-r2/power-supervisor-wiring.json').write_text(json.dumps({'device':'TPS3808G33DBVR','threshold_nominal_V':3.07,'release_delay_nominal_ms':20,'CT':'not connected','J1.1':'carrier_r2.J9.4 PICO_3V3','J1.2':'carrier_r2.J9.1 GND','J1.3':'sensor supply after 1A fuse, NOT Pico3V3','J1.4':'carrier_r2.J9.3 POWER_GOOD','pull_up':'10k to SENS_3V3; existing MCU100k pull-down gives low on broken wire or absent sensor power','limits':'Not a complete overvoltage or battery protection circuit; independent fuse/reverse-polarity protection required'},indent=2))
print('R2 final boards including fail-low power supervisor generated')
