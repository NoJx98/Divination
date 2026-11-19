#!/usr/bin/env python3
"""xingpan.py — 西洋占星星盘排盘引擎（tropical 黄道 / Placidus 分宫 / swisseph 计算）

用法:
  xingpan.py --birth "2000-01-01 13:00" [--lat 39.90 --lon 116.41] [--tz 8]
  xingpan.py --birth "2000-01-01 13:00" --question "星盘排盘自检"
  xingpan.py --test                    # 回归（天文锚点），全过打印「全部通过 ✅」exit 0

默认值假设（不给 --lat/--lon/--tz 时）：北京 39.90°N, 116.41°E, UTC+8（固定偏移，不处理夏令时）；按需传本地坐标。
--birth 给的是当地钟表时间，内部减去 --tz 换算成 UT 再起儒略日。
输出 JSON（ensure_ascii=False, indent=2）；正常排盘把结果追加进 divination_log.jsonl（写失败不崩溃）。
--test 只跑断言，不写任何日志。

计算口径:
 - 黄道 tropical（of date，含光行差与章动，即主流占星软件默认口径）；十大行星 + 北交点(true node)。
 - 显式 FLG_MOSEPH：本机 venv 未装瑞士星历 .se1 文件（de421.bsp 是 JPL SPK，swisseph 不读），
   Moshier 解析级精度，2000-01-01 与 JPL Horizons 对比误差 <0.001°（见下方锚点）。
 - 逆行标志 = FLG_SPEED 给出的黄经日速度 < 0（pyswisseph 2.10.3.2 未导出 SEFLG_RETROGRADE 常量，
   calc 返回的 retflag 里也没有逆行位，故用速度符号判定，与主流口径一致）。
 - 宫位 = swe.houses(jd_ut, lat, lon, b'P') 的 12 个宫头；第 1 宫宫头即上升、第 10 宫宫头即中天，
   ascmc[0]/ascmc[1] 另给出 ASC/MC 用于自洽校验（已实测两者与宫头逐一相等）。
 - 相位：合0 六合60 刑90 拱120 对冲180（规格原文“删180”按对冲处理）。
   容许度：合/对冲 8°、刑/拱 6°、六合 4°；任一端为太阳或月亮再 +2°
   （即日月 合/冲 10°，与规格“大行星 8°/日月 10°、其他按主流惯例”一致）。
   相位只算十大行星两两之间（不含北交点与四轴）。

天文锚点与出处（--test 断言全部用天文值）:
 1) 太阳黄经 2000-01-01 12:00 UT：--test 锚点收紧为 JPL Horizons 地心视黄经 280.3689°±0.1°。
    平黄经（J2000 平黄经）280.46°：NASA/JPL SSD《Approximate Positions of
    the Planets》Table 1：EM Bary L₀=100.46457166°，太阳平黄经 = L+180° = 280.4646°。
    https://ssd.jpl.nasa.gov/planets/approx_pos.html
    同时刻 JPL Horizons 地心视黄经 = 280.3689092°（Horizons 请求模板见 3)~5)）。
    两值关系：平黄经 280.46° 与视黄经 280.3689° 相差 0.0911°，即中心差（equation of center），
    是同一时刻的两种黄经口径；--test 用视黄经 280.3689°±0.1° 断言，不再用平黄经 ±0.5°。
 2) 春分点 2000-03-20 07:35 UT 太阳黄经 ≈ 0°：JPL Horizons 太阳地心视黄经 07:30 UT = 359.9963736°、
    07:40 UT = 0.0032696°，线性内插过 0° 时刻 = 07:35:15 UT（跨 0°/360° 按环形差计算）。
 3) 木星 2000-01-01 12:00 UT 地心视黄经 = 25.2530685°（Horizons COMMAND='599'，QUANTITIES='31'
    即 ObsEcLon：Observer-centered IAU76/80 ecliptic-of-date apparent position）。
 4) 土星 2000-01-01 12:00 UT = 40.3956366°（COMMAND='699'）。
 5) 月亮 2000-01-01 12:00 UT = 223.3237860°（COMMAND='301'）。
    3)~5) 与 1) 的 Horizons 请求模板：
    https://ssd.jpl.nasa.gov/api/horizons.api?format=text&COMMAND='599'&OBJ_DATA='NO'&MAKE_EPHEM='YES'
    &EPHEM_TYPE='OBSERVER'&CENTER='500@399'&START_TIME='2000-01-01 12:00'&STOP_TIME='2000-01-01 12:01'
    &STEP_SIZE='1m'&QUANTITIES='31'&CSV_FORMAT='YES'&ANG_FORMAT='DEG'&CAL_FORMAT='CAL'&TIME_ZONE='+00:00'
    （换 COMMAND 即得 1)/3)/4)/5)；春分点用同一模板 START='2000-03-20 07:00' STOP='2000-03-20 08:00'
    STEP='10m'。）
"""
import os
import argparse
import json
import math
import sys
from datetime import datetime, timedelta

