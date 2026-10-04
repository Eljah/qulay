#!/usr/bin/env python3
"""KiCad checks on serialized circuit boards, with no rule exclusions."""
from pathlib import Path
import sys,json,subprocess,shutil
import pcbnew as p
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'electronics/generated-r2'
sys.path.insert(0,str(ROOT/'electronics'));import polish

def run(args,log):
 r=subprocess.run(args,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=180);log.write_text(r.stdout)
 if r.returncode:print(r.stdout)
 return r.returncode
summary=[];failures=[]
for name in ['force','adc','carrier_r2','power_good']:
 d=OUT/name;pcb=d/f'{name}.kicad_pcb';b=p.LoadBoard(str(pcb));session=d/f'{name}.ses'
 imported=session.is_file() and bool(p.ImportSpecctraSES(b,str(session)))
 b.BuildConnectivity();p.SaveBoard(str(pcb),b);polish.finish(d,name)
 cmds={
 'drc':['kicad-cli','pcb','drc','--format','json','-o',str(d/'drc.json'),str(pcb)],
 'erc':['kicad-cli','sch','erc','--format','json','-o',str(d/'erc.json'),str(d/f'{name}.kicad_sch')],
 'schematic_pdf':['kicad-cli','sch','export','pdf','-o',str(d/f'{name}-schematic.pdf'),str(d/f'{name}.kicad_sch')],
 'pcb_svg':['kicad-cli','pcb','export','svg','--layers','F.Cu,F.SilkS,Edge.Cuts','-o',str(d/f'{name}-pcb.svg'),str(pcb)],
 'assembly_pdf':['kicad-cli','pcb','export','pdf','--layers','F.Fab,Edge.Cuts','-o',str(d/f'{name}-assembly.pdf'),str(pcb)],
 'netlist':['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(d/'netlist.xml'),str(d/f'{name}.kicad_sch')]}
 codes={key:run(args,d/(key+'.log')) for key,args in cmds.items()}
 drc=json.loads((d/'drc.json').read_text()) if (d/'drc.json').is_file() else {}
 erc=json.loads((d/'erc.json').read_text()) if (d/'erc.json').is_file() else {}
 dv=drc.get('violations',[]);ev=[v for s in erc.get('sheets',[]) for v in s.get('violations',[])];unconnected=len(drc.get('unconnected_items',[]))
 parity=polish.compare(d,name,b) if codes['netlist']==0 else {'passed':False}
 de=sum(v.get('severity')=='error' for v in dv);ee=sum(v.get('severity')=='error' for v in ev)
 clean=bool(imported and all(v==0 for v in codes.values()) and 'violations' in drc and 'sheets' in erc and not unconnected and not dv and not ev and parity['passed'])
 report={'board':name,'router_session_imported':bool(imported),'tracks_and_vias':len(list(b.GetTracks())),'drc_errors':de,'drc_warnings':len(dv)-de,'unconnected':unconnected,'erc_errors':ee,'erc_warnings':len(ev)-ee,'netlist_parity':parity,'commands':codes,'digital_checks_passed':clean,'manufacturing_release':False,'hardware_tested':False,'limits':'No EMC, thermal, force-calibration or actual sensor testing is implied.'}
 fab=d/'prototype-fabrication'
 if fab.exists():shutil.rmtree(fab)
 if clean:
  fab.mkdir();report['gerber_export']=run(['kicad-cli','pcb','export','gerbers','-o',str(fab)+'/',str(pcb)],d/'gerber.log');report['drill_export']=run(['kicad-cli','pcb','export','drill','-o',str(fab)+'/',str(pcb)],d/'drill.log')
  (fab/'PROTOTYPE_ONLY.txt').write_text('Prototype output; physical qualification required.\n')
 else:failures.append(name)
 (d/'verification.json').write_text(json.dumps(report,indent=2));summary.append(report)
(OUT/'verification-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if failures:raise RuntimeError('Board verification failed: '+','.join(failures))
