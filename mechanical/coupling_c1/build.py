"""Qulay C1: integral flanged shaft + match-reamed interference dowels.
B-rep manufacturing geometry; nominal CAD is NOT the micrometre fit specification.
Run from any directory. Historical R1 sources are preserved.
"""
from pathlib import Path
import sys, math, json, csv, hashlib, itertools
import cadquery as cq
import ezdxf
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'mechanical'))
import build as base
import revision_b as r1
OUT=Path(__file__).resolve().parent/'generated';OUT.mkdir(parents=True,exist_ok=True)
PINS=[(0.,8.),(1.,-8.)];SCREWS=[(-8.,0.),(8.,0.)]
COLORS={'shaft':(.38,.47,.57),'arm':(.88,.65,.25),'pin':(.75,.24,.18),'screw':(.23,.27,.31)}

def cylinder(r,start,length,x=0,z=0):return base.cyl(r,length,x,start,z)
def annulus(ro,ri,start,length):return cylinder(ro,start,length).cut(cylinder(ri,start-1,length+2))
def arm_xy():
    a=cq.Workplane('XY').center(120,0).slot2D(260,20).extrude(3).val()
    a=a.fuse(cq.Workplane('XY').circle(12).extrude(3).val()).clean()
    for x,z,r in [(0,0,4.025),(240,0,4.05)]+[(x,z,1.5) for x,z in PINS]+[(x,z,1.7) for x,z in SCREWS]:
        a=a.cut(cq.Solid.makeCylinder(r,5,cq.Vector(x,z,-1)))
    # Flange-side chamfer clears the root fillet; assembly-side screw countersinks.
    a=a.cut(cq.Solid.makeCone(4.425,4.025,.4,cq.Vector(0,0,0)))
    for x,z in SCREWS:a=a.cut(cq.Solid.makeCone(1.7,3.1,1.4,cq.Vector(x,z,1.6)))
    return a.clean()

def components():
    shaft=cylinder(12,-12.5,3).fuse(cylinder(4,-9.5,14.5)).clean()
    # One-piece root, not a welded-on washer.
    edges=[e for e in shaft.Edges() if e.geomType()=='CIRCLE' and abs(e.Center().y+9.5)<1e-6 and e.BoundingBox().xlen<8.01]
    if len(edges)!=1:raise ValueError('shaft root edge not found')
    shaft=shaft.fillet(.2,edges)
    for x,z in PINS:shaft=shaft.cut(cylinder(1.5,-13.5,5,x,z))
    for x,z in SCREWS:shaft=shaft.cut(cylinder(1.5,-13.5,5,x,z)) # M3 nominal thread envelope
    # Local z=0 is flange side; countersinks on local z=3 face +Y.
    arm=arm_xy().mirror('XY').rotate((0,0,0),(1,0,0),90).translate((0,-9.5,0))
    parts=[('C1-SHAFT',shaft,COLORS['shaft'],'C45, certificate Rp0.2 >= 300 MPa','one-piece flange; M3 threads represented by major-diameter voids'),
           ('C1-ARM',arm,COLORS['arm'],'steel, certificate Rp0.2 >= 300 MPa','3 mm finish-ground at boss; pin holes machined in matched assembly')]
    for i,(x,z) in enumerate(PINS,1):
        pin=cylinder(1.5,-12.4,5.8,x,z)
        parts.append((f'C1-PIN-{i}',pin,COLORS['pin'],'hardened ground steel dowel','3 mm; finish length 5.80 +/-0.05; ends modelled without grinding relief'))
    for i,(x,z) in enumerate(SCREWS,1):
        screw=cylinder(1.5,-12.3,4.2,x,z).fuse(cq.Solid.makeCone(1.5,3,1.5,cq.Vector(x,-8.1,z),cq.Vector(0,1,0)))
        # Hexagonal key recess, across flats 2 mm. Threads represented by major cylinder.
        socket=cq.Workplane('XZ').center(x,z).polygon(6,4/math.sqrt(3)).extrude(1.2).val().translate((0,-6.5,0))
        screw=screw.cut(socket)
        parts.append((f'C1-SCREW-{i}',screw,COLORS['screw'],'DIN 7991 M3 x 6, class 10.9','finish overall length 5.70 +/-0.05; head <=6.0; nominal countersunk recess 0.10'))
    return parts

