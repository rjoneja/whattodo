from draw1 import C, svg, dots, SPARK, ART

ART["quiz"] = svg(r'''
<g font-family="Georgia,serif" font-weight="700" fill="{amber}"><text x="210" y="160" font-size="110">?</text><text x="470" y="140" font-size="80" fill="{sky}">?</text><text x="140" y="110" font-size="44" fill="{ink}" opacity=".5">?</text><text x="580" y="200" font-size="50" fill="{ink}" opacity=".5">?</text></g>
<g transform="translate(360 104)"><circle r="42" fill="{amber}"/><path d="M-18 40 h36 v16 h-36z" fill="{ink2}"/><path d="M-14 64 h28" stroke="{mute}" stroke-width="6" stroke-linecap="round"/>
<path d="M-12 30 V10 Q-12 0 0 0 Q12 0 12 10 V30" stroke="{amberd}" stroke-width="4" fill="none"/>
<g stroke="{amber}" stroke-width="5" stroke-linecap="round"><path d="M0-58v-16M-44-42l-11-11M44-42l11-11M-60 0h-16M60 0h16"/></g></g>''', bg="bg2")

ART["yoga"] = svg(r'''
<circle cx="360" cy="110" r="70" fill="{amber}" opacity=".9"/><circle cx="360" cy="110" r="94" fill="none" stroke="{amber}" stroke-width="2" opacity=".35"/>
<rect y="170" width="720" height="70" fill="{sky}" opacity=".25"/><g stroke="{ink}" stroke-width="3" opacity=".3" fill="none"><path d="M100 196 q40-10 80 0M480 210 q50-12 100 0"/></g>
<g transform="translate(360 168)"><path d="M0 0 Q-20-50 0-86 Q20-50 0 0Z" fill="{ink}"/><path d="M0 0 Q-50-30-46-70 Q-14-46 0 0Z" fill="{ink2}"/><path d="M0 0 Q50-30 46-70 Q14-46 0 0Z" fill="{ink2}"/>
<path d="M0 0 Q-70-6-84-36 Q-40-34 0 0Z" fill="{moss}"/><path d="M0 0 Q70-6 84-36 Q40-34 0 0Z" fill="{moss}"/><ellipse cy="4" rx="70" ry="8" fill="{leaf}"/></g>''', bg="bg2")

ART["farm"] = svg(r'''
<circle cx="600" cy="60" r="26" fill="{amber}"/>
<path d="M0 170 Q200 150 400 170 T720 166 V240H0Z" fill="{leaf}"/>
<g transform="translate(200 0)"><path d="M-60 100 L0 60 L60 100 V180 H-60Z" fill="{verm}"/><path d="M-70 104 L0 54 L70 104" stroke="{ink}" stroke-width="6" fill="none"/>
<rect x="-22" y="124" width="44" height="56" fill="{ink}"/><path d="M-22 124 L22 180 M22 124 L-22 180" stroke="{verm}" stroke-width="4"/><rect x="-12" y="84" width="24" height="18" fill="{ink}"/></g>
<g stroke="{ink2}" stroke-width="5"><path d="M300 150 H700 M300 172 H700"/><path d="M320 140V190M400 140V190M480 140V190M560 140V190M640 140V190"/></g>
<g transform="translate(460 128)"><ellipse rx="44" ry="26" fill="{ink}"/><rect x="-32" y="18" width="7" height="30" fill="{ink2}"/><rect x="22" y="18" width="7" height="30" fill="{ink2}"/>
<g transform="translate(46 -20)"><ellipse rx="16" ry="20" fill="{ink}" transform="rotate(30)"/><path d="M-6-18 Q-20-40-4-46M6-18 Q12-40 26-40" stroke="{mute}" stroke-width="5" fill="none" stroke-linecap="round"/><circle cx="8" cy="-4" r="3" fill="{night}"/><path d="M14 16 q-2 12-10 14" stroke="{ink2}" stroke-width="4" fill="none"/></g>
<path d="M-44-6 q-14 4-14 16" stroke="{ink}" stroke-width="6" fill="none" stroke-linecap="round"/></g>''', bg="bg")

