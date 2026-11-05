# JauntOut illustration set: 720x240 strips, flat shapes, brand palette. Motifs sit in the middle band so cards crop well.
C = dict(bg="#1C3527", bg2="#16271D", bg3="#22382B", ink="#F2EEE3", ink2="#C2C8BE", mute="#86938A", verm="#EE6A3F",
         moss="#5DB58A", leaf="#2F6B47", amber="#E0A43A", amberd="#C4832A", sky="#7FA9CC", night="#122018", brown="#5B4632")
def svg(body, bg="bg", ground=None):
    g = f'<rect y="204" width="720" height="36" fill="{C[ground]}"/>' if ground else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 240" preserveAspectRatio="xMidYMid slice">'
            f'<rect width="720" height="240" fill="{C[bg]}"/>{g}{body.format(**C)}</svg>')
def dots(pts, col="ink", op=".5", r=2):
    return f'<g fill="{{{col}}}" opacity="{op}">' + "".join(f'<circle cx="{x}" cy="{y}" r="{r}"/>' for x, y in pts) + "</g>"
SPARK = [(40,40),(110,170),(640,60),(690,180),(80,110),(600,200),(30,200),(670,110)]
ART = {}

ART["theatre"] = svg(r'''
<path d="M0 0H720V30H0Z" fill="{verm}"/><path d="M0 30q30 18 60 0t60 0 60 0 60 0 60 0 60 0 60 0 60 0 60 0 60 0 60 0 60 0" fill="{verm}"/>
<path d="M0 0h110q-20 120 10 240H0Z" fill="#C2512C"/><path d="M720 0H610q20 120-10 240h120Z" fill="#C2512C"/>
<path d="M60 0q30 90 6 240" stroke="#A9441F" stroke-width="4" fill="none"/><path d="M660 0q-30 90-6 240" stroke="#A9441F" stroke-width="4" fill="none"/>
<path d="M200 0 L160 240 H560 L520 0Z" fill="{ink}" opacity=".05"/>
<g transform="translate(318 118) rotate(-12)"><path d="M-46-40h92q4 54-46 82q-50-28-46-82z" fill="{ink}"/>
 <path d="M-26-14q8-8 16 0M10-14q8-8 16 0" stroke="{night}" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M-20 12q20 18 40 0" stroke="{night}" stroke-width="5" fill="none" stroke-linecap="round"/></g>
<g transform="translate(402 128) rotate(14)"><path d="M-46-40h92q4 54-46 82q-50-28-46-82z" fill="{amber}"/>
 <path d="M-26-8q8-8 16 0M10-8q8-8 16 0" stroke="{night}" stroke-width="5" fill="none" stroke-linecap="round" transform="rotate(180 -18 -10) translate(-36 -20)"/>
 <path d="M-26-14q8 8 16 0M10-14q8 8 16 0" stroke="{night}" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M-20 22q20-18 40 0" stroke="{night}" stroke-width="5" fill="none" stroke-linecap="round"/></g>
<rect y="204" width="720" height="36" fill="#5B4632"/><rect y="204" width="720" height="5" fill="{amberd}" opacity=".6"/>''', bg="bg2")

ART["books"] = svg(r'''
''' + dots(SPARK) + r'''
<rect x="200" y="176" width="320" height="10" rx="3" fill="{brown}"/>
<g><rect x="232" y="150" width="150" height="26" rx="3" fill="{verm}"/><rect x="236" y="154" width="10" height="18" fill="{ink}" opacity=".5"/>
<rect x="244" y="124" width="132" height="26" rx="3" fill="{moss}"/><rect x="250" y="130" width="70" height="4" fill="{night}" opacity=".4"/>
<rect x="226" y="98" width="144" height="26" rx="3" fill="{amber}"/><rect x="352" y="102" width="8" height="18" fill="{night}" opacity=".3"/>
<rect x="250" y="74" width="118" height="24" rx="3" fill="{sky}"/></g>
<g transform="translate(470 120)"><path d="M-62 40 L-60-22 Q-30-36 0-24 Q30-36 60-22 L62 40 Q30 28 0 40 Q-30 28-62 40Z" fill="{ink}"/>
<path d="M0-24V40" stroke="{mute}" stroke-width="2"/>
<g stroke="{mute}" stroke-width="2"><path d="M-48-8q20-8 40 0M-48 4q20-8 40 0M-48 16q20-8 40 0M8-8q20-8 40 0M8 4q20-8 40 0M8 16q20-8 40 0"/></g></g>
<g transform="translate(166 70)"><path d="M0-14l4 10 10 4-10 4-4 10-4-10-10-4 10-4z" fill="{amber}"/></g>''', ground=None)

