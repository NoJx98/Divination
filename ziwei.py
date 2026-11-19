#!/usr/bin/env python3
"""ziwei.py — 紫微斗数排盘引擎（安星法全量，2026-11-18 创建）

用法:
  python3 ziwei.py "1990-05-15 06:00" --gender f            # 排盘（JSON 输出）
  python3 ziwei.py "1990-05-15 06:00" --gender m --question "问事业"
  python3 ziwei.py --test                                    # 回归测试（黄金锚点）

输入为公历出生日期时间（命盘排盘，非时间起卦），--question 的值只做存档，
绝不会被当成日期解析。输出 JSON（ensure_ascii=False, indent=2）；
正常排盘末尾把结果追加到 divination_log.jsonl（写失败不崩溃）。

──────────────────────── 安星规则与出处 ────────────────────────
1) 命宫/身宫：寅起正月顺数至生月，自生月宫起子时逆数至生时安命、顺数至生时安身。
   出处《紫微斗数全书》卷二·安身命例：
   https://zh.wikisource.org/wiki/紫微斗數全書/卷二
2) 十二宫逆布（命兄弟夫子财疾迁仆官田福父），全书原文「安十二宫例：男女俱从逆转，
   切忌莫顺去」→ 兄弟宫在命宫地支逆行一格，父母宫在顺行一格。同上卷二。
   维基百科「以命宫逆时针布命迁十二宫」同义：
   https://zh.wikipedia.org/wiki/紫微斗数
3) 十二宫天干：五虎遁（甲己丙作首…），全书「起五行寅例」，同上卷二。
4) 五行局：命宫干支纳音定局（水二木三金四土五火六），全书「六十花甲子纳音歌」；
   干支取数捷诀（干1-5 支1-3 相加超5减5）与纳音全 60 组等价，作为回归断言。
   捷诀出处：iztro 安星诀 12「定五行局訣」https://iztro.com/zh_TW/learn/setup
5) 紫微星：起紫微星诀「六五四三二，酉午亥辰丑，局数除日数，商数宫前走；若见数无余，
   便要起虎口，日数小於局，还直宫中守」——日数补 x 凑局数倍数，商数自寅起数，
   补数偶则顺行 x 格、奇则逆行 x 格。全书卷二载水二/木三/金四/土五/火六六局日位图；
   口诀与算例（木三27日戌、火六13日亥、土五6日未）见 iztro 安星诀 8：
   https://iztro.com/zh_TW/learn/setup
   六局×三十日全量速查表核对用：https://9zi.ai/tw/guide/manual-chart-calculation/
6) 十四主星：全书「安南北斗诸星诀」——「紫微天机逆行旁，隔一阳武天同当，又隔二位
   廉贞地，空三复见紫微郎；天府太阴与贪狼，巨门天相及天梁，七杀空三破军位」。
   即紫微系：天机-1、太阳-3、武曲-4、天同-5、廉贞-8（相对紫微逆行）；
   天府与紫微以寅申为轴对称（全书「安天府图：紫居丑则府居卯」）：天府=(4-紫微)%12，
   天府系顺行：太阴+1 贪狼+2 巨门+3 天相+4 天梁+5 七杀+6 破军+10。同上卷二。
7) 辅星杂曜（口诀出处均为全书卷二，对照表另见）：
   - 禄存/擎羊/陀罗（按年干）：甲禄到寅…癸禄居子；禄前擎羊、禄后陀罗。
   - 天魁天钺（按年干）：甲戊庚牛羊、乙己鼠猴乡、丙丁猪狗位、六辛逢虎马、壬癸兔蛇藏。
   - 左辅右弼（按月）：左辅正月起辰顺数至生月；右弼正月起戌逆数至生月。
   - 文昌文曲（按时辰）：文昌戌起子时逆数至生时；文曲辰起子时顺数至生时。
   - 火星铃星（按年支三合组定子时起位，再顺数至生时）：
     寅午戌→火丑铃卯，申子辰→火寅铃戌，巳酉丑→火卯铃戌，亥卯未→火酉铃戌。
     全书「安火铃二星诀」只给起宫；「起子时位顺数至生时」的读法见 iztro 安星诀 17
     （含算例：壬辰年卯时→火在巳、铃在丑）https://iztro.com/zh_TW/learn/setup ，
     与独立引擎对照表 https://knowyourbazi.com/ziwei/huoxing 一致；
     六吉六煞安星依据分类表（火铃=生年地支+生时，不涉生月）：
     https://starqode.com/ziwei-doushu-auxiliary-stars-placement-rules/
     注：本脚本从通行/引擎口径（不加生月一程），与任务描述的「年支+月时」措辞略有出入，
     差异点已在此注明，便于复核。
   左辅右弼/昌曲/魁钺/禄存对照表出处：同 starqode 页面。
8) 生年四化（十天干全表，顺序禄权科忌）：全书卷二「安禄权科忌四星变化诀」：
   甲廉破武阳、乙机梁紫月、丙同机昌廉、丁月同机巨、戊贪月弼机、己武贪梁曲、
   庚日武阴同、辛巨阳曲昌、壬梁紫府武、癸破巨阴贪。
   维基百科同表并注明异文（https://zh.wikipedia.org/wiki/紫微斗数 ）：
   南派/iztro 通行本壬年作「梁紫左武」（左辅化科而非天府化科），
   本脚本从全书原文，异文在此备注，不影响其余 9 干。
9) 大限：全书卷二「安大限诀：阳男阴女从命前一宫起顺行，是父母宫；
   阴男阳女从命后一宫起逆行，是兄弟宫」——即阳男阴女顺行（地支顺行，第二限落父母宫）、
   阴男阳女逆行（地支逆行，第二限落兄弟宫）；起运岁=五行局数，每限十年。
10) 年界取农历正月初一、闰月前半月(<=15日)并入上月、后半月归下月、晚子时算当日，
    为紫微斗数通行口径（9zi 排盘方法论 https://9zi.ai/tw/methodology/ ；
    iztro fixLeap 同口径）。农历换算一律用 sxtwl，禁手写农历表。
    跨脚本口径声明：本脚本晚子时算当日（依 iztro/全书口径），与 qimen.py“晚子时(23:00后)
    日柱进一位”（依 qimen-club 换日点）各依其流派出处，同刻两脚本日柱可能差一位属正常。
11) 黄金锚点（--test 内核对，出处见测试注释）：
    - 1990-05-15 卯时女：https://9zi.ai/tw/guide/manual-chart-calculation/ 完整示例
    - 2000-08-16 寅时女 / 2023-04-10 辰时女（闰月）：
      https://github.com/SylarLong/iztro/blob/main/src/__tests__/astro/astro.test.ts
"""
import os
import sys
import json
from datetime import date, datetime

