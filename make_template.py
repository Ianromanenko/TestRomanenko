#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор шаблона 1:1 для кожаного чехла на зажигалку Clipper (A4, мм)."""

A4_W, A4_H = 210.0, 297.0

# --- Параметры чехла (мм) ---
W = 60.0          # ширина развёртки (обхват вокруг зажигалки)
H = 55.0          # высота чехла (закрывает корпус, верх остаётся открытым)
EDGE = 2.5        # отступ отверстий от кромки шва
PITCH = 4.5       # шаг между отверстиями
HOLE_R = 0.7      # радиус метки отверстия на шаблоне
SEAM_ALLOW = 0    # (шов встык, без нахлёста)

# Положение панели на листе
x0 = 75.0
y0 = 130.0
x1 = x0 + W       # 135
y1 = y0 + H       # 185

# Язычок под кольцо (слева сверху — там, где сходится шов)
TAB_W = 14.0
TAB_H = 20.0
tab_x0 = x0
tab_x1 = x0 + TAB_W
tab_top = y0 - TAB_H
ring_cx = (tab_x0 + tab_x1) / 2
ring_cy = tab_top + 6
ring_r = 1.75      # отверстие под заводное кольцо ~3.5 мм

# Колонки отверстий
xl = x0 + EDGE
xr = x1 - EDGE

# Ряды отверстий
holes_y = []
y = y0 + 3
while y <= y1 - 2.5:
    holes_y.append(round(y, 2))
    y += PITCH

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" '
           f'width="{A4_W}mm" height="{A4_H}mm" '
           f'viewBox="0 0 {A4_W} {A4_H}">')
svg.append('<rect x="0" y="0" width="210" height="297" fill="white"/>')

# стиль
cut = 'fill="none" stroke="#000000" stroke-width="0.4"'
fold = 'fill="none" stroke="#888888" stroke-width="0.3" stroke-dasharray="2,1.5"'
guide = 'fill="none" stroke="#cc3333" stroke-width="0.25" stroke-dasharray="1.5,1.5"'
txt = 'font-family="Arial, sans-serif" fill="#000000"'

# --- Контур основной панели ---
svg.append(f'<rect x="{x0}" y="{y0}" width="{W}" height="{H}" rx="2" {cut}/>')

# --- Язычок ---
svg.append(f'<path d="M {tab_x0} {y0} '
           f'L {tab_x0} {tab_top+3} Q {tab_x0} {tab_top} {tab_x0+3} {tab_top} '
           f'L {tab_x1-3} {tab_top} Q {tab_x1} {tab_top} {tab_x1} {tab_top+3} '
           f'L {tab_x1} {y0}" {cut}/>')
# линия сгиба язычка
svg.append(f'<line x1="{tab_x0}" y1="{y0}" x2="{tab_x1}" y2="{y0}" {fold}/>')
# отверстие под кольцо
svg.append(f'<circle cx="{ring_cx}" cy="{ring_cy}" r="{ring_r}" {cut}/>')

# --- Отверстия шва (две колонки) ---
for hy in holes_y:
    svg.append(f'<circle cx="{xl}" cy="{hy}" r="{HOLE_R}" fill="#000000"/>')
    svg.append(f'<circle cx="{xr}" cy="{hy}" r="{HOLE_R}" fill="#000000"/>')

# --- Иллюстрация крестовой шнуровки (поверх, по центру) ---
midx = (x0 + x1) / 2
for i in range(len(holes_y) - 1):
    y_a = holes_y[i]
    y_b = holes_y[i + 1]
    # X между соседними рядами (схематично, по центру)
    svg.append(f'<line x1="{midx-6}" y1="{y_a}" x2="{midx+6}" y2="{y_b}" {guide}/>')
    svg.append(f'<line x1="{midx+6}" y1="{y_a}" x2="{midx-6}" y2="{y_b}" {guide}/>')

# --- Подписи размеров ---
svg.append(f'<text x="{(x0+x1)/2}" y="{y1+7}" {txt} font-size="3.2" '
           f'text-anchor="middle">ширина (обхват) = 60 мм</text>')
