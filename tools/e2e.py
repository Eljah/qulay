#!/usr/bin/env python3
"""Real JVM server + agent over HTTP. No hardware or radio emulation is claimed."""
import json, os, pathlib, subprocess, tempfile, time, urllib.request, urllib.error, hashlib, secrets
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'generated/verification'; OUT.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:18080'; TOKEN=secrets.token_urlsafe(32); results=[]
def check(name,condition):
    if not condition: raise AssertionError(name)
    results.append({'test':name,'result':'PASS'})
def request(path,method='GET',body=None,auth=True,hash_override=None):
    h={'Content-Type':'application/json'}
    if auth:h['Authorization']='Bearer '+TOKEN
    if body is not None:h['X-Content-SHA256']=hash_override or hashlib.sha256(body).hexdigest()
    req=urllib.request.Request(BASE+path,data=body,method=method,headers=h)
    try:
        with urllib.request.urlopen(req,timeout=90) as response:return response.status,response.read()
    except urllib.error.HTTPError as error:return error.code,error.read()
with tempfile.TemporaryDirectory(prefix='qulay-e2e-') as temp:
    env=dict(os.environ,QULAY_TOKEN=TOKEN,QULAY_PORT='18080',QULAY_BIND='127.0.0.1',QULAY_STORAGE=temp+'/store',QULAY_DEV_MODE='false')
    log=open(OUT/'server.log','w')
    def start():
        p=subprocess.Popen(['java','-jar',str(ROOT/'software/server/target/server-0.1.0.jar')],env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
        for _ in range(120):
            if p.poll() is not None:raise RuntimeError('server exited; see server.log')
            try:
                if request('/health',auth=False)[0]==200:return p
            except OSError:pass
            time.sleep(.5)
        p.terminate();raise TimeoutError('server startup')
    p=start()
    try:
        index=json.loads((ROOT/'generated/demo/index.json').read_text());id=index[0]['id']
        body=(ROOT/'generated/demo/surveys'/f'{id}.json').read_bytes();path='/api/v1/surveys/'+id
        check('unauthenticated request rejected',request('/api/v1/surveys',auth=False)[0]==401)
        check('checksum mismatch rejected',request(path,'PUT',body,hash_override='0'*64)[0]==422)
        code,r=request(path,'PUT',body);check('first upload',code==200 and not json.loads(r)['duplicate'])
        code,r=request(path,'PUT',body);check('idempotent duplicate',code==200 and json.loads(r)['duplicate'])
        changed=json.loads(body);changed['notes']='different immutable payload';changed=json.dumps(changed).encode()
        check('UUID conflict rejected',request(path,'PUT',changed)[0]==409)
        changed=json.loads(body);changed['schema']=999
        check('unknown schema rejected',request(path,'PUT',json.dumps(changed).encode())[0]==400)
        code,r=request(path+'/report');report=json.loads(r)
        check('server computes geometry and blocks acceptance',code==200 and report['acceptanceEligible'] is False and abs(report['maximumLongitudinalGrade']-.05)<.002)
        code,r=request(path+'/points.csv');check('coordinate export',code==200 and r.startswith(b'sequence,channel'))
        plan=(ROOT/'generated/demo/plan.json').read_bytes();plan_id=json.loads(plan)['id']
        check('plan creation',request('/api/v1/plans/'+plan_id,'PUT',plan)[0]==200)
        subprocess.run(['java','-jar',str(ROOT/'software/agent/target/agent-0.1.0.jar'),'pull-plan',plan_id,BASE,temp+'/usb'],env=env,check=True,timeout=60)
        check('plan downloaded to USB directory',(pathlib.Path(temp)/'usb/QULAY/plans'/f'{plan_id}.json').is_file())
        subprocess.run(['java','-jar',str(ROOT/'software/agent/target/agent-0.1.0.jar'),'sync',str(ROOT/'generated/demo/surveys'),BASE],env=env,check=True,timeout=120)
        check('offline agent sync uploads seven passes',len(json.loads(request('/api/v1/surveys')[1]))==7)
        p.terminate();p.wait(timeout=20);p=start()
        check('surveys survive server restart',request(path)[0]==200)
    finally:
        p.terminate();p.wait(timeout=20);log.close()
        (OUT/'e2e.json').write_text(json.dumps({'scope':'JVM + HTTP + filesystem; NOT hardware','checks':results},indent=2))
print(f'{len(results)} end-to-end checks passed')