ART["boats"] = svg(r'''
<circle cx="560" cy="70" r="28" fill="{amber}"/>
<rect y="160" width="720" height="80" fill="#2F5E73"/><g stroke="{sky}" stroke-width="4" opacity=".6" fill="none" stroke-linecap="round"><path d="M60 190 q30-12 60 0t60 0M420 210 q30-12 60 0t60 0 60 0M240 222 q30-12 60 0"/></g>
<g transform="translate(340 0)"><path d="M-80 156 H80 L60 182 H-60Z" fill="{verm}"/><rect x="-3" y="40" width="6" height="116" fill="{ink2}"/><path d="M4 46 L70 146 H4Z" fill="{ink}"/><path d="M-4 66 L-56 146 H-4Z" fill="{ink2}"/><path d="M3 40 l24 8 -24 8z" fill="{amber}"/></g>
<g fill="{ink}" opacity=".7" stroke="{ink}" stroke-width="3"><path d="M140 70q8-6 16 0q8-6 16 0" fill="none"/><path d="M190 50q6-5 12 0q6-5 12 0" fill="none"/></g>''', bg="bg")

ART["trains"] = svg(r'''
<g fill="{ink}" opacity=".35"><circle cx="230" cy="58" r="20"/><circle cx="196" cy="40" r="26"/><circle cx="150" cy="30" r="20"/><circle cx="110" cy="38" r="14"/></g>
<rect y="196" width="720" height="8" fill="{mute}"/><g fill="{brown}"><rect x="20" y="204" width="30" height="8"/><rect x="100" y="204" width="30" height="8"/><rect x="180" y="204" width="30" height="8"/><rect x="260" y="204" width="30" height="8"/><rect x="340" y="204" width="30" height="8"/><rect x="420" y="204" width="30" height="8"/><rect x="500" y="204" width="30" height="8"/><rect x="580" y="204" width="30" height="8"/><rect x="660" y="204" width="30" height="8"/></g>
<g transform="translate(300 0)"><rect x="-40" y="110" width="150" height="56" rx="10" fill="{moss}"/><rect x="70" y="70" width="70" height="96" rx="6" fill="{leaf}"/><rect x="84" y="84" width="42" height="30" rx="4" fill="{amber}"/>
<rect x="-24" y="80" width="22" height="30" fill="{night}"/><rect x="-30" y="72" width="34" height="10" fill="{night}"/><path d="M-60 166 L-40 130 V166Z" fill="{verm}"/><rect x="-40" y="140" width="180" height="8" fill="{amber}"/>
<g fill="{night}"><circle cx="-14" cy="178" r="18"/><circle cx="40" cy="178" r="18"/><circle cx="110" cy="174" r="22"/></g><g fill="{ink2}"><circle cx="-14" cy="178" r="7"/><circle cx="40" cy="178" r="7"/><circle cx="110" cy="174" r="8"/></g>
<path d="M-14 178 H110" stroke="{ink2}" stroke-width="5"/></g>''', bg="bg2", ground="bg3")

ART["diwali"] = svg(r'''
''' + dots(SPARK, "amber", ".8", 2.4) + r'''
<defs><g id="d"><path d="M-40 0 Q0 34 40 0Z" fill="{verm}"/><path d="M-40 0 H40" stroke="{amber}" stroke-width="5" stroke-linecap="round"/><path d="M0-6 Q-14-30 0-52 Q14-30 0-6Z" fill="{amber}"/><path d="M0-10 Q-6-22 0-34 Q6-22 0-10Z" fill="{ink}"/></g></defs>
<use href="#d" x="360" y="150"/><use href="#d" x="240" y="164" transform="translate(240 164) scale(.8) translate(-240 -164)"/><use href="#d" x="480" y="164" transform="translate(480 164) scale(.8) translate(-480 -164)"/>
<g fill="none" stroke-width="3" opacity=".6"><circle cx="360" cy="110" r="70" stroke="{amber}" stroke-dasharray="4 10"/><circle cx="360" cy="110" r="96" stroke="{verm}" stroke-dasharray="2 14"/></g>
<g transform="translate(140 80)"><g fill="{moss}"><ellipse rx="8" ry="18"/><ellipse rx="8" ry="18" transform="rotate(45)"/><ellipse rx="8" ry="18" transform="rotate(90)"/><ellipse rx="8" ry="18" transform="rotate(135)"/></g><circle r="7" fill="{amber}"/></g>
<g transform="translate(590 90)"><g fill="{verm}"><ellipse rx="8" ry="18"/><ellipse rx="8" ry="18" transform="rotate(45)"/><ellipse rx="8" ry="18" transform="rotate(90)"/><ellipse rx="8" ry="18" transform="rotate(135)"/></g><circle r="7" fill="{amber}"/></g>''', bg="bg2")