def placed(parts,angle,y=0,z=220,tag='16'):
    return [(n+'-'+tag,s.rotate((0,0,0),(0,1,0),-angle).translate((0,y,z)),co,ma,no) for n,s,co,ma,no in parts]

def integrated(mode):
    parts,cut=r1.revised(mode)
    parts=[a for a in parts if not a[0].startswith(('A-','PS-'))]
    unit=components()
    for j in range(31):
        y=(j-15)*25;h=150 if mode=='along-curb' and y>0 else 0
        angle=math.degrees(math.asin((h+20-220)/240))
        parts+=placed(unit,angle,y,220,f'{j+1:02d}')
    return parts

def intersect_check(parts):
    hits=[];candidates=0
    for a,b in itertools.combinations(parts,2):
        aa,bb=a[1].BoundingBox(),b[1].BoundingBox()
        if not all(min(getattr(aa,k+'max'),getattr(bb,k+'max'))-max(getattr(aa,k+'min'),getattr(bb,k+'min'))>1e-5 for k in 'xyz'):continue
        candidates+=1;v=a[1].intersect(b[1]).Volume()
        if v>.01:hits.append({'a':a[0],'b':b[0],'volume_mm3':round(v,5)})
    return {'candidates':candidates,'overlaps':hits}

def export_assy(parts,name):
    a=cq.Assembly(name=name)
    for n,s,c,m,note in parts:
        if not s.isValid():raise ValueError('invalid B-rep '+n)
        a.add(s,name=n,color=cq.Color(*c))
    a.save(str(OUT/(name+'.step')))

def dxf():
    # Cutting outline from the actual B-rep top face, including pilot openings.
    cq.exporters.export(cq.Workplane(obj=arm_xy()).faces('>Z'),str(OUT/'C1-arm-finished-face.dxf'))
    # Explicit coordinate drilling template, not the finished interference-fit tolerances.
    d=ezdxf.new('R2010');d.units=4;m=d.modelspace()
    m.add_circle((0,0),12)
    for x,z in PINS:m.add_circle((x,z),1.5)
    for x,z in SCREWS:m.add_circle((x,z),1.5)
    m.add_circle((0,0),4)
    d.saveas(OUT/'C1-flange-hole-map.dxf')

def calculations():
    r=8.;dp=3.;eng=2.4;A=math.pi*dp**2/4;G=80000.;J=math.pi*8**4/32
    rows=[]
    for T in [2400.,4800.]:
        force=T/r
        rows.append({'torque_Nm':T/1000,'equivalent_force_at_240mm_N':T/240,
        'one_pin_force_N':force,'one_pin_shear_MPa':force/A,'one_pin_bearing_MPa':force/(dp*eng),
        'shaft_nominal_torsion_MPa':16*T/(math.pi*8**3),
        'shaft_upper_bound_elastic_twist_deg':T*14.5/(G*J)*180/math.pi,
        'pin_shear_margin_to_assumed_180MPa':180/(force/A),
        'hole_bearing_margin_to_assumed_150MPa':150/(force/(dp*eng))})
    return {'basis':'closed-form conservative one-pin load assumption; no friction credit, no FEA or fatigue validation',
      'assumed_allowable_pin_shear_MPa':180,'assumed_allowable_hole_bearing_MPa':150,
      'steel_certificate_minimum_yield_MPa':300,'cases':rows,
      'joint_lost_motion_acceptance_deg':.02,'indicator_at_100mm_limit_mm':100*math.tan(math.radians(.02)),
      'measured_diametral_interference_mm':[.002,.004],
      'important':'2.4 Nm is specified coupling design torque, not the measured operating torque of the trolley. 4.8 Nm is a proposed static bench proof, not a performed test.'}

