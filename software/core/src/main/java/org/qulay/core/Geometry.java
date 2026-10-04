package org.qulay.core;
import static org.qulay.core.Model.*;
import java.util.*;

/** R = Rz(yaw) Ry(pitch) Rx(roll); right handed. No unobservable heave is invented. */
public final class Geometry {
 private Geometry(){}
 public static double[] rotate(double x,double y,double z,double roll,double pitch,double yaw){
  double a=y*Math.cos(roll)-z*Math.sin(roll),b=y*Math.sin(roll)+z*Math.cos(roll);
  double c=x*Math.cos(pitch)+b*Math.sin(pitch),d=-x*Math.sin(pitch)+b*Math.cos(pitch);
  return new double[]{c*Math.cos(yaw)-a*Math.sin(yaw),c*Math.sin(yaw)+a*Math.cos(yaw),d};
 }
 public static Point center(Frame f,Channel c,int index){
  String reason="";boolean ok=f.attitudeValid()&&f.flags()[index]==0;
  if(!f.attitudeValid())reason="ATTITUDE_INVALID";else if(f.flags()[index]!=0)reason="SENSOR_OR_CONTACT_FLAGS_"+f.flags()[index];
  double angle;try{angle=c.angle(f.angle14()[index]);}catch(IllegalArgumentException e){return new Point(f.sequence(),index,0,0,0,false,"OUTSIDE_CALIBRATION");}
  if(angle<Math.toRadians(-70)||angle>Math.toRadians(20)){ok=false;reason="MECHANICAL_RANGE";}
  double tip=0;
  if(f.r2()!=null){
   var reading=ContactModel.read(c.contact(),f.r2().contactAdc()[index],angle,(f.r2().interlocks()&4)!=0);tip=reading.displacementMm();
   if(reading.flags()!=0||(f.r2().interlocks()&3)!=3){ok=false;reason=reading.flags()!=0?reading.reason():"Q2_INTERLOCK_OPEN";}
  }
  double[] v=rotate(c.pivotXmm()+c.lengthMm()*Math.cos(angle)-tip*Math.sin(angle),c.pivotYmm(),c.pivotZmm()+c.lengthMm()*Math.sin(angle)+tip*Math.cos(angle),f.rollRad(),f.pitchRad(),f.yawRad());
  return new Point(f.sequence(),index,f.xMm()+v[0],v[1],(f.datumZmm()==null?0:f.datumZmm())+v[2],ok,reason);
 }
 public static Point[][] centers(Survey s){
  Model.validate(s);Point[][] p=new Point[s.frames().size()][CHANNELS];
  for(int i=0;i<p.length;i++)for(int j=0;j<CHANNELS;j++)p[i][j]=center(s.frames().get(i),s.calibration().channels().get(j),j);return p;
 }
 /** Smooth-patch spherical/crowned roller correction using two independent local tangents.
  * Discontinuities are masked, never bridged. Z in FREE_ROLL remains relative per frame. */
 public static Point[][] contacts(Survey s,double jumpMm){
  Point[][] c=centers(s),p=new Point[c.length][CHANNELS];boolean datum=s.datum()!=Datum.FREE_ROLL&&s.frames().stream().allMatch(f->f.datumZmm()!=null);
  for(int i=0;i<c.length;i++)for(int j=0;j<CHANNELS;j++){
   Point q=c[i][j];double r=s.calibration().channels().get(j).radiusMm();
   if(!q.valid()){p[i][j]=q;continue;}
   if(!datum){p[i][j]=new Point(q.sequence(),j,q.x(),q.y(),q.z()-r,true,"RELATIVE_Z_VERTICAL_RADIUS_APPROXIMATION");continue;}
   int lo=Math.max(0,i-1),hi=Math.min(c.length-1,i+1),left=Math.max(0,j-1),right=Math.min(CHANNELS-1,j+1);
   Point a=c[lo][j],b=c[hi][j],d=c[i][left],e=c[i][right];
   if(!a.valid()||!b.valid()||!d.valid()||!e.valid()||Math.abs(b.z()-a.z())>jumpMm||Math.abs(e.z()-d.z())>jumpMm||Math.abs(s.frames().get(hi).sequence()-s.frames().get(lo).sequence())>2){p[i][j]=new Point(q.sequence(),j,q.x(),q.y(),q.z(),false,"EDGE_OR_NEIGHBOUR_GAP");continue;}
   double ux=b.x()-a.x(),uy=b.y()-a.y(),uz=b.z()-a.z(),vx=e.x()-d.x(),vy=e.y()-d.y(),vz=e.z()-d.z();
   double nx=uy*vz-uz*vy,ny=uz*vx-ux*vz,nz=ux*vy-uy*vx,n=Math.sqrt(nx*nx+ny*ny+nz*nz);
   if(n<1e-8){p[i][j]=new Point(q.sequence(),j,q.x(),q.y(),q.z(),false,"DEGENERATE_NORMAL");continue;}if(nz<0)n=-n;
   nx/=n;ny/=n;nz/=n;
   if(Math.abs(ny)>.30||nz<.8){p[i][j]=new Point(q.sequence(),j,q.x(),q.y(),q.z(),false,"CROWN_CONTACT_RANGE");continue;}
   p[i][j]=new Point(q.sequence(),j,q.x()-r*nx,q.y()-r*ny,q.z()-r*nz,true,"SMOOTH_PATCH_ESTIMATE");
  }return p;
 }
 public static Decision upperLimit(Double value,double uncertainty,double limit){
  if(value==null)return Decision.INSUFFICIENT_DATA;
  finite(value,"value");finite(uncertainty,"uncertainty");finite(limit,"limit");if(uncertainty<0)throw new IllegalArgumentException("negative uncertainty");
  if(value+uncertainty<=limit)return Decision.PASS;if(value-uncertainty>limit)return Decision.FAIL;return Decision.INDETERMINATE;
 }
 public static Assessment assess(Survey s,RuleProfile rules){
  validate(s);if(!rules.id().equals(s.ruleProfileId()))throw new IllegalArgumentException("unknown/mismatched rule profile");
  var blocks=new ArrayList<String>();if(s.simulated())blocks.add("SIMULATION_NOT_FIELD_EVIDENCE");if(!s.calibration().traceable())blocks.add("CALIBRATION_NOT_TRACEABLE");if(!rules.verifiedNormative())blocks.add("RULES_NOT_NORMATIVE");
  boolean datum=s.datum()!=Datum.FREE_ROLL&&s.frames().stream().allMatch(f->f.datumZmm()!=null);
  if(!datum)blocks.add("NO_INDEPENDENT_HEIGHT_DATUM");
  // QL-01 contains no validated contact detector, temperature qualification or normal uncertainty model.
  blocks.add("PROTOTYPE_METROLOGY_NOT_VALIDATED");
  Point[][] c=centers(s),p=contacts(s,rules.edgeDetectionMm());Double longitudinal=null,cross=null,step=null;long valid=0;
  for(int i=0;i<p.length;i++)for(int j=0;j<CHANNELS;j++){
   if(p[i][j].valid())valid++;
   if(j<CHANNELS-1&&c[i][j].valid()&&c[i][j+1].valid()){
    double dz=Math.abs(c[i][j+1].z()-c[i][j].z());if(dz>rules.edgeDetectionMm())step=step==null?dz:Math.max(step,dz);
   }
   // Full calibrated bases, never a derivative across a missing channel or an edge.
   int right=j;while(right<CHANNELS-1&&p[i][right].valid()&&Math.abs(p[i][right].y()-p[i][j].y())<rules.crossBaseMm())right++;
   boolean good=p[i][j].valid()&&p[i][right].valid();for(int k=j;k<right;k++)if(!p[i][k].valid()||Math.abs(c[i][k+1].z()-c[i][k].z())>rules.edgeDetectionMm())good=false;
   double dy=Math.abs(p[i][right].y()-p[i][j].y());if(good&&dy>=rules.crossBaseMm()*.99){double g=Math.abs((p[i][right].z()-p[i][j].z())/dy);cross=cross==null?g:Math.max(cross,g);}
   if(datum&&p[i][j].valid()){
    int end=i+1;boolean continuous=true;while(end<p.length&&Math.abs(p[end][j].x()-p[i][j].x())<rules.longitudinalBaseMm()){
     if(!p[end][j].valid()||s.frames().get(end).sequence()!=s.frames().get(end-1).sequence()+1||Math.abs(s.frames().get(end).xMm()-s.frames().get(end-1).xMm())>5)continuous=false;end++;
    }
    if(end<p.length&&continuous&&p[end][j].valid()){
     double dx=Math.abs(p[end][j].x()-p[i][j].x());if(dx>=rules.longitudinalBaseMm()*.99&&dx<rules.longitudinalBaseMm()+5){double g=Math.abs((p[end][j].z()-p[i][j].z())/dx);longitudinal=longitudinal==null?g:Math.max(longitudinal,g);}
    }
   }
  }
  double fraction=(double)valid/(CHANNELS*p.length);if(fraction<.999)blocks.add("GAPS_OR_INVALID_CONTACTS_PRESENT");
  Map<String,Decision> d=new LinkedHashMap<>();d.put("longitudinal",upperLimit(longitudinal,s.calibration().expandedGradeUncertainty(),rules.longitudinalLimit()));d.put("cross",upperLimit(cross,s.calibration().expandedGradeUncertainty(),rules.crossLimit()));d.put("adjacentLevelChange",upperLimit(step,s.calibration().expandedHeightUncertaintyMm(),rules.stepLimitMm()));
  return new Assessment("QL-01-0.1",rules.id(),blocks.isEmpty(),List.copyOf(blocks),longitudinal,cross,step,fraction,d,"DEMONSTRATION ONLY. Adjacent level change is not a certified step-height measurement. No detected jump is not proof of absence. FREE_ROLL transverse values use a vertical-radius approximation.");
 }
 public static String pointsCsv(Survey s){var out=new StringBuilder("sequence,channel,x_mm,y_mm,z_mm,valid,meaning\n");for(Point[] row:contacts(s,8))for(Point p:row)out.append(String.format(Locale.ROOT,"%d,%d,%.6f,%.6f,%.6f,%s,%s%n",p.sequence(),p.channel(),p.x(),p.y(),p.z(),p.valid(),p.reason()));return out.toString();}
}
