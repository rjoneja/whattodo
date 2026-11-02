#!/usr/bin/env python3
"""Wrap whattodo.html (artifact-style fragment) into a full document at docs/index.html."""
import sys
src=open(sys.argv[1] if len(sys.argv)>1 else 'whattodo.html').read()
head='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="color-scheme" content="light dark"><style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
open('docs/index.html','w').write(head+src+'</body></html>')
print('wrote docs/index.html')