import swisseph as swe

SIGNS = ['白羊', '金牛', '双子', '巨蟹', '狮子', '处女',
         '天秤', '天蝎', '射手', '摩羯', '水瓶', '双鱼']
PLANETS = [('太阳', swe.SUN), ('月亮', swe.MOON), ('水星', swe.MERCURY), ('金星', swe.VENUS),
           ('火星', swe.MARS), ('木星', swe.JUPITER), ('土星', swe.SATURN),
           ('天王星', swe.URANUS), ('海王星', swe.NEPTUNE), ('冥王星', swe.PLUTO)]
LUMINARIES = {'太阳', '月亮'}
# 相位 → (标称角度, 基础容许度)；日月参与各 +2°
ASPECTS = [('合', 0.0, 8.0), ('六合', 60.0, 4.0), ('刑', 90.0, 6.0),
           ('拱', 120.0, 6.0), ('对冲', 180.0, 8.0)]

DEFAULT_LAT = 39.9042    # 北京（默认地点假设）
DEFAULT_LON = 116.4074
DEFAULT_TZ = 8.0        # UTC+8
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl')
FLAGS = swe.FLG_MOSEPH | swe.FLG_SPEED


# ──────────────────── 基础计算 ────────────────────
def jd_from_local(birth: str, tz: float):
    """'YYYY-MM-DD HH:MM' 当地时间 → (儒略日 UT, 换算后的 UT datetime)。"""
    dt = datetime.strptime(birth, '%Y-%m-%d %H:%M')
    ut = dt - timedelta(hours=tz)
    return swe.julday(ut.year, ut.month, ut.day,
                      ut.hour + ut.minute / 60.0 + ut.second / 3600.0), ut


def body_pos(jd: float, body: int):
    """(黄经 0-360, 是否逆行)。逆行 = swisseph FLG_SPEED 的黄经日速度 < 0。"""
    xx, _ret = swe.calc_ut(jd, body, FLAGS)
    return xx[0] % 360.0, xx[3] < 0.0


