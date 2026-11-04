#!/usr/bin/env node
/*
  Layout check for JauntOut: loads the real app with the real events at several phone sizes and fails if
  any text overlaps other text, is cut off, sticks out sideways, or a button ends up under the tab bar.

    node tests/layout.js                       # chromium only, http://127.0.0.1:8765 (serve docs/ first)
    BROWSERS=chromium,webkit node tests/layout.js
    CARDS=40 node tests/layout.js              # how many deck cards to check per phone

  Outside calls (TfL, weather, postcodes) get fixed, deliberately long answers so the worst case is tested.
  Screenshots of every failure go to tests/out/.
*/
const fs = require('fs'), path = require('path');
const pw = require('playwright');

const BASE = process.env.BASE || 'http://127.0.0.1:8765/';
const BROWSERS = (process.env.BROWSERS || 'chromium').split(',');
const CARDS = +(process.env.CARDS || 30);
const OUT = path.join(__dirname, 'out'); fs.mkdirSync(OUT, { recursive: true });
// visible area once the browser's own bars are taken off
const PHONES = [
  { name: 'iPhone SE', width: 375, height: 553 },
  { name: 'iPhone 15', width: 393, height: 659 },
  { name: 'iPhone 15 Pro Max', width: 430, height: 739 },
  { name: 'small Android', width: 360, height: 560 },
  { name: 'Pixel 8', width: 412, height: 780 },
];

// ---------- fixed outside answers ----------
const iso = d => d.toISOString().slice(0, 10);
const sat = (() => { const d = new Date(); d.setDate(d.getDate() + ((6 - d.getDay() + 7) % 7 || 7)); return iso(d); })();
function weather() {
  const time = [], T = [], P = [], MM = [], C = [], G = [], W = [];
  const d0 = new Date(); d0.setHours(0, 0, 0, 0);
  for (let i = 0; i < 16 * 24; i++) {
    const t = new Date(d0.getTime() + i * 3600e3), h = t.getHours();
    time.push(iso(t) + 'T' + String(h).padStart(2, '0') + ':00');
    T.push(7 + (h > 11 && h < 17 ? 4 : 0)); const wet = h < 12;          // drizzly morning, dry from lunchtime: the longest summary
    P.push(wet ? 70 : 10); MM.push(wet ? 0.4 : 0); C.push(80); G.push(30); W.push(wet ? 51 : 3);
  }
  return { hourly: { time, temperature_2m: T, precipitation_probability: P, precipitation: MM, cloud_cover: C, wind_gusts_10m: G, weather_code: W } };
}
const leg = (id, name, from, to, d, a, b) => ({ mode: { id }, routeOptions: [{ name }], departurePoint: { commonName: from }, arrivalPoint: { commonName: to },
  instruction: { summary: `${name} to ${to}` }, duration: d, path: { lineString: JSON.stringify([a, [(a[0] + b[0]) / 2 + 0.004, (a[1] + b[1]) / 2], b]) } });
const walk = (d, a, b) => ({ mode: { id: 'walking' }, duration: d, path: { lineString: JSON.stringify([a, b]) }, departurePoint: { commonName: 'x' }, arrivalPoint: { commonName: 'y' } });
function tfl(url) {
  const m = /JourneyResults\/([-\d.]+),([-\d.]+)\/to\/([-\d.]+),([-\d.]+)/.exec(url); if (!m) return { journeys: [] };
  const A = [+m[1], +m[2]], B = [+m[3], +m[4]], M1 = [(A[0] * 2 + B[0]) / 3, (A[1] * 2 + B[1]) / 3], M2 = [(A[0] + B[0] * 2) / 3, (A[1] + B[1] * 2) / 3];
  const day = sat + 'T';
  return { journeys: [
    { duration: 74, startDateTime: day + '10:01:00', arrivalDateTime: day + '11:15:00', legs: [walk(6, A, M1),
      leg('national-rail', 'Southeastern', 'Hither Green Rail Station', 'London Bridge Rail Station', 18, M1, M2), leg('tube', 'Northern', 'London Bridge Underground Station', 'Camden Town Underground Station', 22, M2, B),
      leg('bus', '168', 'Camden Town Station', 'Hampstead Heath / Royal Free Hospital', 14, M2, B), walk(9, M2, B)] },
    { duration: 66, startDateTime: day + '10:09:00', arrivalDateTime: day + '11:15:00', legs: [walk(4, A, M1), leg('bus', 'SL7', 'Fountain Roundabout', 'Carshalton High Street', 40, M1, M2), leg('bus', '127', 'Carshalton', 'Purley', 15, M2, B), walk(7, M2, B)] },
    { duration: 58, startDateTime: day + '10:17:00', arrivalDateTime: day + '11:15:00', legs: [walk(58, A, B)] },
  ] };
}

