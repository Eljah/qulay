package org.qulay.core;
import static org.qulay.core.Model.*;
import java.util.*;
/** Simultaneous plateau comparison. Never reconstructs an unobserved vertical face. */
public final class CurbAnalysis {
 private CurbAnalysis(){}
 public record Row(long sequence,double cartXmm,Double signedRightMinusLeftMm,Double contactXOffsetMm,boolean plateauWindowsValid,String reason){}
 public record Report(String algorithm,boolean acceptanceEligible,Double medianAbsoluteLevelDifferenceMm,int validRows,List<String> caveats,List<Row> rows){}
 private static double median(double[] a){Arrays.sort(a);return a.length%2==1?a[a.length/2]:(a[a.length/2-1]+a[a.length/2])/2;}
 public static Report analyze(Survey s){
  validate(s);if(s.mode()!=Mode.ALONG_CURB)throw new IllegalArgumentException("ALONG_CURB required");
  Point[][] points=Geometry.centers(s);var rows=new ArrayList<Row>();var levels=new ArrayList<Double>();
  for(int i=0;i<points.length;i++){
   double[][] z=new double[2][10],x=new double[2][10];boolean ok=true;
   for(int side=0;side<2;side++)for(int k=0;k<10;k++){
    int j=side==0?k:k+21;Point p=points[i][j];if(!p.valid())ok=false;
    z[side][k]=p.z()-s.calibration().channels().get(j).radiusMm();x[side][k]=p.x();
   }
   double zl=median(z[0]),zr=median(z[1]),dx=median(x[1])-median(x[0]);
   // Fixed outer plateau windows are an explicitly constrained prototype, not automatic segmentation.
   for(int side=0;side<2;side++)if(z[side][9]-z[side][0]>4.0)ok=false;
   Double difference=ok?zr-zl:null;if(ok)levels.add(Math.abs(difference));
   rows.add(new Row(s.frames().get(i).sequence(),s.frames().get(i).xMm(),difference,ok?dx:null,ok,ok?"TWO_LOCALLY_FLAT_PLATEAUS; FACE_UNOBSERVED":"INVALID_OR_NONPLANAR_OUTER_WINDOW"));
  }
  var caveats=List.of("PROTOTYPE_NOT_NORMATIVE: no acceptance verdict", "Outer channels 0..9 and 21..30 must lie on different, locally flat plateaus; middle channels are deliberately not interpolated", "Both levels are simultaneous: common cart heave cancels", "Different arm angles cause different contact X; contactXOffsetMm is retained, NOT silently corrected", "Without a bound on longitudinal surface variation, a large X offset prevents a defensible step-height claim", "Vertical radius subtraction assumes locally horizontal plateaus; crowned-contact uncertainty remains to be validated", "No contact-force detector is validated in Q1 hardware");
  Double m=levels.isEmpty()?null:median(levels.stream().mapToDouble(Double::doubleValue).toArray());
  return new Report("QL-01-plateau-difference-0.1",false,m,levels.size(),caveats,List.copyOf(rows));
 }
}
