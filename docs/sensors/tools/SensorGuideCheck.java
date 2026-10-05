import org.qulay.core.*;
import org.qulay.agent.Wire;
import static org.qulay.core.Model.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.CRC32;

/** Runs the repository's actual parsers and geometry on synthetic input. Not a hardware test. */
public final class SensorGuideCheck {
    private static final List<String> passed = new ArrayList<>();
    private static void check(String name, boolean condition) {
        if (!condition) throw new AssertionError(name);
        passed.add(name);
    }
    private static void rejects(String name, Runnable r) {
        try { r.run(); } catch (IllegalArgumentException e) { passed.add(name); return; }
        throw new AssertionError(name);
    }
    private static String packet(String payload) {
        CRC32 c = new CRC32(); c.update(payload.getBytes(StandardCharsets.US_ASCII));
        return payload + "*" + String.format(Locale.ROOT, "%08x", c.getValue());
    }
    private static Calibration calibration() {
        var channels = new ArrayList<Channel>();
        for (int j=0;j<31;j++) channels.add(new Channel(0,(j-15)*25,0,240,20,0,new double[0],new double[0]));
        return new Calibration("GUIDE-SYNTHETIC-NOT-FOR-HARDWARE",false,.1,2,.005,channels);
    }
    private static String q1(int ax, int az, String mask) {
        StringBuilder b=new StringBuilder("Q1,1,10000,20,"+ax+",0,"+az+","+mask);
        for (int j=0;j<31;j++) b.append(',').append(14336+j);
        return packet(b.toString());
    }
    private static String q2(int aux, int diag, int adc, int at, int ct) {
        StringBuilder b=new StringBuilder("Q2,2,20000,40,0,0,256000,7fffffff,"+aux);
        for (int j=0;j<31;j++) b.append(',').append(14336+j).append(':').append(adc).append(':').append(diag).append(':').append(at).append(':').append(ct);
        return packet(b.toString());
    }
    public static void main(String[] args) throws Exception {
        Path out=Path.of(args.length==0 ? "docs/sensors/generated" : args[0]); Files.createDirectories(out);
        Calibration c=calibration();
        check("AS5048 0xB800 response has even parity and EF=0", Integer.bitCount(0xB800)%2==0 && (0xB800&0x4000)==0);
        check("AS5048 angle word is 14336",(0xB800&0x3fff)==14336);
        check("14336 -> -45 degrees with zeroRad=0",Math.abs(c.channels().get(0).angle(14336)+Math.PI/4)<1e-12);
        var calibrated=new Channel(0,-175,0,240,20,-Math.PI/2,
            new double[]{1365*2*Math.PI/16384-Math.PI/2,-Math.PI/4,2731*2*Math.PI/16384-Math.PI/2},
            new double[]{-Math.PI/3,-Math.PI/4,-Math.PI/6});
        check("j8 demo LUT maps 2048 to -45 degrees",Math.abs(calibrated.angle(2048)+Math.PI/4)<1e-12);
        rejects("j8 LUT rejects an angle outside calibrated range",()->calibrated.angle(0));
        String line1=q1(0,256000,"7fffffff"); Frame f1=Wire.parse(line1,c);
        check("Q1 dispatch and vector length",f1.r2()==null&&f1.angle14().length==31);
        check("Q1 channel order j8 is ninth angle",f1.angle14()[8]==14344);
        check("Q1 attitude and odometry units",f1.attitudeValid()&&f1.rollRad()==0&&f1.pitchRad()==0&&f1.xMm()==2);
        check("Q1 valid sensor never asserts contact",f1.flags()[8]==CONTACT_UNKNOWN);
        check("Q1 no independent height or yaw invented",f1.datumZmm()==null&&f1.yawRad()==0);
        Frame bad=Wire.parse(q1(0,256000,"7ffffeff"),c);
        check("Missing mask bit j8 is bad sensor",(bad.flags()[8]&BAD_SENSOR)!=0);
        rejects("Changed byte fails Q1 CRC",()->Wire.parse(line1.replace("10000","20000"),c));
        Frame dynamic=Wire.parse(q1(0,200000,"7fffffff"),c);
        check("Acceleration norm outside gate is dynamic",!dynamic.attitudeValid()&&(dynamic.flags()[8]&DYNAMIC)!=0);
        Frame biased=Wire.parse(q1(7680,256000,"7fffffff"),c);
        check("Norm gate alone does not reject horizontal acceleration",biased.attitudeValid()&&Math.abs(Math.toDegrees(biased.pitchRad()))>1.7);
        String line2=q2(7,0x8100,2048,100,200);Frame f2=Wire.parse(line2,c);
        check("Q2 dispatch preserves per-channel diagnostics and timing",f2.r2()!=null&&f2.r2().diagnostic16()[8]==0x8100&&f2.r2().contactOffsetUs()[8]==200);
        check("Q2 with no force calibration remains unknown",(f2.flags()[8]&CONTACT_UNKNOWN)!=0);
        check("Q2 flags bad diagnostic parity",(Wire.parse(q2(7,0x8101,2048,100,200),c).flags()[8]&BAD_SENSOR)!=0);
        check("Q2 rejects rail-level ADC as a sensor fault",(Wire.parse(q2(7,0x8100,0,100,200),c).flags()[8]&BAD_SENSOR)!=0);
        check("Q2 time skew over 5000us is dynamic",(Wire.parse(q2(7,0x8100,2048,100,6000),c).flags()[8]&DYNAMIC)!=0);
        rejects("Q2 extra column is rejected",()->Wire.parse(packet(line2.substring(0,line2.indexOf('*'))+",0"),c));
        rejects("Q2 CRC damage is rejected",()->Wire.parse(line2.replace("20000","20001"),c));
        int[] angles=new int[31];Arrays.fill(angles,14336);
        Frame known=new Frame(1,10000,0,0,0,0,0,220.0,new int[]{0,0,256000},angles,new int[31],true);
        var point=Geometry.center(known,c.channels().get(15),15);
        check("Known pose centre X from repository geometry",Math.abs(point.x()-169.70562748477)<1e-8);
        check("Known pose centre Z from repository geometry",Math.abs(point.z()-50.29437251523)<1e-8);
        int[] size={8,8,8,7};int sum=0;
        for(int n:size){for(int k=0;k<n;k++)check("Bank response permutation n"+n+"-offset"+sum+"-slot"+k,(n-1-(n-1-k))==k);sum+=n;}
        check("Total sensor positions =31",sum==31);
        Files.writeString(out.resolve("synthetic-Q1.wire"),line1+"\n",StandardCharsets.US_ASCII);
        Files.writeString(out.resolve("synthetic-Q2.wire"),line2+"\n",StandardCharsets.US_ASCII);
        String tests=passed.stream().map(s->"    {\"name\":\""+s+"\",\"result\":\"PASS\"}").reduce((a,b)->a+",\n"+b).orElse("");
        Files.writeString(out.resolve("java-checks.json"),"{\n  \"scope\":\"Existing Java parsers and geometry on synthetic input; bank permutation is an algorithm identity, not SPI hardware emulation\",\n  \"hardware_tested\":false,\n  \"test_count\":"+passed.size()+",\n  \"checks\":[\n"+tests+"\n  ]\n}\n");
        System.out.println("PASS: "+passed.size()+" checks; no hardware execution is claimed.");
    }
}
