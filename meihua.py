#!/usr/bin/env python3
"""meihua.py — 梅花易数起卦引擎（2026-10-08 占卜系统修复工程创建）
时方起卦（年支数+农历月+农历日+时支数），本卦/动爻/变卦全代码计算，禁心算。
翻爻算法为 2026-10-07 事故修复版（旧版反转数组索引错位，变卦全错）。

用法:
  python3 meihua.py                          # 当前时间起卦
  python3 meihua.py 2026-10-07 18:55         # 指定时间起卦
  python3 meihua.py --question "问姻缘"       # 带问题存档
  python3 meihua.py --test                   # 回归测试（黄金锚点）
输出 JSON（含卦辞/爻辞/变卦）。自动存档 divination_log.jsonl。
"""
import os
import sys, json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bazi import TG, DZ, GZ, day_ganzhi, year_ganzhi, shichen_idx  # 复用已验证公式

try:
    from gua_data import GUA
except Exception:
    GUA = {}

# 名称表：(上卦数, 下卦数) → 卦名（八卦数 乾1兑2离3震4巽5坎6艮7坤8）
NAMES = {
 (1,1):'乾为天',(1,2):'天泽履',(1,3):'天火同人',(1,4):'天雷无妄',(1,5):'天风姤',(1,6):'天水讼',(1,7):'天山遁',(1,8):'天地否',
 (2,1):'泽天夬',(2,2):'兑为泽',(2,3):'泽火革',(2,4):'泽雷随',(2,5):'泽风大过',(2,6):'泽水困',(2,7):'泽山咸',(2,8):'泽地萃',
 (3,1):'火天大有',(3,2):'火泽睽',(3,3):'离为火',(3,4):'火雷噬嗑',(3,5):'火风鼎',(3,6):'火水未济',(3,7):'火山旅',(3,8):'火地晋',
 (4,1):'雷天大壮',(4,2):'雷泽归妹',(4,3):'雷火丰',(4,4):'震为雷',(4,5):'雷风恒',(4,6):'雷水解',(4,7):'雷山小过',(4,8):'雷地豫',
 (5,1):'风天小畜',(5,2):'风泽中孚',(5,3):'风火家人',(5,4):'风雷益',(5,5):'巽为风',(5,6):'风水涣',(5,7):'风山渐',(5,8):'风地观',
 (6,1):'水天需',(6,2):'水泽节',(6,3):'水火既济',(6,4):'水雷屯',(6,5):'水风井',(6,6):'坎为水',(6,7):'水山蹇',(6,8):'水地比',
 (7,1):'山天大畜',(7,2):'山泽损',(7,3):'山火贲',(7,4):'山雷颐',(7,5):'山风蛊',(7,6):'山水蒙',(7,7):'艮为山',(7,8):'山地剥',
 (8,1):'地天泰',(8,2):'地泽临',(8,3):'地火明夷',(8,4):'地雷复',(8,5):'地风升',(8,6):'地水师',(8,7):'地山谦',(8,8):'坤为地',
}
# 爻位名（第1爻→初九/初六 视阴阳，输出统一用爻序名）
YAO_NAMES = ['初','二','三','四','五','上']

# 6爻阴阳：字符序 = (下,中,上)，即 '100' = 初阳二阴三阴
BITS = {1:'111',2:'110',3:'101',4:'100',5:'011',6:'010',7:'001',8:'000'}
INV_BITS = {v: k for k, v in BITS.items()}

def single_name(full_name: str) -> str:
    """'泽雷随'→'随'，'乾为天'→'乾'，'风泽中孚'→'中孚'"""
    if '为' in full_name:
        return full_name[0]
    return full_name[2:]

def lunar_ymd(dt):
    """农历年月日：优先 sxtwl（寿星天文历，三方对照胜出），回退 lunardate。
    lunardate 个别年份有1日误差（如1978-09实测比真值大1）。闰月按本月经计。"""
    try:
        import sxtwl
        x = sxtwl.fromSolar(dt.year, dt.month, dt.day)
        return x.getLunarYear(), abs(x.getLunarMonth()), x.getLunarDay()
    except Exception:
        from lunardate import LunarDate
        ld = LunarDate.fromSolarDate(dt.year, dt.month, dt.day)
        return ld.year, ld.month, ld.day

