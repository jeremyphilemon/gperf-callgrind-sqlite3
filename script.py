#!/usr/bin/env python

from pstats import Stats
from collections import OrderedDict
from optparse import OptionParser
from pprint import pprint
import re

def schema():
  print """
    PRAGMA journal_mode=OFF;
    PRAGMA count_changes=OFF;
    DROP TABLE IF EXISTS files;
    DROP TABLE IF EXISTS symbols;
    DROP TABLE IF EXISTS mainrows;
    DROP TABLE IF EXISTS children;
    DROP TABLE IF EXISTS parents;
    DROP TABLE IF EXISTS summary;
    CREATE TABLE children (
        self_id INTEGER CONSTRAINT self_exists REFERENCES mainrows(id),
        parent_id INTEGER CONSTRAINT parent_exists REFERENCES mainrows(id),
        from_parent_count INTEGER,
        from_parent_calls INTEGER,
        from_parent_paths INTEGER,
        pct REAL
    );
    CREATE TABLE files (
        id,
        name TEXT
    );
    CREATE TABLE mainrows (
        id INTEGER PRIMARY KEY,
        symbol_id INTEGER CONSTRAINT symbol_id_exists REFERENCES symbols(id),
        self_count INTEGER,
        cumulative_count INTEGER,
        kids INTEGER,
        self_calls INTEGER,
        total_calls INTEGER,
        self_paths INTEGER,
        total_paths INTEGER,
        pct REAL
    );
    CREATE TABLE parents (
        self_id INTEGER CONSTRAINT self_exists REFERENCES mainrows(id),
        child_id INTEGER CONSTRAINT child_exists REFERENCES mainrows(id),
        to_child_count INTEGER,
        to_child_calls INTEGER,
        to_child_paths INTEGER,
        pct REAL
    );
    CREATE TABLE summary (
        counter TEXT,
        total_count INTEGER,
        total_freq INTEGER,
        tick_period REAL
    );
    CREATE TABLE symbols (
        id,
        name TEXT,
        filename_id INTEGER CONSTRAINT file_id_exists REFERENCES files(id)
    );
    CREATE UNIQUE INDEX fileIndex ON files (id);
    CREATE INDEX selfCountIndex ON mainrows(self_count);
    CREATE UNIQUE INDEX symbolsIndex ON symbols (id);
    CREATE INDEX totalCountIndex ON mainrows(cumulative_count);
"""

