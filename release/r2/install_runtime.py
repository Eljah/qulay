#!/usr/bin/env python3
"""Idempotent, context-checked integration of R2 into the existing Maven modules.
This keeps canonical sources in software/. It never silently replaces unrelated changes.
"""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[2]
def edit(relative,pairs):
 p=ROOT/relative;s=p.read_text()
 for old,new in pairs:
  if new in s:continue
  if s.count(old)!=1:raise RuntimeError('Unexpected source context: '+relative+' / '+old[:60])
  s=s.replace(old,new)
 p.write_text(s)
for name,dest in [('ContactModel.java','software/core/src/main/java/org/qulay/core'),('ContactModelTest.java','software/core/src/test/java/org/qulay/core'),('WireV2.java','software/agent/src/main/java/org/qulay/agent'),('WireV2Test.java','software/agent/src/test/java/org/qulay/agent')]:
 source=ROOT/'release/r2/runtime'/name;target=ROOT/dest/name
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
edit('software/core/src/main/java/org/qulay/core/Model.java',[
 ('double zeroRad,double[] measuredRad,double[] correctedRad) {','double zeroRad,double[] measuredRad,double[] correctedRad, ContactModel.ContactCalibration contact) {\n  public Channel(double px,double py,double pz,double l,double r,double zero,double[] measured,double[] corrected){this(px,py,pz,l,r,zero,measured,corrected,null);}'),
 ('double yawRad,Double datumZmm,int[] accel20,int[] angle14,int[] flags,boolean attitudeValid) {}','double yawRad,Double datumZmm,int[] accel20,int[] angle14,int[] flags,boolean attitudeValid,R2Raw r2) {\n  public Frame(long seq,long time,long odo,double x,double roll,double pitch,double yaw,Double z,int[] accel,int[] angles,int[] status,boolean attitude){this(seq,time,odo,x,roll,pitch,yaw,z,accel,angles,status,attitude,null);}\n }\n public record R2Raw(int[] contactAdc,int[] diagnostic16,int[] angleOffsetUs,int[] contactOffsetUs,int interlocks) {}'),
 ('if(s.schema!=1)','if(s.schema!=1&&s.schema!=2)'),
 ('for(Channel ch:c.channels){','for(Channel ch:c.channels){\n   if(ch.contact()!=null)ContactModel.validate(ch.contact());'),
 ('for(Frame f:s.frames){','for(Frame f:s.frames){\n   if(s.schema==2&&f.r2()==null||s.schema==1&&f.r2()!=null)throw new IllegalArgumentException("schema and Q2 metadata differ");\n   if(f.r2()!=null){R2Raw q=f.r2();if(q.interlocks()<0||(q.interlocks()&~7)!=0)throw new IllegalArgumentException("Q2 interlocks");\n    for(int[] v:new int[][]{q.contactAdc(),q.diagnostic16(),q.angleOffsetUs(),q.contactOffsetUs()})if(v==null||v.length!=31)throw new IllegalArgumentException("Q2 vectors");\n    for(int j=0;j<31;j++)if(q.contactAdc()[j]<0||q.contactAdc()[j]>4095||q.diagnostic16()[j]<0||q.diagnostic16()[j]>65535||q.angleOffsetUs()[j]<0||q.angleOffsetUs()[j]>20000||q.contactOffsetUs()[j]<0||q.contactOffsetUs()[j]>20000)throw new IllegalArgumentException("Q2 raw range");\n   }')])
edit('software/agent/src/main/java/org/qulay/agent/Wire.java',[
 ('public static Frame parse(String line,Calibration calibration){','public static Frame parse(String line,Calibration calibration){\n  if(line!=null&&line.startsWith("Q2,"))return WireV2.parse(line,calibration);')])
edit('software/agent/src/main/java/org/qulay/agent/Agent.java',[
 ('Survey survey=new Survey(1,','int schema=frames.stream().anyMatch(f->f.r2()!=null)?2:1;\n  Survey survey=new Survey(schema,'),
 ('Q1 contact remains unknown; external height datum absent.','Q1 contact unknown; Q2 contact requires qualified per-channel calibration; independent height datum absent.')])
edit('software/core/src/main/java/org/qulay/core/Geometry.java',[
 ('double[] v=rotate(c.pivotXmm()+c.lengthMm()*Math.cos(angle),c.pivotYmm(),c.pivotZmm()+c.lengthMm()*Math.sin(angle),f.rollRad(),f.pitchRad(),f.yawRad());',
 '''double tip=0;
  if(f.r2()!=null){
   var reading=ContactModel.read(c.contact(),f.r2().contactAdc()[index],angle,(f.r2().interlocks()&4)!=0);tip=reading.displacementMm();
   if(reading.flags()!=0||(f.r2().interlocks()&3)!=3){ok=false;reason=reading.flags()!=0?reading.reason():"Q2_INTERLOCK_OPEN";}
  }
  double[] v=rotate(c.pivotXmm()+c.lengthMm()*Math.cos(angle)-tip*Math.sin(angle),c.pivotYmm(),c.pivotZmm()+c.lengthMm()*Math.sin(angle)+tip*Math.cos(angle),f.rollRad(),f.pitchRad(),f.yawRad());''')])
print('R2 canonical runtime sources installed; historical Q1 remains supported; metrology release remains blocked.')