ART["remembrance"] = svg(r'''
<defs><g id="p"><g fill="#D8432B"><circle cx="-12" cy="-8" r="16"/><circle cx="12" cy="-8" r="16"/><circle cx="-10" cy="12" r="16"/><circle cx="10" cy="12" r="16"/></g><circle r="9" fill="{night}"/><path d="M0 26 Q4 60 0 90" stroke="{leaf}" stroke-width="4" fill="none"/></g></defs>
<use href="#p" x="360" y="100"/><use href="#p" x="280" y="128"/><use href="#p" x="440" y="124"/><use href="#p" x="200" y="150"/><use href="#p" x="520" y="152"/>
<path d="M0 200 Q360 180 720 200 V240H0Z" fill="{leaf}"/>''', bg="bg2")

ART["halloween"] = svg(r'''
<circle cx="560" cy="64" r="34" fill="{ink}" opacity=".9"/>''' + dots(SPARK) + r'''
<defs><g id="k"><ellipse rx="52" ry="40" fill="{verm}"/><ellipse rx="20" ry="40" fill="#C2512C"/><path d="M-4-40 q2-14 12-18" stroke="{leaf}" stroke-width="8" fill="none" stroke-linecap="round"/>
<path d="M-26-8 l10-12 10 12z M6-8 l10-12 10 12z" fill="{amber}"/><path d="M-28 12 q28 20 56 0 l-8 8 -8-6 -8 8 -8-8 -8 6z" fill="{amber}"/></g></defs>
<use href="#k" x="320" y="160"/><use href="#k" x="440" y="176" transform="translate(440 176) scale(.7) translate(-440 -176)"/>''', bg="bg2", ground="night")

ART["fireworks"] = svg(r'''
<g stroke-linecap="round" stroke-width="5">
<g transform="translate(260 90)" stroke="{amber}"><path d="M0-50V-20M0 20V50M-50 0H-20M20 0H50M-36-36l20 20M16 16l20 20M36-36l-20 20M-16 16l-20 20"/></g>
<g transform="translate(470 80)" stroke="{verm}"><path d="M0-60V-26M0 26V60M-60 0H-26M26 0H60M-42-42l22 22M20 20l22 22M42-42l-22 22M-20 20l-22 22"/></g>
<g transform="translate(370 140)" stroke="{sky}" stroke-width="4"><path d="M0-36V-14M0 14V36M-36 0H-14M14 0H36M-26-26l14 14M12 12l14 14M26-26l-14 14M-12 12l-14 14"/></g></g>
''' + dots([(260,90),(470,80),(370,140)], "ink", "1", 5) + dots([(200,40),(320,50),(540,150),(600,40),(150,140),(420,30)], "amber", ".9", 3) + r'''
<path d="M0 214 L60 190 L110 204 L170 176 L230 200 L300 186 L360 206 L430 180 L500 200 L560 184 L630 204 L720 186 V240H0Z" fill="{night}"/>''', bg="bg2")

