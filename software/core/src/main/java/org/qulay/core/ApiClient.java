package org.qulay.core;
import java.net.*;import java.net.http.*;import java.time.Duration;import java.io.*;import java.util.*;
public final class ApiClient {
 private final String base,token;private final HttpClient http=HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).followRedirects(HttpClient.Redirect.NEVER).build();
 public ApiClient(String base,String token){URI u=URI.create(base);boolean local=Set.of("localhost","127.0.0.1","::1","[::1]").contains(u.getHost());if(!"https".equals(u.getScheme())&&!("http".equals(u.getScheme())&&local))throw new IllegalArgumentException("HTTPS required except on loopback");if(u.getUserInfo()!=null||u.getQuery()!=null||u.getFragment()!=null)throw new IllegalArgumentException("invalid server URL");this.base=base.replaceAll("/+$","");this.token=Objects.requireNonNullElse(token,"");}
 public byte[] get(String path)throws IOException,InterruptedException{return execute(HttpRequest.newBuilder(URI.create(base+path)).GET());}
 public byte[] put(String path,byte[] data)throws IOException,InterruptedException{return execute(HttpRequest.newBuilder(URI.create(base+path)).header("Content-Type","application/json").header("X-Content-SHA256",Json.sha256(data)).PUT(HttpRequest.BodyPublishers.ofByteArray(data)));}
 private byte[] execute(HttpRequest.Builder b)throws IOException,InterruptedException{if(!token.isBlank())b.header("Authorization","Bearer "+token);var r=http.send(b.timeout(Duration.ofSeconds(90)).build(),HttpResponse.BodyHandlers.ofByteArray());if(r.statusCode()<200||r.statusCode()>=300)throw new IOException("HTTP "+r.statusCode()+": "+new String(r.body(),java.nio.charset.StandardCharsets.UTF_8));return r.body();}
 public byte[] upload(byte[] data)throws IOException,InterruptedException{var s=Json.read(data,Model.Survey.class);Model.validate(s);return put("/api/v1/surveys/"+s.id(),data);}
}
