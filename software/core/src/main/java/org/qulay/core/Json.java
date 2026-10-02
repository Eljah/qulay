package org.qulay.core;
import com.fasterxml.jackson.core.*;
import com.fasterxml.jackson.databind.*;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.HexFormat;
public final class Json {
 private Json(){}
 public static final ObjectMapper MAPPER=new ObjectMapper(JsonFactory.builder().streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(40).maxStringLength(20000).maxNumberLength(100).build()).build()).enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES).enable(DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES);
 public static byte[] bytes(Object x)throws IOException{return MAPPER.writerWithDefaultPrettyPrinter().writeValueAsBytes(x);}
 public static <T>T read(byte[] b,Class<T> type)throws IOException{return MAPPER.readValue(b,type);}
 public static String sha256(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException e){throw new AssertionError(e);}}
 public static void atomicWrite(Path target,byte[] bytes)throws IOException{
  Files.createDirectories(target.toAbsolutePath().getParent());Path tmp=Files.createTempFile(target.toAbsolutePath().getParent(),".qulay-",".partial");
  try{try(var out=java.nio.channels.FileChannel.open(tmp,StandardOpenOption.WRITE)){java.nio.ByteBuffer b=java.nio.ByteBuffer.wrap(bytes);while(b.hasRemaining())out.write(b);out.force(true);}try{Files.move(tmp,target,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}catch(AtomicMoveNotSupportedException e){Files.move(tmp,target,StandardCopyOption.REPLACE_EXISTING);}}finally{Files.deleteIfExists(tmp);}
 }
 public static void writeSurvey(Path directory,Model.Survey survey)throws IOException{
  Model.validate(survey);byte[] data=bytes(survey);Path p=directory.resolve(survey.id()+".json");
  atomicWrite(p,data);atomicWrite(directory.resolve(survey.id()+".sha256"),(sha256(data)+"\n").getBytes(java.nio.charset.StandardCharsets.US_ASCII));
 }
 public static byte[] checkedRead(Path path)throws IOException{
  if(Files.size(path)>32L*1024*1024)throw new IOException("file exceeds 32 MiB");byte[] data=Files.readAllBytes(path);
  String name=path.getFileName().toString();if(!name.endsWith(".json"))throw new IOException("expected .json");
  Path hash=path.resolveSibling(name.substring(0,name.length()-5)+".sha256");
  if(!Files.isRegularFile(hash)||!sha256(data).equals(Files.readString(hash).trim()))throw new IOException("missing or mismatched SHA-256 sidecar");return data;
 }
}
