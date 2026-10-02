package org.qulay.desktop;
import org.qulay.core.*;import javax.swing.*;import java.awt.*;import java.nio.file.*;import java.nio.charset.StandardCharsets;import java.util.*;
public final class DesktopApp extends JFrame {
 private final JTextField server=new JTextField("http://127.0.0.1:8080",25);private final JPasswordField token=new JPasswordField(24);private final JTextArea log=new JTextArea();private final Plot plot=new Plot();private byte[] selected;private Model.Survey survey;
 public DesktopApp(){super("Qulay · QL-01 · сбор данных и планы");setDefaultCloseOperation(EXIT_ON_CLOSE);setSize(1150,800);
  JPanel top=new JPanel();top.add(new JLabel("Сервер"));top.add(server);top.add(new JLabel("Токен"));top.add(token);token.setText(Objects.toString(System.getenv("QULAY_TOKEN"),""));
  JButton open=new JButton("Открыть проход с флеш-памяти"),send=new JButton("На сервер"),plan=new JButton("План на флеш-память"),csv=new JButton("Экспорт координат CSV");
  JPanel buttons=new JPanel();for(JButton b:new JButton[]{open,send,plan,csv})buttons.add(b);JPanel header=new JPanel(new BorderLayout());header.add(top,BorderLayout.NORTH);header.add(buttons,BorderLayout.SOUTH);add(header,BorderLayout.NORTH);
  log.setEditable(false);log.setLineWrap(true);log.setWrapStyleWord(true);JSplitPane split=new JSplitPane(JSplitPane.VERTICAL_SPLIT,plot,new JScrollPane(log));split.setResizeWeight(.55);add(split);log.setText("Инженерный прототип. Приёмка заблокирована. Откройте .json с парным .sha256. На графике: центр канала №15, X/Z; пропуски не соединяются.\n");
  open.addActionListener(e->{JFileChooser fc=new JFileChooser();if(fc.showOpenDialog(this)==JFileChooser.APPROVE_OPTION){Path p=fc.getSelectedFile().toPath();work(()->{byte[] data=Json.checkedRead(p);var s=Json.read(data,Model.Survey.class);Model.validate(s);var result=Geometry.assess(s,Model.demoRules());SwingUtilities.invokeLater(()->{selected=data;survey=s;plot.set(s);});return new String(Json.bytes(result),StandardCharsets.UTF_8);});}});
  send.addActionListener(e->{byte[] b=selected;if(b==null){message("Сначала откройте проход");return;}ApiClient api=api();work(()->new String(api.upload(b),StandardCharsets.UTF_8));});
  plan.addActionListener(e->{ApiClient api=api();work(()->{String plans=new String(api.get("/api/v1/plans"),StandardCharsets.UTF_8);SwingUtilities.invokeLater(()->downloadPlan(api,plans));return plans;});});
  csv.addActionListener(e->{Model.Survey s=survey;if(s==null)return;JFileChooser fc=new JFileChooser();fc.setSelectedFile(new java.io.File("qulay-points.csv"));if(fc.showSaveDialog(this)==JFileChooser.APPROVE_OPTION){Path p=fc.getSelectedFile().toPath();work(()->{Json.atomicWrite(p,Geometry.pointsCsv(s).getBytes(StandardCharsets.UTF_8));return "CSV: "+p;});}});
 }
 private ApiClient api(){return new ApiClient(server.getText().trim(),new String(token.getPassword()));}
 private void downloadPlan(ApiClient api,String list){String id=JOptionPane.showInputDialog(this,"Введите UUID плана из списка внизу");if(id==null)return;UUID uuid;try{uuid=UUID.fromString(id.trim());}catch(Exception e){message("Некорректный UUID");return;}JFileChooser fc=new JFileChooser();fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);if(fc.showSaveDialog(this)!=JFileChooser.APPROVE_OPTION)return;Path root=fc.getSelectedFile().toPath();work(()->{byte[] bytes=api.get("/api/v1/plans/"+uuid);var p=Json.read(bytes,Model.Plan.class);Model.validate(p);Path dst=root.resolve("QULAY/plans/"+uuid+".json");Json.atomicWrite(dst,bytes);Json.atomicWrite(dst.resolveSibling(uuid+".sha256"),(Json.sha256(bytes)+"\n").getBytes(StandardCharsets.US_ASCII));return "План записан: "+dst;});}
 private void message(String text){log.append(text+"\n");}
 @FunctionalInterface interface Task{String run()throws Exception;}
 private void work(Task task){new SwingWorker<String,Void>(){protected String doInBackground()throws Exception{return task.run();}protected void done(){try{message(get());}catch(Exception e){message("ОШИБКА: "+(e.getCause()==null?e:e.getCause()).getMessage());}}}.execute();}
 private static final class Plot extends JPanel {
  private Model.Point[][] points;
  void set(Model.Survey s){points=Geometry.contacts(s,8);repaint();}
  @Override protected void paintComponent(Graphics g){super.paintComponent(g);g.drawString("X, мм →    Z, мм ↑    Канал 15. FREE_ROLL: только относительная высота!",20,22);if(points==null)return;
   double minX=Double.POSITIVE_INFINITY,maxX=-minX,minZ=minX,maxZ=-minX;for(var row:points){var p=row[15];if(p.valid()){minX=Math.min(minX,p.x());maxX=Math.max(maxX,p.x());minZ=Math.min(minZ,p.z());maxZ=Math.max(maxZ,p.z());}}if(!Double.isFinite(minX))return;
   g.drawString(String.format(Locale.ROOT,"X %.1f..%.1f; Z %.1f..%.1f",minX,maxX,minZ,maxZ),20,42);int px=0,py=0;boolean prev=false;
   for(var row:points){var p=row[15];if(!p.valid()){prev=false;continue;}int x=30+(int)((p.x()-minX)/Math.max(1,maxX-minX)*(getWidth()-60)),y=getHeight()-30-(int)((p.z()-minZ)/Math.max(1,maxZ-minZ)*(getHeight()-100));if(prev)g.drawLine(px,py,x,y);px=x;py=y;prev=true;}
  }
 }
 public static void main(String[] args){SwingUtilities.invokeLater(()->new DesktopApp().setVisible(true));}
}
