package org.qulay.core;

import com.fasterxml.jackson.core.*;
import com.fasterxml.jackson.databind.*;
import com.fasterxml.jackson.databind.json.JsonMapper;
import java.io.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.*;
import java.util.HexFormat;

public final class Json {
 private Json() {}
 public static final int MAX_BYTES=32*1024*1024;
 public static final ObjectMapper MAPPER=JsonMapper.builder(JsonFactory.builder()
  .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
  .streamReadConstraints(StreamReadConstraints.builder().maxNestingDepth(40).maxStringLength(20000).maxNumberLength(100).build()).build())
  .enable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES,DeserializationFeature.FAIL_ON_NULL_FOR_PRIMITIVES,DeserializationFeature.FAIL_ON_TRAILING_TOKENS)
  .disable(DeserializationFeature.ACCEPT_FLOAT_AS_INT)
  .disable(MapperFeature.ALLOW_COERCION_OF_SCALARS).build();
 public static byte[] bytes(Object x)throws IOException{return MAPPER.writerWithDefaultPrettyPrinter().writeValueAsBytes(x);}
 public static <T>T read(byte[] b,Class<T> type)throws IOException{if(b.length>MAX_BYTES)throw new IOException("JSON exceeds 32 MiB");return MAPPER.readValue(b,type);}
 public static String sha256(byte[] bytes){try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}catch(NoSuchAlgorithmException e){throw new AssertionError(e);}}
 public static byte[] boundedRead(Path path,int limit)throws IOException{
  if(limit<0||limit>MAX_BYTES)throw new IllegalArgumentException("invalid read limit");
  if(!Files.isRegularFile(path,LinkOption.NOFOLLOW_LINKS))throw new IOException("expected regular non-symlink file: "+path);
  try(InputStream in=Files.newInputStream(path,LinkOption.NOFOLLOW_LINKS)){byte[] data=in.readNBytes(limit+1);if(data.length>limit)throw new IOException("file exceeds byte limit: "+path);return data;}
 }
 public static void atomicWrite(Path target,byte[] bytes)throws IOException{
  Files.createDirectories(target.toAbsolutePath().getParent());Path tmp=Files.createTempFile(target.toAbsolutePath().getParent(),".qulay-",".partial");
  try{try(var out=java.nio.channels.FileChannel.open(tmp,StandardOpenOption.WRITE)){java.nio.ByteBuffer b=java.nio.ByteBuffer.wrap(bytes);while(b.hasRemaining())out.write(b);out.force(true);}try{Files.move(tmp,target,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);}catch(AtomicMoveNotSupportedException e){Files.move(tmp,target,StandardCopyOption.REPLACE_EXISTING);}}finally{Files.deleteIfExists(tmp);}
 }
 public static void writeChecked(Path target,byte[] bytes)throws IOException{
  String name=target.getFileName().toString();if(!name.endsWith(".json"))throw new IllegalArgumentException("expected .json");
  atomicWrite(target,bytes);atomicWrite(target.resolveSibling(name.substring(0,name.length()-5)+".sha256"),(sha256(bytes)+"\n").getBytes(StandardCharsets.US_ASCII));
 }
 public static void writeSurvey(Path directory,Model.Survey survey)throws IOException{Model.validate(survey);writeChecked(directory.resolve(survey.id()+".json"),bytes(survey));}
 public static byte[] checkedRead(Path path)throws IOException{
  String name=path.getFileName().toString();if(!name.endsWith(".json"))throw new IOException("expected .json");
  byte[] data=boundedRead(path,MAX_BYTES);Path sidecar=path.resolveSibling(name.substring(0,name.length()-5)+".sha256");
  String hash=new String(boundedRead(sidecar,128),StandardCharsets.US_ASCII).trim();
  if(!hash.matches("[a-f0-9]{64}")||!sha256(data).equals(hash))throw new IOException("missing or mismatched SHA-256 sidecar");return data;
 }
}