def build():
    unit=components();export_assy(unit,'C1-coupling')
    for n,s,c,m,note in unit:cq.exporters.export(s,str(OUT/(n+'.step')))
    dxf();checks={'nominal_unit':intersect_check(unit),'unit_solids_valid':all(a[1].isValid() for a in unit),
        'interference_fit_model':'nominal coincident pin surfaces; 2..4 micrometre interference is a manufacturing requirement, not a CAD collision',
        'pitch_mm':25,'nominal_flange_to_previous_PCB_clearance_mm':1.0,
        'axial_tolerance_budget_mm':{'flange_location':.05,'PCB_and_mount_stack':.10,'axial_float_limit':.05,'PCB_warp':.10},
        'minimum_clearance_with_allocated_budget_mm':.7,
        'scope':'changed coupling against retained R1 neighbours; not certification of complete trolley',
        'static_modes':{},'sweep':[]}
    for mode in ['crossing','along-curb','datum-rail']:
        parts=integrated(mode)
        selected=[a for a in parts if a[0]=='C01-pivot-beam' or a[0].endswith(('-15','-16','-17','-15a','-15b','-16a','-16b','-17a','-17b'))]
        checks['static_modes'][mode]=intersect_check(selected)
        export_assy(parts,'Qulay-C1-'+mode)
        if mode=='crossing':base.render(parts,OUT/'trolley.png',size=(1900,1350))
    # Every 5 degrees, new coupling vs the retained bearing, bracket, spacer, PCB and neighbours.
    original=r1.revised('crossing')[0]
    env=[a for a in original if (a[0]=='C01-pivot-beam' or a[0].endswith(('-15','-16','-17'))) and not a[0].startswith(('A-','PS-','R-','RA-','RB-'))]
    for ang in range(-70,21,5):
        scan=placed(unit,ang)
        hits=[]
        for a in scan:
            for b in env:
                report=intersect_check([a,b]);hits+=report['overlaps']
        checks['sweep'].append({'angle_deg':ang,'new_vs_retained_overlaps':hits})
    checks['passed']=not checks['nominal_unit']['overlaps'] and all(not v['overlaps'] for v in checks['static_modes'].values()) and all(not v['new_vs_retained_overlaps'] for v in checks['sweep'])
    (OUT/'verification.json').write_text(json.dumps(checks,indent=2))
    (OUT/'calculations.json').write_text(json.dumps(calculations(),indent=2))
    with (OUT/'BOM.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['id','quantity_per_channel','quantity_31_channels','material','note'])
        for n,s,c,m,note in unit:w.writerow([n,1,31,m,note])
    close=[(n,s.intersect(base.box(60,100,80,12,0,0)),c,m,note) for n,s,c,m,note in unit]
    base.render(close,OUT/'joint.png',direction=(.6,1,.65),size=(1600,1200))
    offsets={'C1-ARM':20,'C1-PIN-1':12,'C1-PIN-2':12,'C1-SCREW-1':36,'C1-SCREW-2':36}
    exploded=[(n,s.translate((0,offsets.get(n,0),0)),c,m,note) for n,s,c,m,note in close]
    export_assy(exploded,'C1-exploded');base.render(exploded,OUT/'exploded.png',direction=(.65,1,.65),size=(1750,1300))
    section=[(n,s.intersect(base.box(60,100,40,12,0,-20)),c,m,note) for n,s,c,m,note in close]
    section=[a for a in section if a[1].Volume()>1e-6]
    base.render(section,OUT/'section.png',direction=(0,0,1),size=(1750,950))
    (OUT/'SHA256SUMS').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='SHA256SUMS')+'\n')
    print(json.dumps(checks,indent=2))
    if not checks['passed']:raise RuntimeError('C1 mechanical check failed: see verification.json')
if __name__=='__main__':build()
