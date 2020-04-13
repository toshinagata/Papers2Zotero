#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  Usage: python3 BetterExportFromPapers2.py Papers2_directory >BetterExportOut.xml

import sqlite3
import re
import xml.etree.ElementTree as ET
import xml.sax.saxutils as SU
import urllib.parse
import sys
import os

def dict_factory(cursor, row):
   d = {}
   for idx, col in enumerate(cursor.description):
       d[col[0]] = row[idx]
   return d

if len(sys.argv) == 2:
  os.chdir(sys.argv[1])
else:
  sys.stderr.write("Usage: python3 BetterExportFromPapers2.py Papers2_directory >BetterExportOut.xml\n")
  sys.exit(1)
cwd = os.getcwd()

#  ------  Read Papers2 Database  ------

dbpath = cwd + "/Library.papers2/Database.papersdb"
connection = sqlite3.connect(dbpath)
connection.row_factory = dict_factory
cursor = connection.cursor()

#  Get list of publications
cursor.execute("SELECT * FROM Publication")
fields = list(map(lambda f: f[0], cursor.description))
publications = {}
journals = {}
for i in cursor.fetchall():
  if i["type"] == 400:
    publications[i["ROWID"]] = i
    i["collections"] = []
    i["authors"] = {}   #  This is dictionary
    i["PDFs"] = []
  elif i["type"] == -100:
    journals[i["ROWID"]] = i

#  Get list of authors
cursor.execute("SELECT * FROM Author")
fields = list(map(lambda f: f[0], cursor.description))
authors = {}
for i in cursor.fetchall():
  authors[i["ROWID"]] = i["standard_name"]

#  Get authors for each publication
cursor.execute("SELECT * FROM OrderedAuthor")
fields = list(map(lambda f: f[0], cursor.description))
for i in cursor.fetchall():
  if i["object_id"] in publications:
    publications[i["object_id"]]["authors"][i["priority"]] = authors[i["author_id"]]

#  Get list of PDFs
cursor.execute("SELECT * FROM PDF")
for i in cursor.fetchall():
  if i["object_id"] in publications:
    p = publications[i["object_id"]]
    if i["is_primary"] == 1:
      p["PDFs"].insert(0, i["path"])
    else:
      p["PDFs"].append(i["path"])

#  Get list of collections
cursor.execute("SELECT * FROM Collection")
fields = list(map(lambda f: f[0], cursor.description))
collections = {}
for i in cursor.fetchall():
  if i["type"] == 0:
    i["items"] = []
    collections[i["ROWID"]] = i

#  Get list of collection items
cursor.execute("SELECT * FROM CollectionItem")
fields = list(map(lambda f: f[0], cursor.description))
collectionItems = {}
for i in cursor.fetchall():
  c_id = i["collection"]
  if c_id in collections:
    c = collections[c_id]
    if i["object_id"] in publications:
      c["items"].append(i["object_id"])
      publications[i["object_id"]]["collections"].append(c["name"])

#  Set 'parent_name' field to the collection
for k, i in collections.items():
  if i == None:
    continue
  if i["type"] == 0:
    name = i["name"]
    if i["parent"] not in collections:
      i["parent_name"] = None
    else:
      i["parent_name"] = collections[i["parent"]]["name"]

cursor.close()
connection.close()

#  ------  Output XML  ------

#  XML indent function
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

root = ET.Element("xml")
records = ET.SubElement(root, "records")

for key in sorted(publications.keys()):
    rec = ET.SubElement(records, "record")
    p = publications[key]
    # print(p)
    ET.SubElement(rec, "database", {"name":"test.xml", "path":"test.xml"}).text = "test.xml"
    ET.SubElement(rec, "source-app", {"name":"Papers2", "version":"2.8.1"}).text = "Papers2"
    ET.SubElement(rec, "rec-number").text = str(p["ROWID"])
    ET.SubElement(rec, "ref-type", {"name":"Journal Article"}).text = "17"
    a = ET.SubElement(ET.SubElement(rec, "contributors"), "authors")
    for k in sorted(p["authors"].keys()):
      ET.SubElement(a, "author").text = p["authors"][k]
    ts = ET.SubElement(rec, "titles")
    ET.SubElement(ts, "title").text = p["title"]
    if p["bundle"] in journals:
      bundle = journals[p["bundle"]]
    else:
      bundle = {"abbreviation":"", "title":""}
    ET.SubElement(ts, "secondary-title").text = bundle["title"]
    per = ET.SubElement(rec, "periodical")
    ET.SubElement(per, "abbr-1").text = bundle["abbreviation"]
    ET.SubElement(per, "full-title").text = bundle["title"]
    ET.SubElement(rec, "custom3").text = "papers2://publication/uuid/" + p["uuid"]
    urls = ET.SubElement(rec, "urls")
    if "doi" in p:
      doi = p["doi"]
    else:
      doi = None
    if doi:
      doitext = urllib.parse.quote(doi)
      doiurl = "https://doi.org/" + doitext
    else:
      doitext = ""
      doiurl = ""
    ET.SubElement(ET.SubElement(urls, "related-urls"), "url").text = doiurl
    for pdf in p["PDFs"]:
      url = "file://localhost" + urllib.parse.quote(cwd + "/" + pdf)
      ET.SubElement(ET.SubElement(urls, "pdf-urls"), "url").text = url
    dates = ET.SubElement(rec, "dates")
    pubdate = p["publication_date"]
    if pubdate:
      y = pubdate[2:6]
      m = pubdate[6:8]
      d = pubdate[8:10]
      md = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][int(m) - 1] + " " + d
    else:
      y = ""
      md = ""
    ET.SubElement(dates, "year").text = y
    ET.SubElement(ET.SubElement(dates, "pub-dates"), "date").text = md
    spage = p["startpage"]
    epage = p["endpage"]
    if epage:
      pages = spage + "-" + epage
    else:
      pages = spage
    ET.SubElement(rec, "pages").text = pages
    ET.SubElement(rec, "volume").text = p["volume"]
    ET.SubElement(rec, "abstract").text = p["summary"]
    ET.SubElement(rec, "electronic-resource-num").text = doitext

#  ---  Create collections  ---
cc = ET.SubElement(ET.SubElement(records, "record"), "create-collections")
for k, i in collections.items():
  col = ET.SubElement(cc, "collection")
  ET.SubElement(col, "name").text = i["name"]
  if i["parent"]:
    ET.SubElement(col, "parent").text = i["parent_name"]
  for item in i["items"]:
    ET.SubElement(col, "item").text = str(item)

indent(root)
ET.dump(root)

