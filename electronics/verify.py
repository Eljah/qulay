#!/usr/bin/env python3
"""Actual routes, unsuppressed ERC/DRC and schematic-to-PCB electrical parity."""
from pathlib import Path
import json,subprocess,shutil
import pcbnew as p
import polish
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'electronics/generated'
def run(args,log):
    result=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    log.write_text(result.stdout)
    if result.returncode:print(result.stdout)
    return result.returncode
summary=[];failures=[]
for name in ['encoder','carrier']:
    d=OUT/name;pcb=d/f'{name}.kicad_pcb';session=d/f'{name}.ses';b=p.LoadBoard(str(pcb))
    imported=False
    if session.exists():
        imported=bool(p.ImportSpecctraSES(b,str(session)))
        b.BuildConnectivity()
    if name=='encoder':
        positions={'J1':(9,5.5),'C1':(16.5,12),'C2':(10,19)}
        for f in b.GetFootprints():
            if f.GetReference() in positions:
                x,y=positions[f.GetReference()];f.Reference().SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
    p.SaveBoard(str(pcb),b);polish.finish(d,name)
    statuses={}
    statuses['drc']=run(['kicad-cli','pcb','drc','--format','json','-o',str(d/'drc.json'),str(pcb)],d/'drc.log')
    statuses['erc']=run(['kicad-cli','sch','erc','--format','json','-o',str(d/'erc.json'),str(d/f'{name}.kicad_sch')],d/'erc.log')
    statuses['schematic_pdf']=run(['kicad-cli','sch','export','pdf','-o',str(d/f'{name}-schematic.pdf'),str(d/f'{name}.kicad_sch')],d/'schematic-export.log')
    statuses['pcb_svg']=run(['kicad-cli','pcb','export','svg','--layers','F.Cu,F.SilkS,Edge.Cuts','-o',str(d/f'{name}-pcb.svg'),str(pcb)],d/'pcb-export.log')
    statuses['netlist']=run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(d/'netlist.xml'),str(d/f'{name}.kicad_sch')],d/'netlist-export.log')
    drc=json.loads((d/'drc.json').read_text()) if (d/'drc.json').exists() else {}
    erc=json.loads((d/'erc.json').read_text()) if (d/'erc.json').exists() else {}
    unconnected=len(drc.get('unconnected_items',[]));dv=drc.get('violations',[]);ev=[v for sheet in erc.get('sheets',[]) for v in sheet.get('violations',[])]
    parity=polish.compare(d,name,b) if statuses['netlist']==0 else {'passed':False}
    de=sum(v.get('severity')=='error' for v in dv);ee=sum(v.get('severity')=='error' for v in ev)
    clean=imported and all(v==0 for v in statuses.values()) and 'violations' in drc and 'sheets' in erc and unconnected==0 and de==0 and ee==0 and parity['passed']
    info={'board':name,'router_session_imported':imported,'tracks_and_vias':len(list(b.GetTracks())),'drc_unconnected_items':unconnected,'drc_errors':de,'drc_warnings':len(dv)-de,'erc_errors':ee,'erc_warnings':len(ev)-ee,'netlist_parity':parity,'commands':statuses,'digital_checks_passed':clean,'manufacturing_release':False,'reason':'Digital checks do not validate real power distribution, EMC, contact sensing, magnetic cross-talk, tolerances or metrological accuracy.'}
    fab=d/'prototype-fabrication'
    if fab.exists():shutil.rmtree(fab)
    if clean:
        fab.mkdir();info['gerber_export']=run(['kicad-cli','pcb','export','gerbers','-o',str(fab)+'/',str(pcb)],d/'gerber.log');info['drill_export']=run(['kicad-cli','pcb','export','drill','-o',str(fab)+'/',str(pcb)],d/'drill.log')
        (fab/'NOT_RELEASED.txt').write_text('PROTOTYPE ONLY. No manufacturing release. Check verification.json and hardware review.\n')
    else:failures.append(name)
    (d/'verification.json').write_text(json.dumps(info,indent=2));summary.append(info)
(OUT/'verification-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if failures:raise RuntimeError('Electrical/format checks failed: '+', '.join(failures))
