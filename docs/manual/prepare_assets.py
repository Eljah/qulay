"""Additional views from the unchanged QL-01.R1 CAD; no generative images."""
from pathlib import Path
import sys,json,math
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'mechanical'))
import revision_b as rev
import build as base
import vtk
OUT=Path(__file__).resolve().parent/'assets';OUT.mkdir(exist_ok=True)

def render(parts,name,direction,focus=None,viewup=(0,0,1)):
    renderer=vtk.vtkRenderer();renderer.SetBackground(1,1,1)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1);window.SetSize(2200,1500);window.AddRenderer(renderer)
    for n,s,color,_,_ in parts:
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(base.solid_mesh(s))
        actor=vtk.vtkActor();actor.SetMapper(mapper);actor.GetProperty().SetColor(*color)
        actor.GetProperty().SetSpecular(.14);actor.GetProperty().SetSpecularPower(14);renderer.AddActor(actor)
    boxes=[s.BoundingBox() for _,s,*_ in parts]
    limits=[(min(getattr(b,k+'min') for b in boxes),max(getattr(b,k+'max') for b in boxes)) for k in 'xyz']
    centre=focus or [sum(pair)/2 for pair in limits]
    cam=renderer.GetActiveCamera();cam.SetFocalPoint(*centre);cam.SetPosition(*[centre[i]+3000*direction[i] for i in range(3)])
    cam.SetViewUp(*viewup);cam.ParallelProjectionOn();renderer.ResetCamera();cam.Zoom(.94);window.Render()
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.Update();writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/(name+'.png')));writer.SetInputConnection(capture.GetOutputPort());writer.Write()
    coordinates={}
    for n,s,*_ in parts:
        c=s.Center();renderer.SetWorldPoint(c.x,c.y,c.z,1);renderer.WorldToDisplay();x,y,_=renderer.GetDisplayPoint();coordinates[n]=[round(x,2),round(1500-y,2)]
    (OUT/(name+'.json')).write_text(json.dumps(coordinates,indent=2))
    window.Finalize()

parts,cuts=rev.revised('crossing')
render(parts,'r1-top',(0,0,1),viewup=(1,0,0))
render(parts,'r1-side',(0,-1,0))
frame=[p for p in parts if p[0].startswith(('F01','F02','F03','W-leg','C01','C-slide'))]
render(frame,'r1-frame',(1.1,-1.4,1))
channel=[p for p in parts if p[0].endswith(('-16','-16a','-16b'))]
render(channel,'r1-channel',(1.0,-1.7,.7))
pivot=[p for p in channel if not p[0].startswith(('A-','R-','RB-','RA-'))]
shift={'PS':-55,'PC':-30,'SP':-30,'PB':-10,'BR':0,'PM':16,'IC':35,'PE':52,'STL':26,'STR':26}
exploded=[(n,s.translate((0,shift[n.rsplit('-',1)[0]],0)),c,m,note) for n,s,c,m,note in pivot]
render(exploded,'r1-pivot-exploded',(1.1,-1.6,.7))
# Only geometric observations; not a claim that every assembly interface is manufacturable.
meta={n:{'bounds_mm':{k:[round(getattr(s.BoundingBox(),k+'min'),5),round(getattr(s.BoundingBox(),k+'max'),5)] for k in 'xyz'},'volume_mm3':round(s.Volume(),5)} for n,s,*_ in parts}
(OUT/'cad-observations.json').write_text(json.dumps(meta,indent=2))
print('CAD document views generated')
