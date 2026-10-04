package org.qulay.agent;
import org.qulay.core.Model;import static org.qulay.core.Model.*;import java.nio.charset.StandardCharsets;import java.util.zip.CRC32;
public final class Wire {
 private Wire(){}
 public static Frame parse(String line,Calibration calibration){
  if(line!=null&&line.startsWith("Q2,"))return WireV2.parse(line,calibration);
  if(line.length()>1024)throw new IllegalArgumentException("oversized wire line");int star=line.lastIndexOf('*');if(star<0)throw new IllegalArgumentException("missing CRC");String payload=line.substring(0,star);CRC32 crc=new CRC32();crc.update(payload.getBytes(StandardCharsets.US_ASCII));if(Long.parseUnsignedLong(line.substring(star+1).trim(),16)!=crc.getValue())throw new IllegalArgumentException("CRC mismatch");
  String[] a=payload.split(",",-1);if(a.length!=39||!a[0].equals("Q1"))throw new IllegalArgumentException("wire version/length");
  long seq=Long.parseLong(a[1]),us=Long.parseLong(a[2]),odom=Long.parseLong(a[3]),valid=Long.parseUnsignedLong(a[7],16);
  int[] accel={Integer.parseInt(a[4]),Integer.parseInt(a[5]),Integer.parseInt(a[6])},angles=new int[31],flags=new int[31];
  double ax=accel[0]/256000.0,ay=accel[1]/256000.0,az=accel[2]/256000.0,n=Math.sqrt(ax*ax+ay*ay+az*az);
  boolean attitude=n>.98&&n<1.02&&az>0;double roll=Math.atan2(ay,az),pitch=Math.atan2(-ax,Math.hypot(ay,az));
  for(int j=0;j<31;j++){angles[j]=Integer.parseInt(a[j+8]);if(angles[j]<0||angles[j]>16383)throw new IllegalArgumentException("angle word");flags[j]=CONTACT_UNKNOWN;if((valid&(1L<<j))==0)flags[j]|=BAD_SENSOR;if(!attitude)flags[j]|=DYNAMIC;}
  // No validated contact detector or independent height datum is claimed by this board revision.
  return new Frame(seq,us,odom,odom*calibration.odometerMmPerTick(),roll,pitch,0,null,accel,angles,flags,attitude);
 }
}
