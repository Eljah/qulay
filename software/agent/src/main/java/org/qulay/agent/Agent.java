package org.qulay.agent;

import org.qulay.core.*;
import static org.qulay.core.Model.*;
import java.util.*;
import java.nio.file.*;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.TimeUnit;

public final class Agent {
 public static void main(String[] args)throws Exception{
  if(args.length==0)throw new IllegalArgumentException("capture <serial-or-file> <calibration.json> <plan.json> <frame-count> <out-dir> [idle-seconds] [target-index] | sync <survey-dir> <server-url> | pull-plan <uuid> <server-url> <usb-dir>");
  switch(args[0]){
   case "capture"->{if(args.length<6||args.length>8)throw new IllegalArgumentException("capture argument count");capture(args);}
   case "sync"->{if(args.length!=3)throw new IllegalArgumentException("sync argument count");sync(Path.of(args[1]),new ApiClient(args[2],System.getenv("QULAY_TOKEN")));}
   case "pull-plan"->{
    if(args.length!=4)throw new IllegalArgumentException("pull-plan argument count");UUID id=UUID.fromString(args[1]);
    byte[] data=new ApiClient(args[2],System.getenv("QULAY_TOKEN")).get("/api/v1/plans/"+id);
    Plan plan=Json.read(data,Plan.class);validate(plan);if(!id.equals(plan.id()))throw new IOException("server returned a different plan UUID");
    Json.writeChecked(Path.of(args[3],"QULAY","plans",id+".json"),data);
   }
   default->throw new IllegalArgumentException("unknown command");
  }
 }
 static void sync(Path directory,ApiClient api)throws Exception{
  List<String> failed=new ArrayList<>();
  try(var paths=Files.list(directory)){
   for(Path path:paths.filter(x->x.toString().endsWith(".json")&&Files.isRegularFile(x,LinkOption.NOFOLLOW_LINKS)).sorted().toList()){
    try{
     byte[] bytes=Json.checkedRead(path);
     // A receipt on this USB drive does not prove another server still holds the object.
     // Always confirm with the server's idempotent PUT instead of trusting a stale .uploaded marker.
     api.upload(bytes);System.out.println("Confirmed on server: "+path.getFileName());
    }catch(IOException|IllegalArgumentException e){failed.add(path.getFileName()+": "+e.getMessage());System.err.println(failed.getLast());}
   }
  }
  if(!failed.isEmpty())throw new IOException("Synchronization incomplete; "+failed.size()+" file(s) failed. Other files were still attempted.");
 }
 private static void capture(String[] a)throws Exception{
  Path serial=Path.of(a[1]);Calibration cal=Json.read(Json.boundedRead(Path.of(a[2]),Json.MAX_BYTES),Calibration.class);
  Plan plan=Json.read(Json.checkedRead(Path.of(a[3])),Plan.class);validate(plan);
  int count=Integer.parseInt(a[4]),idle=a.length>=7?Integer.parseInt(a[6]):10,target=a.length==8?Integer.parseInt(a[7]):0;
  if(count<3||count>20000||idle<1||idle>120)throw new IllegalArgumentException("frames 3..20000, idle timeout 1..120 seconds");
  if(plan.targets().isEmpty()||target<0||target>=plan.targets().size())throw new IllegalArgumentException("select an existing target in the plan");
  Path out=Path.of(a[5]);Files.createDirectories(out);UUID id=UUID.randomUUID();Path journal=out.resolve(id+".wire.partial");
  var frames=new ArrayList<Frame>();long lastSeq=-1,lastTime=-1;int rejected=0;boolean replay=Files.isRegularFile(serial);
  if(serial.toString().startsWith("/dev/")){
   Process p=new ProcessBuilder("stty","-F",serial.toString(),"115200","raw","-echo").inheritIO().start();
   if(!p.waitFor(5,TimeUnit.SECONDS)){p.destroyForcibly();throw new IOException("stty timeout");}if(p.exitValue()!=0)throw new IOException("stty failed");
  }
  long deadline=System.nanoTime()+TimeUnit.MILLISECONDS.toNanos(30_000L+count*100L);
  try(var lines=new TimedLines(Files.newInputStream(serial),1024);var log=FileChannel.open(journal,StandardOpenOption.WRITE,StandardOpenOption.CREATE_NEW)){
   try{
    while(frames.size()<count){
     if(System.nanoTime()>deadline)throw new IOException("total capture deadline exceeded; raw partial journal retained");
     String line=lines.next(Duration.ofSeconds(idle));if(line==null)break;
     ByteBuffer bytes=ByteBuffer.wrap((line+"\n").getBytes(StandardCharsets.US_ASCII));while(bytes.hasRemaining())log.write(bytes);
     try{
      Frame f=Wire.parse(line,cal);
      if(f.sequence()<=lastSeq||f.timeUs()<=lastTime)throw new IllegalArgumentException("out of order");
      lastSeq=f.sequence();lastTime=f.timeUs();frames.add(f);
      if(frames.size()%100==0)log.force(false);
     }catch(IllegalArgumentException e){
      System.err.println("Rejected frame: "+e.getMessage());
      if(++rejected>Math.max(100,count/10))throw new IOException("too many rejected frames; partial journal retained");
     }
    }
   }finally{log.force(true);}
  }
  if(frames.size()<count)throw new IOException("incomplete pass retained as .wire.partial; no finished survey emitted");
  String device=Objects.toString(System.getenv("QULAY_DEVICE_ID"),"QL01-PICO-PROTOTYPE");
  int schema=frames.stream().anyMatch(f->f.r2()!=null)?2:1;
  Survey survey=new Survey(schema,id,plan.id(),device,plan.targets().get(target).mode(),Datum.FREE_ROLL,replay,plan.ruleProfileId(),cal,frames,
    "Target index="+target+"; source="+(replay?"FILE_REPLAY_NOT_FIELD_EVIDENCE":"USB_CDC")+"; rejected="+rejected+". Q1 contact unknown; Q2 contact requires qualified per-channel calibration; independent height datum absent.");
  Json.writeSurvey(out,survey);Files.move(journal,out.resolve(id+".wire"));
  System.out.println("Saved "+id+"; metrological acceptance remains blocked");
 }
}
