#!/usr/bin/env python3
"""KiCad 9 entrypoint: explicit native IO plus save/reload coordinate checks."""
from pathlib import Path
import runpy,json,re
import pcbnew as p
HERE=Path(__file__).resolve().parent
_native=p.PCB_IO_KICAD_SEXPR()
def save_footprint(libname,footprint):
    return _native.FootprintSave(str(libname),footprint)
p.FootprintSave=save_footprint
ns=runpy.run_path(str(HERE/'build.py'),run_name='__main__')
vec=ns['vec'];layout=ns['pad_layout'];out=HERE/'generated'
for name in ['encoder','carrier']:
    d=out/name;pcb=d/f'{name}.kicad_pcb';b=p.LoadBoard(str(pcb));checks=[]
    for f in b.GetFootprints():
        if f.GetReference().startswith('MH'):
            f.SetFPID(p.LIB_ID('QL','MountingHole_2.2mm'))
            for pad in f.Pads():pad.SetFPRelativePosition(vec(0,0))
            save_footprint(d/'QL.pretty',f)
            continue
        kind=str(f.GetFPID().GetLibItemName());expected={row[0]:row[1:] for row in layout(kind)}
        for pad in f.Pads():
            dx,dy,*_=expected[str(pad.GetNumber())]
            pad.SetFPRelativePosition(vec(dx,dy))
            world=pad.GetPosition();origin=f.GetPosition()
            assert abs(world.x-origin.x-p.FromMM(dx))<2 and abs(world.y-origin.y-p.FromMM(dy))<2,(f.GetReference(),pad.GetNumber())
        coords={(pad.GetPosition().x,pad.GetPosition().y) for pad in f.Pads()}
        assert len(coords)==len(expected),'overlapping pad origins'
        checks.append({'reference':f.GetReference(),'distinct_pad_positions':len(coords)})
        save_footprint(d/'QL.pretty',f)
    b.BuildConnectivity();p.SaveBoard(str(pcb),b)
    loaded=p.LoadBoard(str(pcb))
    for f in loaded.GetFootprints():
        if f.GetReference().startswith('MH'):continue
        coords={(pad.GetPosition().x,pad.GetPosition().y) for pad in f.Pads()}
        assert len(coords)==len(list(f.Pads())),f.GetReference()+' serialized pad coordinates collapsed'
    p.ExportSpecctraDSN(loaded,str(d/f'{name}.dsn'))
    dsn=(d/f'{name}.dsn').read_text()
    dsn=re.sub(r'\(clearance 200\.1(?=[ )])','(clearance 150.1',dsn)
    (d/f'{name}.dsn').write_text(dsn)
    (d/'pad-coordinate-checks.json').write_text(json.dumps(checks,indent=2))
print('Every PCB pad retains distinct footprint-local coordinates after serialization')
