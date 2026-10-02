package org.qulay.agent;

import java.io.*;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.*;

/** Bounds line length and queue memory even when a peripheral never emits a newline. */
public final class TimedLines implements AutoCloseable {
 private record Event(String line,IOException error,boolean end) {}
 private final InputStream input;
 private final BlockingQueue<Event> queue=new ArrayBlockingQueue<>(16);
 private final Thread worker;
 private volatile boolean closed;
 public TimedLines(InputStream input,int maximumBytes){
  if(maximumBytes<1||maximumBytes>65536)throw new IllegalArgumentException("line limit");
  this.input=input;
  worker=Thread.ofPlatform().name("qulay-serial-reader").daemon(true).start(()->{
   try{
    byte[] bytes=new byte[maximumBytes];int used=0;
    while(!closed){
     int value=input.read();
     if(value<0){if(used!=0)throw new EOFException("truncated serial line");queue.put(new Event(null,null,true));return;}
     if(value=='\n'){
      int length=used>0&&bytes[used-1]=='\r'?used-1:used;
      queue.put(new Event(new String(bytes,0,length,StandardCharsets.US_ASCII),null,false));used=0;
     }else{
      if(value>127)throw new IOException("non-ASCII serial byte");
      if(used==maximumBytes)throw new IOException("serial line exceeds "+maximumBytes+" bytes");
      bytes[used++]=(byte)value;
     }
    }
   }catch(IOException e){offerError(e);}catch(InterruptedException e){Thread.currentThread().interrupt();}
  });
 }
 private void offerError(IOException error){try{if(!closed)queue.put(new Event(null,error,false));}catch(InterruptedException e){Thread.currentThread().interrupt();}}
 public String next(Duration timeout)throws IOException,InterruptedException{
  if(timeout.isNegative()||timeout.isZero())throw new IllegalArgumentException("positive timeout required");
  Event event=queue.poll(timeout.toMillis(),TimeUnit.MILLISECONDS);
  if(event==null)throw new SocketTimeoutException("no complete serial frame within "+timeout);
  if(event.error()!=null)throw event.error();return event.end()?null:event.line();
 }
 @Override public void close()throws IOException{closed=true;worker.interrupt();input.close();}
}
