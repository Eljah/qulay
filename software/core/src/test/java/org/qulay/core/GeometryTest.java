package org.qulay.core;
import org.junit.jupiter.api.Test;import static org.junit.jupiter.api.Assertions.*;import static org.qulay.core.Model.*;import java.util.*;
class GeometryTest {
 Channel ch(){return new Channel(0,100,0,240,20,0,new double[0],new double[0]);}
 Frame f(double roll,Double z){return new Frame(0,0,0,0,roll,0,0,z,new int[]{0,0,256000},new int[31],new int[31],true);}
 @Test void flatCenters(){Point p=Geometry.center(f(0,220.0),ch(),0);assertEquals(240,p.x(),1e-9);assertEquals(220,p.z(),1e-9);}
 @Test void rollRotatesTransverseHeight(){Point p=Geometry.center(f(.1,220.0),ch(),0);assertEquals(220+100*Math.sin(.1),p.z(),1e-9);}
 @Test void rotationOrder(){double[] v=Geometry.rotate(1,0,0,0,Math.PI/2,0);assertEquals(-1,v[2],1e-9);}
 @Test void yawRotation(){double[] v=Geometry.rotate(1,0,0,0,0,Math.PI/2);assertEquals(1,v[1],1e-9);}
 @Test void quantizedNegativeAngle(){assertEquals(-Math.PI/2,ch().angle(12288),1e-12);}
 @Test void lookupInterpolation(){var c=new Channel(0,0,0,240,20,0,new double[]{-1,0,1},new double[]{-.9,.1,1.1});assertEquals(.1,c.angle(0),1e-9);}
 @Test void lookupOutOfRange(){var c=new Channel(0,0,0,240,20,0,new double[]{-.1,.1},new double[]{-.1,.1});assertThrows(IllegalArgumentException.class,()->c.angle(4096));}
 @Test void guardBandPass(){assertEquals(Decision.PASS,Geometry.upperLimit(.07,.005,.08));}
 @Test void guardBandFail(){assertEquals(Decision.FAIL,Geometry.upperLimit(.09,.005,.08));}
 @Test void guardBandIndeterminate(){assertEquals(Decision.INDETERMINATE,Geometry.upperLimit(.08,.005,.08));}
 @Test void absentIsNotPass(){assertEquals(Decision.INSUFFICIENT_DATA,Geometry.upperLimit(null,1,15));}
 @Test void rejectsNegativeUncertainty(){assertThrows(IllegalArgumentException.class,()->Geometry.upperLimit(.1,-1,.2));}
 @Test void unknownContactIsInvalid(){Frame a=f(0,220.0);a.flags()[0]=CONTACT_UNKNOWN;assertFalse(Geometry.center(a,ch(),0).valid());}
 @Test void angleChangesX(){Frame a=f(0,220.0);a.angle14()[0]=14336;assertEquals(240/Math.sqrt(2),Geometry.center(a,ch(),0).x(),1e-9);}
 @Test void noDatumNotInvented(){assertEquals(0,Geometry.center(f(0,null),ch(),0).z(),1e-9);}
 @Test void knownHash(){assertEquals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",Json.sha256(new byte[0]));}
 @Test void remoteHttpRejected(){assertThrows(IllegalArgumentException.class,()->new ApiClient("http://example.com",""));}
}