svg.append(f'<text x="{x1+4}" y="{(y0+y1)/2}" {txt} font-size="3.2" '
           f'text-anchor="middle" transform="rotate(90 {x1+4} {(y0+y1)/2})">'
           f'высота = 55 мм</text>')
svg.append(f'<text x="{tab_x1+2}" y="{tab_top+11}" {txt} font-size="2.8">'
           f'язычок 14×20 мм</text>')
svg.append(f'<text x="{ring_cx+4}" y="{ring_cy+1}" {txt} font-size="2.6">'
           f'кольцо ⌀3.5</text>')
svg.append(f'<text x="{xl-3}" y="{y0-2}" {txt} font-size="2.6" '
           f'text-anchor="middle">шов</text>')
svg.append(f'<text x="{xr+3}" y="{y0-2}" {txt} font-size="2.6" '
           f'text-anchor="middle">шов</text>')

# --- Заголовок ---
svg.append(f'<text x="20" y="22" {txt} font-size="6" font-weight="bold">'
           f'Шаблон чехла для зажигалки Clipper — масштаб 1:1</text>')
svg.append(f'<text x="20" y="30" {txt} font-size="3">'
           f'Печать БЕЗ масштабирования (Actual size / 100%). '
           f'Отступ отверстий от кромки {EDGE} мм, шаг {PITCH} мм, '
           f'всего {len(holes_y)} отв. на сторону.</text>')

# --- Калибровочная линейка 50 мм ---
rx, ry = 20, 45
svg.append(f'<text x="{rx}" y="{ry-2}" {txt} font-size="3">'
           f'Проверка масштаба — линия должна быть ровно 50 мм:</text>')
svg.append(f'<line x1="{rx}" y1="{ry}" x2="{rx+50}" y2="{ry}" '
           f'stroke="#000" stroke-width="0.4"/>')
for i in range(0, 51, 5):
    h = 2.5 if i % 10 == 0 else 1.4
    svg.append(f'<line x1="{rx+i}" y1="{ry}" x2="{rx+i}" y2="{ry-h}" '
               f'stroke="#000" stroke-width="0.3"/>')
svg.append(f'<text x="{rx+52}" y="{ry+1}" {txt} font-size="2.6">50 мм</text>')

# --- Контрольный квадрат 10×10 мм ---
sq_x, sq_y = 90, 42
svg.append(f'<rect x="{sq_x}" y="{sq_y}" width="10" height="10" '
           f'fill="none" stroke="#000" stroke-width="0.3"/>')
svg.append(f'<text x="{sq_x+12}" y="{sq_y+6}" {txt} font-size="2.6">'
           f'квадрат 10×10 мм</text>')

# --- Легенда ---
ly = 60
svg.append(f'<line x1="20" y1="{ly}" x2="28" y2="{ly}" stroke="#000" stroke-width="0.4"/>')
svg.append(f'<text x="30" y="{ly+1}" {txt} font-size="2.8">— линия реза кожи</text>')
svg.append(f'<line x1="20" y1="{ly+5}" x2="28" y2="{ly+5}" {fold}/>')
svg.append(f'<text x="30" y="{ly+6}" {txt} font-size="2.8">— линия сгиба язычка</text>')
svg.append(f'<circle cx="24" cy="{ly+10}" r="0.7" fill="#000"/>')
svg.append(f'<text x="30" y="{ly+11}" {txt} font-size="2.8">— отверстие под прошивку (пробить ⌀1–1.5 мм)</text>')
svg.append(f'<line x1="20" y1="{ly+15}" x2="28" y2="{ly+15}" {guide}/>')
svg.append(f'<text x="30" y="{ly+16}" {txt} font-size="2.8">— схема крестового шва (только показ, не резать)</text>')

svg.append('</svg>')

with open('clipper_case_template.svg', 'w', encoding='utf-8') as f:
    f.write('\n'.join(svg))

print('OK holes per side:', len(holes_y))
print('panel:', W, 'x', H, 'mm')
