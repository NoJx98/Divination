#!/usr/bin/env python3
"""bazi.py — 八字排盘引擎（2026-10-08 占卜系统修复工程创建）
干支/大运/十神/桃花/红鸾全部代码计算，禁心算。

用法:
  python3 bazi.py 2000-01-01 13              # 四柱排盘（13=小时，自动转时辰）
  python3 bazi.py 2000-01-01 13 --gender m   # 含大运/起运（m男 f女）
  python3 bazi.py --test                     # 回归测试（黄金锚点）
输出 JSON。结果自动追加存档到 divination_log.jsonl。
"""
import os
import sys, json, math
from datetime import date, datetime

TG = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
DZ = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
GZ = [TG[i % 10] + DZ[i % 12] for i in range(60)]

NAYIN = ['海中金','炉中火','大林木','路旁土','剑锋金','山头火','涧下水','城头土',
         '白蜡金','杨柳木','泉中水','屋上土','霹雳火','松柏木','长流水','砂石金',
         '山下火','平地木','壁上土','金箔金','覆灯火','天河水','大驿土','钗钏金',
         '桑柘木','大溪水','沙中土','天上火','石榴木','大海水']

WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土',
          '庚':'金','辛':'金','壬':'水','癸':'水',
          '子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
          '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
YINYANG = {g: ('阳' if i % 2 == 0 else '阴') for i, g in enumerate(TG)}
YINYANG.update({z: ('阳' if i % 2 == 0 else '阴') for i, z in enumerate(DZ)})

SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
KE   = {'木':'土','土':'水','水':'火','火':'金','金':'木'}

# 节气近似交节日（固定日期表，交节日±1天需人工复核）
JIEQI = [(1,6,'小寒'),(2,4,'立春'),(3,6,'惊蛰'),(4,5,'清明'),(5,6,'立夏'),(6,6,'芒种'),
         (7,7,'小暑'),(8,7,'立秋'),(9,8,'白露'),(10,8,'寒露'),(11,7,'立冬'),(12,7,'大雪')]

try:
    import sxtwl as _sxtwl
except Exception:
    _sxtwl = None

def _jq_hour(x):
    """sxtwl 交节时刻（北京时小时，浮点）。JD 小数部即北京时（2024立春16:26实测吻合）"""
    jd = x.getJieQiJD()
    if not jd:
        return None
    return ((jd + 0.5) % 1) * 24

def sxtwl_pillars(d: date, hour=None):
    """(年柱, 月柱) 按 sxtwl 真实天文历。
    关键：交节当天按**交节时刻**判月（Bug#17，2026-10-08真案例发现）——
    如1898-03-05惊蛰20:50，生于当日卯时的周恩来应在寅月(甲寅)，日粒度会误判为卯月(乙卯)。
    hour 传北京时间小时数可精确到时刻；不传则用日粒度。"""
    if _sxtwl is None:
        return None
    x = _sxtwl.fromSolar(d.year, d.month, d.day)
    if hour is not None and x.hasJieQi():
        th = _jq_hour(x)
        if th is not None and hour < th:
            p = date.fromordinal(d.toordinal() - 1)
            x = _sxtwl.fromSolar(p.year, p.month, p.day)
    y, m = x.getYearGZ(), x.getMonthGZ()
    return TG[y.tg] + DZ[y.dz], TG[m.tg] + DZ[m.dz]

def real_jie_days(d: date, shun: bool):
    """距上/下一个节（月柱切换日）的天数。sxtwl 不可用返回 None"""
    if _sxtwl is None:
        return None
    base = _sxtwl.fromSolar(d.year, d.month, d.day).getMonthGZ()
    step = 1 if shun else -1
    for delta in range(1, 400):
        p = date.fromordinal(d.toordinal() + step * delta)
        cur = _sxtwl.fromSolar(p.year, p.month, p.day).getMonthGZ()
        if (cur.tg, cur.dz) != (base.tg, base.dz):
            # 逆排时扫到的是旧月最后一天，节在它的次日 → 减1（2026-10-08迭代修正）
            return delta if shun else delta - 1
    return None

