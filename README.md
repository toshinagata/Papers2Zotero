# Papers2 to Zotero: Migration Helper

These scripts help migration from Papers2 to Zotero.

# Requirements

* Python 3
* Zotero (standalone)

# Usage

## Create an XML from Papers2

```
$ python3 BetterExportFromPapers2.py Papers2_directory >FromPapers2.xml
```

## Import to Zotero

* Start up Zotero, and set up library folder
* Quit Zotero
* Replace translators/EndNote XML.js in the Zotero library folder with the version in this repository
* Start Zotero
* Import FromPapers2.xml

# Restriction

Currently, only journal articles in the Papers2 database are exported (because these are all I needed).

BetterExportFromPapers2.py is pretty straightforward, so you can extend it easily to meet your own needs.

