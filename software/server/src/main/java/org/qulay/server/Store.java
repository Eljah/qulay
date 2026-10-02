package org.qulay.server;
import org.qulay.core.Json;import org.springframework.beans.factory.annotation.Value;import org.springframework.stereotype.Component;import org.springframework.web.server.ResponseStatusException;import org.springframework.http.HttpStatus;
import java.nio.file.*;import java.io.*;import java.util.*;
/** Single-process persistent immutable object store. Do not share its directory between server processes. */
@Component public class Store {
 private final Path root;
 public Store(@Value("${qulay.storage}")String directory)throws IOException{root=Path.of(directory).toAbsolutePath().normalize();Files.createDirectories(root);}
 private Path file(String kind,UUID id)throws IOException{if(!Set.of("surveys","plans").contains(kind))throw new IllegalArgumentException("kind");Path dir=root.resolve(kind);Files.createDirectories(dir);return dir.resolve(id+".json");}
 public synchronized Map<String,Object> put(String kind,UUID id,byte[] bytes,String hash)throws IOException{
  if(hash==null||!hash.matches("[a-f0-9]{64}")||!Json.sha256(bytes).equals(hash))throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_ENTITY,"SHA256 mismatch");
  Path p=file(kind,id);boolean duplicate=false;
  if(Files.exists(p,LinkOption.NOFOLLOW_LINKS)){if(!Files.isRegularFile(p,LinkOption.NOFOLLOW_LINKS))throw new IOException("unsafe store entry");if(!Json.sha256(Files.readAllBytes(p)).equals(hash))throw new ResponseStatusException(HttpStatus.CONFLICT,"immutable UUID already has different content");duplicate=true;}else Json.atomicWrite(p,bytes);
  return Map.of("id",id,"sha256",hash,"duplicate",duplicate);
 }
 public byte[] get(String kind,UUID id)throws IOException{Path p=file(kind,id);if(!Files.isRegularFile(p,LinkOption.NOFOLLOW_LINKS))throw new ResponseStatusException(HttpStatus.NOT_FOUND);return Files.readAllBytes(p);}
 public List<Map<String,Object>> list(String kind)throws IOException{file(kind,new UUID(0,0));try(var stream=Files.list(root.resolve(kind))){var result=new ArrayList<Map<String,Object>>();for(Path p:stream.filter(x->Files.isRegularFile(x,LinkOption.NOFOLLOW_LINKS)&&x.getFileName().toString().endsWith(".json")).sorted().limit(2000).toList()){String n=p.getFileName().toString();result.add(Map.of("id",n.substring(0,n.length()-5),"bytes",Files.size(p)));}return result;}}
}
