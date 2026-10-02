package org.qulay.simulator;
import org.qulay.core.*;import static org.qulay.core.Model.*;import org.junit.jupiter.api.Test;import static org.junit.jupiter.api.Assertions.*;
class SimulatorTest {
 @Test void planeRecovery(){var r=Geometry.assess(Simulator.scenario("gentle"),demoRules());assertEquals(.05,r.maximumLongitudinalGrade(),.002);assertEquals(.01,r.maximumCrossGrade(),.003);assertFalse(r.acceptanceEligible());}
 @Test void excessiveGrade(){var r=Geometry.assess(Simulator.scenario("steep"),demoRules());assertEquals(Decision.FAIL,r.demonstrationDecisions().get("longitudinal"));}
 @Test void excessiveCrossfall(){var r=Geometry.assess(Simulator.scenario("crossfall"),demoRules());assertEquals(Decision.FAIL,r.demonstrationDecisions().get("cross"));}
 @Test void noDatumNoLongitudinalClaim(){var r=Geometry.assess(Simulator.scenario("no-datum"),demoRules());assertNull(r.maximumLongitudinalGrade());assertTrue(r.blockers().contains("NO_INDEPENDENT_HEIGHT_DATUM"));}
 @Test void dropoutHasGap(){var r=Geometry.assess(Simulator.scenario("dropout"),demoRules());assertTrue(r.validFraction()<.99);}
 @Test void reverseRecovery(){var r=Geometry.assess(Simulator.scenario("reverse"),demoRules());assertEquals(.05,r.maximumLongitudinalGrade(),.002);}
 @Test void noSimulationCanBeAcceptance(){for(String n:new String[]{"gentle","steep","curb150","no-datum"})assertFalse(Geometry.assess(Simulator.scenario(n),demoRules()).acceptanceEligible());}
 @Test void jsonRoundTrip()throws Exception{var s=Simulator.scenario("gentle");var t=Json.read(Json.bytes(s),Survey.class);validate(t);assertEquals(s.frames().size(),t.frames().size());}
}
