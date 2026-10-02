package org.qulay.server;
import org.qulay.core.*;import org.springframework.web.bind.annotation.*;import java.io.IOException;import java.util.UUID;
@RestController public class CurbApi {
 private final Store store;public CurbApi(Store store){this.store=store;}
 @GetMapping("/api/v1/surveys/{id}/curb-profile")public CurbAnalysis.Report report(@PathVariable UUID id)throws IOException{return CurbAnalysis.analyze(Json.read(store.get("surveys",id),Model.Survey.class));}
}
