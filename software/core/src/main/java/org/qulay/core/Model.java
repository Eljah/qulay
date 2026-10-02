package org.qulay.core;

import java.util.*;

/** Units are millimetres, radians, microseconds. All measurements retain their raw words. */
public final class Model {
 private Model() {}
 public static final int CHANNELS=31;
 public static final int BAD_SENSOR=1, NO_CONTACT=2, CONTACT_UNKNOWN=4, DYNAMIC=8, END_STOP=16;
 public enum Mode { CROSSING, ALONG_CURB }
 public enum Datum { FREE_ROLL, DATUM_RAIL, EXTERNAL_POSE }
 public enum Decision { PASS, FAIL, INDETERMINATE, INSUFFICIENT_DATA }
 public record Channel(double pivotXmm,double pivotYmm,double pivotZmm,double lengthMm,double radiusMm,
                       double zeroRad,double[] measuredRad,double[] correctedRad) {
  public double angle(int word) {
   double a=Math.IEEEremainder((word & 0x3fff)*2*Math.PI/16384.0+zeroRad,2*Math.PI);
   if(measuredRad.length==0) return a;
   if(a<measuredRad[0]||a>measuredRad[measuredRad.length-1]) throw new IllegalArgumentException("outside calibrated angular range");
   int k=Arrays.binarySearch(measuredRad,a); if(k>=0)return correctedRad[k]; k=-k-1;
   double t=(a-measuredRad[k-1])/(measuredRad[k]-measuredRad[k-1]);
   return correctedRad[k-1]+t*(correctedRad[k]-correctedRad[k-1]);
  }
 }
 public record Calibration(String id,boolean traceable,double odometerMmPerTick,double expandedHeightUncertaintyMm,
                           double expandedGradeUncertainty,List<Channel> channels) {}
 public record Frame(long sequence,long timeUs,long odometerTicks,double xMm,double rollRad,double pitchRad,
                     double yawRad,Double datumZmm,int[] accel20,int[] angle14,int[] flags,boolean attitudeValid) {}
 public record Survey(int schema,UUID id,UUID planId,String deviceId,Mode mode,Datum datum,boolean simulated,
                      String ruleProfileId,Calibration calibration,List<Frame> frames,String notes) {}
 public record Target(String name,double latitude,double longitude,Mode mode,String notes) {}
 public record Plan(int schema,UUID id,String title,String ruleProfileId,List<Target> targets) {}
 public record RuleProfile(String id,String document,String clause,boolean verifiedNormative,
                           double longitudinalLimit,double crossLimit,double stepLimitMm,double longitudinalBaseMm,
                           double crossBaseMm,double edgeDetectionMm) {}
 public record Point(long sequence,int channel,double x,double y,double z,boolean valid,String reason) {}
 public record Assessment(String algorithm,String ruleProfile,boolean acceptanceEligible,List<String> blockers,
                          Double maximumLongitudinalGrade,Double maximumCrossGrade,Double largestAdjacentLevelChangeMm,
                          double validFraction,Map<String,Decision> demonstrationDecisions,String warning) {}
 public static RuleProfile demoRules() {
  return new RuleProfile("DEMO-ONLY-01","Demonstration, NOT a normative document","not applicable",false,.08,.02,15,200,100,8);
 }
 public static void finite(double v,String label){if(!Double.isFinite(v))throw new IllegalArgumentException(label+" must be finite");}
 public static void validate(Survey s) {
  Objects.requireNonNull(s); if(s.schema!=1)throw new IllegalArgumentException("unsupported schema");
  Objects.requireNonNull(s.id);Objects.requireNonNull(s.planId);Objects.requireNonNull(s.mode);Objects.requireNonNull(s.datum);
  if(s.deviceId==null||s.deviceId.isBlank()||s.deviceId.length()>120)throw new IllegalArgumentException("deviceId");
  if(s.ruleProfileId==null||s.ruleProfileId.length()>120)throw new IllegalArgumentException("ruleProfileId");
  if(s.notes!=null&&s.notes.length()>10000)throw new IllegalArgumentException("notes too long");
  Calibration c=Objects.requireNonNull(s.calibration);
  if(c.id==null||c.id.isBlank()||c.id.length()>200)throw new IllegalArgumentException("calibration id");
  if(c.channels==null||c.channels.size()!=CHANNELS)throw new IllegalArgumentException("31 channel calibrations required");
  finite(c.odometerMmPerTick,"odometry scale");if(c.odometerMmPerTick<=0)throw new IllegalArgumentException("odometry scale");
  finite(c.expandedGradeUncertainty,"grade uncertainty");finite(c.expandedHeightUncertaintyMm,"height uncertainty");
  if(c.expandedGradeUncertainty<0||c.expandedHeightUncertaintyMm<0)throw new IllegalArgumentException("negative uncertainty");
  double previousY=Double.NEGATIVE_INFINITY;
  for(Channel ch:c.channels){
   for(double x:new double[]{ch.pivotXmm,ch.pivotYmm,ch.pivotZmm,ch.lengthMm,ch.radiusMm,ch.zeroRad})finite(x,"geometry");
   if(ch.lengthMm<10||ch.lengthMm>1000||ch.radiusMm<1||ch.radiusMm>100||ch.pivotYmm<=previousY)throw new IllegalArgumentException("channel geometry/order");previousY=ch.pivotYmm;
   if(ch.measuredRad==null||ch.correctedRad==null||ch.measuredRad.length!=ch.correctedRad.length||ch.measuredRad.length==1)throw new IllegalArgumentException("calibration LUT");
   for(int i=0;i<ch.measuredRad.length;i++){finite(ch.measuredRad[i],"LUT");finite(ch.correctedRad[i],"LUT");if(i>0&&(ch.measuredRad[i]<=ch.measuredRad[i-1]||ch.correctedRad[i]<=ch.correctedRad[i-1]))throw new IllegalArgumentException("LUT must increase");}
  }
  if(s.frames==null||s.frames.size()<3||s.frames.size()>20000)throw new IllegalArgumentException("frame count 3..20000");
  long lastSeq=-1,lastTime=-1;
  for(Frame f:s.frames){
   if(f.sequence<=lastSeq||f.timeUs<=lastTime)throw new IllegalArgumentException("sequence/time must increase");lastSeq=f.sequence;lastTime=f.timeUs;
   if(f.angle14==null||f.flags==null||f.angle14.length!=CHANNELS||f.flags.length!=CHANNELS||f.accel20==null||f.accel20.length!=3)throw new IllegalArgumentException("frame vector sizes");
   for(double x:new double[]{f.xMm,f.rollRad,f.pitchRad,f.yawRad})finite(x,"pose");if(f.datumZmm!=null)finite(f.datumZmm,"datum Z");
   if(Math.abs(f.rollRad)>Math.PI||Math.abs(f.pitchRad)>Math.PI||Math.abs(f.yawRad)>2*Math.PI)throw new IllegalArgumentException("angle units must be radians");
   for(int i=0;i<CHANNELS;i++)if(f.angle14[i]<0||f.angle14[i]>16383||f.flags[i]<0||(f.flags[i]&~31)!=0)throw new IllegalArgumentException("raw sensor value/status");
  }
 }
 public static void validate(Plan p){
  if(p.schema!=1||p.id==null||p.title==null||p.title.isBlank()||p.title.length()>300||p.targets==null||p.targets.size()>1000||p.ruleProfileId==null)throw new IllegalArgumentException("invalid plan");
  for(Target t:p.targets){finite(t.latitude,"latitude");finite(t.longitude,"longitude");if(Math.abs(t.latitude)>90||Math.abs(t.longitude)>180||t.name==null||t.name.length()>300||t.mode==null||t.notes!=null&&t.notes.length()>2000)throw new IllegalArgumentException("invalid target");}
 }
}