# ──────────────────────────── 基础表 ────────────────────────────
TG = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DZ = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
GZ = [TG[i % 10] + DZ[i % 12] for i in range(60)]

NAYIN = ['海中金', '炉中火', '大林木', '路旁土', '剑锋金', '山头火', '涧下水', '城头土',
         '白蜡金', '杨柳木', '泉中水', '屋上土', '霹雳火', '松柏木', '长流水', '砂石金',
         '山下火', '平地木', '壁上土', '金箔金', '覆灯火', '天河水', '大驿土', '钗钏金',
         '桑柘木', '大溪水', '沙中土', '天上火', '石榴木', '大海水']
JU_OF_ELEMENT = {'水': 2, '木': 3, '金': 4, '土': 5, '火': 6}
JU_NAME = {2: '水二局', 3: '木三局', 4: '金四局', 5: '土五局', 6: '火六局'}

# 十二宫：从命宫起地支逆行布（全书「男女俱从逆转」）
PALACES = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄', '迁移', '仆役',
           '官禄', '田宅', '福德', '父母']

# 五虎遁：年干 → 寅宫天干
TIGER = {'甲': 2, '己': 2, '乙': 4, '庚': 4, '丙': 6, '辛': 6,
         '丁': 8, '壬': 8, '戊': 0, '癸': 0}

# 五鼠遁：日干 → 子时天干
RAT = {'甲': 0, '己': 0, '乙': 2, '庚': 2, '丙': 4, '辛': 4,
       '丁': 6, '壬': 6, '戊': 8, '癸': 8}

# 生年四化（全书「安禄权科忌四星变化诀」，顺序：化禄 化权 化科 化忌）
SIHUA = {
    '甲': ['廉贞', '破军', '武曲', '太阳'],
    '乙': ['天机', '天梁', '紫微', '太阴'],
    '丙': ['天同', '天机', '文昌', '廉贞'],
    '丁': ['太阴', '天同', '天机', '巨门'],
    '戊': ['贪狼', '太阴', '右弼', '天机'],
    '己': ['武曲', '贪狼', '天梁', '文曲'],
    '庚': ['太阳', '武曲', '太阴', '天同'],
    '辛': ['巨门', '太阳', '文曲', '文昌'],
    '壬': ['天梁', '紫微', '天府', '武曲'],
    '癸': ['破军', '巨门', '太阴', '贪狼'],
}
HUA = ['化禄', '化权', '化科', '化忌']

# 禄存（按年干）；擎羊=禄前一位、陀罗=禄后一位
LUCUN = {'甲': 2, '乙': 3, '丙': 5, '丁': 6, '戊': 5, '己': 6,
         '庚': 8, '辛': 9, '壬': 11, '癸': 0}
# 天魁天钺（按年干）
KUIYUE = {'甲': (1, 7), '戊': (1, 7), '庚': (1, 7), '乙': (0, 8), '己': (0, 8),
          '丙': (11, 9), '丁': (11, 9), '辛': (6, 2), '壬': (3, 5), '癸': (3, 5)}
# 火星铃星（按年支三合组，子时起位）
HUOLING = {'寅': (1, 3), '午': (1, 3), '戌': (1, 3),
           '申': (2, 10), '子': (2, 10), '辰': (2, 10),
           '巳': (3, 10), '酉': (3, 10), '丑': (3, 10),
           '亥': (9, 10), '卯': (9, 10), '未': (9, 10)}
# 命主（按命宫地支）/ 身主（按生年地支），全书卷二
MINGZHU = {'子': '贪狼', '丑': '巨门', '寅': '禄存', '卯': '文曲', '辰': '廉贞',
           '巳': '武曲', '午': '破军', '未': '武曲', '申': '廉贞', '酉': '文曲',
           '戌': '禄存', '亥': '巨门'}
SHENZHU = {'子': '火星', '午': '火星', '丑': '天相', '未': '天相', '寅': '天梁',
           '申': '天梁', '卯': '天同', '酉': '天同', '辰': '文昌', '戌': '文昌',
           '巳': '天机', '亥': '天机'}

MAJOR = ['紫微', '天机', '太阳', '武曲', '天同', '廉贞', '天府', '太阴',
         '贪狼', '巨门', '天相', '天梁', '七杀', '破军']

try:
    import sxtwl as _sxtwl
except Exception:                                    # pragma: no cover
    _sxtwl = None

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl')