ART["park"] = svg(r'''
<circle cx="560" cy="70" r="30" fill="{amber}"/>
<path d="M0 170 Q160 120 340 160 T720 150 V240H0Z" fill="{leaf}"/><path d="M0 200 Q200 160 400 196 T720 190 V240H0Z" fill="#3F7F57"/>
<path d="M300 240 Q350 200 330 170 Q320 160 360 150" stroke="{ink2}" stroke-width="16" fill="none" opacity=".35" stroke-linecap="round"/>
<g transform="translate(220 0)"><rect x="-6" y="120" width="12" height="60" fill="{brown}"/><circle cy="100" r="44" fill="{moss}"/><circle cx="-26" cy="122" r="26" fill="{moss}"/><circle cx="26" cy="120" r="28" fill="{moss}"/></g>
<g transform="translate(450 10)"><rect x="-5" y="120" width="10" height="50" fill="{brown}"/><path d="M0 40 L36 130 H-36Z" fill="#3F7F57"/><path d="M0 70 L44 150 H-44Z" fill="{moss}"/></g>
<g transform="translate(120 20)"><rect x="-4" y="120" width="8" height="40" fill="{brown}"/><circle cy="112" r="26" fill="#3F7F57"/></g>
<g transform="translate(560 140)"><rect x="-28" y="0" width="56" height="7" rx="2" fill="{brown}"/><rect x="-24" y="7" width="5" height="16" fill="{brown}"/><rect x="19" y="7" width="5" height="16" fill="{brown}"/><rect x="-28" y="-16" width="56" height="6" rx="2" fill="{brown}"/></g>
<g fill="{ink}" opacity=".8"><path d="M90 60q8-6 16 0q8-6 16 0" stroke="{ink}" stroke-width="3" fill="none"/><path d="M380 44q6-5 12 0q6-5 12 0" stroke="{ink}" stroke-width="3" fill="none"/></g>''', bg="bg")

ART["wildlife"] = svg(r'''
<circle cx="560" cy="66" r="34" fill="{ink}" opacity=".9"/><circle cx="574" cy="58" r="30" fill="{bg2}"/>
''' + dots(SPARK) + r'''
<path d="M180 150 Q360 130 540 150" stroke="{brown}" stroke-width="10" fill="none" stroke-linecap="round"/>
<g transform="translate(330 112)"><ellipse rx="40" ry="48" fill="{amberd}"/><ellipse cy="12" rx="26" ry="32" fill="{amber}"/>
<path d="M-36-38l8 18 10-14zM36-38l-8 18-10-14z" fill="{amberd}"/>
<circle cx="-15" cy="-16" r="14" fill="{ink}"/><circle cx="15" cy="-16" r="14" fill="{ink}"/><circle cx="-15" cy="-16" r="7" fill="{night}"/><circle cx="15" cy="-16" r="7" fill="{night}"/>
<path d="M-6-4l6 10 6-10z" fill="{verm}"/><g fill="{brown}"><path d="M-14 26q4 4 8 0M-2 34q4 4 8 0M8 24q4 4 8 0"/></g>
<path d="M-14 46l-4 8M14 46l4 8" stroke="{amber}" stroke-width="4" stroke-linecap="round"/></g>
<g fill="{moss}"><path d="M150 240 Q154 160 170 120 Q164 180 168 240Z"/><path d="M170 240 Q180 170 200 140 Q186 200 186 240Z"/><path d="M560 240 Q566 170 580 136 Q574 190 576 240Z"/><path d="M584 240 Q590 186 612 160 Q598 206 600 240Z"/></g>
<g transform="translate(470 120)"><path d="M0 0q-14-16-28-2q14 4 28 2zM0 0q14-16 28-2q-14 4-28 2z" fill="{sky}"/><rect x="-2" y="-6" width="4" height="12" rx="2" fill="{night}"/></g>''', bg="bg2")