// ---------- checks, run inside the page ----------
function pageChecks(scopeSel, label) {
  const issues = [];
  const vw = innerWidth, vh = innerHeight;
  const vis = el => { if (!el.isConnected) return false; const s = getComputedStyle(el); if (s.visibility === 'hidden' || s.display === 'none' || +s.opacity === 0) return false;
    if (el.closest('[hidden], .card.under, .card.under2, .stamp')) return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const textRect = el => { const rs = []; for (const n of el.childNodes) if (n.nodeType === 3 && n.textContent.trim()) { const rg = document.createRange(); rg.selectNodeContents(n); rs.push(...rg.getClientRects()); }
    return rs.filter(r => r.width > 0.5 && r.height > 0.5); };
  const name = el => (el.id ? '#' + el.id : el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : '')) + ' "' + el.textContent.trim().slice(0, 40) + '"';
  const scopes = [...document.querySelectorAll(scopeSel)].filter(vis);
  if (!scopes.length) issues.push({ kind: 'nothing to check (screen not shown?)', where: label, el: scopeSel });
  for (const scope of scopes) {
    const els = [...scope.querySelectorAll('*')].filter(vis).concat(vis(scope) ? [scope] : []);
    const boxes = [];
    for (const el of els) {
      if (el.closest('svg') && el.tagName.toLowerCase() !== 'text') continue;
      let rects = el.tagName.toLowerCase() === 'text' ? [el.getBoundingClientRect()] : textRect(el);
      if (!rects.length) continue;
      const s = getComputedStyle(el);
      // text cut off by its own box (ellipsis is a deliberate cut, so it's allowed)
      if (el.tagName.toLowerCase() !== 'text' && /hidden|clip/.test(s.overflow + s.overflowX) && s.textOverflow !== 'ellipsis' && el.scrollWidth > el.clientWidth + 2)
        issues.push({ kind: 'cut off sideways', where: label, el: name(el) });
      // what's actually visible of each line: clipped by every ancestor that hides overflow.
      // A cut is fine when it's deliberate ("…" ellipsis, line clamp, a scroll area); otherwise it's a bug.
      const sr = scope.getBoundingClientRect();
      for (const r0 of rects) {
        let r = { left: r0.left, right: r0.right, top: r0.top, bottom: r0.bottom }, badCut = false;
        for (let a = el; a && a !== document.documentElement; a = a.parentElement) {
          const as = getComputedStyle(a); if (!/hidden|clip|auto|scroll/.test(as.overflow + as.overflowX + as.overflowY)) continue;
          const ar = a.getBoundingClientRect();
          const nr = { left: Math.max(r.left, ar.left), right: Math.min(r.right, ar.right), top: Math.max(r.top, ar.top), bottom: Math.min(r.bottom, ar.bottom) };
          const cut = nr.right < r.right - 2 || nr.left > r.left + 2 || nr.bottom < r.bottom - 2 || nr.top > r.top + 2;
          const ok = as.textOverflow === 'ellipsis' || (as.webkitLineClamp || 'none') !== 'none' || /auto|scroll/.test(as.overflow + as.overflowY) || a.classList.contains('peek');
          // a line sliced part-way (some of it showing, some not) is never deliberate, except inside a scroll area
          const lineH = r.bottom - r.top, shown = Math.max(0, nr.bottom - nr.top);
          const sliced = lineH > 4 && shown > lineH * 0.12 && shown < lineH * 0.88 && !/auto|scroll/.test(as.overflow + as.overflowY) && !a.classList.contains('peek');
          if ((cut && !ok) || sliced) badCut = true;
          r = nr; if (r.right <= r.left || r.bottom <= r.top) break;
        }
        if (badCut) issues.push({ kind: 'text cut off', where: label, el: name(el) });
        if (r.right <= r.left + 1 || r.bottom <= r.top + 1) continue;            // fully hidden on purpose (scrolled away / clamped)
        if (r.right > vw + 1 || r.left < -1) issues.push({ kind: 'off screen sideways', where: label, el: name(el) });
        if (scope !== el && (r.right > sr.right + 1 || r.left < sr.left - 1)) issues.push({ kind: 'sticks out of its box', where: label, el: name(el) });
        boxes.push({ el, r });
      }
    }
    // text on text
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      const A = boxes[i], B = boxes[j]; if (A.el === B.el || A.el.contains(B.el) || B.el.contains(A.el)) continue;
      const w = Math.min(A.r.right, B.r.right) - Math.max(A.r.left, B.r.left), h = Math.min(A.r.bottom, B.r.bottom) - Math.max(A.r.top, B.r.top);
      if (w > 2 && h > 2) issues.push({ kind: 'text overlaps text', where: label, el: name(A.el) + '  ×  ' + name(B.el) });
    }
  }
  // nothing wider than the screen
  if (document.documentElement.scrollWidth > vw + 1) issues.push({ kind: 'page scrolls sideways', where: label, el: 'document ' + document.documentElement.scrollWidth + 'px' });
  // buttons people must reach are not hidden under the tab bar or off the bottom
  const nav = document.querySelector('#nav'); const nr = nav && !nav.hidden ? nav.getBoundingClientRect() : { top: vh };
  for (const sel of ['#bPass', '#bSave', '#bBeen', '#bUndo', '.step:not([hidden]) .cta', '#tripDone']) {
    const b = document.querySelector(sel); if (!b || !vis(b)) continue; const r = b.getBoundingClientRect();
    const limit = b.closest('.sheet') ? vh : nr.top;
    if (r.bottom > limit + 1) issues.push({ kind: 'button hidden under the tab bar / off screen', where: label, el: sel });
  }
  return issues;
}

