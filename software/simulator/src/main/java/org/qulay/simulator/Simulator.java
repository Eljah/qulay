package org.qulay.simulator;
import org.qulay.core.*;import static org.qulay.core.Model.*;import java.util.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;
/** Deterministic geometric forward model. Not an MCU, contact dynamics or RF emulator. */
public final class Simulator {
 public static final UUID PLAN=UUID.nameUUIDFromBytes("QL-01-demo-plan".getBytes(StandardCharsets.UTF_8));
 public static Calibration calibration(){var channels=new ArrayList<Channel>();for(int j=0;j<31;j++)channels.add(new Channel(0,(j-15)*25,0,240,20,0,new double[0],new double[0]));return new Calibration("SYNTHETIC-QL01-NOT-FOR-HARDWARE",false,.1,2,.005,channels);}
 private static double[] center(double a,Channel c,double roll,double pitch){return Geometry.rotate(c.lengthMm()*Math.cos(a),c.pivotYmm(),c.lengthMm()*Math.sin(a),roll,pitch,0);}
 public static Survey scenario(String name){
  Calibration cal=calibration();boolean curb=name.equals("curb150"),reverse=name.equals("reverse");double g=name.equals("steep")?.12:curb?0:.05,gy=name.equals("crossfall")?.04:curb?0:.01;
  var frames=new ArrayList<Frame>();
  for(int i=0;i<=300;i++){
   double x=(reverse?300-i:i)*2,roll=.018*Math.sin(x/170),pitch=.009*Math.cos(x/230),z=220+8*Math.sin(x/150);
   int[] words=new int[31],flags=new int[31];
   for(int j=0;j<31;j++){
    Channel c=cal.channels().get(j);double lo=Math.toRadians(-70),hi=Math.toRadians(20);
    for(int k=0;k<60;k++){double a=(lo+hi)/2;double[] v=center(a,c,roll,pitch);double surface=curb?(v[1]>0?150:0):g*(x+v[0])+gy*v[1];double f=z+v[2]-surface-c.radiusMm()*Math.sqrt(1+g*g+gy*gy);if(f>0)hi=a;else lo=a;}
    double a=(lo+hi)/2;words[j]=((int)Math.round(a*16384/(2*Math.PI)))&16383;
    if(curb&&j==15)flags[j]=NO_CONTACT;
    if(name.equals("dropout")&&i>=100&&i<=130&&j>=12&&j<=18)flags[j]=NO_CONTACT;
   }
   int[] accel={(int)Math.round(-Math.sin(pitch)*256000),(int)Math.round(Math.sin(roll)*Math.cos(pitch)*256000),(int)Math.round(Math.cos(roll)*Math.cos(pitch)*256000)};
   frames.add(new Frame(i,i*10000L,Math.round(x/.1),x,roll,pitch,0,name.equals("no-datum")?null:z,accel,words,flags,true));
  }
  return new Survey(1,UUID.nameUUIDFromBytes(("QL-01-"+name).getBytes(StandardCharsets.UTF_8)),PLAN,"SIMULATOR-NOT-HARDWARE",curb?Mode.ALONG_CURB:Mode.CROSSING,name.equals("no-datum")?Datum.FREE_ROLL:Datum.EXTERNAL_POSE,true,"DEMO-ONLY-01",cal,frames,"Synthetic scenario: "+name+". Ideal crowned contact on planes, known pose, 14-bit quantization; curb boundary marked unobservable.");
 }
 public static void main(String[] args)throws Exception{
  Path out=Path.of(args.length>0?args[0]:"generated/demo");Files.createDirectories(out.resolve("surveys"));Files.createDirectories(out.resolve("reports"));
  Json.atomicWrite(out.resolve("calibration-template.json"),Json.bytes(calibration()));
  Json.atomicWrite(out.resolve("plan.json"),Json.bytes(new Plan(1,PLAN,"Демонстрационный стенд, не полевой объект","DEMO-ONLY-01",List.of(new Target("Виртуальная рампа",55.79,49.12,Mode.CROSSING,"Coordinates are illustrative, not surveyed")))));
  var index=new ArrayList<Map<String,Object>>();
  for(String name:List.of("gentle","steep","crossfall","curb150","dropout","no-datum","reverse")){
   Survey s=scenario(name);Json.writeSurvey(out.resolve("surveys"),s);var report=Geometry.assess(s,demoRules());
   Json.atomicWrite(out.resolve("reports/"+name+".json"),Json.bytes(report));Json.atomicWrite(out.resolve("reports/"+name+".csv"),Geometry.pointsCsv(s).getBytes(StandardCharsets.UTF_8));index.add(Map.of("scenario",name,"id",s.id()));
   System.out.println(name+": "+report.demonstrationDecisions()+", acceptanceEligible="+report.acceptanceEligible());
  }
  Json.atomicWrite(out.resolve("index.json"),Json.bytes(index));
 }
}