ART["film"] = svg(r'''
<path d="M410 112 L720 40 V200 Z" fill="{ink}" opacity=".08"/>
<g transform="translate(300 128)"><rect x="-70" y="-28" width="110" height="64" rx="8" fill="{mute}"/><circle cx="-40" cy="-54" r="30" fill="{ink2}"/><circle cx="16" cy="-50" r="26" fill="{ink2}"/>
<circle cx="-40" cy="-54" r="10" fill="{night}"/><circle cx="16" cy="-50" r="9" fill="{night}"/><path d="M40-10 L76-24 V24 L40 10Z" fill="{ink2}"/><circle cx="-50" cy="4" r="8" fill="{verm}"/>
<rect x="-56" y="36" width="10" height="24" fill="{mute}"/><rect x="18" y="36" width="10" height="24" fill="{mute}"/></g>
<g transform="translate(120 70) rotate(-10)"><rect width="120" height="40" fill="{night}"/><g fill="{ink}" opacity=".7"><rect x="6" y="4" width="10" height="6"/><rect x="26" y="4" width="10" height="6"/><rect x="46" y="4" width="10" height="6"/><rect x="66" y="4" width="10" height="6"/><rect x="86" y="4" width="10" height="6"/><rect x="106" y="4" width="10" height="6"/>
<rect x="6" y="30" width="10" height="6"/><rect x="26" y="30" width="10" height="6"/><rect x="46" y="30" width="10" height="6"/><rect x="66" y="30" width="10" height="6"/><rect x="86" y="30" width="10" height="6"/><rect x="106" y="30" width="10" height="6"/></g>
<rect x="8" y="13" width="30" height="14" fill="{amber}"/><rect x="46" y="13" width="30" height="14" fill="{sky}"/><rect x="84" y="13" width="30" height="14" fill="{verm}"/></g>
<g transform="translate(540 150) rotate(8)"><rect x="-50" y="-10" width="100" height="56" rx="4" fill="{night}"/><path d="M-50-30 L50-44 L52-30 L-48-16Z" fill="{ink}"/><path d="M-30-27l14 12M-6-30l14 12M18-34l14 12" stroke="{night}" stroke-width="6"/>
<rect x="-50" y="-10" width="100" height="10" fill="{ink}"/><path d="M-36-10l14 10M-12-10l14 10M12-10l14 10" stroke="{night}" stroke-width="6"/></g>''', bg="bg2")

ART["dance"] = svg(r'''
<path d="M360 0V44" stroke="{mute}" stroke-width="3"/>
<g transform="translate(360 90)"><circle r="46" fill="{ink2}"/><g fill="{ink}"><rect x="-34" y="-22" width="14" height="12"/><rect x="-14" y="-36" width="14" height="12"/><rect x="6" y="-22" width="14" height="12"/><rect x="-24" y="2" width="14" height="12"/><rect x="0" y="12" width="14" height="12"/><rect x="18" y="-4" width="14" height="12"/></g>
<g fill="{sky}"><rect x="-4" y="-12" width="14" height="12"/><rect x="-40" y="-2" width="12" height="12"/><rect x="26" y="-30" width="10" height="10"/></g></g>
<g stroke-linecap="round" stroke-width="6"><path d="M300 110 L150 230" stroke="{verm}" opacity=".5"/><path d="M420 110 L570 230" stroke="{amber}" opacity=".5"/><path d="M360 140 L360 240" stroke="{moss}" opacity=".5"/><path d="M330 130 L250 240" stroke="{sky}" opacity=".4"/><path d="M390 130 L470 240" stroke="{ink}" opacity=".3"/></g>
''' + dots([(80,60),(140,40),(620,50),(660,110),(90,150),(590,170)], "amber", ".8", 3) + r'''
<rect y="214" width="720" height="26" fill="{night}"/><g fill="{bg3}"><rect x="0" y="214" width="60" height="26"/><rect x="120" y="214" width="60" height="26"/><rect x="240" y="214" width="60" height="26"/><rect x="360" y="214" width="60" height="26"/><rect x="480" y="214" width="60" height="26"/><rect x="600" y="214" width="60" height="26"/></g>''', bg="bg2")

