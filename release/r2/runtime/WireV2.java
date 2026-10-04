package org.qulay.agent;
import org.qulay.core.*;
import static org.qulay.core.Model.*;
import java.util.zip.CRC32;
import java.nio.charset.StandardCharsets;

/** Q2 preserves angle, analog displacement, diagnostics and each bus read timestamp. */
public final class WireV2 {
 private WireV2() {}
 public static Frame parse(String line,Calibration c){
  if(line==null||line.length()>1024)throw new IllegalArgumentException("Q2 line size");
  int star=line.lastIndexOf('*');if(star<0||line.indexOf('*')!=star||!line.substring(star+1).matches("[0-9a-fA-F]{8}"))throw new IllegalArgumentException("Q2 CRC syntax");
  String payload=line.substring(0,star);CRC32 crc=new CRC32();crc.update(payload.getBytes(StandardCharsets.US_ASCII));
  if(crc.getValue()!=Long.parseUnsignedLong(line.substring(star+1),16))throw new IllegalArgumentException("Q2 CRC mismatch");
  String[] a=payload.split(",",-1);if(a.length!=40||!a[0].equals("Q2"))throw new IllegalArgumentException("Q2 field count");
  long seq=Long.parseLong(a[1]),us=Long.parseLong(a[2]),odom=Long.parseLong(a[3]);int aux=Integer.parseInt(a[8]);
  if(seq<0||us<0||aux<0||(aux&~7)!=0)throw new IllegalArgumentException("Q2 header");
  long mask=Long.parseUnsignedLong(a[7],16);if((mask&~0x7fffffffL)!=0)throw new IllegalArgumentException("Q2 validity mask");
  int[] accel={Integer.parseInt(a[4]),Integer.parseInt(a[5]),Integer.parseInt(a[6])};
  for(int v:accel)if(v< -524288||v>524287)throw new IllegalArgumentException("Q2 acceleration range");
  double ax=accel[0]/256000.0,ay=accel[1]/256000.0,az=accel[2]/256000.0,n=Math.sqrt(ax*ax+ay*ay+az*az);
  boolean attitude=n>.98&&n<1.02&&az>0;double roll=Math.atan2(ay,az),pitch=Math.atan2(-ax,Math.hypot(ay,az));
  int[] angle=new int[31],adc=new int[31],diag=new int[31],at=new int[31],ct=new int[31],flags=new int[31];
  for(int j=0;j<31;j++){
   String[] v=a[9+j].split(":",-1);if(v.length!=5)throw new IllegalArgumentException("Q2 channel tuple");
   angle[j]=Integer.parseInt(v[0]);adc[j]=Integer.parseInt(v[1]);diag[j]=Integer.parseInt(v[2]);at[j]=Integer.parseInt(v[3]);ct[j]=Integer.parseInt(v[4]);
   if(angle[j]<0||angle[j]>16383||adc[j]<0||adc[j]>4095||diag[j]<0||diag[j]>65535||at[j]<0||at[j]>20000||ct[j]<0||ct[j]>20000)throw new IllegalArgumentException("Q2 channel range");
   int parity=Integer.bitCount(diag[j])&1;
   if((mask&(1L<<j))==0||parity!=0||(diag[j]&0x4000)!=0||(diag[j]&0x100)==0||(diag[j]&0xe00)!=0)flags[j]|=BAD_SENSOR;
   double alpha;try{alpha=c.channels().get(j).angle(angle[j]);}catch(IllegalArgumentException e){alpha=0;flags[j]|=BAD_SENSOR;}
   flags[j]|=ContactModel.read(c.channels().get(j).contact(),adc[j],alpha,(aux&4)!=0).flags();
   if(!attitude)flags[j]|=DYNAMIC;
   if((aux&3)!=3)flags[j]|=CONTACT_UNKNOWN;
   if(Math.abs(at[j]-ct[j])>5000)flags[j]|=DYNAMIC;
  }
  return new Frame(seq,us,odom,odom*c.odometerMmPerTick(),roll,pitch,0,null,accel,angle,flags,attitude,new R2Raw(adc,diag,at,ct,aux));
 }
}
