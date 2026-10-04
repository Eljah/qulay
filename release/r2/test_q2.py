#!/usr/bin/env python3
"""Synthetic Q2 -> real Java agent -> immutable files -> real HTTP server.
This is deliberately NOT execution on RP2040 or an analogue electronics simulation.
"""
import pathlib,json,zlib,hashlib,tempfile,subprocess,os,time,secrets,urllib.request,urllib.error
R=pathlib.Path(__file__).resolve().parents[2];O=R/'generated/verification-r2';O.mkdir(parents=True,exist_ok=True)
checks=[]
def check(n,b):
 if not b:raise AssertionError(n)
 checks.append({'test':n,'result':'PASS'})
def write(p,data):
 b=json.dumps(data,ensure_ascii=False).encode();p.write_bytes(b);p.with_suffix('.sha256').write_text(hashlib.sha256(b).hexdigest()+'\n')
with tempfile.TemporaryDirectory(prefix='ql-q2-') as t:
 root=pathlib.Path(t);plan=json.loads((R/'generated/demo/plan.json').read_text());write(root/'plan.json',plan)
 cal=json.loads((R/'generated/demo/calibration-template.json').read_text());cal['id']='SYNTHETIC-Q2-E2E-NOT-FOR-HARDWARE';cal['traceable']=False
 for c in cal['channels']:c['contact']={'qualified':True,'certificate':'SYNTHETIC-Q2-TEST-ONLY','adcCounts':[1000,2000,3000],'displacementMm':[-.1,.1,.3],'angleRad':[-1.3,0,.5],'hangingMm':[0,0,0],'stiffnessNPerMm':10,'expandedDisplacementUncertaintyMm':.005}
 write(root/'calibration.json',cal)
 lines=[]
 for i in range(30):
  payload=f'Q2,{i},{i*10000},0,0,0,256000,7fffffff,7'+',14336:2000:33024:100:200'*31
  lines.append(payload+'*'+format(zlib.crc32(payload.encode())&0xffffffff,'08x'))
 (root/'input.wire').write_text('\n'.join(lines)+'\n')
 result=subprocess.run(['java','-jar',str(R/'software/agent/target/agent-0.1.0.jar'),'capture',str(root/'input.wire'),str(root/'calibration.json'),str(root/'plan.json'),'30',str(root/'out')],capture_output=True,text=True,timeout=30)
 (O/'q2-capture.log').write_text(result.stdout+result.stderr);check('Q2 agent capture completes',result.returncode==0)
 files=list((root/'out').glob('*.json'));check('one complete survey',len(files)==1);b=files[0].read_bytes();s=json.loads(b)
 check('schema2 metadata retained',s['schema']==2 and len(s['frames'][0]['r2']['contactAdc'])==31)
 check('replay cannot become field evidence',s['simulated'] is True)
 check('qualified synthetic static contact reaches geometry',all(f==0 for f in s['frames'][0]['flags']))
 token=secrets.token_urlsafe(32);env=dict(os.environ,QULAY_TOKEN=token,QULAY_PORT='18082',QULAY_STORAGE=str(root/'store'),QULAY_BIND='127.0.0.1',QULAY_DEV_MODE='false')
 log=open(O/'q2-server.log','w');proc=subprocess.Popen(['java','-jar',str(R/'software/server/target/server-0.1.0.jar')],env=env,cwd=R,stdout=log,stderr=subprocess.STDOUT)
 base='http://127.0.0.1:18082'
 def request(path,method='GET',data=None):
  h={'Authorization':'Bearer '+token,'Content-Type':'application/json'}
  if data is not None:h['X-Content-SHA256']=hashlib.sha256(data).hexdigest()
  with urllib.request.urlopen(urllib.request.Request(base+path,data=data,method=method,headers=h),timeout=30) as r:return r.status,r.read()
 try:
  for _ in range(120):
   if proc.poll() is not None:raise RuntimeError('Server failed')
   try:
    if request('/health')[0]==200:break
   except OSError:time.sleep(.25)
  path='/api/v1/surveys/'+s['id'];check('schema2 upload accepted',request(path,'PUT',b)[0]==200)
  received=json.loads(request(path)[1]);check('Q2 raw diagnostic survives HTTP roundtrip',received['frames'][0]['r2']['diagnostic16'][0]==33024)
  report=json.loads(request(path+'/report')[1]);check('prototype cannot issue acceptance',report['acceptanceEligible'] is False)
  check('no longitudinal height fabricated',report['maximumLongitudinalGrade'] is None)
  (O/'q2-survey.json').write_bytes(b);(O/'q2-report.json').write_text(json.dumps(report,indent=2))
 finally:proc.terminate();proc.wait(timeout=20);log.close()
(O/'q2-e2e.json').write_text(json.dumps({'scope':'synthetic Q2 input, real JVM agent, disk, HTTP and server; no physical hardware','checks':checks},indent=2))
print(len(checks),'Q2 integration checks passed')
