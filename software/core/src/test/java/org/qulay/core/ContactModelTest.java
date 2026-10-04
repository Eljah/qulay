package org.qulay.core;
import org.junit.jupiter.api.Test;import static org.junit.jupiter.api.Assertions.*;import static org.qulay.core.Model.*;
class ContactModelTest {
 static ContactModel.ContactCalibration cal(boolean q){return new ContactModel.ContactCalibration(q,q?"SIMULATED-UNIT-TEST":"",new double[]{1000,2000,3000},new double[]{-.1,.1,.3},new double[]{-1.3,0,.5},new double[]{0,0,0},10,.005);}
 @Test void missing(){assertEquals(CONTACT_UNKNOWN,ContactModel.read(null,2000,0,true).flags());}
 @Test void unqualified(){assertEquals(CONTACT_UNKNOWN,ContactModel.read(cal(false),2000,0,true).flags());}
 @Test void load(){assertEquals(0,ContactModel.read(cal(true),2000,0,true).flags());}
 @Test void displacement(){assertEquals(.1,ContactModel.read(cal(true),2000,0,true).displacementMm(),1e-12);}
 @Test void force(){assertEquals(1,ContactModel.read(cal(true),2000,0,true).projectedForceN(),1e-12);}
 @Test void disconnected(){assertEquals(BAD_SENSOR,ContactModel.read(cal(true),0,0,true).flags());}
 @Test void rail(){assertEquals(BAD_SENSOR,ContactModel.read(cal(true),4095,0,true).flags());}
 @Test void freeHanging(){assertEquals(NO_CONTACT,ContactModel.read(cal(true),1500,0,true).flags());}
 @Test void guardedThreshold(){assertEquals(CONTACT_UNKNOWN,ContactModel.read(cal(true),1600,0,true).flags());}
 @Test void moving(){assertEquals(DYNAMIC,ContactModel.read(cal(true),2000,0,false).flags());}
 @Test void outOfAngleRange(){assertEquals(CONTACT_UNKNOWN,ContactModel.read(cal(true),2000,1,true).flags());}
 @Test void reverseHallPolarity(){var c=new ContactModel.ContactCalibration(true,"UNIT-TEST",new double[]{1000,2000,3000},new double[]{.3,.1,-.1},new double[]{-1.3,0,.5},new double[]{0,0,0},10,.005);assertEquals(0,ContactModel.read(c,2000,0,true).flags());}
 @Test void physicalTipCorrection(){int[] a=new int[31];int[] adc=new int[31];java.util.Arrays.fill(adc,2000);var f=new Frame(0,0,0,0,0,0,0,220.0,new int[]{0,0,256000},a,new int[31],true,new R2Raw(adc,new int[31],new int[31],new int[31],7));var c=new Channel(0,0,0,240,20,0,new double[0],new double[0],cal(true));assertEquals(220.1,Geometry.center(f,c,0).z(),1e-9);}
}
