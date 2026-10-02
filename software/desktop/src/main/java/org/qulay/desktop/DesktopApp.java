package org.qulay.desktop;

import org.qulay.core.*;
import javax.swing.*;
import java.awt.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import javax.imageio.ImageIO;

/** Offline-first survey review. A raw-angle display is never labelled as a surface profile. */
public final class DesktopApp extends JFrame {
 private final JTextField server=new JTextField("http://127.0.0.1:8080",24);
 private final JPasswordField token=new JPasswordField(20);
 private final JTextArea log=new JTextArea();
 private final View matrix=new View(true),profile=new View(false);
 private final JSpinner channel=new JSpinner(new SpinnerNumberModel(15,0,30,1));
 private final JCheckBox raw=new JCheckBox("Сырые углы, не высота поверхности");
 private byte[] selected;private Model.Survey survey;
 private final Path screenshot;
 public DesktopApp(Path screenshot){
  super("Qulay · QL-01.R1 · сбор данных и планы");this.screenshot=screenshot;
  setDefaultCloseOperation(EXIT_ON_CLOSE);setSize(1180,820);setLocation(20,20);
  JPanel top=new JPanel();top.add(new JLabel("Сервер"));top.add(server);top.add(new JLabel("Токен"));top.add(token);
  // Automated screenshots intentionally never display a real authentication token.
  if(screenshot==null)token.setText(Objects.toString(System.getenv("QULAY_TOKEN"),""));
  JButton open=new JButton("Открыть проход"),send=new JButton("На сервер"),plan=new JButton("План на флешку"),csv=new JButton("CSV координат");
  JPanel buttons=new JPanel();for(JButton b:new JButton[]{open,send,plan,csv})buttons.add(b);buttons.add(new JLabel("Канал"));buttons.add(channel);buttons.add(raw);
  JPanel head=new JPanel(new BorderLayout());head.add(top,BorderLayout.NORTH);head.add(buttons,BorderLayout.SOUTH);add(head,BorderLayout.NORTH);
  JTabbedPane tabs=new JTabbedPane();tabs.addTab("Матрица: кадры × 31 канал",matrix);tabs.addTab("Продольный профиль выбранного канала",profile);
  log.setEditable(false);log.setLineWrap(true);log.setWrapStyleWord(true);
  JSplitPane split=new JSplitPane(JSplitPane.VERTICAL_SPLIT,tabs,new JScrollPane(log));split.setResizeWeight(.65);add(split);
  message("Инженерный прототип. Положительная приёмка заблокирована. Серое поле — пропуск или недостоверный контакт. Для отладки платы можно отдельно просмотреть сырые углы.");
  raw.addActionListener(e->{matrix.raw=profile.raw=raw.isSelected();matrix.repaint();profile.repaint();});
  channel.addChangeListener(e->{profile.channel=(Integer)channel.getValue();profile.repaint();});
  open.addActionListener(e->{JFileChooser fc=new JFileChooser();if(fc.showOpenDialog(this)==JFileChooser.APPROVE_OPTION)load(fc.getSelectedFile().toPath());});
  send.addActionListener(e->{if(selected==null){message("Сначала откройте проход");return;}ApiClient api=api();if(api==null)return;byte[] data=selected;work(()->new String(api.upload(data),StandardCharsets.UTF_8));});
  plan.addActionListener(e->{ApiClient api=api();if(api==null)return;work(()->{String text=new String(api.get("/api/v1/plans"),StandardCharsets.UTF_8);SwingUtilities.invokeLater(()->{message(text);downloadPlan(api);});return "Список планов получен.";});});
  csv.addActionListener(e->{Model.Survey s=survey;if(s==null)return;JFileChooser fc=new JFileChooser();fc.setSelectedFile(new java.io.File("qulay-points.csv"));if(fc.showSaveDialog(this)==JFileChooser.APPROVE_OPTION){Path p=fc.getSelectedFile().toPath();work(()->{Json.atomicWrite(p,Geometry.pointsCsv(s).getBytes(StandardCharsets.UTF_8));return "CSV: "+p;});}});
 }
 private ApiClient api(){try{return new ApiClient(server.getText().trim(),new String(token.getPassword()));}catch(IllegalArgumentException e){message("Адрес сервера: "+e.getMessage());return null;}}
 private void load(Path path){work(()->{
  byte[] data=Json.checkedRead(path);Model.Survey s=Json.read(data,Model.Survey.class);Model.validate(s);
  Model.Point[][] points=Geometry.contacts(s,8);
  String report=s.ruleProfileId().equals(Model.demoRules().id())?new String(Json.bytes(Geometry.assess(s,Model.demoRules())),StandardCharsets.UTF_8):"Профиль правил не установлен; показаны исходные данные без оценки.";
  SwingUtilities.invokeLater(()->{
   selected=data;survey=s;matrix.set(s,points);profile.set(s,points);
   message("Проход "+s.id()+"; кадров "+s.frames().size()+"; режим "+s.mode()+"; высотная база "+s.datum()+"; simulated="+s.simulated());message(report);
   if(screenshot!=null){javax.swing.Timer timer=new javax.swing.Timer(800,e->{try{Files.createDirectories(screenshot.toAbsolutePath().getParent());ImageIO.write(new Robot().createScreenCapture(getBounds()),"png",screenshot.toFile());dispose();System.exit(0);}catch(Exception ex){ex.printStackTrace();System.exit(1);}});timer.setRepeats(false);timer.start();}
  });return "Проверены контрольная сумма и формат файла.";
 });}
 private void downloadPlan(ApiClient api){
  String id=JOptionPane.showInputDialog(this,"UUID плана из списка в журнале");if(id==null)return;UUID uuid;
  try{uuid=UUID.fromString(id.trim());}catch(Exception e){message("Некорректный UUID");return;}
  JFileChooser fc=new JFileChooser();fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);if(fc.showSaveDialog(this)!=JFileChooser.APPROVE_OPTION)return;Path root=fc.getSelectedFile().toPath();
  work(()->{byte[] bytes=api.get("/api/v1/plans/"+uuid);Model.Plan p=Json.read(bytes,Model.Plan.class);Model.validate(p);if(!uuid.equals(p.id()))throw new java.io.IOException("UUID ответа не совпадает с запросом");Path dst=root.resolve("QULAY/plans/"+uuid+".json");Json.writeChecked(dst,bytes);return "План и SHA-256 записаны: "+dst;});
 }
 private void message(String text){log.append(text+"\n");}
 @FunctionalInterface interface Task{String run()throws Exception;}
 private void work(Task task){new SwingWorker<String,Void>(){
  protected String doInBackground()throws Exception{return task.run();}
  protected void done(){try{message(get());}catch(Exception e){message("ОШИБКА: "+(e.getCause()==null?e:e.getCause()).getMessage());if(screenshot!=null)System.exit(1);}}
 }.execute();}
 private static final class View extends JPanel {
  private final boolean matrix;private boolean raw;private int channel=15;private Model.Survey survey;private Model.Point[][] points;
  View(boolean matrix){this.matrix=matrix;setBackground(Color.WHITE);}
  void set(Model.Survey s,Model.Point[][] p){survey=s;points=p;repaint();}
  double value(int i,int j){
   if(raw){if((survey.frames().get(i).flags()[j]&Model.BAD_SENSOR)!=0)return Double.NaN;try{return Math.toDegrees(survey.calibration().channels().get(j).angle(survey.frames().get(i).angle14()[j]));}catch(IllegalArgumentException e){return Double.NaN;}}
   return points[i][j].valid()?points[i][j].z():Double.NaN;
  }
  @Override protected void paintComponent(Graphics graphics){
   super.paintComponent(graphics);Graphics2D g=(Graphics2D)graphics.create();try{
    g.setColor(Color.DARK_GRAY);g.drawString(raw?"УГОЛ РЫЧАГА, градусы. Это не высота и не подтверждение контакта.":"Высота Z, мм. FREE_ROLL — только относительная высота в каждом кадре.",20,24);
    if(points==null){g.drawString("Откройте JSON с парным SHA-256.",20,50);return;}
    double min=Double.POSITIVE_INFINITY,max=Double.NEGATIVE_INFINITY;
    for(int i=0;i<points.length;i++)for(int j=matrix?0:channel;j<=(matrix?30:channel);j++){double v=value(i,j);if(Double.isFinite(v)){min=Math.min(min,v);max=Math.max(max,v);}}
    if(!Double.isFinite(min)){g.drawString("Нет достоверных точек. Просмотр сырых углов доступен отдельно.",20,50);return;}
    g.drawString(String.format(Locale.ROOT,"Диапазон %.3f … %.3f · %d кадров · %s",min,max,points.length,survey.mode()),20,46);
    int width=Math.max(1,getWidth()-95),height=Math.max(1,getHeight()-115);
    if(matrix){
     int bins=Math.min(points.length,width);
     for(int k=0;k<bins;k++)for(int j=0;j<31;j++){
      int from=k*points.length/bins,to=(k+1)*points.length/bins;double sum=0;boolean valid=true;
      for(int i=from;i<to;i++){double v=value(i,j);if(!Double.isFinite(v)){valid=false;break;}sum+=v;}
      float fraction=(float)((sum/Math.max(1,to-from)-min)/Math.max(1e-9,max-min));
      g.setColor(valid?Color.getHSBColor(.66f*(1-Math.max(0,Math.min(1,fraction))),.75f,.87f):new Color(205,205,205));
      int x=55+k*width/bins,y=65+(30-j)*height/31;
      g.fillRect(x,y,Math.max(1,(k+1)*width/bins-k*width/bins),Math.max(1,(31-j)*height/31-(30-j)*height/31));
     }
     g.setColor(Color.DARK_GRAY);for(int j=0;j<31;j+=5)g.drawString(""+j,25,70+(30-j)*height/31);
     g.drawString("Номер кадра → (не равномерная координата X). Y: номер канала. Синий=min, красный=max.",55,90+height);
    }else{
     double minX=Arrays.stream(points).mapToDouble(row->row[channel].x()).min().orElse(0),maxX=Arrays.stream(points).mapToDouble(row->row[channel].x()).max().orElse(1);
     int px=0,py=0;boolean previous=false;g.setColor(new Color(30,85,150));
     for(int i=0;i<points.length;i++){
      double v=value(i,channel);if(!Double.isFinite(v)){previous=false;continue;}
      int x=55+(int)((points[i][channel].x()-minX)/Math.max(1,maxX-minX)*width),y=65+height-(int)((v-min)/Math.max(1e-9,max-min)*height);
      if(previous&&survey.frames().get(i).sequence()==survey.frames().get(i-1).sequence()+1)g.drawLine(px,py,x,y);
      px=x;py=y;previous=true;
     }
     g.setColor(Color.DARK_GRAY);g.drawString(String.format(Locale.ROOT,"X %.1f … %.1f мм; канал %d. Пропуски не соединяются.",minX,maxX,channel),55,90+height);
    }
   }finally{g.dispose();}
  }
 }
 public static void main(String[] args){
  if(args.length!=0&&(args.length!=4||!args[0].equals("--preview")||!args[2].equals("--screenshot")))throw new IllegalArgumentException("Usage: desktop.jar [--preview survey.json --screenshot image.png]");
  SwingUtilities.invokeLater(()->{DesktopApp app=new DesktopApp(args.length==4?Path.of(args[3]):null);app.setVisible(true);if(args.length==4)app.load(Path.of(args[1]));});
 }
}
