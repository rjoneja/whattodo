#!/usr/bin/env python3
"""Wrap whattodo.html (artifact-style fragment) into a full document at docs/index.html,
stamp it with a version, and write docs/version.json so open copies can spot they're stale."""
import sys, hashlib, json
src=open(sys.argv[1] if len(sys.argv)>1 else 'whattodo.html').read()
v=hashlib.sha1(src.encode()).hexdigest()[:10]
# On open (and when the tab comes back into view), ask for version.json without the cache; if the site has
# moved on, load the new page under a fresh URL so Safari can't hand back its stored copy. Once per version.
upd=("<script>window.WTD_VERSION='%s';(function(){var u=new URL(location.href);"
     "if(u.searchParams.has('v')){u.searchParams.delete('v');history.replaceState(null,'',u.pathname+(u.search||'')+u.hash);}"
     "function chk(){if(!/^https?:/.test(location.protocol))return;fetch('/version.json?t='+Date.now(),{cache:'no-store'}).then(function(r){return r.ok?r.json():null}).then(function(j){"
     "if(!j||!j.v||j.v===window.WTD_VERSION)return;try{if(sessionStorage.getItem('wtd.upd')===j.v)return;sessionStorage.setItem('wtd.upd',j.v)}catch(e){}"
     "var n=new URL(location.href);n.searchParams.set('v',j.v);location.replace(n.toString())}).catch(function(){})}"
     "chk();document.addEventListener('visibilitychange',function(){if(document.visibilityState==='visible')chk()})})();</script>") % v
head='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="color-scheme" content="dark"><meta name="theme-color" content="#122018"><style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}body{margin:0;background:#122018}img{max-width:100%}[hidden]{display:none!important}</style>'+upd+'</head><body>'
open('docs/index.html','w').write(head+src+'</body></html>')
json.dump({"v":v},open('docs/version.json','w'))
print('wrote docs/index.html', v)
