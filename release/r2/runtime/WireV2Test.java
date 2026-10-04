package org.qulay.agent;
import org.qulay.core.*;import static org.qulay.core.Model.*;import org.junit.jupiter.api.Test;import static org.junit.jupiter.api.Assertions.*;import java.util.*;import java.util.zip.CRC32;import java.nio.charset.StandardCharsets;
class WireV2Test {
 Calibration c(){var l=new ArrayList<Channel>();for(int j=0;j<31;j++)l.add(new Channel(0,(j-15)*25,0,240,20,0,new double[0],new double[0]));return new Calibration("UNIT-TEST",false,.1,1,.01,l);}
 String line(int adc,int diagnostic,int aux){StringBuilder b=new StringBuilder("Q2,1,10000,10,0,0,256000,7fffffff,"+aux);for(int j=0;j<31;j++)b.append(",14336:").append(adc).append(':').append(diagnostic).append(":100:200");CRC32 crc=new CRC32();crc.update(b.toString().getBytes(StandardCharsets.US_ASCII));return b+"*"+String.format("%08x",crc.getValue());}
 @Test void acceptAndRetain(){Frame f=Wire.parse(line(2000,33024,7),c());assertEquals(2000,f.r2().contactAdc()[30]);assertEquals(33024,f.r2().diagnostic16()[0]);}
 @Test void stillUnknownWithoutCalibration(){assertEquals(CONTACT_UNKNOWN,Wire.parse(line(2000,33024,7),c()).flags()[0]);}
 @Test void badAnalog(){assertTrue((Wire.parse(line(0,33024,7),c()).flags()[0]&BAD_SENSOR)!=0);}
 @Test void badDiagnostic(){assertTrue((Wire.parse(line(2000,0,7),c()).flags()[0]&BAD_SENSOR)!=0);}
 @Test void malformedCrc(){assertThrows(IllegalArgumentException.class,()->Wire.parse(line(2000,33024,7)+"0",c()));}
 @Test void changedPayload(){assertThrows(IllegalArgumentException.class,()->Wire.parse(line(2000,33024,7).replace("2000:","2001:"),c()));}
 @Test void unknownAux(){assertThrows(IllegalArgumentException.class,()->Wire.parse(line(2000,33024,8),c()));}
}
