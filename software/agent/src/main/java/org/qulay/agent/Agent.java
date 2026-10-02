package org.qulay.agent;
import org.qulay.core.*;import static org.qulay.core.Model.*;import java.util.*;import java.nio.file.*;import java.io.*;import java.nio.charset.StandardCharsets;
public final class Agent {
 public static void main(String[] args)throws Exception{
  if(args.length==0)throw new IllegalArgumentException("capture <serial-or-file> <calibration.json> <plan.json> <frame-count> <out-dir> | sync <survey-dir> <server-url> | pull-plan <uuid> <server-url> <usb-dir>");
  switch(args[0]){
   case "capture"->{if(args.length!=6)throw new IllegalArgumentException("capture argument count");capture(args);}
   case "sync"->{if(args.length!=3)throw new IllegalArgumentException("sync argument count");var api=new ApiClient(args[2],System.getenv("QULAY_TOKEN"));try(var paths=Files.list(Path.of(args[1]))){for(Path p:paths.filter(x->x.toString().endsWith(".json")).sorted().toList()){Path receipt=p.resolveSibling(p.getFileName()+".uploaded");byte[] b=Json.checkedRead(p);String hash=Json.sha256(b);if(Files.exists(receipt)&&Files.readString(receipt).trim().equals(hash))continue;api.upload(b);Json.atomicWrite(receipt,(hash+"\n").getBytes(StandardCharsets.US_ASCII));System.out.println("Uploaded "+p.getFileName());}}}
   case "pull-plan"->{if(args.length!=4)throw new IllegalArgumentException("pull-plan argument count");UUID id=UUID.fromString(args[1]);byte[] p=new ApiClient(args[2],System.getenv("QULAY_TOKEN")).get("/api/v1/plans/"+id);Plan plan=Json.read(p,Plan.class);validate(plan);Json.atomicWrite(Path.of(args[3],"QULAY","plans",id+".json"),p);}
   default->throw new IllegalArgumentException("unknown command");
  }
 }
 private static void capture(String[] a)throws Exception{
  Path serial=Path.of(a[1]);Calibration cal=Json.read(Files.readAllBytes(Path.of(a[2])),Calibration.class);Plan plan=Json.read(Files.readAllBytes(Path.of(a[3])),Plan.class);validate(plan);
  int count=Integer.parseInt(a[4]);if(count<3||count>20000)throw new IllegalArgumentException("frame count 3..20000");Path out=Path.of(a[5]);Files.createDirectories(out);
  UUID id=UUID.randomUUID();Path journal=out.resolve(id+".wire.partial");var frames=new ArrayList<Frame>();long lastSeq=-1,lastTime=-1;
  if(serial.toString().startsWith("/dev/")){Process p=new ProcessBuilder("stty","-F",serial.toString(),"115200","raw","-echo").inheritIO().start();if(p.waitFor()!=0)throw new IOException("stty failed");}
  try(var in=Files.newBufferedReader(serial,StandardCharsets.US_ASCII);var log=Files.newBufferedWriter(journal,StandardCharsets.US_ASCII,StandardOpenOption.CREATE_NEW)){
   while(frames.size()<count){String line=in.readLine();if(line==null)break;if(line.length()>1024)throw new IOException("oversized serial line");log.write(line);log.newLine();log.flush();try{Frame f=Wire.parse(line,cal);if(f.sequence()<=lastSeq||f.timeUs()<=lastTime)throw new IllegalArgumentException("out of order");lastSeq=f.sequence();lastTime=f.timeUs();frames.add(f);}catch(IllegalArgumentException ex){System.err.println("Rejected frame: "+ex.getMessage());}}
  }
  if(frames.size()<count)throw new IOException("incomplete pass retained as .wire.partial; no finished survey emitted");
  Survey s=new Survey(1,id,plan.id(),"QL01-PICO-PROTOTYPE",plan.targets().isEmpty()?Mode.CROSSING:plan.targets().getFirst().mode(),Datum.FREE_ROLL,false,plan.ruleProfileId(),cal,frames,"Raw hardware capture; contact unknown and no external pose in this firmware revision. Blocking serial capture requires connected streaming hardware.");
  Json.writeSurvey(out,s);Files.move(journal,out.resolve(id+".wire"));System.out.println("Saved "+id+"; strict acceptance remains blocked");
 }
}
