package org.qulay.agent;
import org.junit.jupiter.api.Test;import static org.junit.jupiter.api.Assertions.*;import org.qulay.core.Model.*;import java.util.*;import java.util.zip.CRC32;import java.nio.charset.StandardCharsets;
class WireTest {
 String line(){StringBuilder b=new StringBuilder("Q1,1,10000,20,0,0,256000,7fffffff");for(int j=0;j<31;j++)b.append(",14336");CRC32 c=new CRC32();c.update(b.toString().getBytes(StandardCharsets.US_ASCII));return b+"*"+Long.toHexString(c.getValue());}
 Calibration c(){return new Calibration("test",false,.1,1,.01,List.of());}
 @Test void validFrame(){var f=Wire.parse(line(),c());assertEquals(2,f.xMm());assertTrue(f.attitudeValid());assertEquals(4,f.flags()[0]);}
 @Test void damagedFrame(){assertThrows(IllegalArgumentException.class,()->Wire.parse(line().replace("10000","20000"),c()));}
 @Test void absentCrc(){assertThrows(IllegalArgumentException.class,()->Wire.parse("Q1",c()));}
}
