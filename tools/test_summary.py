#!/usr/bin/env python3
"""Summarize executed tests; never turn compilation into a hardware validation claim."""
from pathlib import Path
import os,json,xml.etree.ElementTree as ET,hashlib
root=Path(__file__).resolve().parents[1];out=root/'generated/verification';out.mkdir(parents=True,exist_ok=True)
suites=[]
for path in sorted(root.glob('software/*/target/surefire-reports/TEST-*.xml')):
    element=ET.parse(path).getroot()
    suites.append({'suite':element.attrib['name'],'tests':int(element.attrib.get('tests',0)),'failures':int(element.attrib.get('failures',0)),'errors':int(element.attrib.get('errors',0)),'skipped':int(element.attrib.get('skipped',0))})
e2e=json.loads((out/'e2e.json').read_text())
images=[]
for path in sorted(out.glob('*.png')):
    images.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'meaning':'actual Swing window pixels captured under Xvfb with synthetic survey input'})
result={'source_commit':os.environ.get('GITHUB_SHA'),'run_id':os.environ.get('GITHUB_RUN_ID'),'suites':suites,'totals':{key:sum(s[key] for s in suites) for key in ['tests','failures','errors','skipped']},'end_to_end_checks':e2e['checks'],'screenshots':images,'hardware_executed':False,'metrological_accuracy_validated':False}
(out/'summary.json').write_text(json.dumps(result,indent=2))
assert suites and result['totals']['failures']==0 and result['totals']['errors']==0
assert e2e['checks'] and all(c['result']=='PASS' for c in e2e['checks'])
print(json.dumps(result['totals']),len(e2e['checks']),'end-to-end checks')