def shichen_idx(hour):
    """时辰索引（唯一正确公式 ((hour+1)//2)%12，2026-10-08修复版）"""
    return ((hour + 1) // 2) % 12

def day_ganzhi(d: date) -> str:
    return GZ[(d.toordinal() - date(1900, 1, 1).toordinal() + 10) % 60]

def year_ganzhi(y: int) -> str:
    return GZ[(y - 4) % 60]

def hour_ganzhi(day_gan: str, hour: int) -> str:
    """五鼠遁：甲己起甲子… 时柱GZ索引 = (6*子时天干序 + 时辰idx) % 60"""
    start_tg = {'甲':0,'己':0,'乙':2,'庚':2,'丙':4,'辛':4,'丁':6,'壬':6,'戊':8,'癸':8}[day_gan]
    return GZ[(6 * start_tg + shichen_idx(hour)) % 60]

def month_ganzhi(year_gan: str, d: date) -> str:
    """月柱：节气定月(近似) + 五虎遁。返回(干支, 月支名, 边界警告)"""
    y, m, day = d.year, d.month, d.day
    # 节→月支（节气近似交节日）
    jie_zhi = {'小寒':'丑','立春':'寅','惊蛰':'卯','清明':'辰','立夏':'巳','芒种':'午',
               '小暑':'未','立秋':'申','白露':'酉','寒露':'戌','立冬':'亥','大雪':'子'}
    cur = '子'   # 元旦~小寒前=子月(大雪节)，默认丑月曾在1月初翻车(2026-10-08 sxtwl交叉抓出)
    near = None
    for jm, jd, name in JIEQI:
        if (m, day) >= (jm, jd):
            cur = jie_zhi[name]
            near = (jm, jd, name)
    # 五虎遁：甲己丙作首…年干→正月(寅月)天干
    start = {'甲':2,'己':2,'乙':4,'庚':4,'丙':6,'辛':6,'丁':8,'壬':8,'戊':0,'癸':0}[year_gan]
    mz_idx = DZ.index(cur)
    offset = (mz_idx - DZ.index('寅')) % 12   # 距寅月几个月
    mg = TG[(start + offset) % 10]
    warn = ""
    if near and abs(day - near[1]) <= 1:
        warn = f"出生日临{near[2]}交节日(近似{near[0]}月{near[1]}日)，月柱需人工复核"
    return mg + cur, warn

def shishen(day_gan: str, other: str) -> str:
    """十神（other相对日干）"""
    dg, og = WUXING[day_gan], WUXING[other]
    same_yy = YINYANG[day_gan] == YINYANG[other]
    if og == dg:  return '劫财' if not same_yy else '比肩'
    if SHENG[dg] == og: return '伤官' if not same_yy else '食神'
    if KE[dg] == og:    return '正财' if not same_yy else '偏财'   # 异性=正财 同性=偏财
    if KE[og] == dg:    return '正官' if not same_yy else '七杀'   # 异性=正官 同性=七杀
    return '正印' if not same_yy else '偏印'                       # 异性=正印 同性=偏印

def taohua(branch: str) -> str:
    for group, hua in [('寅午戌','卯'), ('巳酉丑','午'), ('亥卯未','子'), ('申子辰','酉')]:
        if branch in group: return hua
    return ''

def hongluan(branch: str) -> str:
    """红鸾：卯上起子逆行。天喜=红鸾对冲"""
    return DZ[(3 - DZ.index(branch)) % 12]

def dayun(year_gan: str, month_gz: str, gender: str, d: date):
    """大运：阳男阴女顺排，阴男阳女逆排。起运=到下一/上一节天数÷3"""
    yang_year = YINYANG[year_gan] == '阳'
    shun = (yang_year and gender == 'm') or ((not yang_year) and gender == 'f')
    base = GZ.index(month_gz)
    step = 1 if shun else -1
    pillars = [GZ[(base + step * i) % 60] for i in range(1, 9)]
    # 起运天数：顺→到下一个节；逆→到上一个节。优先 sxtwl 真实节气
    # （近似表在交节日±1天曾翻出29天误差：2005惊蛰真在3/5而表写3/6）
    days = real_jie_days(d, shun)
    if days is None:
        y, m, day = d.year, d.month, d.day
        cand = []
        for jm, jd, name in JIEQI:
            for yy in (y, y + 1, y - 1):
                cd = date(yy, jm, jd)
                diff = (cd - d).days
                if shun and diff > 0: cand.append(diff)
                if (not shun) and diff < 0: cand.append(-diff)
        days = min(cand)
    qiyun = days / 3.0
    return {'方向': '顺排' if shun else '逆排', '起运天数': days,
            '起运岁': round(qiyun, 1), '大运': pillars}

def bazi(birth: date, hour: int, gender: str = None) -> dict:
    # 年柱/月柱：优先 sxtwl 真实节气时刻界；回退近似表（立春2/4、节±1天）
    sp = sxtwl_pillars(birth, hour)
    if sp:
        ygz, mgz = sp
        mwarn = ""
    else:
        y = birth.year - 1 if (birth.month, birth.day) < (2, 4) else birth.year
        ygz = year_ganzhi(y)
        mgz, mwarn = month_ganzhi(ygz[0], birth)
    dgz = day_ganzhi(birth)
    hgz = hour_ganzhi(dgz[0], hour)
    res = {
        '公历': birth.isoformat(), '小时': hour,
        '时辰': DZ[shichen_idx(hour)],
        '年柱': ygz, '月柱': mgz, '日柱': dgz, '时柱': hgz,
        '纳音': {p: NAYIN[GZ.index(p) // 2] for p in (ygz, mgz, dgz, hgz)},
        '日主': dgz[0], '日主五行': WUXING[dgz[0]], '日主阴阳': YINYANG[dgz[0]],
        '十神': {'年干': shishen(dgz[0], ygz[0]), '月干': shishen(dgz[0], mgz[0]),
                 '时干': shishen(dgz[0], hgz[0]), '日支': shishen(dgz[0], dgz[1])},
        '桃花': {'年支查': taohua(ygz[1]), '日支查': taohua(dgz[1])},
        '红鸾天喜': {'年支查': (hongluan(ygz[1]), DZ[(DZ.index(hongluan(ygz[1])) + 6) % 12]),
                     '日支查': (hongluan(dgz[1]), DZ[(DZ.index(hongluan(dgz[1])) + 6) % 12])},
    }
    if mwarn: res['警告'] = mwarn
    if gender:
        res['大运'] = dayun(ygz[0], mgz, gender, birth)
    return res

def flow_year_shishen(day_gan: str, years) -> dict:
    return {y: {'干支': year_ganzhi(y), '天干十神': shishen(day_gan, year_ganzhi(y)[0])} for y in years}

# ──────────────────────────── 回归测试 ────────────────────────────
def test():
    fails = []
    def eq(label, got, want):
        ok = got == want
        print(f"{'✓' if ok else '✗'} {label}: {got!r}" + ("" if ok else f" ≠ {want!r}"))
        if not ok: fails.append(label)

    # 时辰边界（修复前 hour//2 和 (hour-1)//2 都在此翻车）
    for h, want in [(0,'子'),(1,'丑'),(2,'丑'),(3,'寅'),(9,'巳'),(10,'巳'),(11,'午'),
                    (12,'午'),(13,'未'),(14,'未'),(16,'申'),(17,'酉'),(18,'酉'),(20,'戌'),(23,'子')]:
        eq(f"时辰{h}点", DZ[shichen_idx(h)], want)
    # 时柱黄金锚点
    eq("乙日未时", hour_ganzhi('乙', 13), '癸未')
    eq("甲日酉时", hour_ganzhi('甲', 18), '癸酉')
    eq("乙日丑时", hour_ganzhi('乙', 1), '丁丑')
    # 日柱锚点
    eq("2026-10-07日柱", day_ganzhi(date(2026,10,7)), '甲寅')
    eq("2000-01-01日柱", day_ganzhi(date(2000,1,1)), '戊午')
    # 年柱
    eq("2026年柱", year_ganzhi(2026), '丙午')
    # 示例八字全锚点（2000-01-01 未时，公开示例日期；四柱经 sxtwl 独立核验）
    b = bazi(date(2000,1,1), 13, 'm')
    eq("示例年柱", b['年柱'], '己卯')
    eq("示例月柱", b['月柱'], '丙子')
    eq("示例日柱", b['日柱'], '戊午')
    eq("示例时柱", b['时柱'], '己未')
    eq("大运方向", b['大运']['方向'], '逆排')          # 己=阴年，阴男逆排
    eq("起运天数", b['大运']['起运天数'], 25)           # 逆数至大雪(1999-12-07)
    eq("起运岁", b['大运']['起运岁'], 8.3)              # 25/3 ≈ 8.3岁
    eq("大运1", b['大运']['大运'][0], '乙亥')           # 逆排取前一月柱
    eq("大运2", b['大运']['大运'][1], '甲戌')
    eq("大运3", b['大运']['大运'][2], '癸酉')
    # 桃花/红鸾（卯年、午日）
    eq("年支卯桃花", b['桃花']['年支查'], '子')
    eq("日支午桃花", b['桃花']['日支查'], '卯')
    eq("年支卯红鸾", b['红鸾天喜']['年支查'][0], '子')
    eq("年支卯天喜", b['红鸾天喜']['年支查'][1], '午')
    eq("日支午红鸾", b['红鸾天喜']['日支查'][0], '酉')
    eq("日支午天喜", b['红鸾天喜']['日支查'][1], '卯')
    # 十神
    eq("戊对乙=正财", shishen('乙','戊'), '正财')
    eq("癸对乙=偏印", shishen('乙','癸'), '偏印')
    # 立春边界（月柱五虎遁的年干必须用立春修正后的年柱）
    b2 = bazi(date(1998, 1, 10), 13)
    eq("1998-01-10年柱(立春前)", b2['年柱'], '丁丑')
    eq("1998-01-10月柱(五虎遁)", b2['月柱'], '癸丑')
    eq("2026-02-03年柱(立春前)", bazi(date(2026,2,3), 13)['年柱'], '乙巳')
    eq("2026-02-05月柱(立春后)", bazi(date(2026,2,5), 13)['月柱'], '庚寅')
    # 小寒边界（元旦~小寒前=子月，sxtwl交叉校准锚点）
    b5 = bazi(date(2000, 1, 1), 13)
    eq("2000-01-01年柱", b5['年柱'], '己卯')
    eq("2000-01-01月柱(子月)", b5['月柱'], '丙子')
    b6 = bazi(date(1900, 1, 1), 13)
    eq("1900-01-01年柱", b6['年柱'], '己亥')
    eq("1900-01-01月柱(子月)", b6['月柱'], '丙子')
    # 起运节气边界（2026-10-08修复：近似表曾在交节日±1天翻出29天误差，现走sxtwl真节气）
    b7 = bazi(date(2005, 3, 6), 10, 'm')   # 乙酉阴年男=逆排，惊蛰3/5=前1天
    eq("2005-03-06逆排起运天数", b7['大运']['起运天数'], 1)
    b8 = bazi(date(2005, 3, 6), 10, 'f')   # 阴年女=顺排，清明4/5
    eq("2005-03-06顺排起运天数", b8['大运']['起运天数'], 30)
    # ── 真实案例：《韶山四修族谱》毛泽东 1893-12-26 辰时（多源公认癸巳甲子丁酉甲辰）──
    mz = bazi(date(1893, 12, 26), 8, 'm')
    eq("毛泽东年柱", mz['年柱'], '癸巳')
    eq("毛泽东月柱", mz['月柱'], '甲子')
    eq("毛泽东日柱", mz['日柱'], '丁酉')
    eq("毛泽东时柱", mz['时柱'], '甲辰')
    eq("毛泽东大运方向", mz['大运']['方向'], '逆排')      # 癸巳阴年男
    eq("毛泽东大运首运", mz['大运']['大运'][0], '癸亥')
    eq("毛泽东大运二运", mz['大运']['大运'][1], '壬戌')
    # ── 真实案例：蒋介石 1887-10-31 午时（天机阁/枇杷八字等多源：丁亥庚戌己巳庚午）──
    jj = bazi(date(1887, 10, 31), 12, 'm')
    eq("蒋介石年柱", jj['年柱'], '丁亥')
    eq("蒋介石月柱", jj['月柱'], '庚戌')
    eq("蒋介石日柱", jj['日柱'], '己巳')
    eq("蒋介石时柱", jj['时柱'], '庚午')
    # ── 真实案例：鲁迅 1881-9-25 辰时（周作人《越城周氏支谱》：辛巳丁酉壬戌甲辰）──
    lx = bazi(date(1881, 9, 25), 8, 'm')
    eq("鲁迅年柱", lx['年柱'], '辛巳')
    eq("鲁迅月柱", lx['月柱'], '丁酉')
    eq("鲁迅日柱", lx['日柱'], '壬戌')
    eq("鲁迅时柱", lx['时柱'], '甲辰')
    eq("鲁迅大运首运", lx['大运']['大运'][0], '丙申')      # 辛巳阴年男逆排
    # ── 真实案例：周恩来 1898-3-5 卯时（族谱《老八房祭簿》：戊戌甲寅丁卯癸卯）──
    zl = bazi(date(1898, 3, 5), 6, 'm')
    eq("周恩来年柱", zl['年柱'], '戊戌')
    eq("周恩来月柱", zl['月柱'], '甲寅')       # 惊蛰1898在3/5 20:50，卯时在交节前（Bug#17修复）
    eq("周恩来日柱", zl['日柱'], '丁卯')
    eq("周恩来时柱", zl['时柱'], '癸卯')
    eq("周恩来大运首运", zl['大运']['大运'][0], '乙卯')    # 戊戌阳年男顺排
    # ── 真实案例：曾国藩 1811-11-26 亥时（《曾国藩年谱》及多源：辛未己亥丙辰己亥）──
    zgf = bazi(date(1811, 11, 26), 22, 'm')
    eq("曾国藩年柱", zgf['年柱'], '辛未')
    eq("曾国藩月柱", zgf['月柱'], '己亥')
    eq("曾国藩日柱", zgf['日柱'], '丙辰')
    eq("曾国藩时柱", zgf['时柱'], '己亥')
    eq("曾国藩大运方向", zgf['大运']['方向'], '逆排')      # 辛未阴年男逆排
    # 交节时刻边界（2026立春=2/4 04:01）：同一日按时刻分两月
    eq("2026-02-04 02时年柱(立春前)", bazi(date(2026, 2, 4), 2)['年柱'], '乙巳')
    eq("2026-02-04 02时月柱(立春前)", bazi(date(2026, 2, 4), 2)['月柱'], '己丑')
    eq("2026-02-04 10时年柱(立春后)", bazi(date(2026, 2, 4), 10)['年柱'], '丙午')
    eq("2026-02-04 10时月柱(立春后)", bazi(date(2026, 2, 4), 10)['月柱'], '庚寅')
    print("\n" + ("全部通过 ✅" if not fails else f"失败 {len(fails)} 项 ❌: {fails}"))
    return 0 if not fails else 1

if __name__ == '__main__':
    if '--test' in sys.argv:
        sys.exit(test())
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    try:
        birth = date.fromisoformat(sys.argv[1])
        hour = int(sys.argv[2])
    except (ValueError, IndexError):
        print("用法: python3 bazi.py YYYY-MM-DD 小时 [--gender m|f]，如 2000-01-01 13"); sys.exit(1)
    if not 0 <= hour <= 23:
        print("小时必须是 0-23 的整数"); sys.exit(1)
    gender = None
    if '--gender' in sys.argv:
        gender = sys.argv[sys.argv.index('--gender') + 1]
    out = bazi(birth, hour, gender)
    if gender:
        out['流年十神'] = flow_year_shishen(day_ganzhi(birth)[0], range(2026, 2037))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # 存档
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl'), 'a') as f:
            f.write(json.dumps({'type': 'bazi', 'ts': datetime.now().isoformat(), 'result': out},
                               ensure_ascii=False) + '\n')
    except Exception:
        pass