ART["talks"] = svg(r'''
<g transform="translate(260 96)"><rect x="-80" y="-44" width="160" height="80" rx="20" fill="{ink}"/><path d="M-40 36 L-56 66 L-10 36Z" fill="{ink}"/><g fill="{mute}"><rect x="-54" y="-18" width="108" height="8" rx="4"/><rect x="-54" y="0" width="70" height="8" rx="4"/></g></g>
<g transform="translate(450 120)"><rect x="-70" y="-36" width="140" height="70" rx="20" fill="{amber}"/><path d="M40 34 L58 62 L10 34Z" fill="{amber}"/><g fill="{night}" opacity=".4"><circle cx="-26" r="7"/><circle r="7"/><circle cx="26" r="7"/></g></g>
''' + dots(SPARK), bg="bg3")

ART["history"] = svg(r'''
<g transform="translate(300 0)"><rect x="-80" y="80" width="160" height="124" fill="{ink2}"/><g fill="{ink2}"><rect x="-80" y="60" width="24" height="24"/><rect x="-40" y="60" width="24" height="24"/><rect x="0" y="60" width="24" height="24"/><rect x="40" y="60" width="24" height="24"/></g>
<rect x="-110" y="40" width="40" height="164" fill="{ink}"/><rect x="70" y="40" width="40" height="164" fill="{ink}"/><g fill="{ink}"><rect x="-114" y="26" width="12" height="16"/><rect x="-96" y="26" width="12" height="16"/><rect x="-78" y="26" width="12" height="16"/><rect x="66" y="26" width="12" height="16"/><rect x="84" y="26" width="12" height="16"/><rect x="102" y="26" width="12" height="16"/></g>
<path d="M-24 204 V150 Q0 124 24 150 V204Z" fill="{brown}"/><rect x="-96" y="70" width="12" height="22" rx="6" fill="{night}"/><rect x="84" y="70" width="12" height="22" rx="6" fill="{night}"/>
<path d="M90 26 V-4" stroke="{mute}" stroke-width="3"/><path d="M92-4 h34 l-8 10 8 10 h-34z" fill="{verm}"/></g>
<g transform="translate(500 140) rotate(-8)"><rect x="-40" y="-30" width="80" height="60" fill="{amber}"/><circle cx="-40" cy="0" r="10" fill="{amberd}"/><circle cx="40" cy="0" r="10" fill="{amberd}"/><g stroke="{amberd}" stroke-width="3"><path d="M-26-12h52M-26 0h40M-26 12h48"/></g></g>''', bg="bg2", ground="leaf")

ART["choir"] = svg(r'''
<g transform="translate(360 0)"><path d="M-60 204 V110 Q0 30 60 110 V204Z" fill="{bg3}"/><path d="M-60 204 V110 Q0 30 60 110 V204Z" fill="none" stroke="{ink2}" stroke-width="5"/>
<path d="M-40 204 V120 Q0 60 40 120 V204" fill="none" stroke="{ink2}" stroke-width="3" opacity=".5"/><path d="M-40 150 H40 M0 70 V204" stroke="{ink2}" stroke-width="3" opacity=".5"/>
<g fill="{sky}" opacity=".7"><path d="M-36 146 V122 Q-20 92 -4 86 V146Z"/><path d="M4 146 V86 Q20 92 36 122 V146Z"/></g><g fill="{amber}" opacity=".7"><rect x="-36" y="154" width="32" height="46"/><rect x="4" y="154" width="32" height="46"/></g></g>
<g transform="translate(200 120)"><rect x="-8" y="0" width="16" height="70" rx="3" fill="{ink}"/><path d="M0 0 Q-10-20 0-36 Q10-20 0 0Z" fill="{amber}"/></g>
<g transform="translate(520 130)"><rect x="-8" y="0" width="16" height="60" rx="3" fill="{ink}"/><path d="M0 0 Q-10-20 0-36 Q10-20 0 0Z" fill="{amber}"/></g>
<g fill="{ink}" opacity=".8"><ellipse cx="130" cy="80" rx="9" ry="7" transform="rotate(-20 130 80)"/><rect x="137" y="40" width="3.5" height="40"/><ellipse cx="600" cy="70" rx="9" ry="7" transform="rotate(-20 600 70)"/><rect x="607" y="30" width="3.5" height="40"/><path d="M610.5 30 q16 4 16 20 q-4-10-16-10z"/></g>''', bg="bg2", ground="night")