ART["craft"] = svg(r'''
''' + dots(SPARK) + r'''
<g transform="translate(300 124)"><path d="M-70 0 Q-80-56-10-60 Q70-62 74-10 Q76 30 30 24 Q8 22 10 44 Q12 66-30 58 Q-66 50-70 0Z" fill="{ink}"/><circle cx="16" cy="40" r="0" fill="{bg}"/>
<circle cx="-40" cy="-20" r="12" fill="{verm}"/><circle cx="-6" cy="-36" r="12" fill="{amber}"/><circle cx="32" cy="-30" r="12" fill="{moss}"/><circle cx="46" cy="2" r="11" fill="{sky}"/><circle cx="-40" cy="18" r="11" fill="{night}"/></g>
<g transform="translate(450 80) rotate(35)"><rect x="-5" y="0" width="10" height="110" rx="4" fill="{amberd}"/><rect x="-6" y="-10" width="12" height="16" fill="{ink2}"/><path d="M-6-10 Q0-40 6-10Z" fill="{verm}"/></g>
<g transform="translate(500 150)"><circle cx="-14" cy="22" r="11" fill="none" stroke="{verm}" stroke-width="6"/><circle cx="14" cy="22" r="11" fill="none" stroke="{verm}" stroke-width="6"/><path d="M-8 12 L20-44 M8 12 L-20-44" stroke="{ink2}" stroke-width="6" stroke-linecap="round"/></g>
<g transform="translate(170 160)"><circle r="26" fill="{amber}"/><path d="M-26 0q26-14 52 0M-20-16q20 8 40 0M-20 16q20-8 40 0" stroke="{amberd}" stroke-width="3" fill="none"/><path d="M20 18 Q40 40 60 30" stroke="{amber}" stroke-width="3" fill="none"/></g>''', bg="bg3")

ART["food"] = svg(r'''
<g stroke="{ink}" stroke-width="4" fill="none" opacity=".5" stroke-linecap="round"><path d="M330 60q-10-14 0-28t0-28"/><path d="M360 56q-10-14 0-28t0-28"/><path d="M390 60q-10-14 0-28t0-28"/></g>
<ellipse cx="360" cy="176" rx="150" ry="16" fill="{night}" opacity=".5"/>
<g transform="translate(360 118)"><path d="M-96 0 H96 Q92 56 0 60 Q-92 56-96 0Z" fill="{verm}"/><path d="M-96 0 H96" stroke="{ink}" stroke-width="6" stroke-linecap="round"/>
<path d="M-70 0 Q-60-26-30-14 Q-10-34 14-16 Q40-32 64-10 L70 0Z" fill="{amber}"/><circle cx="-30" cy="-10" r="9" fill="{moss}"/><circle cx="20" cy="-14" r="8" fill="{ink}"/><circle cx="50" cy="-8" r="7" fill="{moss}"/><circle cx="-4" cy="-6" r="6" fill="#C2512C"/></g>
<g transform="translate(190 150) rotate(-20)"><rect x="-4" y="-60" width="8" height="90" rx="3" fill="{ink2}"/><path d="M-12-60v26q12 8 24 0v-26" stroke="{ink2}" stroke-width="5" fill="none"/></g>
<g transform="translate(540 150) rotate(20)"><rect x="-4" y="-20" width="8" height="60" rx="3" fill="{ink2}"/><path d="M0-62 Q16-40 4-18 H-4 Q-12-40 0-62Z" fill="{ink2}"/></g>''', bg="bg2")