def sign_of(lon: float) -> str:
    return SIGNS[int((lon % 360.0) // 30) % 12]


def deg_min(lon: float):
    """星座内度分（按总分四舍五入，避免 59.999→60 的进位错位）。"""
    total = int(round((lon % 360.0) * 60)) % 21600      # 21600 = 360° 的总分数
    _sign_idx, rem = divmod(total, 1800)                # 1800 = 30°
    d, m = divmod(rem, 60)
    return d, m


def fmt_pos(lon: float) -> str:
    """如 '24°15′ 巨蟹'。"""
    d, m = deg_min(lon)
    return f"{d}°{m:02d}′ {sign_of(lon)}"


def point(lon: float) -> dict:
    d, m = deg_min(lon)
    return {'黄经': round(lon % 360.0, 4), '星座': sign_of(lon),
            '度数': f"{d}°{m:02d}′", '位置': f"{d}°{m:02d}′ {sign_of(lon)}"}


def find_aspects(pos: dict) -> list:
    """两两求黄经分离角（取 ≤180 的那个），按容许度判相位。pos: {名称: 黄经}。"""
    names = list(pos)
    out = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            sep = abs(pos[a] - pos[b]) % 360.0
            if sep > 180.0:
                sep = 360.0 - sep
            for name, angle, base in ASPECTS:
                orb = base + (2.0 if (a in LUMINARIES or b in LUMINARIES) else 0.0)
                dev = abs(sep - angle)
                if dev <= orb + 1e-9:
                    out.append({'行星A': a, '行星B': b, '相位': name,
                                '标称角度': angle, '实际角度': round(sep, 2),
                                '偏差': round(dev, 2), '容许度': orb})
                    break
    return out


def chart(birth: str, lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON,
          tz: float = DEFAULT_TZ, question: str = None) -> dict:
    jd, ut = jd_from_local(birth, tz)

    pos, retro = {}, {}
    for name, pid in PLANETS:
        pos[name], retro[name] = body_pos(jd, pid)
    node_lon, _ = body_pos(jd, swe.TRUE_NODE)

    cusps, ascmc = swe.houses(jd, lat, lon, b'P')       # Placidus：第1宫=上升，第10宫=中天
    asc, mc = ascmc[0] % 360.0, ascmc[1] % 360.0

    out = {
        '类型': '西洋占星星盘',
        '出生数据': {
            '出生时间': birth,
            '时区': f"UTC{tz:+g}",
            'UT时间': ut.strftime('%Y-%m-%d %H:%M'),
            '纬度': lat, '经度': lon,
            '地点': '北京（默认）' if (lat, lon, tz) == (DEFAULT_LAT, DEFAULT_LON, DEFAULT_TZ) else '自定义',
            '黄道': 'tropical', '分宫制': 'Placidus', '星历': 'pyswisseph FLG_MOSEPH',
        },
        '十大行星': [
            dict(名称=name, **point(pos[name]), 逆行=retro[name]) for name, _ in PLANETS
        ],
        '北交点': dict(名称='北交点', **point(node_lon), 说明='true node（真交点）'),
        '上升ASC': dict(名称='上升', **point(asc)),
        '中天MC': dict(名称='中天', **point(mc)),
        '宫位': [dict(宫=i + 1, **point(c)) for i, c in enumerate(cusps)],
        '相位': find_aspects(pos),
        '月亮星座': sign_of(pos['月亮']),
        '水星逆行': retro['水星'],
        '金星逆行': retro['金星'],
    }
    if question:
        out['问题'] = question
    return out


# ──────────────────── 回归测试（天文锚点，出处见 docstring） ────────────────────
def test() -> int:
    fails = []

    def check(label, cond, detail=''):
        print(f"{'✓' if cond else '✗'} {label}" + (f" — {detail}" if detail else ''))
        if not cond:
            fails.append(label)

    def circ(label, got, want, tol):
        d = abs(got - want) % 360.0
        d = min(d, 360.0 - d)
        check(label, d <= tol, f"实测 {got:.4f}°，锚点 {want}°±{tol}°，环形偏差 {d:.4f}°")

    jd0101 = swe.julday(2000, 1, 1, 12.0)
    # 1) 太阳：JPL Horizons 视黄经 280.3689°（±0.1° 收紧锚点；平黄经 280.46° 与其差 0.0911°=中心差，
    #    见 docstring 锚点 1）
    circ('太阳视黄经 2000-01-01 12:00 UT ≈ 280.3689°', body_pos(jd0101, swe.SUN)[0], 280.3689, 0.1)
    # 2) 春分点：Horizons 内插过 0° 时刻 = 2000-03-20 07:35:15 UT
    jd_eq = swe.julday(2000, 3, 20, 7 + 35 / 60.0)
    circ('春分点 2000-03-20 07:35 UT 太阳黄经 ≈ 0°', body_pos(jd_eq, swe.SUN)[0], 0.0, 0.5)
    # 3) 木星：Horizons ObsEcLon = 25.2530685°
    circ('木星黄经 2000-01-01 12:00 UT ≈ 25.253°', body_pos(jd0101, swe.JUPITER)[0], 25.2530685, 1.0)
    # 4) 土星：Horizons ObsEcLon = 40.3956366°
    circ('土星黄经 2000-01-01 12:00 UT ≈ 40.396°', body_pos(jd0101, swe.SATURN)[0], 40.3956366, 1.0)
    # 5) 月亮：Horizons ObsEcLon = 223.3237860°
    circ('月亮黄经 2000-01-01 12:00 UT ≈ 223.324°', body_pos(jd0101, swe.MOON)[0], 223.3237860, 2.0)

    # 6) 出生盘自洽性（2000-01-01 13:00 UTC+8，北京默认坐标）
    out = chart('2000-01-01 13:00')
    cusps = [c['黄经'] for c in out['宫位']]
    uniq = len({round(c, 6) for c in cusps})
    check('12 宫头互不相同', uniq == 12, f'去重后 {uniq} 个')
    span = sum((cusps[(i + 1) % 12] - cusps[i]) % 360.0 for i in range(12))
    check('宫位总跨度 360°', abs(span - 360.0) < 1e-6, f'{span:.6f}°')
    check('ASC 宫头=上升', abs(out['上升ASC']['黄经'] - cusps[0]) < 1e-9,
          f"上升 {out['上升ASC']['黄经']} vs 第1宫宫头 {cusps[0]}")
    check('中天=第10宫宫头', abs(out['中天MC']['黄经'] - cusps[9]) < 1e-9,
          f"中天 {out['中天MC']['黄经']} vs 第10宫宫头 {cusps[9]}")
    # MC 独立校验：恒星时→RAMC→MC 解析式（不经过 swe.houses）
    jd_birth, ut = jd_from_local('2000-01-01 13:00', DEFAULT_TZ)
    ramc = swe.sidtime(jd_birth) * 15.0 + DEFAULT_LON
    eps = math.radians(23.4393)                      # J2000 黄赤交角（任意年份差 <0.001°）
    mc_calc = math.degrees(math.atan2(math.sin(math.radians(ramc)),
                                      math.cos(math.radians(ramc)) * math.cos(eps))) % 360.0
    check('MC 与恒星时解析式互证', abs(mc_calc - cusps[9]) < 0.01,
          f'解析 {mc_calc:.4f}° vs Placidus {cusps[9]:.4f}°')
    planets = out['十大行星']
    all_sign = len(planets) == 10 and all(p['星座'] in SIGNS and 0 <= p['黄经'] < 360 for p in planets)
    check('10 大行星全部标注星座与度数', all_sign,
          '、'.join(f"{p['名称']}={p['位置']}" for p in planets[:3]) + ' …')

    # 7) 相位：已知 180° 对冲必须识别，超容许度不判
    a180 = find_aspects({'甲': 10.0, '乙': 190.0})
    check('180° 对冲角识别为对冲', bool(a180) and a180[0]['相位'] == '对冲',
          str([x['相位'] for x in a180]))
    a_over = find_aspects({'甲': 0.0, '乙': 189.0})   # 分离 171°，超出对冲容许度 8°
    check('超容许度不判相位', a_over == [], str(a_over))

    # 8) 自检：2000-01-01 13:00 太阳必须是摩羯
    check('2000-01-01 13:00 太阳=摩羯', planets[0]['星座'] == '摩羯', planets[0]['位置'])
    check('水星/金星逆行字段为布尔',
          isinstance(out['水星逆行'], bool) and isinstance(out['金星逆行'], bool),
          f"水星逆行={out['水星逆行']} 金星逆行={out['金星逆行']}")

    print("\n" + ("全部通过 ✅" if not fails else f"失败 {len(fails)} 项 ❌: {fails}"))
    return 0 if not fails else 1


# ──────────────────── CLI ────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description='西洋占星星盘排盘（tropical / Placidus / swisseph）')
    ap.add_argument('--birth', help='出生时间 "YYYY-MM-DD HH:MM"（当地时间）')
    ap.add_argument('--lat', type=float, default=DEFAULT_LAT, help=f'纬度，默认 {DEFAULT_LAT}（北京）')
    ap.add_argument('--lon', type=float, default=DEFAULT_LON, help=f'经度，默认 {DEFAULT_LON}（北京）')
    ap.add_argument('--tz', type=float, default=DEFAULT_TZ, help=f'时区小时数，默认 {DEFAULT_TZ:g}（UTC+8）')
    ap.add_argument('--question', default=None, help='带问存档')
    ap.add_argument('--test', action='store_true', help='回归测试（天文锚点）')
    try:
        args = ap.parse_args()
    except SystemExit as e:
        # argparse 报错原本 exit 2，统一为 exit 1；--help 的 exit 0 保持不变
        return 0 if e.code in (0, None) else 1

    if args.test:
        return test()
    if args.question is not None and len(args.question) > 2000:
        print('--question 超过 2000 字符上限', file=sys.stderr)
        return 1
    if not args.birth:
        print('用法: xingpan.py --birth "YYYY-MM-DD HH:MM" [--lat --lon --tz] [--question "问题"]',
              file=sys.stderr)
        return 1
    if not -90 <= args.lat <= 90 or not -180 <= args.lon <= 180:
        print(f'经纬度超出范围: lat={args.lat} lon={args.lon}', file=sys.stderr)
        return 1
    if not -12 <= args.tz <= 14:
        print(f'时区超出范围 -12~14: tz={args.tz}', file=sys.stderr)
        return 1

    try:
        out = chart(args.birth, args.lat, args.lon, args.tz, args.question)
    except ValueError:
        print(f'出生时间无法解析: "{args.birth}"，应为 YYYY-MM-DD HH:MM', file=sys.stderr)
        return 1
    except swe.Error as e:
        print(f'星盘计算失败（分宫/星历）: {e}', file=sys.stderr)
        return 1

    print(json.dumps(out, ensure_ascii=False, indent=2))
    try:  # 存档失败不崩溃
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'xingpan',
                                'ts': datetime.now().isoformat(),
                                'result': out}, ensure_ascii=False) + '\n')
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
