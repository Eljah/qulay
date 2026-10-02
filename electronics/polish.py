#!/usr/bin/env python3
"""Finish self-contained schematics and independently compare exported netlists."""
from pathlib import Path
import re,csv,json,xml.etree.ElementTree as ET

def matching(text,start):
    depth=0;quoted=False;escaped=False
    for i in range(start,len(text)):
        c=text[i]
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
        elif c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return i
    raise ValueError('Unbalanced schematic expression')

def finish(directory,name):
    path=directory/f'{name}.kicad_sch';text=path.read_text()
    def snap(match):
        x,y=float(match[2]),float(match[3])
        return f'({match[1]} {round(round(x/1.27)*1.27,6):g} {round(round(y/1.27)*1.27,6):g}'
    text=re.sub(r'\((at|xy)\s+(-?\d+(?:\.\d*)?)\s+(-?\d+(?:\.\d*)?)',snap,text)
    start=text.index('(lib_symbols');end=matching(text,start)
    library=text[start+len('(lib_symbols'):end]
    library=re.sub(r'\(symbol "QL:([^\"]+)"',r'(symbol "\1"',library)
    (directory/'QL.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") '+library+')')
    (directory/'sym-lib-table').write_text('(sym_lib_table (lib (name "QL") (type "KiCad") (uri "${KIPRJMOD}/QL.kicad_sym") (options "") (descr "Qulay embedded circuit symbols")))')
    path.write_text(text)

def compare(directory,name,board):
    xml=ET.parse(directory/'netlist.xml');sch={}
    for net in xml.findall('.//nets/net'):
        for node in net.findall('node'):sch[(node.attrib['ref'],node.attrib['pin'])]=net.attrib['name'].lstrip('/')
    pcb={(str(f.GetReference()),str(pad.GetNumber())):str(pad.GetNetname()).lstrip('/') for f in board.GetFootprints() for pad in f.Pads()}
    errors=[];checked=0
    for row in csv.DictReader((directory/'connections.csv').open()):
        ref,pin,net=row['reference'],row['pin'],row['net'];key=(ref,pin)
        if net=='NC':
            if pcb.get(key,''):errors.append({'pin':key,'expected':'NC','pcb':pcb[key]})
            continue
        checked+=1
        if sch.get(key)!=net or pcb.get(key)!=net:errors.append({'pin':key,'expected':net,'schematic':sch.get(key),'pcb':pcb.get(key)})
    result={'board':name,'checked_connected_pins':checked,'mismatches':errors,'passed':not errors}
    (directory/'netlist-parity.json').write_text(json.dumps(result,indent=2))
    return result