ART["swim"] = svg(r'''
<circle cx="580" cy="60" r="28" fill="{amber}"/>
<rect y="120" width="720" height="120" fill="#3B8FA8"/><g fill="none" stroke="{ink}" stroke-width="5" opacity=".7" stroke-linecap="round"><path d="M40 150 q30-14 60 0t60 0 60 0M420 170 q30-14 60 0t60 0 60 0M200 200 q30-14 60 0t60 0 60 0"/></g>
<g stroke="{verm}" stroke-width="6"><path d="M0 130 H720" stroke-dasharray="20 14"/></g>
<g transform="translate(340 140)"><circle r="40" fill="none" stroke="{verm}" stroke-width="20"/><circle r="40" fill="none" stroke="{ink}" stroke-width="20" stroke-dasharray="31.4 31.4"/></g>''', bg="bg")

ART["cycling"] = svg(r'''
<g transform="translate(360 140)" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="-80" cy="20" r="46" stroke="{ink}" stroke-width="8"/><circle cx="80" cy="20" r="46" stroke="{ink}" stroke-width="8"/>
<circle cx="-80" cy="20" r="5" fill="{ink}"/><circle cx="80" cy="20" r="5" fill="{ink}"/><path d="M-80 20 L-20 20 L36-40 L-30-40 Z M-20 20 L-40-56 M36-40 L80 20 M30-60 L36-40" stroke="{verm}" stroke-width="8"/>
<path d="M-56-58 h32" stroke="{night}" stroke-width="10"/><path d="M18-62 q14-6 26 2" stroke="{ink2}" stroke-width="7"/><circle cx="-20" cy="20" r="11" stroke="{amber}" stroke-width="5"/></g>
<rect y="210" width="720" height="30" fill="{bg3}"/><path d="M0 210 H720" stroke="{amber}" stroke-width="3" stroke-dasharray="30 20" opacity=".6"/>''', bg="bg2")

ART["running"] = svg(r'''
<rect y="150" width="720" height="90" fill="#B5553A"/><g stroke="{ink}" stroke-width="3" opacity=".8"><path d="M0 176 H720M0 204 H720"/></g>
<g transform="translate(380 110) rotate(-8)"><path d="M-80 30 Q-82 -8-50-12 L-10-14 Q6-40 30-30 Q50-20 60 10 Q90 14 92 34 Q92 46 76 46 H-70 Q-80 46-80 30Z" fill="{ink}"/>
<path d="M-80 38 H92" stroke="{verm}" stroke-width="10"/><g stroke="{verm}" stroke-width="4" stroke-linecap="round"><path d="M10-8 l20 10M18-20 l20 10M26-32 l18 8"/></g><path d="M-50-12 Q-40 10-20 12" stroke="{amber}" stroke-width="5" fill="none"/></g>
<g stroke="{ink}" stroke-width="5" opacity=".5" stroke-linecap="round"><path d="M240 100h-60M250 122h-90M244 144h-50"/></g>''', bg="bg2")

