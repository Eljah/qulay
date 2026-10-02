package org.qulay.simulator;
import org.junit.jupiter.api.Test;import static org.junit.jupiter.api.Assertions.*;import org.qulay.core.*;
class CurbTest {
 @Test void recoversTwoLevelsDespiteUnobservedFace(){var r=CurbAnalysis.analyze(Simulator.scenario("curb150"));assertEquals(150,r.medianAbsoluteLevelDifferenceMm(),.2);assertEquals(301,r.validRows());assertFalse(r.acceptanceEligible());}
 @Test void doesNotHideLongitudinalMisregistration(){var r=CurbAnalysis.analyze(Simulator.scenario("curb150"));assertTrue(Math.abs(r.rows().getFirst().contactXOffsetMm())>60);}
 @Test void crossingIsNotAlongCurb(){assertThrows(IllegalArgumentException.class,()->CurbAnalysis.analyze(Simulator.scenario("gentle")));}
}
