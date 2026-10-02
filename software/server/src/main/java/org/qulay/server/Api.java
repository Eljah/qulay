package org.qulay.server;
import org.qulay.core.*;import org.springframework.web.bind.annotation.*;import org.springframework.http.*;import org.springframework.web.server.ResponseStatusException;import jakarta.servlet.http.HttpServletRequest;import java.io.*;import java.util.*;
@RestController public class Api {
 private final Store store;private static final int MAX=32*1024*1024;
 public Api(Store store){this.store=store;}
 @GetMapping("/health")public Map<String,String> health(){return Map.of("status","UP","revision","QL-01-0.1","metrology","prototype-not-validated");}
 private byte[] body(HttpServletRequest request)throws IOException{byte[] b=request.getInputStream().readNBytes(MAX+1);if(b.length>MAX)throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE);return b;}
 @PutMapping(value="/api/v1/surveys/{id}",consumes="application/json") public Map<String,Object> upload(@PathVariable UUID id,HttpServletRequest req)throws IOException{
  byte[] b=body(req);Model.Survey s=Json.read(b,Model.Survey.class);Model.validate(s);if(!id.equals(s.id()))throw new IllegalArgumentException("path/body UUID mismatch");return store.put("surveys",id,b,req.getHeader("X-Content-SHA256"));
 }
 @GetMapping("/api/v1/surveys")public Object surveys()throws IOException{return store.list("surveys");}
 @GetMapping(value="/api/v1/surveys/{id}",produces="application/json")public byte[] survey(@PathVariable UUID id)throws IOException{return store.get("surveys",id);}
 @GetMapping("/api/v1/surveys/{id}/report")public Model.Assessment report(@PathVariable UUID id)throws IOException{return Geometry.assess(Json.read(store.get("surveys",id),Model.Survey.class),Model.demoRules());}
 @GetMapping(value="/api/v1/surveys/{id}/points.csv",produces="text/csv")public String points(@PathVariable UUID id)throws IOException{return Geometry.pointsCsv(Json.read(store.get("surveys",id),Model.Survey.class));}
 @PutMapping(value="/api/v1/plans/{id}",consumes="application/json")public Map<String,Object> plan(@PathVariable UUID id,HttpServletRequest req)throws IOException{byte[] b=body(req);Model.Plan p=Json.read(b,Model.Plan.class);Model.validate(p);if(!id.equals(p.id()))throw new IllegalArgumentException("path/body UUID mismatch");return store.put("plans",id,b,req.getHeader("X-Content-SHA256"));}
 @GetMapping("/api/v1/plans")public Object plans()throws IOException{return store.list("plans");}
 @GetMapping(value="/api/v1/plans/{id}",produces="application/json")public byte[] plan(@PathVariable UUID id)throws IOException{return store.get("plans",id);}
 @GetMapping("/api/v1/rule-profiles")public Object rules(){return List.of(Model.demoRules());}
 @ExceptionHandler({IllegalArgumentException.class,NullPointerException.class,com.fasterxml.jackson.core.JacksonException.class})public ResponseEntity<?> invalid(Exception e){return ResponseEntity.badRequest().body(Map.of("error","invalid request","detail",Objects.toString(e.getMessage(),"missing required value")));}
}
