package org.qulay.core;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.*;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

class JsonIntegrityTest {
 @TempDir Path temp;
 record Sample(int schema,boolean simulated) {}
 byte[] utf(String s){return s.getBytes(StandardCharsets.UTF_8);}
 @Test void duplicateKeysRejected(){assertThrows(IOException.class,()->Json.read(utf("{\"schema\":1,\"schema\":2,\"simulated\":false}"),Sample.class));}
 @Test void secondDocumentRejected(){assertThrows(IOException.class,()->Json.read(utf("{\"schema\":1,\"simulated\":false} {}"),Sample.class));}
 @Test void fractionalIntegerRejected(){assertThrows(IOException.class,()->Json.read(utf("{\"schema\":1.5,\"simulated\":false}"),Sample.class));}
 @Test void stringBooleanRejected(){assertThrows(IOException.class,()->Json.read(utf("{\"schema\":1,\"simulated\":\"false\"}"),Sample.class));}
 @Test void unknownFieldRejected(){assertThrows(IOException.class,()->Json.read(utf("{\"schema\":1,\"simulated\":false,\"extra\":0}"),Sample.class));}
 @Test void exactRoundTrip()throws Exception{Path f=temp.resolve("test.json");byte[] b=Json.bytes(new Sample(1,false));Json.writeChecked(f,b);assertArrayEquals(b,Json.checkedRead(f));}
 @Test void modifiedPayloadRejected()throws Exception{Path f=temp.resolve("test.json");Json.writeChecked(f,utf("{}"));Files.writeString(f,"[]");assertThrows(IOException.class,()->Json.checkedRead(f));}
 @Test void absentSidecarRejected()throws Exception{Path f=temp.resolve("test.json");Files.writeString(f,"{}");assertThrows(IOException.class,()->Json.checkedRead(f));}
 @Test void oversizedHashRejected()throws Exception{Path f=temp.resolve("test.json");Json.writeChecked(f,utf("{}"));Files.writeString(temp.resolve("test.sha256"),"a".repeat(200));assertThrows(IOException.class,()->Json.checkedRead(f));}
 @Test void boundedInputRejected()throws Exception{Path f=temp.resolve("test.json");Files.writeString(f,"123456");assertThrows(IOException.class,()->Json.boundedRead(f,5));}
}
