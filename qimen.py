#!/usr/bin/env python3
"""qimen.py — 时家奇门遁甲排盘引擎（拆补法定局，2026-11-18 创建）

用法:
  python3 qimen.py                          # 当前时间排盘
  python3 qimen.py 2026-09-12 22:00         # 位置参数指定时间（YYYY-MM-DD HH:MM）
  python3 qimen.py --question "问事业"       # 带问存档（其值绝不会被当成日期解析）
  python3 qimen.py --test                   # 回归测试（黄金锚点+自洽性），不写日志
输出 JSON（ensure_ascii=False, indent=2）。正常排盘末尾追加一行 divination_log.jsonl（写失败不崩溃）。

═══ 算法规矩与出处（2026-11-18 联网核实）═══
1) 拆补法定局 = 节气定阴阳遁 + 符头定三元 + 二十四节气用局表查局数：
   · 阴阳遁：冬至→芒种为阳遁，夏至→大雪为阴遁，以交节**时刻**为界（sxtwl 真太阳交节）。
   · 符头：日柱往前（含当日）最近的甲日/己日——六十甲子五日一组，组首必为甲/己。
     三元只看**符头地支**：子午卯酉(四仲)=上元、寅申巳亥(四孟)=中元、辰戌丑未(四季)=下元。
     ⚠️ 常见误传“甲己上元/乙庚中元/丙辛下元”不是拆补法规则：拆补法符头恒为甲/己日，
        乙庚丙辛丁壬戊癸永不做符头；元别与日干天干无关，只与符头地支有关。
     出处：时问奇门《奇门遁甲排盘步骤详解》符头表/三元表
           https://www.askqimen.com/zh-CN/knowledge/qimen-dunjia-charting-steps
           奇门问事《奇门遁甲排盘方法》“符頭＝由當日往前最近嘅甲日或己日…子午卯酉＝上元”
           https://qimen-club.com/learn/qimen-dunjia-paipan-method
           对照实现：kinqimen findyuen_dict/qimen_ju_name_chaibu
           https://github.com/kentang2017/kinqimen
   · 用局表（24节气×三元，冬至起阳遁、夏至起阴遁）：
       冬至174 小寒285 大寒369 立春852 雨水963 惊蛰174 春分369 清明417 谷雨528
       立夏417 小满528 芒种639 | 夏至936 小暑825 大暑714 立秋258 处暑147 白露936
       秋分714 寒露693 霜降582 立冬693 小雪582 大雪471
     （askqimen 用局表、qimen-club 举例、kinqimen jieqicode_jq 三源逐格一致）
2) 地盘：三奇六仪按 戊己庚辛壬癸丁丙乙 次序，从局数宫起布；阳遁按九宫数序顺排
   （坎一→坤二→…→离九），阴遁逆排（离九→…→坎一）。出处：askqimen 第二步/表8。
3) 值符值使：时柱定旬首（甲子→戊 甲戌→己 甲申→庚 甲午→辛 甲辰→壬 甲寅→癸，
   即六甲遁六仪，见 https://zh.wikipedia.org/wiki/奇門遁甲 ）；旬首六仪所落之宫记 P0，
   P0 的本位星=值符星、本位门=值使门（中五无门，取寄坤二之死门）。
   出处：askqimen 第三/五步“地盘值符在坎宫，坎宫本位星为天蓬/本位门为休门”。
4) 天盘（值符随时干）：时干在地盘之宫记 Pt（甲时按其遁干，即旬首仪之宫）；
   值符星自本宫沿**外圈顺时针环**（坎→艮→震→巽→离→坤→兑→乾）按遁向移动
   （阳遁顺时针、阴遁逆时针）至 Pt，其余八星与天盘干整体同移；
   天盘干 = 该星本宫之地盘干；中五天禽恒居中五（寄坤二论位移），中五天盘干=中五地盘干。
   任一“落宫”为中五时按寄坤二处理。
   出处：askqimen 第三/五步（2024-01-01 12:00 阳遁一局例“天蓬到震”“天盘戊在震”）
         qimen-club 第四步+实盘（2026-09-12 22:00 阴遁六局“值符天禽…天禽恆居中五”）
5) 人盘（值使随时支）：值使门自 P0 起，沿九宫数序阳顺阴逆走 (时支−旬首支) 步落宫
   （落中五寄坤二）；其余七门沿外圈按八门顺序 休生伤杜景死惊开，阳顺（顺时针+序）
   阴逆（逆时针−序）排布，中五无门。
   出处：askqimen 第六步“从地盘值符所在的坎宫起甲子…数到庚午→休门到兑宫”
         kinqimen zhishi_pai/pan_door 实现一致（时干在旬内序号 ≡ 时支−旬首支）。
6) 八神：值符起于地盘时干之宫 Pt（中五寄坤二），其余按 值符腾蛇太阴六合白虎玄武九地九天
   沿外圈阳遁顺时针、阴遁逆时针布，中五无神。
   出处：askqimen 第四/五步（天八神值符在震、阳遁顺时针）
         qimen-club 实盘（阴遁：值符在兑、逆时针螣蛇在坤…）
7) 旬空：时柱所在旬的空亡二支（甲子旬戌亥、甲戌旬申酉、甲申旬午未、甲午旬辰巳、
   甲辰旬寅卯、甲寅旬子丑），日柱同理。出处：askqimen 7.1。
8) 马星：按时支三合取驿马（申子辰→寅、寅午戌→申、巳酉丑→亥、亥卯未→巳）。
   出处：askqimen 7.2“驿马按时支查”；qimen-club 实盘（乙亥时→马在巳）。
9) 晚子时（23:00 起）日柱进一位（“子时起新一日”）。出处：qimen-club 换日点说明。
   跨脚本口径声明：本脚本晚子时(23:00后)日柱进一位（依 qimen-club 换日点），与 ziwei.py
   “晚子时算当日”（依 iztro/全书口径）各依其流派出处，同刻两脚本日柱可能差一位属正常。
10) 寄宫异说：天禽“恒居中五”（本实现，qimen-club）vs“随天芮同宫”（askqimen/kinqimen
    把天禽标签写在天芮所在宫）。两说只差天禽标签位置，地盘/天盘干、八门、八神、
    值符值使落宫完全一致。

═══ 黄金锚点（--test 逐宫核对，出处见上）═══
  A. 2024-01-01 12:00 → 甲子日庚午时，冬至节气、甲子符头上元 → 阳遁一局（askqimen 同例）
  B. 2026-09-12 22:00 → 己丑日乙亥时，白露节气、己丑符头下元 → 阴遁六局（qimen-club 同例）
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bazi import DZ, GZ, day_ganzhi, hour_ganzhi, shichen_idx  # 复用已验证干支公式

try:
    import sxtwl
except Exception:  # pragma: no cover
    sxtwl = None

# ──────────────────────────── 基础表 ────────────────────────────
GONG = {1: '坎', 2: '坤', 3: '震', 4: '巽', 5: '中', 6: '乾', 7: '兑', 8: '艮', 9: '离'}
STAR = {1: '天蓬', 2: '天芮', 3: '天冲', 4: '天辅', 5: '天禽',
        6: '天心', 7: '天柱', 8: '天任', 9: '天英'}
DOOR = {1: '休门', 2: '死门', 3: '伤门', 4: '杜门', 5: None,
        6: '开门', 7: '惊门', 8: '生门', 9: '景门'}
DOOR_ORDER = ['休门', '生门', '伤门', '杜门', '景门', '死门', '惊门', '开门']  # 八门顺序
GODS = ['值符', '腾蛇', '太阴', '六合', '白虎', '玄武', '九地', '九天']
YI = list('戊己庚辛壬癸丁丙乙')          # 三奇六仪布列次序（六仪6+三奇3=9个）
RING = [1, 8, 3, 4, 9, 2, 7, 6]          # 外八宫顺时针环：坎艮震巽离坤兑乾
XUN_YI = {'甲子': '戊', '甲戌': '己', '甲申': '庚', '甲午': '辛', '甲辰': '壬', '甲寅': '癸'}
KONG = {'甲子': ('戌', '亥'), '甲戌': ('申', '酉'), '甲申': ('午', '未'),
        '甲午': ('辰', '巳'), '甲辰': ('寅', '卯'), '甲寅': ('子', '丑')}
ZHI_GONG = {'子': 1, '丑': 8, '寅': 8, '卯': 3, '辰': 4, '巳': 4,
            '午': 9, '未': 2, '申': 2, '酉': 7, '戌': 6, '亥': 6}
MA = {frozenset('寅午戌'): '申', frozenset('申子辰'): '寅',
      frozenset('巳酉丑'): '亥', frozenset('亥卯未'): '巳'}
# sxtwl 节气编号（实测 2026 年 0..23 连续循环，冬至=0）
JQ = ['冬至', '小寒', '大寒', '立春', '雨水', '惊蛰', '春分', '清明', '谷雨', '立夏',
      '小满', '芒种', '夏至', '小暑', '大暑', '立秋', '处暑', '白露', '秋分', '寒露',
      '霜降', '立冬', '小雪', '大雪']
# 二十四节气用局表（上,中,下）；冬至→芒种阳遁、夏至→大雪阴遁
JU = {'冬至': (1, 7, 4), '小寒': (2, 8, 5), '大寒': (3, 9, 6), '立春': (8, 5, 2),
      '雨水': (9, 6, 3), '惊蛰': (1, 7, 4), '春分': (3, 9, 6), '清明': (4, 1, 7),
      '谷雨': (5, 2, 8), '立夏': (4, 1, 7), '小满': (5, 2, 8), '芒种': (6, 3, 9),
      '夏至': (9, 3, 6), '小暑': (8, 2, 5), '大暑': (7, 1, 4), '立秋': (2, 5, 8),
      '处暑': (1, 4, 7), '白露': (9, 3, 6), '秋分': (7, 1, 4), '寒露': (6, 9, 3),
      '霜降': (5, 8, 2), '立冬': (6, 9, 3), '小雪': (5, 8, 2), '大雪': (4, 7, 1)}
YUANS = ('上元', '中元', '下元')


def wrap9(p: int) -> int:
    """九宫数序回绕：10→1，0→9"""
    return (p - 1) % 9 + 1


def ring_step(p: int, k: int) -> int:
    """外圈顺时针环上走 k 步（k 可为负=逆时针）"""
    return RING[(RING.index(p) + k) % 8]


def jieqi_id_at(dt: datetime) -> int:
    """当前（已交节）节气编号 0..23。按交节**时刻**判定：当天有节气但未到时刻则回退。"""
    if sxtwl is None:
        raise RuntimeError('sxtwl 不可用，无法定节气')

    def probe(d):
        x = sxtwl.fromSolar(d.year, d.month, d.day)
        if not x.hasJieQi():
            return None, None
        jd = x.getJieQiJD()          # 小数部即北京时（bazi.py 2024立春16:26实测吻合）
        return x.getJieQi(), ((jd + 0.5) % 1) * 24

    frac = dt.hour + dt.minute / 60 + dt.second / 3600
    jid, th = probe(dt.date())
    if jid is not None and frac >= th:
        return jid
    d = dt.date()
    for _ in range(40):              # 回退找最近一个已交节的节气
        d -= timedelta(days=1)
        jid2, _ = probe(d)
        if jid2 is not None:
            return jid2
    raise RuntimeError('找不到节气')


def futou_yuan(day_gz: str):
    """拆补法符头定三元：日柱所在五日组组首（必为甲/己）→ 按符头地支定上中下元。
    出处：askqimen 符头表+三元表；qimen-club“符頭＝往前最近嘅甲日或己日”。"""
    i = GZ.index(day_gz)
    futou = GZ[(i // 5) * 5]
    z = futou[1]
    if z in '子午卯酉':
        return futou, '上元'
    if z in '寅申巳亥':
        return futou, '中元'
    return futou, '下元'          # 辰戌丑未


def dipan(ju: int, yang: bool) -> dict:
    """地盘：三奇六仪从局数宫起，阳遁顺九宫数序、阴遁逆九宫数序。"""
    earth, p = {}, ju
    for g in YI:
        earth[p] = g
        p = wrap9(p + 1) if yang else wrap9(p - 1)
    return earth


def qimen(dt: datetime) -> dict:
    """时家奇门拆补法排盘：地盘/天盘/人盘/神盘四层 + 值符值使/旬空/马星。"""
    # 晚子时（23:00 起）日柱进一位
    day = dt.date() + (timedelta(days=1) if dt.hour >= 23 else timedelta(0))
    day_gz = day_ganzhi(day)
    shi_zhi = DZ[shichen_idx(dt.hour)]
    shi_gz = hour_ganzhi(day_gz[0], dt.hour)

    jq_id = jieqi_id_at(dt)
    jq = JQ[jq_id]
    yang = jq_id < 12                      # 冬至..芒种=阳遁，夏至..大雪=阴遁
    dun = '阳遁' if yang else '阴遁'
    futou, yuan = futou_yuan(day_gz)
    ju = JU[jq][YUANS.index(yuan)]

    earth = dipan(ju, yang)
    g2p = {v: k for k, v in earth.items()}

    # 旬首 → 值符值使
    i = GZ.index(shi_gz)
    xun_shou = GZ[(i // 10) * 10]           # 甲子/甲戌/甲申/甲午/甲辰/甲寅
    yi = XUN_YI[xun_shou]
    p0 = g2p[yi]                            # 旬首六仪所落之宫
    zhifu_star = STAR[p0]                   # 该宫本位星（中五=天禽）
    zhishi_door = DOOR[p0] or DOOR[2]       # 该宫本位门（中五无门→寄坤二死门）

    # 值符随时干：时干地盘之宫（甲时按遁干=旬首仪）
    shi_gan_earth = yi if shi_gz[0] == '甲' else shi_gz[0]
    pt = g2p[shi_gan_earth]
    p02 = 2 if p0 == 5 else p0              # 中五寄坤二（论位移）
    pt2 = 2 if pt == 5 else pt
    k = (RING.index(pt2) - RING.index(p02)) % 8 if yang \
        else (RING.index(p02) - RING.index(pt2)) % 8
    sk = k if yang else -k                  # 阳遁顺时针 / 阴遁逆时针

    # 九星 + 天盘干（天禽恒居中五，中五天盘干=中五地盘干）
    stars, sky = {5: STAR[5]}, {5: earth[5]}
    for h in RING:
        p = ring_step(h, sk)
        stars[p] = STAR[h]
        sky[p] = earth[h]

    # 八神：值符起于地盘时干之宫，阳顺时针/阴逆时针
    gods = {}
    for j in range(8):
        gods[ring_step(pt2, j if yang else -j)] = GODS[j]

    # 八门：值使随时支，自 P0 沿九宫数序阳顺阴逆走 (时支−旬首支) 步
    steps = (DZ.index(shi_zhi) - DZ.index(xun_shou[1])) % 12
    raw = wrap9(p0 + steps) if yang else wrap9(p0 - steps)
    door_pal = 2 if raw == 5 else raw       # 落中五寄坤二
    d0 = DOOR_ORDER.index(zhishi_door)
    doors = {}
    for j in range(8):
        s = j if yang else -j
        doors[ring_step(door_pal, s)] = DOOR_ORDER[(d0 + s) % 8]

    # 旬空 / 马星
    kong_day = KONG[GZ[(GZ.index(day_gz) // 10) * 10]]
    kong_shi = KONG[xun_shou]
    ma = next(m for group, m in MA.items() if shi_zhi in group)

    palaces = []
    for p in range(1, 10):
        e = {'宫': p, '方位': GONG[p], '天盘干': sky[p], '地盘干': earth[p],
             '门': doors.get(p), '星': stars.get(p), '神': gods.get(p),
             '空亡': any(ZHI_GONG[z] == p for z in kong_shi),
             '马星': ZHI_GONG[ma] == p}
        if p == 5:
            e['寄宫'] = '坤二'
        palaces.append(e)

    fuyin = all(sky[p] == earth[p] for p in range(1, 10))
    return {
        '时间': dt.strftime('%Y-%m-%d %H:%M'),
        '节气': jq,
        '遁': dun,
        '三元': yuan,
        '符头': futou,
        '日干支': day_gz,
        '时干支': shi_gz,
        '旬首': xun_shou,
        '定局': f'{dun}{"一二三四五六七八九"[ju - 1]}局',
        '局数': ju,
        '值符': {'星': zhifu_star, '原宫': p0, '落宫': pt2,
                 **({'寄宫': '坤二'} if p0 == 5 else {})},
        '值使': {'门': zhishi_door, '原宫': p0, '落宫': door_pal},
        '九宫': palaces,
        '旬空': {'日旬空': list(kong_day), '时旬空': list(kong_shi)},
        '马星': ma,
        '伏吟': fuyin,
    }


# ──────────────────────────── 回归测试 ────────────────────────────
def _chart(r):
    """从排盘结果抽出便于比对的层"""
    ps = {e['宫']: e for e in r['九宫']}
    return {
        '地盘': {p: e['地盘干'] for p, e in ps.items()},
        '天盘': {p: e['天盘干'] for p, e in ps.items()},
        '星': {p: e['星'] for p, e in ps.items()},
        '门': {p: e['门'] for p, e in ps.items()},
        '神': {p: e['神'] for p, e in ps.items()},
    }


# 锚点A：2024-01-01 12:00 阳遁一局（出处 askqimen 排盘步骤同例，逐宫核对其盘面图）
ANCHOR_A = {
    '时间': '2024-01-01 12:00', '节气': '冬至', '遁': '阳遁', '三元': '上元',
    '符头': '甲子', '日干支': '甲子', '时干支': '庚午', '旬首': '甲子',
    '定局': '阳遁一局', '局数': 1,
    '地盘': {1: '戊', 2: '己', 3: '庚', 4: '辛', 5: '壬', 6: '癸', 7: '丁', 8: '丙', 9: '乙'},
    '天盘': {1: '丁', 2: '辛', 3: '戊', 4: '丙', 5: '壬', 6: '己', 7: '乙', 8: '癸', 9: '庚'},
    '星': {1: '天柱', 2: '天辅', 3: '天蓬', 4: '天任', 5: '天禽',
           6: '天芮', 7: '天英', 8: '天心', 9: '天冲'},
    '门': {1: '伤门', 2: '开门', 3: '景门', 4: '死门', 5: None,
           6: '生门', 7: '休门', 8: '杜门', 9: '惊门'},
    '神': {1: '九地', 2: '六合', 3: '值符', 4: '腾蛇', 5: None,
           6: '玄武', 7: '白虎', 8: '九天', 9: '太阴'},
    '值符': ('天蓬', 1, 3), '值使': ('休门', 1, 7),
    '旬空': ['戌', '亥'], '马星': '申',
}
# 锚点B：2026-09-12 22:00 阴遁六局（出处 qimen-club 排盘方法实盘示范，逐宫核对其表）
ANCHOR_B = {
    '时间': '2026-09-12 22:00', '节气': '白露', '遁': '阴遁', '三元': '下元',
    '符头': '己丑', '日干支': '己丑', '时干支': '乙亥', '旬首': '甲戌',
    '定局': '阴遁六局', '局数': 6,
    '地盘': {1: '癸', 2: '壬', 3: '辛', 4: '庚', 5: '己', 6: '戊', 7: '乙', 8: '丙', 9: '丁'},
    '天盘': {1: '戊', 2: '丁', 3: '丙', 4: '辛', 5: '己', 6: '乙', 7: '壬', 8: '癸', 9: '庚'},
    '星': {1: '天心', 2: '天英', 3: '天任', 4: '天冲', 5: '天禽',
           6: '天柱', 7: '天芮', 8: '天蓬', 9: '天辅'},
    '门': {1: '伤门', 2: '开门', 3: '景门', 4: '死门', 5: None,
           6: '生门', 7: '休门', 8: '杜门', 9: '惊门'},
    '神': {1: '九地', 2: '腾蛇', 3: '白虎', 4: '六合', 5: None,
           6: '九天', 7: '值符', 8: '玄武', 9: '太阴'},
    '值符': ('天禽', 5, 7), '值使': ('死门', 5, 4),
    '旬空': ['申', '酉'], '马星': '巳',
}


def test():
    fails = []

    def eq(label, got, want):
        ok = got == want
        print(f"{'✓' if ok else '✗'} {label}: {got!r}" + ("" if ok else f" ≠ {want!r}"))
        if not ok:
            fails.append(label)

    # ── 1. 用局表：24节气×三元 72格无缺，且与两出处逐格一致 ──
    want_ju = {'冬至': (1, 7, 4), '小寒': (2, 8, 5), '大寒': (3, 9, 6), '立春': (8, 5, 2),
               '雨水': (9, 6, 3), '惊蛰': (1, 7, 4), '春分': (3, 9, 6), '清明': (4, 1, 7),
               '谷雨': (5, 2, 8), '立夏': (4, 1, 7), '小满': (5, 2, 8), '芒种': (6, 3, 9),
               '夏至': (9, 3, 6), '小暑': (8, 2, 5), '大暑': (7, 1, 4), '立秋': (2, 5, 8),
               '处暑': (1, 4, 7), '白露': (9, 3, 6), '秋分': (7, 1, 4), '寒露': (6, 9, 3),
               '霜降': (5, 8, 2), '立冬': (6, 9, 3), '小雪': (5, 8, 2), '大雪': (4, 7, 1)}
    eq('用局表24节气×三元逐格(72格)', JU, want_ju)
    cells = [n for v in JU.values() for n in v]
    eq('用局表72格无缺且全为1-9',
       (len(JQ), len(JU), len(cells), all(1 <= n <= 9 for n in cells),
        all(len(v) == 3 for v in JU.values()), set(JQ) == set(JU)),
       (24, 24, 72, True, True, True))
    # 节气编号→阳遁前12/阴遁后12
    eq('节气编号冬至=0…大雪=23', (JQ[0], JQ[11], JQ[12], JQ[23]), ('冬至', '芒种', '夏至', '大雪'))

    # ── 2. 黄金锚点A：2024-01-01 12:00 阳遁一局（askqimen 同例） ──
    ra = qimen(datetime(2024, 1, 1, 12, 0))
    ca = _chart(ra)
    for k in ('时间', '节气', '遁', '三元', '符头', '日干支', '时干支', '旬首', '定局', '局数'):
        eq(f'A {k}', ra[k], ANCHOR_A[k])
    for k in ('地盘', '天盘', '星', '门', '神'):
        eq(f'A 九宫{k}', ca[k], ANCHOR_A[k])
    eq('A 值符(星,原宫,落宫)',
       (ra['值符']['星'], ra['值符']['原宫'], ra['值符']['落宫']), ANCHOR_A['值符'])
    eq('A 值使(门,原宫,落宫)',
       (ra['值使']['门'], ra['值使']['原宫'], ra['值使']['落宫']), ANCHOR_A['值使'])
    eq('A 时旬空', ra['旬空']['时旬空'], ANCHOR_A['旬空'])
    eq('A 马星', ra['马星'], ANCHOR_A['马星'])

    # ── 3. 黄金锚点B：2026-09-12 22:00 阴遁六局（qimen-club 同例） ──
    rb = qimen(datetime(2026, 9, 12, 22, 0))
    cb = _chart(rb)
    for k in ('时间', '节气', '遁', '三元', '符头', '日干支', '时干支', '旬首', '定局', '局数'):
        eq(f'B {k}', rb[k], ANCHOR_B[k])
    for k in ('地盘', '天盘', '星', '门', '神'):
        eq(f'B 九宫{k}', cb[k], ANCHOR_B[k])
    eq('B 值符(星,原宫,落宫)',
       (rb['值符']['星'], rb['值符']['原宫'], rb['值符']['落宫']), ANCHOR_B['值符'])
    eq('B 值使(门,原宫,落宫)',
       (rb['值使']['门'], rb['值使']['原宫'], rb['值使']['落宫']), ANCHOR_B['值使'])
    eq('B 时旬空', rb['旬空']['时旬空'], ANCHOR_B['旬空'])
    eq('B 马星', rb['马星'], ANCHOR_B['马星'])

    # ── 4. 地盘自洽：18局全部三奇六仪9个布齐无重（六仪6+三奇3=9；任务书“11个”系笔误） ──
    for yang in (True, False):
        for ju in range(1, 10):
            e = dipan(ju, yang)
            eq(f'地盘布齐无重 {"阳" if yang else "阴"}遁{ju}局',
               (sorted(e.values()) == sorted(YI), len(e)), (True, 9))
    # 阳顺/阴逆九宫序验证：阳遁沿1..9递增、阴遁沿9..1递减
    for ju in range(1, 10):
        e = dipan(ju, True)
        seq = [e[wrap9(ju + i)] for i in range(9)]
        eq(f'阳遁{ju}局顺布九宫序', seq, YI)
        e = dipan(ju, False)
        seq = [e[wrap9(ju - i)] for i in range(9)]
        eq(f'阴遁{ju}局逆布九宫序', seq, YI)

    # ── 5. 阴遁一局地盘（askqimen 表8“阴遁逆排 离九→…→坎一”推得） ──
    eq('阴遁一局地盘', dipan(1, False),
       {1: '戊', 2: '乙', 3: '丙', 4: '丁', 5: '癸', 6: '壬', 7: '辛', 8: '庚', 9: '己'})

    # ── 6. 符头三元（拆补法核心规则，勿再改） ──
    for gz, want in [('甲子', ('甲子', '上元')), ('己卯', ('己卯', '上元')),
                     ('戊子', ('甲申', '中元')), ('癸酉', ('己巳', '中元')),
                     ('乙卯', ('甲寅', '中元')), ('己丑', ('己丑', '下元')),
                     ('庚辰', ('己卯', '上元')), ('丁未', ('甲辰', '下元'))]:
        eq(f'符头三元 {gz}', futou_yuan(gz), want)

    # ── 7. 值符随时干 / 值使随时支（两锚点均须落对宫） ──
    for tag, r in (('A', ra), ('B', rb)):
        earth = {e['宫']: e['地盘干'] for e in r['九宫']}
        yi = XUN_YI[r['旬首']]
        shi_gan = yi if r['时干支'][0] == '甲' else r['时干支'][0]
        eq(f'{tag} 值符落宫==地盘时干之宫', r['值符']['落宫'],
           [p for p, g in earth.items() if g == shi_gan][0]
           if shi_gan in earth.values() and [p for p, g in earth.items() if g == shi_gan] else None)
        p0 = r['值使']['原宫']
        steps = (DZ.index(r['时干支'][1]) - DZ.index(r['旬首'][1])) % 12
        want = wrap9(p0 + steps) if r['遁'] == '阳遁' else wrap9(p0 - steps)
        eq(f'{tag} 值使落宫==P0±(时支-旬首支)', r['值使']['落宫'], 2 if want == 5 else want)

    # ── 8. 甲子时伏吟（值符随时干→时干即旬首仪之宫，天盘=地盘） ──
    rf = qimen(datetime(2024, 1, 1, 0, 0))
    eq('2024-01-01 00:00 甲子时定局', rf['定局'], '阳遁一局')
    eq('甲子时伏吟(天盘=地盘)', (rf['伏吟'], _chart(rf)['天盘'] == _chart(rf)['地盘']),
       (True, True))

    # ── 9. 节气边界（交节时刻精确判定） ──
    eq('2024-01-01 节气=冬至/阳遁', (jieqi_id_at(datetime(2024, 1, 1, 12, 0)), JQ[0]),
       (0, '冬至'))
    eq('2026-11-18 节气=立冬/阴遁', (jieqi_id_at(datetime(2026, 11, 18, 21, 0)),
                                JQ[21], JQ[21] >= '夏至'),
       (21, '立冬', True))
    # 用 sxtwl 自己的交节时刻验证“未到回退、到了生效”
    if sxtwl is not None:
        x = sxtwl.fromSolar(2026, 11, 22)
        if x.hasJieQi():
            th = ((x.getJieQiJD() + 0.5) % 1) * 24
            h0 = int(th)
            m0 = int((th - h0) * 60)
            before = datetime(2026, 11, 22, h0, max(m0 - 1, 0))
            after = datetime(2026, 11, 22, h0, m0 + 1)
            eq('交节时刻前仍属上一节气(立冬)',
               JQ[jieqi_id_at(before)], '立冬')
            eq('交节时刻后进入小雪', JQ[jieqi_id_at(after)], '小雪')

    # ── 10. --question 的值绝不被当成日期解析 ──
    q1, dt1 = parse_args(['qimen.py', '--question', '2026-01-02'])
    eq('--question 日期串只当问题', (q1, dt1 is None), ('2026-01-02', True))
    q2, dt2 = parse_args(['qimen.py', '2026-01-02', '10:00',
                          '--question', '2025-03-04 05:06'])
    eq('--question 不吃位置时间',
       (q2, dt2.strftime('%Y-%m-%d %H:%M') if dt2 else None),
       ('2025-03-04 05:06', '2026-01-02 10:00'))

    print("\n" + ("全部通过 ✅" if not fails else f"失败 {len(fails)} 项 ❌: {fails}"))
    return 0 if not fails else 1


def parse_args(argv):
    """命令行解析：--question 的值绝不参与日期解析（meihua.py 同款跳位法）。
    未知 --flag、--question 缺值/超 2000 字符、第 3 个多余位置参数一律 exit 1（不写日志）。"""
    question, skip = None, set()
    if '--question' in argv:
        qi = argv.index('--question')
        if qi + 1 >= len(argv):
            print("--question 缺少值（后面应跟问题字符串）", file=sys.stderr)
            sys.exit(1)
        question = argv[qi + 1]
        skip.add(qi + 1)
        if len(question) > 2000:
            print("--question 超过 2000 字符上限", file=sys.stderr)
            sys.exit(1)
    unknown = [a for i, a in enumerate(argv[1:], 1)
               if a.startswith('--') and i not in skip and a not in ('--question', '--test')]
    if unknown:
        print(f"未知参数: {unknown[0]}", file=sys.stderr)
        sys.exit(1)
    args = [a for i, a in enumerate(argv[1:], 1)
            if not a.startswith('--') and i not in skip]
    if len(args) > 2:
        print(f"位置参数过多: {args[2:]}（只接受 'YYYY-MM-DD HH:MM'）", file=sys.stderr)
        sys.exit(1)
    if len(args) >= 2:
        try:
            dt = datetime.strptime(args[0] + ' ' + args[1], '%Y-%m-%d %H:%M')
        except ValueError:
            print(f"时间格式无法解析: '{args[0]} {args[1]}'，应为 YYYY-MM-DD HH:MM")
            sys.exit(1)
    elif len(args) == 1:
        try:
            dt = datetime.strptime(args[0], '%Y-%m-%d')
            print("注意：只给了日期未给时间，按 00:00 排盘", file=sys.stderr)
        except ValueError:
            print(f"日期格式无法解析: '{args[0]}'，应为 YYYY-MM-DD")
            sys.exit(1)
    else:
        dt = None
    return question, dt


if __name__ == '__main__':
    if '--test' in sys.argv:
        sys.exit(test())
    question, dt = parse_args(sys.argv)
    out = qimen(dt or datetime.now())
    if question:
        out['问题'] = question
    print(json.dumps(out, ensure_ascii=False, indent=2))
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'qimen', 'ts': datetime.now().isoformat(),
                                'result': out}, ensure_ascii=False) + '\n')
    except Exception:
        pass