def hu_gua(upper, lower, b_upper, b_lower):
    """互卦（原书·互卦起例）：重卦去初爻与上爻，中间四爻分作两卦。
    上互=爻三四五，下互=爻二三四。乾坤无互，互其变卦。"""
    if NAMES[(upper, lower)] in ('乾为天', '坤为地'):
        yao = BITS[b_lower] + BITS[b_upper]        # 乾坤无互→取变卦之互
    else:
        yao = BITS[lower] + BITS[upper]
    return NAMES[(INV_BITS[yao[2:5]], INV_BITS[yao[1:4]])]

def _assemble(upper, lower, moving, extra=None):
    """（上卦数, 下卦数, 动爻）→ 完整卦象：本卦/互卦/动爻/变卦 + 卦辞爻辞"""
    yao = list(BITS[lower] + BITS[upper])          # [初,二,三,四,五,上]
    yao[moving - 1] = '0' if yao[moving - 1] == '1' else '1'
    b_upper, b_lower = INV_BITS[''.join(yao[3:])], INV_BITS[''.join(yao[:3])]
    name, b_name = NAMES[(upper, lower)], NAMES[(b_upper, b_lower)]
    g_ci, b_ci = GUA.get(single_name(name), {}), GUA.get(single_name(b_name), {})
    out = dict(extra or {})
    out.update({
        '本卦': name,
        '本卦卦辞': g_ci.get('gua_ci', '（卦辞数据未加载）'),
        '互卦': hu_gua(upper, lower, b_upper, b_lower),
        '动爻': moving,
        '动爻爻辞': (g_ci.get('yao_ci') or [''] * 6)[moving - 1] or '（爻辞数据未加载）',
        '变卦': b_name,
        '变卦卦辞': b_ci.get('gua_ci', '（卦辞数据未加载）'),
    })
    return out

def numbers_qigua(u_num, l_num=None, h_num=0, mode='端法'):
    """非时方起卦（原书·物数占/声音占/端法方位占）
    mode='端法'：上卦=物数%8，下卦=方位(或后声)%8，动爻=(物+方+时)%6。观梅类"人物方位占"用此。
    mode='一数'：上卦=数%8，下卦=(数+时)%8，动爻=(数+时)%6。
    整除取坤(8)/上爻(6)，同原书"卦以八除、爻以六除"。
    """
    if mode == '一数':
        total = u_num + h_num
        upper, lower, moving = u_num % 8 or 8, total % 8 or 8, total % 6 or 6
    else:
        upper, lower = u_num % 8 or 8, l_num % 8 or 8
        moving = (u_num + l_num + h_num) % 6 or 6
    return _assemble(upper, lower, moving, extra={
        '起卦参数': {'上卦数': u_num, '下卦数': l_num, '时支数': h_num, 'mode': mode}})

def qigua(dt: datetime) -> dict:
    """时方起卦。返回完整卦象信息。"""
    ly, lm, lday = lunar_ymd(dt)
    yb = ((ly - 4) % 12) + 1                   # 农历年支数 子=1…亥=12（古法用农历年；曾误用公历年，1-2月生日全错）
    hidx = shichen_idx(dt.hour)
    hb = hidx + 1
    upper = (yb + lm + lday) % 8 or 8
    lower = (yb + lm + lday + hb) % 8 or 8
    moving = (yb + lm + lday + hb) % 6 or 6

    return _assemble(upper, lower, moving, extra={
        '起卦时间': dt.isoformat(sep=' ', timespec='minutes'),
        '公历日干支': day_ganzhi(dt.date()),
        '时辰': DZ[hidx],
        '农历': f"{ly}年{lm}月{lday}日",
        '起卦参数': {'年支数': yb, '农历月': lm, '农历日': lday, '时支数': hb},
    })