def shichen_idx(hour: int) -> int:
    """时辰索引：子0 丑1 … 亥11（23~00 与 00~01 均为子）"""
    return ((hour + 1) // 2) % 12


def lunar_of(d: date):
    """sxtwl 公历→农历，返回 (农历年, 月, 日, 是否闰月)"""
    if _sxtwl is None:
        raise RuntimeError('sxtwl 不可用，无法做农历换算')
    x = _sxtwl.fromSolar(d.year, d.month, d.day)
    return x.getLunarYear(), x.getLunarMonth(), x.getLunarDay(), bool(x.isLunarLeap())


def day_ganzhi(d: date) -> str:
    if _sxtwl is None:
        raise RuntimeError('sxtwl 不可用')
    g = _sxtwl.fromSolar(d.year, d.month, d.day).getDayGZ()
    return TG[g.tg] + DZ[g.dz]


def year_ganzhi(lunar_year: int) -> str:
    """紫微斗数年干支：按农历年（正月初一界）"""
    return GZ[(lunar_year - 4) % 60]


def month_ganzhi(year_gan: str, lunar_month: int) -> str:
    """紫微斗数月柱：五虎遁按农历月（寅=正月），非八字节气月柱"""
    idx = (2 + lunar_month - 1) % 12
    return TG[(TIGER[year_gan] + lunar_month - 1) % 10] + DZ[idx]


def hour_ganzhi(day_gan: str, hour_idx: int) -> str:
    """五鼠遁时柱"""
    return GZ[(6 * RAT[day_gan] + hour_idx) % 60]


def nayin(gz: str) -> str:
    return NAYIN[GZ.index(gz) // 2]


def wuxing_ju(palace_gz: str) -> int:
    """五行局：命宫干支纳音 → 水二木三金四土五火六（纳音名末字即五行）"""
    return JU_OF_ELEMENT[nayin(palace_gz)[-1]]


def ju_by_numbers(heavenly: str, earthly: str) -> int:
    """干支取数捷诀（与纳音等价，作为回归断言）"""
    gn = TG.index(heavenly) // 2 + 1
    zn = (DZ.index(earthly) % 6) // 2 + 1
    s = gn + zn
    while s > 5:
        s -= 5
    return {1: 3, 2: 4, 3: 2, 4: 6, 5: 5}[s]


def soul_body(lunar_month: int, hour_idx: int):
    """命宫/身宫（子基地支索引）。寅起正月顺数至生月，生月宫起子时逆数安命、顺数安身"""
    month_branch = (2 + lunar_month - 1) % 12          # 生月所在宫
    soul = (month_branch - hour_idx) % 12
    body = (month_branch + hour_idx) % 12
    return soul, body


def ziwei_index(ju: int, lunar_day: int) -> int:
    """起紫微星诀（子基地支索引）：日数补 x 凑局数倍数，商数自寅起，补数偶顺奇逆"""
    off = 0
    while (lunar_day + off) % ju:
        off += 1
    quotient = ((lunar_day + off) // ju) % 12
    yin_based = quotient - 1 + (off if off % 2 == 0 else -off)
    return (yin_based + 2) % 12                        # 寅基→子基


def major_stars(z: int) -> dict:
    """十四主星：紫微系逆行 + 天府系（天府与紫微寅申轴对称）顺行"""
    t = (4 - z) % 12
    stars = {
        '紫微': z, '天机': (z - 1) % 12, '太阳': (z - 3) % 12, '武曲': (z - 4) % 12,
        '天同': (z - 5) % 12, '廉贞': (z - 8) % 12,
        '天府': t, '太阴': (t + 1) % 12, '贪狼': (t + 2) % 12, '巨门': (t + 3) % 12,
        '天相': (t + 4) % 12, '天梁': (t + 5) % 12, '七杀': (t + 6) % 12,
        '破军': (t + 10) % 12,
    }
    return stars


def minor_stars(year_gan: str, year_zhi: str, lunar_month: int, hour_idx: int) -> dict:
    """辅星杂曜：禄存羊陀(年干) 魁钺(年干) 左右(月) 昌曲(时) 火铃(年支+时)"""
    out = {}
    lu = LUCUN[year_gan]
    out['禄存'] = lu
    out['擎羊'] = (lu + 1) % 12
    out['陀罗'] = (lu - 1) % 12
    kui, yue = KUIYUE[year_gan]
    out['天魁'] = kui
    out['天钺'] = yue
    out['左辅'] = (4 + lunar_month - 1) % 12           # 辰起正月顺数
    out['右弼'] = (8 - (lunar_month - 1)) % 12         # 戌起正月逆数
    out['文昌'] = (10 - hour_idx) % 12                 # 戌起子时逆数至生时
    out['文曲'] = (4 + hour_idx) % 12                  # 辰起子时顺数至生时
    huo, ling = HUOLING[year_zhi]
    out['火星'] = (huo + hour_idx) % 12
    out['铃星'] = (ling + hour_idx) % 12
    return out


def effective_month(lunar_month: int, lunar_day: int, is_leap: bool) -> int:
    """闰月口径：前半月(<=15日)并入上月，后半月归下月（iztro fixLeap / 9zi 通行口径）"""
    if not is_leap:
        return lunar_month
    if lunar_day <= 15:
        return lunar_month - 1 if lunar_month > 1 else 12
    return lunar_month + 1 if lunar_month < 12 else 1


MONTH_CN = ['正', '二', '三', '四', '五', '六', '七', '八', '九', '十', '冬', '腊']


def cn_day(n: int) -> str:
    """农历日中文：初一…初十、十一…十九、二十、廿一…廿九、三十"""
    if n <= 10:
        return '初' + '一二三四五六七八九十'[n - 1]
    if n < 20:
        return '十' + '一二三四五六七八九'[n - 11]
    if n == 20:
        return '二十'
    if n < 30:
        return '廿' + '一二三四五六七八九'[n - 21]
    return '三十'


def palace_stem(year_gan: str, branch_idx: int) -> str:
    """五虎遁：寅宫起年干对应天干，按地支顺行推（偏移必须 mod 12 后再 mod 10）"""
    return TG[(TIGER[year_gan] + (branch_idx - 2) % 12) % 10]


def decadals(soul: int, ju: int, year_gan: str, gender):
    """大限：阳男阴女顺行（第二限父母宫），阴男阳女逆行（第二限兄弟宫）；局数起岁，每限十年"""
    if gender not in ('m', 'f'):
        return None
    yang_year = TG.index(year_gan) % 2 == 0
    forward = yang_year if gender == 'm' else (not yang_year)
    seq = []
    for i in range(12):
        idx = (soul + i) % 12 if forward else (soul - i) % 12
        start = ju + 10 * i
        seq.append((idx, [start, start + 9]))
    return {'方向': '顺行' if forward else '逆行', '起运岁': ju, '序列': seq}


def chart(dt: datetime, gender=None) -> dict:
    d = dt.date()
    hour_idx = shichen_idx(dt.hour)
    ly, lm, ld, leap = lunar_of(d)
    use_m = effective_month(lm, ld, leap)
    yg = year_ganzhi(ly)
    year_gan, year_zhi = yg[0], yg[1]

    soul, body = soul_body(use_m, hour_idx)
    soul_gz = palace_stem(year_gan, soul) + DZ[soul]
    ju = wuxing_ju(soul_gz)

    z = ziwei_index(ju, ld)
    majors = major_stars(z)
    minors = minor_stars(year_gan, year_zhi, use_m, hour_idx)
    sihua = dict(zip(HUA, SIHUA[year_gan]))

    # 十二宫（宫名序：命→父母），地支逆行
    by_branch = {}
    palace_list = []
    dalu = decadals(soul, ju, year_gan, gender)
    dalu_map = {}
    if dalu:
        for idx, rng in dalu['序列']:
            dalu_map[idx] = rng

    for j, name in enumerate(PALACES):
        b = (soul - j) % 12
        gz = palace_stem(year_gan, b) + DZ[b]
        mstars = [s for s, i in majors.items() if i == b]
        xstars = [s for s, i in minors.items() if i == b]
        hua_here = [f'{k}-{v}' for k, v in sihua.items()
                    if v in mstars or v in xstars]
        item = {'宫': name, '地支': DZ[b], '干支': gz,
                '主星': mstars, '辅星': xstars, '四化': hua_here}
        if dalu:
            item['大限'] = dalu_map[b]
        palace_list.append(item)
        by_branch[b] = (name, mstars, xstars)

    # 四化落宫
    sihua_full = {}
    for k, star in sihua.items():
        for b, (pname, ms, xs) in by_branch.items():
            if star in ms or star in xs:
                sihua_full[k] = {'星': star, '宫': pname, '地支': DZ[b]}
                break

    lunar_text = f'{yg}年{"闰" if leap else ""}{MONTH_CN[lm - 1]}月{cn_day(ld)}日'
    res = {
        '公历': dt.strftime('%Y-%m-%d %H:%M'),
        '性别': {'m': '男', 'f': '女'}.get(gender, gender),
        '农历': lunar_text,
        '时辰': DZ[hour_idx] + '时',
        # 早/晚子时细分（原 "时辰" 字段值不变）：23 时=晚子时(timeIndex 12)、0 时=早子时(timeIndex 0)
        '时辰细分': ('晚子时' if dt.hour == 23 else
                     '早子时' if dt.hour == 0 else DZ[hour_idx] + '时'),
        '四柱': {'年柱': yg,
                 '月柱': month_ganzhi(year_gan, use_m),
                 '日柱': day_ganzhi(d),
                 '时柱': hour_ganzhi(day_ganzhi(d)[0], hour_idx)},
        '排盘月': use_m,
        '五行局': JU_NAME[ju],
        '命宫': {'地支': DZ[soul], '干支': soul_gz},
        '身宫': {'地支': DZ[body]},
        '命主': MINGZHU[DZ[soul]],
        '身主': SHENZHU[year_zhi],
        '紫微在': DZ[z],
        '生年四化': sihua_full,
        '十二宫': palace_list,
        '大限': (None if not dalu else
                 {'方向': dalu['方向'], '起运岁': dalu['起运岁'],
                  '规则': '阳男阴女顺行、阴男阳女逆行；起运岁=五行局数，每限十年'}),
    }
    if leap:
        res['备注'] = '闰月：前半月并上月、后半月归下月（当前排盘月=%d）' % use_m
    return res


# ──────────────────────────── CLI ────────────────────────────
def parse_cli(argv):
    """返回 (test_flag, datetime, gender, question)。--question/--gender 的值绝不进日期解析"""
    question = None
    gender = None
    skip = set()
    test = False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--test':
            test = True
        elif a == '--question':
            if i + 1 >= len(argv):
                raise ValueError('--question 缺少值（后面应跟问题字符串）')
            question = argv[i + 1]
            if len(question) > 2000:
                raise ValueError('--question 超过 2000 字符上限')
            skip.update((i, i + 1))
            i += 1
        elif a.startswith('--question='):
            question = a.split('=', 1)[1]
            if len(question) > 2000:
                raise ValueError('--question 超过 2000 字符上限')
            skip.add(i)
        elif a == '--gender' and i + 1 < len(argv):
            gender = argv[i + 1]
            skip.update((i, i + 1))
            i += 1
        elif a.startswith('--gender='):
            gender = a.split('=', 1)[1]
            skip.add(i)
        i += 1

    pos = [argv[i] for i in range(1, len(argv))
           if i not in skip and not argv[i].startswith('--')]
    dt = None
    if pos:
        text = ' '.join(pos)
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        if dt is None:
            raise ValueError(f'日期时间无法解析: "{text}"，应为 YYYY-MM-DD HH:MM')
    if gender is not None and gender not in ('m', 'f'):
        raise ValueError('--gender 只能是 m 或 f')
    return test, dt, gender, question


# ──────────────────────────── 回归测试 ────────────────────────────
# 六局×三十日紫微位置速查表（出处：9zi.ai 手工排盘八步与速查表·紫微星位置表，
# https://9zi.ai/tw/guide/manual-chart-calculation/ ；与《全书》卷二六局日位图同源）
GOLD_ZIWEI = {
    2: '丑寅寅卯卯辰辰巳巳午午未未申申酉酉戌戌亥亥子子丑丑寅寅卯卯辰',
    3: '辰丑寅巳寅卯午卯辰未辰巳申巳午酉午未戌未申亥申酉子酉戌丑戌亥',
    4: '亥辰丑寅子巳寅卯丑午卯辰寅未辰巳卯申巳午辰酉午未巳戌未申午亥',
    5: '午亥辰丑寅未子巳寅卯申丑午卯辰酉寅未辰巳戌卯申巳午亥辰酉午未',
    6: '酉午亥辰丑寅戌未子巳寅卯亥申丑午卯辰子酉寅未辰巳丑戌卯申巳午',
}
# 命宫速查表（9zi，行=农历月，格=子时..亥时）；身宫表同源，腊月行原站有误故只核 1~11 月
GOLD_SOUl = {
    1: '寅丑子亥戌酉申未午巳辰卯', 2: '卯寅丑子亥戌酉申未午巳辰',
    3: '辰卯寅丑子亥戌酉申未午巳', 4: '巳辰卯寅丑子亥戌酉申未午',
    5: '午巳辰卯寅丑子亥戌酉申未', 6: '未午巳辰卯寅丑子亥戌酉申',
    7: '申未午巳辰卯寅丑子亥戌酉', 8: '酉申未午巳辰卯寅丑子亥戌',
    9: '戌酉申未午巳辰卯寅丑子亥', 10: '亥戌酉申未午巳辰卯寅丑子',
    11: '子亥戌酉申未午巳辰卯寅丑', 12: '丑子亥戌酉申未午巳辰卯寅',
}
GOLD_BODY = {
    1: '寅卯辰巳午未申酉戌亥子丑', 2: '卯辰巳午未申酉戌亥子丑寅',
    3: '辰巳午未申酉戌亥子丑寅卯', 4: '巳午未申酉戌亥子丑寅卯辰',
    5: '午未申酉戌亥子丑寅卯辰巳', 6: '未申酉戌亥子丑寅卯辰巳午',
    7: '申酉戌亥子丑寅卯辰巳午未', 8: '酉戌亥子丑寅卯辰巳午未申',
    9: '戌亥子丑寅卯辰巳午未申酉', 10: '亥子丑寅卯辰巳午未申酉戌',
    11: '子丑寅卯辰巳午未申酉戌亥',
}
# 辅星对照表（出处：starqode 安星规则对照表 / knowyourbazi 火星页）
GOLD_LUCUN = dict(zip(TG, [2, 3, 5, 6, 5, 6, 8, 9, 11, 0]))          # 禄存子基索引
GOLD_KUIYUE = {'甲': (1, 7), '乙': (0, 8), '丙': (11, 9), '丁': (11, 9), '戊': (1, 7),
               '己': (0, 8), '庚': (1, 7), '辛': (6, 2), '壬': (3, 5), '癸': (3, 5)}
GOLD_ZUOYOU = {1: (4, 8), 2: (5, 7), 3: (6, 6), 4: (7, 5), 5: (8, 4), 6: (9, 3),
               7: (10, 2), 8: (11, 1), 9: (0, 0), 10: (1, 11), 11: (2, 10), 12: (3, 9)}
GOLD_CHANGQU = {0: (10, 4), 1: (9, 5), 2: (8, 6), 3: (7, 7), 4: (6, 8), 5: (5, 9),
                6: (4, 10), 7: (3, 11), 8: (2, 0), 9: (1, 1), 10: (0, 2), 11: (11, 3)}
GOLD_HUOLING = {'寅': (1, 3), '午': (1, 3), '戌': (1, 3), '申': (2, 10), '子': (2, 10),
                '辰': (2, 10), '巳': (3, 10), '酉': (3, 10), '丑': (3, 10),
                '亥': (9, 10), '卯': (9, 10), '未': (9, 10)}
# 五虎遁全表（9zi 手工排盘第三步，按寅→丑十二宫）
GOLD_TIGER = {'甲': '丙丁戊己庚辛壬癸甲乙丙丁', '己': '丙丁戊己庚辛壬癸甲乙丙丁',
              '乙': '戊己庚辛壬癸甲乙丙丁戊己', '庚': '戊己庚辛壬癸甲乙丙丁戊己',
              '丙': '庚辛壬癸甲乙丙丁戊己庚辛', '辛': '庚辛壬癸甲乙丙丁戊己庚辛',
              '丁': '壬癸甲乙丙丁戊己庚辛壬癸', '壬': '壬癸甲乙丙丁戊己庚辛壬癸',
              '戊': '甲乙丙丁戊己庚辛壬癸甲乙', '癸': '甲乙丙丁戊己庚辛壬癸甲乙'}


def test():
    fails = []
    count = 0

    def eq(label, got, want):
        nonlocal count
        count += 1
        ok = got == want
        print(f"{'✓' if ok else '✗'} {label}: {got!r}" + ("" if ok else f" ≠ {want!r}"))
        if not ok:
            fails.append(label)

    # ── 锚点1：9zi.ai 完整示例 1990-05-15 07:30 北京女（当年夏令时，真太阳时 06:20 属卯时，
    #    本脚本不做真太阳时校正，取等效卯时 06:00 排盘）
    #    出处 https://9zi.ai/tw/guide/manual-chart-calculation/ ──
    c1 = chart(datetime(1990, 5, 15, 6, 0), 'f')
    eq('锚点1 农历', c1['农历'], '庚午年四月廿一日')
    eq('锚点1 时辰', c1['时辰'], '卯时')
    eq('锚点1 四柱', c1['四柱'], {'年柱': '庚午', '月柱': '辛巳', '日柱': '庚辰', '时柱': '己卯'})
    eq('锚点1 命宫干支', c1['命宫'], {'地支': '寅', '干支': '戊寅'})
    eq('锚点1 身宫', c1['身宫']['地支'], '申')
    eq('锚点1 五行局', c1['五行局'], '土五局')
    eq('锚点1 紫微在', c1['紫微在'], '戌')
    want_stars = {'紫微': '戌', '天机': '酉', '太阳': '未', '武曲': '午', '天同': '巳',
                  '廉贞': '寅', '天府': '午', '太阴': '未', '贪狼': '申', '巨门': '酉',
                  '天相': '戌', '天梁': '亥', '七杀': '子', '破军': '辰'}
    got_stars = {}
    for p in c1['十二宫']:
        for s in p['主星']:
            got_stars[s] = p['地支']
    eq('锚点1 十四主星落宫', got_stars, want_stars)
    eq('锚点1 生年四化', {k: v['星'] for k, v in c1['生年四化'].items()},
       {'化禄': '太阳', '化权': '武曲', '化科': '太阴', '化忌': '天同'})
    eq('锚点1 命主身主', (c1['命主'], c1['身主']), ('禄存', '火星'))
    eq('锚点1 大限方向', c1['大限']['方向'], '逆行')          # 庚=阳干 × 女 → 阳女逆行
    eq('锚点1 大限起运岁', c1['大限']['起运岁'], 5)
    p1 = {p['宫']: p for p in c1['十二宫']}
    eq('锚点1 命宫大限', p1['命宫']['大限'], [5, 14])
    eq('锚点1 兄弟宫大限', p1['兄弟']['大限'], [15, 24])
    eq('锚点1 夫妻宫大限', p1['夫妻']['大限'], [25, 34])

    # ── 锚点2：iztro 测试用例 byLunar(2000-7-17, 寅时, 女)
    #    出处 https://github.com/SylarLong/iztro/blob/main/src/__tests__/astro/astro.test.ts ──
    c2 = chart(datetime(2000, 8, 16, 4, 0), 'f')
    eq('锚点2 农历', c2['农历'], '庚辰年七月十七日')
    eq('锚点2 四柱', c2['四柱'], {'年柱': '庚辰', '月柱': '甲申', '日柱': '丙午', '时柱': '庚寅'})
    eq('锚点2 命宫', c2['命宫']['地支'], '午')
    eq('锚点2 身宫', c2['身宫']['地支'], '戌')
    eq('锚点2 五行局', c2['五行局'], '木三局')
    eq('锚点2 命主身主', (c2['命主'], c2['身主']), ('破军', '文昌'))
    eq('锚点2 大限方向', c2['大限']['方向'], '逆行')
    p2 = {p['地支']: p for p in c2['十二宫']}
    eq('锚点2 寅宫大限[43,52]', p2['寅']['大限'], [43, 52])   # iztro 断言 palaces[0]
    eq('锚点2 丑宫大限[53,62]', p2['丑']['大限'], [53, 62])   # iztro 断言 palaces[11]

    # ── 锚点3：iztro 测试用例 bySolar(2023-4-10, 辰时, 女, fixLeap=true)——闰月口径
    #    出处同上；iztro 断言：命宫子/身宫申/金四局/紫微在迁移宫(=午)/命主贪狼/身主天同 ──
    c3 = chart(datetime(2023, 4, 10, 8, 0), 'f')
    eq('锚点3 农历', c3['农历'], '癸卯年闰二月二十日')
    eq('锚点3 排盘月(后半月归三月)', c3['排盘月'], 3)
    eq('锚点3 命宫', c3['命宫']['地支'], '子')
    eq('锚点3 身宫', c3['身宫']['地支'], '申')
    eq('锚点3 五行局', c3['五行局'], '金四局')
    eq('锚点3 紫微在(迁移宫=午)', c3['紫微在'], '午')
    eq('锚点3 命主身主', (c3['命主'], c3['身主']), ('贪狼', '天同'))

    # ── 紫微星：6 局 × 30 日全量速查表 + 每局 12 宫全覆盖 ──
    for ju, gold in GOLD_ZIWEI.items():
        got = ''.join(DZ[ziwei_index(ju, day)] for day in range(1, 31))
        eq(f'紫微表 {JU_NAME[ju]} 30日', got, gold)
        cov = {ziwei_index(ju, day) for day in range(1, 31)}
        eq(f'紫微表 {JU_NAME[ju]} 12宫覆盖', len(cov), 12)
    # iztro 安星诀三个算例：木三27→戌、火六13→亥、土五6→未
    eq('紫微算例 木三27日', DZ[ziwei_index(3, 27)], '戌')
    eq('紫微算例 火六13日', DZ[ziwei_index(6, 13)], '亥')
    eq('紫微算例 土五6日', DZ[ziwei_index(5, 6)], '未')

    # ── 十四主星：每盘 14 颗齐全、不重 ──
    for yr in (1984, 1996, 2008, 2026):
        for mo in (1, 4, 7, 11):
            for dy in (3, 17, 28):
                c = chart(datetime(yr, mo, dy, 9, 0), 'm')
                allstars = [s for p in c['十二宫'] for s in p['主星']]
                eq(f'主星齐全不重 {yr}-{mo:02d}-{dy:02d}',
                   (len(allstars), sorted(allstars) == sorted(MAJOR)), (14, True))

    # ── 四化表：10 天干 × 4 全、每干四星不重、全书原文值 ──
    eq('四化表覆盖10干', sorted(SIHUA.keys()), sorted(TG))
    for g, want in SIHUA.items():
        eq(f'四化 {g}干4星', (len(want), len(set(want))), (4, 4))
    eq('四化 甲', SIHUA['甲'], ['廉贞', '破军', '武曲', '太阳'])
    eq('四化 庚', SIHUA['庚'], ['太阳', '武曲', '太阴', '天同'])
    eq('四化 壬(全书原文梁紫府武)', SIHUA['壬'], ['天梁', '紫微', '天府', '武曲'])
    eq('四化 癸', SIHUA['癸'], ['破军', '巨门', '太阴', '贪狼'])
    eq('四化明星覆盖', sorted({s for v in SIHUA.values() for s in v}),
       sorted(['廉贞', '破军', '武曲', '太阳', '天机', '天梁', '紫微', '太阴',
               '天同', '文昌', '巨门', '贪狼', '右弼', '文曲', '天府']))

    # ── 命宫起法：12 月 × 12 时 全 144 格（9zi 速查表）＋身宫 1~11 月 ──
    for m in range(1, 13):
        got = ''.join(DZ[soul_body(m, h)[0]] for h in range(12))
        eq(f'命宫速查表 {m}月', got, GOLD_SOUl[m])
        if m in GOLD_BODY:
            gotb = ''.join(DZ[soul_body(m, h)[1]] for h in range(12))
            eq(f'身宫速查表 {m}月', gotb, GOLD_BODY[m])
    # 身宫腊月（原站该行有误，按安身命例公式核）：生月宫丑起子时顺数
    eq('身宫速查表 12月(公式)', ''.join(DZ[soul_body(12, h)[1]] for h in range(12)),
       '丑寅卯辰巳午未申酉戌亥子')

    # ── 十二宫干支与四柱一致性 ──
    samples = [(datetime(1990, 5, 15, 6, 0), 'f'), (datetime(2000, 8, 16, 4, 0), 'f'),
               (datetime(2026, 11, 18, 21, 0), 'm'), (datetime(1984, 2, 1, 0, 0), 'm')]
    for dt, gd in samples:
        c = chart(dt, gd)
        ly, lm, ld, leap = lunar_of(dt.date())
        use_m = c['排盘月']
        yg = year_ganzhi(ly)
        # 年柱=农历年干支、月柱=五虎遁农历月、时柱=五鼠遁日干
        eq(f'四柱年 {dt.date()}', c['四柱']['年柱'], yg)
        eq(f'四柱月 {dt.date()}', c['四柱']['月柱'], month_ganzhi(yg[0], use_m))
        eq(f'四柱时 {dt.date()}', c['四柱']['时柱'],
           hour_ganzhi(c['四柱']['日柱'][0], shichen_idx(dt.hour)))
        # 十二宫干支全部符合五虎遁
        bad = [p['干支'] for p in c['十二宫']
               if p['干支'] != palace_stem(yg[0], DZ.index(p['地支'])) + p['地支']]
        eq(f'十二宫干支五虎遁 {dt.date()}', bad, [])
        # 命宫干支与独立五虎遁推算一致
        eq(f'命宫干支 {dt.date()}', c['命宫']['干支'],
           palace_stem(yg[0], DZ.index(c['命宫']['地支'])) + c['命宫']['地支'])
        # 命宫干支纳音 = 五行局；且与干支取数捷诀一致
        eq(f'纳音定局 {dt.date()}', wuxing_ju(c['命宫']['干支']), ju_by_numbers(*c['命宫']['干支']))
        eq(f'五行局名 {dt.date()}', c['五行局'], JU_NAME[wuxing_ju(c['命宫']['干支'])])
        # 宫名布列：兄弟=命逆行一格、父母=顺行一格
        eq(f'十二宫逆布 {dt.date()}',
           (c['十二宫'][1]['地支'], c['十二宫'][11]['地支']),
           (DZ[(DZ.index(c['命宫']['地支']) - 1) % 12], DZ[(DZ.index(c['命宫']['地支']) + 1) % 12]))

    # ── 五行局：纳音法与干支取数捷诀 60 组全等 ──
    eq('纳音≡取数捷诀 60干支',
       [wuxing_ju(g) for g in GZ], [ju_by_numbers(g[0], g[1]) for g in GZ])

    # ── 五虎遁宫干全表（10 年干 × 12 宫，防 mod12/mod10 负索引回归）──
    for g, want in GOLD_TIGER.items():
        got = ''.join(palace_stem(g, (2 + k) % 12) for k in range(12))
        eq(f'五虎遁 {g}年', got, want)

    # ── 辅星对照表全量核对 ──
    for g in TG:
        m = minor_stars(g, '子', 1, 0)
        eq(f'禄存 {g}年', m['禄存'], GOLD_LUCUN[g])
        eq(f'擎羊陀罗 {g}年', (m['擎羊'], m['陀罗']),
           ((GOLD_LUCUN[g] + 1) % 12, (GOLD_LUCUN[g] - 1) % 12))
        eq(f'魁钺 {g}年', (m['天魁'], m['天钺']), GOLD_KUIYUE[g])
    for mo in range(1, 13):
        m = minor_stars('甲', '子', mo, 0)
        eq(f'左辅右弼 {mo}月', (m['左辅'], m['右弼']), GOLD_ZUOYOU[mo])
    for h in range(12):
        m = minor_stars('甲', '子', 1, h)
        eq(f'文昌文曲 {DZ[h]}时', (m['文昌'], m['文曲']), GOLD_CHANGQU[h])
    for z in DZ:
        m = minor_stars('甲', z, 1, 0)
        eq(f'火星铃星 {z}年', (m['火星'], m['铃星']), GOLD_HUOLING[z])
    # iztro 火铃算例：壬辰年卯时 → 火在巳、铃在丑
    eq('火铃算例 壬辰年卯时', (minor_stars('壬', '辰', 1, 3)['火星'],
                                minor_stars('壬', '辰', 1, 3)['铃星']), (5, 1))

    # ── 大限方向：阳男阴女顺、阴男阳女逆；顺行第二限落父母宫、逆行第二限落兄弟宫
    #    （全书「安大限诀：阳男阴女从命前一宫起顺行是父母宫，阴男阳女从命后一宫起
    #    逆行是兄弟宫」）──
    for gan, gd, want_dir, want_2nd in [('庚', 'm', '顺行', '父母'), ('庚', 'f', '逆行', '兄弟'),
                                         ('乙', 'm', '逆行', '兄弟'), ('乙', 'f', '顺行', '父母')]:
        d = decadals(0, 3, gan, gd)                    # 命宫设在子，第二限即命±1
        second_branch = 1 if d['方向'] == '顺行' else 11   # 子±1 的地支索引
        second = PALACES[(0 - second_branch) % 12]
        eq(f'大限 {gan}年{"男" if gd == "m" else "女"}',
           (d['方向'], second), (want_dir, want_2nd))
        eq(f'大限序列单调 {gan}{gd}',
           [r for _, r in d['序列']][:3], [[3, 12], [13, 22], [23, 32]])
    eq('大限无性别', decadals(0, 3, '甲', None), None)

    # ── CLI：--question 的值绝不能被当成日期解析 ──
    t, dt, gd, q = parse_cli(['ziwei.py', '1990-05-15 06:00', '--gender', 'f',
                              '--question', '1990-05-15 06:00 能不能成'])
    eq('CLI 日期解析', dt, datetime(1990, 5, 15, 6, 0))
    eq('CLI 问题透传', q, '1990-05-15 06:00 能不能成')
    eq('CLI 性别', gd, 'f')
    t2, dt2, _, q2 = parse_cli(['ziwei.py', '2026-11-18', '21:30', '--question=问事业'])
    eq('CLI 两段位置参数', dt2, datetime(2026, 11, 18, 21, 30))
    eq('CLI --question= 语法', q2, '问事业')
    eq('CLI --test 标志', parse_cli(['ziwei.py', '--test'])[0], True)
    bad = 0
    try:
        parse_cli(['ziwei.py', '--question', '不是日期哦', '乱写的时间'])
    except ValueError:
        bad = 1
    eq('CLI 非法日期报错', bad, 1)

    # ── 时辰细分：新增字段区分早/晚子时（timeIndex 0=早子时、12=晚子时；
    #    原 "时辰" 字段值保持不变）──
    c_early = chart(datetime(2026, 11, 19, 0, 30), 'm')
    c_late = chart(datetime(2026, 11, 19, 23, 30), 'm')
    c_mao = chart(datetime(2026, 11, 19, 6, 0), 'm')
    eq('时辰细分 早子时(00:30)且原时辰不变', (c_early['时辰'], c_early['时辰细分']),
       ('子时', '早子时'))
    eq('时辰细分 晚子时(23:30)且原时辰不变', (c_late['时辰'], c_late['时辰细分']),
       ('子时', '晚子时'))
    eq('时辰细分 非子时沿用时辰标签(06:00)', (c_mao['时辰'], c_mao['时辰细分']),
       ('卯时', '卯时'))

    print(f"\n共 {count} 条断言")
    print("全部通过 ✅" if not fails else f"失败 {len(fails)} 项 ❌: {fails}")
    return 0 if not fails else 1


if __name__ == '__main__':
    try:
        is_test, dt, gender, question = parse_cli(sys.argv)
    except ValueError as e:
        print(e)
        print(__doc__)
        sys.exit(1)
    if is_test:
        sys.exit(test())
    if dt is None:
        print(__doc__)
        sys.exit(1)
    out = chart(dt, gender)
    if question:
        out['问题'] = question
    print(json.dumps(out, ensure_ascii=False, indent=2))
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'ziwei', 'ts': datetime.now().isoformat(),
                                'result': out}, ensure_ascii=False) + '\n')
    except Exception:
        pass