ART["museum"] = svg(r'''
<g transform="translate(250 0)"><path d="M-80 70 L0 30 L80 70Z" fill="{ink}"/><rect x="-80" y="70" width="160" height="10" fill="{ink2}"/>
<g fill="{ink}"><rect x="-70" y="84" width="16" height="96"/><rect x="-34" y="84" width="16" height="96"/><rect x="2" y="84" width="16" height="96"/><rect x="38" y="84" width="16" height="96"/></g>
<rect x="-86" y="180" width="172" height="12" fill="{ink2}"/><rect x="-96" y="192" width="192" height="12" fill="{ink}"/></g>
<g transform="translate(470 110)"><rect x="-64" y="-50" width="128" height="96" fill="{amber}"/><rect x="-54" y="-40" width="108" height="76" fill="{sky}"/>
<path d="M-54 36 L-20-4 L4 20 L24 0 L54 36Z" fill="{leaf}"/><circle cx="28" cy="-18" r="10" fill="{ink}"/></g>
<rect x="430" y="176" width="80" height="6" rx="3" fill="{mute}"/>''', bg="bg3", ground="bg2")

ART["science"] = svg(r'''
''' + dots(SPARK) + r'''
<g transform="translate(300 124)"><path d="M-14-70 H14 V-20 L50 44 Q56 58 40 58 H-40 Q-56 58-50 44 L-14-20Z" fill="{ink}" opacity=".95"/><path d="M-38 30 H38 L50 44 Q56 58 40 58 H-40 Q-56 58-50 44Z" fill="{moss}"/>
<circle cx="-12" cy="40" r="6" fill="{ink}"/><circle cx="14" cy="34" r="4" fill="{ink}"/><rect x="-20" y="-76" width="40" height="10" rx="3" fill="{ink2}"/>
<circle cx="0" cy="-92" r="6" fill="{moss}" opacity=".7"/><circle cx="10" cy="-108" r="4" fill="{moss}" opacity=".5"/></g>
<g transform="translate(470 110)" fill="none" stroke-width="5"><ellipse rx="62" ry="22" stroke="{amber}"/><ellipse rx="62" ry="22" stroke="{sky}" transform="rotate(60)"/><ellipse rx="62" ry="22" stroke="{verm}" transform="rotate(-60)"/></g>
<circle cx="470" cy="110" r="12" fill="{ink}"/>''', bg="bg2")

ART["sport"] = svg(r'''
<rect y="150" width="720" height="90" fill="{leaf}"/><g fill="#3F7F57"><rect x="0" y="150" width="80" height="90"/><rect x="160" y="150" width="80" height="90"/><rect x="320" y="150" width="80" height="90"/><rect x="480" y="150" width="80" height="90"/><rect x="640" y="150" width="80" height="90"/></g>
<g transform="translate(470 0)"><path d="M-90 150 V64 H90 V150" stroke="{ink}" stroke-width="8" fill="none"/><g stroke="{ink}" stroke-width="1.5" opacity=".35"><path d="M-80 70V150M-60 70V150M-40 70V150M-20 70V150M0 70V150M20 70V150M40 70V150M60 70V150M80 70V150M-86 84H86M-86 104H86M-86 124H86M-86 144H86"/></g></g>
<g transform="translate(260 150)"><circle r="34" fill="{ink}"/><path d="M0-12 L11-4 L7 10 H-7 L-11-4Z" fill="{night}"/><path d="M0-12V-34M11-4 L30-14M7 10 L20 28M-7 10 L-20 28M-11-4 L-30-14" stroke="{night}" stroke-width="3"/></g>
<g stroke="{ink}" stroke-width="4" opacity=".5" stroke-linecap="round"><path d="M200 136h-40M206 154h-60M200 172h-36"/></g>''', bg="bg2")