# ──────────────────────────── 回归测试 ────────────────────────────
def test():
    fails = []
    def eq(label, got, want):
        ok = got == want
        print(f"{'✓' if ok else '✗'} {label}: {got!r}" + ("" if ok else f" ≠ {want!r}"))
        if not ok: fails.append(label)

    r = qigua(datetime(2026, 10, 7, 18, 55))
    eq("2026-10-07 18:55 本卦", r['本卦'], '泽雷随')
    eq("2026-10-07 18:55 动爻", r['动爻'], 4)
    eq("2026-10-07 18:55 变卦", r['变卦'], '水雷屯')   # 旧版bug=泽火革
    eq("2026-10-07 时辰", r['时辰'], '酉')
    eq("2026-10-07 农历", r['农历'], '2026年8月27日')

    r2 = qigua(datetime(2026, 10, 8, 10, 9))
    eq("2026-10-08 10:09 本卦", r2['本卦'], '火天大有')
    eq("2026-10-08 10:09 动爻", r2['动爻'], 1)
    eq("2026-10-08 10:09 变卦", r2['变卦'], '火风鼎')

    # 翻爻算法直接回归（泽雷随䷐ 九四动 → 水雷屯）
    yao = list(BITS[4] + BITS[2])
    yao[3] = '0' if yao[3] == '1' else '1'
    eq("随九四翻爻→变卦", NAMES[(INV_BITS[''.join(yao[3:])], INV_BITS[''.join(yao[:3])])], '水雷屯')
    # 农历年支/农历日（2026-10-08修复：曾误用公历年支；农历源换sxtwl）
    r = qigua(datetime(2024, 2, 5, 7, 45))
    eq("2024-02-05年支数(农历癸卯)", r['起卦参数']['年支数'], 4)
    eq("2024-02-05 07:45本卦", r['本卦'], '泽山咸')
    eq("2024-02-05 07:45动爻", r['动爻'], 5)
    r2 = qigua(datetime(1978, 9, 10, 0, 4))
    eq("1978-09-10农历日(sxtwl)", r2['起卦参数']['农历日'], 8)
    eq("1978-09-10 00:04本卦", r2['本卦'], '山地剥')
    eq("1978-09-10 00:04动爻", r2['动爻'], 6)
    # ── 《梅花易数》原书真实卦例（2026-10-08 真案迭代）──
    # 观梅占：辰年十二月十七日申时 → 泽火革初爻动，变泽山咸，互见乾巽
    rw = qigua(datetime(2013, 1, 28, 16, 0))          # 农历2012(壬辰)年12月17日申时
    eq("观梅占 本卦", rw['本卦'], '泽火革')
    eq("观梅占 动爻", rw['动爻'], 1)
    eq("观梅占 变卦", rw['变卦'], '泽山咸')
    eq("观梅占 互卦", rw['互卦'], '天风姤')
    # 扣门借物占：一声(乾)+五声(巽)酉时 → 天风姤四爻动，变巽为风，互卦重乾
    rb = numbers_qigua(1, 5, 10)
    eq("借物占 本卦", rb['本卦'], '天风姤')
    eq("借物占 动爻", rb['动爻'], 4)
    eq("借物占 变卦", rb['变卦'], '巽为风')
    eq("借物占 互卦", rb['互卦'], '乾为天')
    # 少年有喜色占：艮7(少年)+离3(离方)午时 → 山火贲五爻动，变风火家人，互卦震坎
    rs = numbers_qigua(7, 3, 7)
    eq("少年占 本卦", rs['本卦'], '山火贲')
    eq("少年占 动爻", rs['动爻'], 5)
    eq("少年占 变卦", rs['变卦'], '风火家人')
    eq("少年占 互卦", rs['互卦'], '雷水解')
    # 牡丹占：巳年三月十六日卯时 → 天风姤五爻动，变火风鼎（原书"得姤兆，为马所践"）
    rm = qigua(datetime(2013, 4, 25, 6, 0))           # 农历2013(癸巳)年3月16日卯时
    eq("牡丹占 本卦", rm['本卦'], '天风姤')
    eq("牡丹占 动爻", rm['动爻'], 5)
    eq("牡丹占 变卦", rm['变卦'], '火风鼎')
    eq("牡丹占 互卦", rm['互卦'], '乾为天')
    # 老人有忧色占：乾1(老人)+巽5(巽方)卯时4 → 天风姤九四（原书"天风姤之九四"）
    ro = numbers_qigua(1, 5, 4)
    eq("老人占 本卦", ro['本卦'], '天风姤')
    eq("老人占 动爻", ro['动爻'], 4)
    eq("老人占 变卦", ro['变卦'], '巽为风')
    eq("老人占 互卦", ro['互卦'], '乾为天')
    # 壬申年四月十一日巳时（曲辛梓例）→ 地水师六爻动
    rq = qigua(datetime(1992, 5, 13, 10, 0))          # 农历1992(壬申)年4月11日巳时
    eq("壬申例 本卦", rq['本卦'], '地水师')
    eq("壬申例 动爻", rq['动爻'], 6)
    # ── 《梅花易数》卷二·后天物卦/字画卦例（2026-10-08 真案迭代第二批）──
    # 牛哀鸣占：坤8(牛)+坎6(坎方)午时7 → 地水师三爻动，变地风升，互见坤震
    rn = numbers_qigua(8, 6, 7)
    eq("牛哀鸣占 本卦", rn['本卦'], '地水师')
    eq("牛哀鸣占 动爻", rn['动爻'], 3)
    eq("牛哀鸣占 变卦", rn['变卦'], '地风升')
    eq("牛哀鸣占 互卦", rn['互卦'], '地雷复')
    # 鸡悲鸣占：巽5(鸡)+乾1(乾方)卯时4 → 风天小畜四爻动，变乾，互见离兑
    rj = numbers_qigua(5, 1, 4)
    eq("鸡悲鸣占 本卦", rj['本卦'], '风天小畜')
    eq("鸡悲鸣占 动爻", rj['动爻'], 4)
    eq("鸡悲鸣占 变卦", rj['变卦'], '乾为天')
    eq("鸡悲鸣占 互卦", rj['互卦'], '火泽睽')
    # 枯枝坠地占：离3(枯木)+兑2(兑方)辰时5 → 火泽睽四爻动，变山泽损，互见坎离
    rk = numbers_qigua(3, 2, 5)
    eq("枯枝坠地占 本卦", rk['本卦'], '火泽睽')
    eq("枯枝坠地占 动爻", rk['动爻'], 4)
    eq("枯枝坠地占 变卦", rk['变卦'], '山泽损')
    eq("枯枝坠地占 互卦", rk['互卦'], '水火既济')
    # 西林寺牌额占（字画占）：西7画(艮)+林8画(坤) → 山地剥三爻动，变艮，互见重坤
    rx = numbers_qigua(7, 8, 0)
    eq("西林寺占 本卦", rx['本卦'], '山地剥')
    eq("西林寺占 动爻", rx['动爻'], 3)
    eq("西林寺占 变卦", rx['变卦'], '艮为山')
    eq("西林寺占 互卦", rx['互卦'], '坤为地')
    # 今日动静如何（字占声调数）：8(坤)+5(巽) → 地风升初爻动，变泰，互见震兑
    rd = numbers_qigua(8, 5, 0)
    eq("今日动静 本卦", rd['本卦'], '地风升')
    eq("今日动静 动爻", rd['动爻'], 1)
    eq("今日动静 变卦", rd['变卦'], '地天泰')
    eq("今日动静 互卦", rd['互卦'], '雷泽归妹')

    print("\n" + ("全部通过 ✅" if not fails else f"失败 {len(fails)} 项 ❌: {fails}"))
    return 0 if not fails else 1

