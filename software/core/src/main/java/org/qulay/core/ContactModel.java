package org.qulay.core;

import static org.qulay.core.Model.*;
import java.util.*;

/** Calibration of the parallel-leaf tip. No factory accuracy or contact qualification is invented. */
public final class ContactModel {
 private ContactModel() {}
 public record ContactCalibration(boolean qualified, String certificate,
   double[] adcCounts, double[] displacementMm, double[] angleRad, double[] hangingMm,
   double stiffnessNPerMm, double expandedDisplacementUncertaintyMm) {}
 public record Reading(double displacementMm, double projectedForceN, int flags, String reason) {}
 public static void validate(ContactCalibration c) {
  Objects.requireNonNull(c);
  table(c.adcCounts(),c.displacementMm(),"adc/displacement");
  table(c.angleRad(),c.hangingMm(),"angle/hanging");
  if(c.adcCounts()[0]<65||c.adcCounts()[c.adcCounts().length-1]>4030)throw new IllegalArgumentException("calibrated ADC range");
  int direction=0;
  for(int i=1;i<c.displacementMm().length;i++){
   double difference=c.displacementMm()[i]-c.displacementMm()[i-1];
   int next=Double.compare(difference,0);if(next==0||direction!=0&&direction!=next)throw new IllegalArgumentException("displacement calibration must be monotonic");direction=next;
  }
  finite(c.stiffnessNPerMm(),"tip stiffness");finite(c.expandedDisplacementUncertaintyMm(),"tip uncertainty");
  if(c.stiffnessNPerMm()<=0||c.expandedDisplacementUncertaintyMm()<0)throw new IllegalArgumentException("tip stiffness/uncertainty");
  if(c.qualified()&&(c.certificate()==null||c.certificate().isBlank()))throw new IllegalArgumentException("qualified calibration requires certificate identifier");
 }
 private static void table(double[] x,double[] y,String label){
  if(x==null||y==null||x.length!=y.length||x.length<3||x.length>512)throw new IllegalArgumentException(label);
  for(int i=0;i<x.length;i++){finite(x[i],label);finite(y[i],label);if(i>0&&x[i]<=x[i-1])throw new IllegalArgumentException(label+" input order");}
 }
 public static double interpolate(double x,double[] axis,double[] values){
  if(!Double.isFinite(x)||x<axis[0]||x>axis[axis.length-1])throw new IllegalArgumentException("outside calibrated range");
  int k=Arrays.binarySearch(axis,x);if(k>=0)return values[k];k=-k-1;
  double t=(x-axis[k-1])/(axis[k]-axis[k-1]);return values[k-1]+t*(values[k]-values[k-1]);
 }
 public static Reading read(ContactCalibration c,int adc,double angle,boolean encoderQuiet){
  if(adc<65||adc>4030)return new Reading(0,0,BAD_SENSOR,"CONTACT_ADC_RAIL_OR_DISCONNECTED");
  if(c==null)return new Reading(0,0,CONTACT_UNKNOWN,"CONTACT_CALIBRATION_MISSING");
  validate(c);double d,h;
  try{d=interpolate(adc,c.adcCounts(),c.displacementMm());h=interpolate(angle,c.angleRad(),c.hangingMm());}
  catch(IllegalArgumentException e){return new Reading(0,0,CONTACT_UNKNOWN,"CONTACT_OUTSIDE_CALIBRATION");}
  double force=(d-h)*c.stiffnessNPerMm();
  if(!c.qualified())return new Reading(d,force,CONTACT_UNKNOWN,"CONTACT_CALIBRATION_NOT_QUALIFIED");
  if(d<=-.19||d>=.44)return new Reading(d,force,END_STOP,"TIP_DEFLECTION_END_STOP");
  if(!encoderQuiet)return new Reading(d,force,DYNAMIC,"ENCODER_NOT_QUIET_300MS");
  double u=c.expandedDisplacementUncertaintyMm()*c.stiffnessNPerMm();
  if(force+u<.2)return new Reading(d,force,NO_CONTACT,"PROJECTED_CONTACT_FORCE_TOO_LOW");
  if(force-u<.2)return new Reading(d,force,CONTACT_UNKNOWN,"CONTACT_FORCE_GUARD_BAND");
  return new Reading(d,force,0,"CALIBRATED_CONTACT_ESTIMATE_NOT_CERTIFICATION");
 }
}
