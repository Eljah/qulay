package org.qulay.server;
import org.junit.jupiter.api.Test;import org.junit.jupiter.api.io.TempDir;import static org.junit.jupiter.api.Assertions.*;import org.qulay.core.Json;import java.nio.file.Path;import java.util.UUID;import org.springframework.web.server.ResponseStatusException;
class StoreTest{@TempDir Path tmp;
 @Test void persistsAndDeduplicates()throws Exception{var s=new Store(tmp.toString());var id=UUID.randomUUID();byte[] b="{}".getBytes();assertEquals(false,s.put("plans",id,b,Json.sha256(b)).get("duplicate"));assertEquals(true,s.put("plans",id,b,Json.sha256(b)).get("duplicate"));assertArrayEquals(b,new Store(tmp.toString()).get("plans",id));}
 @Test void immutableConflict()throws Exception{var s=new Store(tmp.toString());var id=UUID.randomUUID();byte[] b="{}".getBytes(),c="[]".getBytes();s.put("plans",id,b,Json.sha256(b));assertThrows(ResponseStatusException.class,()->s.put("plans",id,c,Json.sha256(c)));}
 @Test void hashMismatch()throws Exception{var s=new Store(tmp.toString());assertThrows(ResponseStatusException.class,()->s.put("plans",UUID.randomUUID(),new byte[0],"00"));}
 @Test void mandatorySecret(){assertThrows(IllegalStateException.class,()->new TokenFilter("",false));}
}