if __name__ == '__main__':
    if '--test' in sys.argv:
        sys.exit(test())
    question = None
    skip = set()
    if '--question' in sys.argv:
        qi = sys.argv.index('--question')
        if qi + 1 < len(sys.argv):
            question = sys.argv[qi + 1]
            skip.add(qi + 1)
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith('--') and i not in skip]
    if len(args) >= 2:
        try:
            dt = datetime.strptime(args[0] + ' ' + args[1], '%Y-%m-%d %H:%M')
        except ValueError:
            print(f"时间格式无法解析: '{args[0]} {args[1]}'，应为 YYYY-MM-DD HH:MM"); sys.exit(1)
    elif len(args) == 1:
        try:
            dt = datetime.strptime(args[0], '%Y-%m-%d')
            print("注意：只给了日期未给时间，按 00:00 子时起卦", file=sys.stderr)
        except ValueError:
            print(f"日期格式无法解析: '{args[0]}'，应为 YYYY-MM-DD"); sys.exit(1)
    else:
        dt = datetime.now()
    out = qigua(dt)
    if question:
        out['问题'] = question
    print(json.dumps(out, ensure_ascii=False, indent=2))
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl'), 'a') as f:
            f.write(json.dumps({'type': 'meihua', 'ts': datetime.now().isoformat(), 'result': out},
                               ensure_ascii=False) + '\n')
    except Exception:
        pass
