package org.qulay.agent;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import static org.qulay.core.Model.*;
import org.qulay.core.Json;
import java.io.*;
import java.net.SocketTimeoutException;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.*;
import java.util.zip.CRC32;

class CaptureSafetyTest {
 @TempDir Path temp;
 @Test void readsCrLfAndEof()throws Exception{
  try(var r=new TimedLines(new ByteArrayInputStream("abc\r\nxyz\n".getBytes()),10)){
   assertEquals("abc",r.next(Duration.ofSeconds(1)));assertEquals("xyz",r.next(Duration.ofSeconds(1)));assertNull(r.next(Duration.ofSeconds(1)));
  }
 }
 @Test void boundsUnterminatedLine(){assertThrows(IOException.class,()->{try(var r=new TimedLines(new ByteArrayInputStream("123456".getBytes()),5)){r.next(Duration.ofSeconds(1));}});}
 @Test void detectsTruncatedLine(){assertThrows(EOFException.class,()->{try(var r=new TimedLines(new ByteArrayInputStream("abc".getBytes()),10)){r.next(Duration.ofSeconds(1));}});}
 @Test void rejectsNonAscii(){assertThrows(IOException.class,()->{try(var r=new TimedLines(new ByteArrayInputStream(new byte[]{(byte)200,10}),10)){r.next(Duration.ofSeconds(1));}});}
 @Test void idlePeripheralTimesOut(){assertTimeoutPreemptively(Duration.ofSeconds(3),()->{
  try(var pipe=new PipedInputStream();var writer=new PipedOutputStream(pipe);var r=new TimedLines(pipe,10)){
   assertThrows(SocketTimeoutException.class,()->r.next(Duration.ofMillis(100)));
  }
 });}
 Calibration calibration(){var ch=new ArrayList<Channel>();for(int j=0;j<31;j++)ch.add(new Channel(0,(j-15)*25,0,240,20,0,new double[0],new double[0]));return new Calibration("TEST-ONLY",false,.1,2,.005,ch);}
 String frame(int i){StringBuilder b=new StringBuilder("Q1,"+i+","+(i*10000)+","+i+",0,0,256000,7fffffff");for(int j=0;j<31;j++)b.append(",14336");CRC32 crc=new CRC32();crc.update(b.toString().getBytes(StandardCharsets.US_ASCII));return b+"*"+Long.toHexString(crc.getValue())+"\n";}
 void setup(int frames)throws Exception{
  Json.atomicWrite(temp.resolve("calibration.json"),Json.bytes(calibration()));
  Json.writeChecked(temp.resolve("plan.json"),Json.bytes(new Plan(1,UUID.randomUUID(),"test","DEMO-ONLY-01",List.of(new Target("test",0,0,Mode.CROSSING,"synthetic")))));
  StringBuilder b=new StringBuilder();for(int i=0;i<frames;i++)b.append(frame(i));Files.writeString(temp.resolve("serial.txt"),b);
 }
 String[] args(){return new String[]{"capture",temp.resolve("serial.txt").toString(),temp.resolve("calibration.json").toString(),temp.resolve("plan.json").toString(),"3",temp.resolve("out").toString(),"1","0"};}
 @Test void realAgentReplayProducesCheckedSurvey()throws Exception{
  setup(3);Agent.main(args());
  try(var files=Files.list(temp.resolve("out"))){Path json=files.filter(p->p.toString().endsWith(".json")).findFirst().orElseThrow();Survey s=Json.read(Json.checkedRead(json),Survey.class);validate(s);assertTrue(s.simulated());assertEquals(3,s.frames().size());assertEquals(CONTACT_UNKNOWN,s.frames().getFirst().flags()[0]);}
 }
 @Test void incompleteCaptureCannotBecomeSurvey()throws Exception{
  setup(2);assertThrows(IOException.class,()->Agent.main(args()));
  try(var files=Files.list(temp.resolve("out"))){var names=files.map(p->p.getFileName().toString()).toList();assertEquals(1,names.size());assertTrue(names.getFirst().endsWith(".wire.partial"));}
 }
}