(async () => {
  const all = [];
  for (const bname of BROWSERS) {
    const browser = await pw[bname].launch();
    for (const ph of PHONES) {
      const ctx = await browser.newContext({ viewport: { width: ph.width, height: ph.height }, deviceScaleFactor: 2, isMobile: bname !== 'firefox', hasTouch: true });
      const page = await ctx.newPage();
      const errs = []; page.on('pageerror', e => errs.push(e.message));
      await page.route('**/*', r => {
        const u = r.request().url(), t = r.request().resourceType();
        if (u.includes('api.tfl.gov.uk')) return r.fulfill({ json: tfl(u), headers: { 'access-control-allow-origin': '*' } });
        if (u.includes('api.open-meteo.com')) return r.fulfill({ json: weather(), headers: { 'access-control-allow-origin': '*' } });
        if (u.includes('api.postcodes.io')) return r.fulfill({ json: { status: 200, result: { latitude: 51.4565, longitude: -0.0245, admin_ward: 'Ladywell' } }, headers: { 'access-control-allow-origin': '*' } });
        if (t === 'image' || u.includes('posthog')) return r.abort();
        return r.continue();
      });
      const where = s => `${bname} · ${ph.name} · ${s}`;
      const snap = async (s, issues) => { if (issues.length) { const f = path.join(OUT, `${bname}-${ph.width}-${s.replace(/[^a-z0-9]+/gi, '_').slice(0, 50)}.png`); await page.screenshot({ path: f }); issues.forEach(x => x.shot = path.relative(process.cwd(), f)); } all.push(...issues); };
      await page.goto(BASE);
      if (process.env.INJECT_CSS) await page.addInitScript(css => { document.addEventListener('DOMContentLoaded', () => { const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st); }); }, process.env.INJECT_CSS);
      await page.evaluate(sat => { localStorage.clear(); localStorage.setItem('wtd.places', JSON.stringify(['SE4 1QA', 'KT2 5RA', 'NW7 1LA', 'E17 4PP']));
        localStorage.setItem('wtd.setup', JSON.stringify({ who: 'family', date: sat, pc: 'SE4 1QA', lat: 51.4565, lon: -0.0245, place: 'Ladywell', modes: ['transit', 'bike', 'car'], ages: ['0-2', '3-5', '6-9', '10-13'] })); }, sat);
      await page.reload(); await page.waitForTimeout(1200);
      // setup steps
      for (const step of ['s-who', 's-when', 's-where']) {
        await page.evaluate(id => { go('setup', false); document.querySelectorAll('.step').forEach(s => s.hidden = s.id !== id); if (id === 's-where') renderWhere(); }, step);
        await page.waitForTimeout(150);
        await snap('setup ' + step, await page.evaluate(([sel, w]) => (eval('('+sel+')'))('.step:not([hidden]), .bar', w), [pageChecks.toString(), where('setup ' + step)]));
      }
      // deck: each card in turn as the top card
      await page.evaluate(() => go('deck', false)); await page.waitForTimeout(1500);
      const n = await page.evaluate(() => deck.length);
      if (n < 5) all.push({ kind: 'deck nearly empty (test setup broken?)', where: where('deck'), el: n + ' cards' });
      for (let i = 0; i < Math.min(CARDS, n); i++) {
        await page.evaluate(i => { if (i) { deck.push(deck.shift()); } renderStack(); }, i);
        await page.waitForTimeout(120);
        const nm = await page.evaluate(() => deck[0] && deck[0].name);
        await snap('card ' + (i + 1) + ' ' + nm, await page.evaluate(([sel, w]) => (eval('('+sel+')'))('#stack .card:not(.under):not(.under2), .strip, .actions, #nav', w), [pageChecks.toString(), where('card ' + (i + 1) + ' "' + nm + '"')]));
        if (i < 6) { // journey sheet for the first few
          await page.evaluate(() => openTrip(deck[0])); await page.waitForTimeout(250);
          await snap('trip ' + nm, await page.evaluate(([sel, w]) => (eval('('+sel+')'))('#tripSheet .panel', w), [pageChecks.toString(), where('journey sheet "' + nm + '"')]));
          await page.evaluate(() => { document.querySelector('#tripSheet').hidden = true; });
        }
      }
      // my list and map
      await page.evaluate(() => { deck.slice(0, 8).forEach(c => status[c.id] = 'saved'); save(); go('list'); }); await page.waitForTimeout(300);
      await snap('my list', await page.evaluate(([sel, w]) => (eval('('+sel+')'))('#v-list', w), [pageChecks.toString(), where('my list')]));
      await page.evaluate(() => go('map')); await page.waitForTimeout(400);
      await snap('map', await page.evaluate(([sel, w]) => (eval('('+sel+')'))('#v-map', w), [pageChecks.toString(), where('map')]));
      errs.forEach(m => all.push({ kind: 'script error', where: where('page'), el: m }));
      await ctx.close();
      console.log(`${bname} · ${ph.name}: checked`);
    }
    await browser.close();
  }
  // one line per distinct problem
  const seen = new Set(), uniq = all.filter(x => { const k = x.kind + x.where.split(' · ').slice(0, 2).join() + x.el; if (seen.has(k)) return false; seen.add(k); return true; });
  fs.writeFileSync(path.join(OUT, 'report.json'), JSON.stringify(uniq, null, 1));
  if (!uniq.length) { console.log('layout: all clear'); return; }
  console.log(`layout: ${uniq.length} problem(s)`);
  for (const x of uniq.slice(0, 80)) console.log(`  ✗ ${x.kind} — ${x.where} — ${x.el}${x.shot ? '  [' + x.shot + ']' : ''}`);
  process.exitCode = 1;
})().catch(e => { console.error(e); process.exitCode = 2; });