INSERT_MAINROWS_QUERY="""INSERT INTO mainrows(id, self_count,
                         cumulative_count, kids,
                         self_calls, total_calls, self_paths, total_paths, pct)
                         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
INSERT_CHILDREN_QUERY="""INSERT INTO children(self_id, parent_id,
                         from_parent_count, from_parent_calls, from_parent_paths, pct)
                         VALUES(%s, %s, %s, %s, %s, %s);"""
INSERT_PARENTS_QUERY="""INSERT INTO parents(self_id, child_id,
                                            to_child_count, to_child_calls,
                                            to_child_paths, pct)
                         VALUES(%s, %s, %s, %s, %s, %s);"""
INSERT_FILES_QUERY="""INSERT INTO files(name)
                      VALUES("%s");"""
INSERT_SYMBOLS_QUERY="""INSERT INTO symbols(id, name)
                        VALUES(%s, "%s");"""
INSERT_SUMMARY_TABLE = """INSERT INTO summary (counter, total_count,
                                               total_freq, tick_period)
                          VALUES("PERF_TICKS", %s, %s, %s);"""


files=[] #Done
symbols=[] #Done
mainrowsTupled=[]
childrenTupled=[]
parentsTupled=[]
parents=[]
children=[]

mainrows={}

max=0;

filesRegex=re.compile(r'c?fl=(?:\(\d\))(\n|.*\n)')
symbolsRegex=re.compile(r'(?:\b(?:c?fn)=(?:\(\d\)|..|(?:\S+))(?:\n|\s(\S+\n)))')
fnRegex=re.compile(r'(?:\bc?fn=\((\d+)\))')
selfCount=re.compile(r'(?:(\d+)\s(\d+))')
callsRegex=re.compile(r'(?:(calls=(?:(\d+)\s(\d+))))')
pFunctionAlone=re.compile(r'(?:fn=\((\d)\)(\n|.+)?\n(?:(\d+)\s(\d+)))')
twoRegex=re.compile(r'(?:\n(\d+)\s(\d+))')

def counter(object, resultTuple):
    cfn=x['child']
    pfn=x['parent']
    for y in block:
      functionIDMatch=fnRegex.findall(y)
      if(len(functionIDMatch)>1):
        p=(functionIDMatch[0])
        c=(functionIDMatch[1])
        if(cfn==c and pfn==p):
          appendCalls=twoRegex.search(y)
          if(appendCalls):
            x['count']+=int(appendCalls.group(2))
    resultTuple.append((cfn, pfn, x['count'], x['count'], 1, round((x['count']/float(max))*100, 2)))

if __name__ == "__main__":
  parser = OptionParser()
  opts, args = parser.parse_args()
  if len(args) > 1:
    parser.error("Too many dumps")
  filename = str(args[0])
  fBlock=open(filename)
  text=fBlock.read()
  fLine=open(filename)
  line=fLine.readlines()
  for x in line:
    fileMatch=filesRegex.match(x)
    if fileMatch and fileMatch.group(1)!='\n':
      files.append(fileMatch.group(1))

  block=re.split(r"\n\n", text);

  for x in block:
    functionIDMatch=fnRegex.findall(x)
    if functionIDMatch:
      symbolsMatch=filter(None, symbolsRegex.findall(x))
      if symbolsMatch:
        if(len(symbolsMatch)==1 and len(functionIDMatch)>1):
          functionIDMatch.sort(reverse=True)
        symbolName=symbolsMatch[0][:-1]
        mainrows[functionIDMatch[0]]={'count':0, 'name': symbolName, 'self-count':0, 'kids':0, 'pct': 0, 'parent': (), 'children': ()}
        if(len(symbolsMatch)>1):
          symbolName=symbolsMatch[1][:-1]
          mainrows[functionIDMatch[1]]={'count':0, 'name': symbolName, 'self-count':0, 'kids':0, 'pct': 0, 'parent': (), 'children': ()}

  mainrowsChildren=mainrows
        
  for x in block:
    functionIDMatch=fnRegex.findall(x)
    if functionIDMatch: 
      fn=(functionIDMatch[0])
      appendCalls=twoRegex.search(x)
      if(appendCalls):
        mainrows[fn]['count']+=int(appendCalls.group(2))
      if(len(functionIDMatch)==1):
        mainrows[fn]['self-count']+=int(appendCalls.group(2))
      if(len(functionIDMatch)>1):
        fnk=(functionIDMatch[1])
        mainrows[fnk]['parent']+=(functionIDMatch[0], )
        mainrows[fn]['children']+=(functionIDMatch[1], )

  for i in range(1, len(mainrows)+1):
    fn=str(i)
    if(mainrows[fn]['count']>=max):
      max=mainrows[fn]['count']
    mainrows[fn]['kids']=mainrows[fn]['count']-mainrows[fn]['self-count']
    mainrows[fn]['pct']=round((mainrows[fn]['count']/float(max))*100, 2)
    mainrows[fn]['parent']=tuple(set(mainrows[fn]['parent']))
    mainrows[fn]['children']=tuple(set(mainrows[fn]['children']))

  mainrowsSorted=sorted(mainrows.items(), key=lambda t: int(t[0]))

  schema()

  for x in mainrowsSorted:
    key=x[0]
    meta=x[1]
    symbols.append((key, meta['name']))
    mainrowsTupled.append((key, meta['self-count'], meta['count'], meta['kids'], meta['self-count'], meta['count'], len(meta['parent']), len(meta['parent']), meta['pct']))
    for i in range(0, len(meta['parent'])):
      children.append({'child': key, 'parent': meta['parent'][i], 'count': 0, })
    for i in range(0, len(meta['children'])):
      parents.append({'parent': key, 'child': meta['children'][i], 'count':0, })

  for x in children:
    counter(x, childrenTupled)

  for x in parents:
    counter(x, parentsTupled)

  for x in files:
  	print re.sub("\n[ ]*", "", INSERT_FILES_QUERY % x[1::])

  for x in symbols:
    print re.sub("\n[ ]*", "", INSERT_SYMBOLS_QUERY % x)

  for x in mainrowsTupled:
    print re.sub("\n[ ]*", "", INSERT_MAINROWS_QUERY % x)

  for x in childrenTupled:
      print re.sub("\n[ ]*", "", INSERT_CHILDREN_QUERY % x)

  for x in parentsTupled:
      print re.sub("\n[ ]*", "", INSERT_PARENTS_QUERY % x)

  print re.sub("\n[ ]*", "", INSERT_SUMMARY_TABLE % (max, 1, 1.0/100))