ART["kids"] = svg(r'''
''' + dots(SPARK) + r'''
<g><path d="M280 130 Q270 180 300 230" stroke="{ink2}" stroke-width="2" fill="none"/><ellipse cx="280" cy="96" rx="30" ry="36" fill="{verm}"/><path d="M276 132 l4-6 4 6z" fill="{verm}"/>
<path d="M330 120 Q340 180 312 236" stroke="{ink2}" stroke-width="2" fill="none"/><ellipse cx="332" cy="84" rx="28" ry="34" fill="{amber}"/><path d="M328 118 l4-6 4 6z" fill="{amber}"/>
<path d="M240 140 Q250 190 236 236" stroke="{ink2}" stroke-width="2" fill="none"/><ellipse cx="238" cy="112" rx="24" ry="30" fill="{sky}"/><path d="M234 142 l4-6 4 6z" fill="{sky}"/>
<ellipse cx="258" cy="84" rx="6" ry="9" fill="{ink}" opacity=".35"/><ellipse cx="312" cy="72" rx="6" ry="9" fill="{ink}" opacity=".35"/></g>
<g transform="translate(480 90) rotate(20)"><path d="M0-50 L34 0 L0 50 L-34 0Z" fill="{moss}"/><path d="M0-50 V50M-34 0H34" stroke="{leaf}" stroke-width="3"/>
<path d="M0 50 Q20 80 0 100 Q-20 120 10 150" stroke="{ink}" stroke-width="2" fill="none"/><path d="M4 76l10-4-2 10zM-4 104l-10-2 6 8z" fill="{verm}"/></g>''', bg="bg")

ART["comedy"] = svg(r'''
<path d="M360 0 L250 240 H470Z" fill="{ink}" opacity=".08"/>
<rect y="204" width="720" height="36" fill="{verm}" opacity=".7"/>
<g transform="translate(360 0)"><rect x="-3" y="120" width="6" height="84" fill="{mute}"/><path d="M-30 204 h60" stroke="{mute}" stroke-width="6" stroke-linecap="round"/>
<path d="M0 120 L-40 100" stroke="{mute}" stroke-width="5"/><g transform="translate(-48 92) rotate(-30)"><rect x="-14" y="-6" width="28" height="44" rx="12" fill="{night}"/><rect x="-18" y="-40" width="36" height="40" rx="18" fill="{ink2}"/>
<g stroke="{mute}" stroke-width="2"><path d="M-16-26h32M-17-16h34M-16-6h32"/></g></g></g>
<g fill="{amber}"><path d="M480 90l4 12 12 4-12 4-4 12-4-12-12-4 12-4z"/><path d="M230 70l3 9 9 3-9 3-3 9-3-9-9-3 9-3z"/></g>
<g font-family="Georgia,serif" font-size="34" fill="{ink}" opacity=".85"><text x="440" y="70">ha</text><text x="500" y="128" font-size="26">ha</text><text x="196" y="140" font-size="24" opacity=".7">ha</text></g>''', bg="bg2")

ART["skating"] = svg(r'''
''' + dots(SPARK, "ink", ".7", 2.4) + r'''
<rect y="176" width="720" height="64" fill="#A8C7DC"/><g stroke="{ink}" stroke-width="3" opacity=".6" fill="none" stroke-linecap="round"><path d="M120 200 q80-20 160 0 t160 0"/><path d="M380 222 q60-14 120 0"/></g>
<g transform="translate(360 60)"><path d="M-40 0 h50 v50 q40 6 46 30 v8 h-96Z" fill="{ink}"/><path d="M-40 88 h96" stroke="{mute}" stroke-width="4"/>
<path d="M-50 100 H70 Q80 100 78 92" stroke="{ink2}" stroke-width="5" fill="none" stroke-linecap="round"/><path d="M-30 92 v8M40 92 v8" stroke="{ink2}" stroke-width="4"/>
<g stroke="{verm}" stroke-width="3"><path d="M-6 16 l14 6M-6 28 l14 6M-6 40 l14 6"/></g><rect x="-40" y="0" width="50" height="10" fill="{verm}"/></g>''', bg="bg")