ART["games"] = svg(r'''
<rect x="170" y="70" width="180" height="130" fill="{ink}"/><g fill="{leaf}"><rect x="170" y="70" width="30" height="26"/><rect x="230" y="70" width="30" height="26"/><rect x="290" y="70" width="30" height="26"/>
<rect x="200" y="96" width="30" height="26"/><rect x="260" y="96" width="30" height="26"/><rect x="320" y="96" width="30" height="26"/><rect x="170" y="122" width="30" height="26"/><rect x="230" y="122" width="30" height="26"/><rect x="290" y="122" width="30" height="26"/>
<rect x="200" y="148" width="30" height="26"/><rect x="260" y="148" width="30" height="26"/><rect x="320" y="148" width="30" height="26"/><rect x="170" y="174" width="30" height="26"/><rect x="230" y="174" width="30" height="26"/><rect x="290" y="174" width="30" height="26"/></g>
<g transform="translate(300 52)"><path d="M-22 76 H22 L16 50 Q30 40 20 20 Q30 0 10-6 L10-20 H4 V-30 H-4 V-20 H-10 L-10-6 Q-30 0-20 20 Q-30 40-16 50Z" fill="{night}"/></g>
<g transform="translate(470 130) rotate(15)"><rect x="-36" y="-36" width="72" height="72" rx="14" fill="{verm}"/><g fill="{ink}"><circle cx="-16" cy="-16" r="7"/><circle r="7"/><circle cx="16" cy="16" r="7"/></g></g>
<g transform="translate(560 90) rotate(-20)"><rect x="-26" y="-26" width="52" height="52" rx="10" fill="{amber}"/><g fill="{night}"><circle cx="-10" cy="-10" r="5"/><circle cx="10" cy="10" r="5"/></g></g>''', bg="bg3")

ART["dinosaurs"] = svg(r'''
''' + dots(SPARK) + r'''
<g transform="translate(360 150)" fill="none" stroke="{ink}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">
<path d="M-160 10 Q-100 -10 -60-30 Q-20-50 30-50 Q70-50 90-80 Q110-110 140-100 Q160-90 150-74 Q130-70 120-60 Q110-40 80-20 Q60 0 40 10"/>
<path d="M-40-36v40M-20-44v44M0-48v48M20-48v46"/><path d="M-40 4 Q0 16 40 10" /><path d="M-30 10 L-40 50 M-10 14 L-6 50 M20 12 L16 50 M34 10 L44 50"/></g>
<circle cx="500" cy="62" r="5" fill="{night}"/><rect y="200" width="720" height="40" fill="{bg3}"/>''', bg="bg2")

ART["circus"] = svg(r'''
''' + dots(SPARK, "amber", ".8", 2.5) + r'''
<g transform="translate(360 0)"><path d="M0 30 L-130 120 H130Z" fill="{verm}"/><path d="M0 30 L-44 120 H44Z" fill="{ink}"/><path d="M0 30 L-130 120 H-88Z" fill="{ink}"/><path d="M0 30 L130 120 H88Z" fill="{ink}"/>
<rect x="-120" y="120" width="240" height="84" fill="{ink}"/><g fill="{verm}"><rect x="-120" y="120" width="40" height="84"/><rect x="-40" y="120" width="40" height="84" fill="none"/><rect x="40" y="120" width="40" height="84"/></g>
<path d="M-30 204 V150 Q0 130 30 150 V204Z" fill="{night}"/><path d="M0 30 V8" stroke="{ink2}" stroke-width="3"/><path d="M2 8 l26 8-26 8z" fill="{amber}"/>
<path d="M-130 120 q16 14 32 0 t32 0 32 0 32 0 32 0 32 0 32 0 32 0" fill="{amber}"/></g>''', bg="bg2", ground="night")

ART["default"] = svg(r'''
<g stroke="{bg3}" stroke-width="10" fill="none" stroke-linecap="round"><path d="M0 180 Q200 140 360 170 T720 120"/><path d="M120 0 Q180 120 140 240"/><path d="M520 0 Q480 110 600 240"/></g>
<path d="M0 200 Q200 160 360 190 T720 140" stroke="{sky}" stroke-width="14" fill="none" opacity=".35"/>
<g transform="translate(360 116)"><path d="M0 74 C0 74 -46 24 -46-6 A46 46 0 1 1 46-6 C46 24 0 74 0 74Z" fill="{verm}"/><circle cy="-6" r="17" fill="{bg}"/></g>
<ellipse cx="360" cy="196" rx="30" ry="7" fill="{night}" opacity=".6"/>''', bg="bg")

if __name__ == "__main__":
    import os
    out = os.path.join(os.path.dirname(__file__), "..", "docs", "art")
    os.makedirs(out, exist_ok=True)
    for k, v in ART.items():
        open(os.path.join(out, k + ".svg"), "w").write(v)
    print(len(ART), "drawn:", ", ".join(ART))
