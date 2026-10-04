#!/usr/bin/env python3
"""R2 final routing entry. Keep the existing 0.20 mm rule; do not suppress DRC findings."""
from pathlib import Path
import sys,runpy,re,json
import pcbnew as p
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
# Generate the preserved R2 circuit, then route against exactly the same rules as KiCad.
ns=runpy.run_path(str(HERE/'build.py'),run_name='__main__')
for name in ['force','adc','carrier_r2']:
 d=ROOT/'electronics/generated-r2'/name; pcb=d/f'{name}.kicad_pcb'; b=p.LoadBoard(str(pcb))
 for item in b.GetDrawings():
  if isinstance(item,p.PCB_TEXT):
   item.SetTextSize(p.VECTOR2I(p.FromMM(.9),p.FromMM(.9)))
   # The small force PCB has no spare readable legend area: assembly layer, not over a pad.
   if name=='force':item.SetLayer(p.F_Fab)
 if name=='carrier_r2':
  net=b.GetNetsByName()['MOSI0_BUF']
  points=[(55.85,36.675),(57.5,36.675),(61.175,33),(63.2,33)]
  for a,z in zip(points,points[1:]):
   tr=p.PCB_TRACK(b);tr.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));tr.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));tr.SetWidth(p.FromMM(.2));tr.SetLayer(p.F_Cu);tr.SetNet(net);b.Add(tr)
 b.BuildConnectivity();p.SaveBoard(str(pcb),b)
 project=d/f'{name}.kicad_pro';j=json.loads(project.read_text())
 for cl in j['net_settings']['classes']:cl['clearance']=.2
 j['board']['design_settings']['rules']['min_clearance']=.2
 project.write_text(json.dumps(j,indent=2))
 p.ExportSpecctraDSN(b,str(d/f'{name}.dsn'))
 path=d/f'{name}.dsn';s=path.read_text()
 s=re.sub(r'\(clearance\s+150(?:\.1)?(?=[ )])','(clearance 200.1',s)
 s=re.sub(r'\(clearance\s+200(?=[ )])','(clearance 200.1',s)
 path.write_text(s)
 (d/'routing-policy.json').write_text(json.dumps({'minimum_clearance_mm':.2,'router_clearance_mm':.2001,'violations_excluded':False,'pre_routed_net':'MOSI0_BUF' if name=='carrier_r2' else None},indent=2))
print('R2 final route input generated without lowering clearance rules')
