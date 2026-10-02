#!/usr/bin/env python3
"""Import actual router sessions, run KiCad checks, preserve failures rather than hiding them."""
from pathlib import Path
import json,subprocess,pcbnew as p
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'electronics/generated'
def run(args,log):
    result=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    log.write_text(result.stdout);return result.returncode
summary=[]
for name in ['encoder','carrier']:
    d=OUT/name;pcb=d/f'{name}.kicad_pcb';session=d/f'{name}.ses';b=p.LoadBoard(str(pcb))
    imported=False
    if session.exists():
        p.ImportSpecctraSES(b,str(session));b.BuildConnectivity();p.SaveBoard(str(pcb),b);imported=True
    statuses={}
    statuses['drc']=run(['kicad-cli','pcb','drc','--format','json','-o',str(d/'drc.json'),str(pcb)],d/'drc.log')
    statuses['erc']=run(['kicad-cli','sch','erc','--format','json','-o',str(d/'erc.json'),str(d/f'{name}.kicad_sch')],d/'erc.log')
    statuses['schematic_pdf']=run(['kicad-cli','sch','export','pdf','-o',str(d/f'{name}-schematic.pdf'),str(d/f'{name}.kicad_sch')],d/'schematic-export.log')
    statuses['pcb_svg']=run(['kicad-cli','pcb','export','svg','--layers','F.Cu,F.Silkscreen,Edge.Cuts','-o',str(d/'views')+'/',str(pcb)],d/'pcb-export.log')
    drc=json.loads((d/'drc.json').read_text()) if (d/'drc.json').exists() else {}
    erc=json.loads((d/'erc.json').read_text()) if (d/'erc.json').exists() else {}
    unconnected=len(drc.get('unconnected_items',[]));violations=drc.get('violations',[])
    info={'board':name,'router_session_imported':imported,'tracks_and_vias':len(list(b.GetTracks())),'drc_unconnected_items':unconnected,'drc_violations':len(violations),'commands':statuses,'manufacturing_release':False,'reason':'Prototype requires independent circuit, power, connector, EMC and magnetic calibration review. DRC/ERC reports are preserved without exclusions.'}
    if imported and 'violations' in drc and unconnected==0 and not any(v.get('severity')=='error' for v in violations):
        fab=d/'prototype-fabrication';fab.mkdir(exist_ok=True)
        info['gerber_export']=run(['kicad-cli','pcb','export','gerbers','-o',str(fab)+'/',str(pcb)],d/'gerber.log')
        info['drill_export']=run(['kicad-cli','pcb','export','drill','-o',str(fab)+'/',str(pcb)],d/'drill.log')
        (fab/'NOT_RELEASED.txt').write_text('PROTOTYPE OUTPUT ONLY. No manufacturing release. Read design-status.json and verification.json.\n')
    (d/'verification.json').write_text(json.dumps(info,indent=2));summary.append(info)
    # A parser/export failure is a build failure, regardless of prototype DRC issues.
    if statuses['schematic_pdf']!=0 or statuses['drc'] not in (0,5):raise RuntimeError(name+': KiCad parse/export failed; inspect logs')
(OUT/'verification-summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
