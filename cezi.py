#!/usr/bin/env python3
"""cezi.py — 测字（字占）起卦引擎

起卦法出处（维基文库全文，公有领域，2026-11-19 逐条核对原页）：
  https://zh.wikisource.org/wiki/梅花易數/卷一
  原文要点：
    ·「卦以八除」——凡起卦过八数即以八数递除，以馀数作卦；如得八数整，即坤卦。
    ·「爻以六除」——凡起动爻，以重卦总数除六，以馀数作动爻；「取爻当以时加之」（通则）。
    ·「互卦起例」——重卦去初爻及上爻，中间四爻分作两卦；「乾坤无互，互其变卦」。
    ·「字占」——凡见字数如停匀，即平分一半为上卦，一半为下卦。
    ·「一字占至十一字占」——「二字为两仪平分。以一字为上卦，一字为下卦」；
      「三字为三才。以一字为上卦，二字为下卦」。
    ·「西林寺牌额占」（系字画占例）——「以西字七画为艮，作上卦；以林八画为坤，
      作下卦。以上七画下八画总十五画，除二六一十二，余数得三，是山地剥卦。
      第三爻动，变艮，互见重坤」：两字总画除六取动爻，不加时。

出处口径（2026-11-19 查证修正，引用与实现一一对应）：
  · 一字占【通行变体，非原书法】：原书一字占为左右分画法——「如楷书，则取其字画，
    以左为阳画，右为阴画。居左者看几数，取为上卦。居右者看几数，取为下卦。
    又以一字之阴阳，全画取爻」；需人工拆分左右部件笔画、无法自动化，本脚本不实现。
    查证结论：原书无「字画加时」占法（字画占例取爻亦不加时）；加时取爻见于
    「年月日时起例」「物数占例」「尺寸占」等数占法，非字画占。
    故本脚本一字占采用「总笔画+时支」综合起卦法，属通行变体（其结构与「年月日时
    起例」同构：先得数为上卦、加时总数为下卦、总数取爻，以笔画数代入）。
  · 二字占：上下卦依「二字为两仪平分」；取爻依字画占例「西林寺牌额占」，
    两字总画除六、不加时（2026-11-19 修正：原实现加时取爻，未时起卦复现不出书例）。
  · 三字占：分卦依「三字为三才」；取爻加时依「取爻当以时加之」通则。
  卦数：乾一、兑二、离三、震四、巽五、坎六、艮七、坤八（先天八卦数）。

算法步骤（本脚本实现）：
  一字占：设该字总笔画数 S，时支数 T（子=1…亥=12）
    上卦 = S % 8（余 0 → 8 坤）
    下卦 = (S + T) % 8（余 0 → 8 坤）
    动爻 = (S + T) % 6（余 0 → 6 上爻）      ← 通行变体加时（非原书左右分画法）
  二字占：两字笔画 a、b（二字为两仪平分，一字为上卦一字为下卦）
    上卦 = a % 8，下卦 = b % 8（余 0 → 8）
    动爻 = (a + b) % 6（余 0 → 6）           ← 西林寺字画占例：总画除六，不加时
  三字占：三字为三才，第一字为上卦，第二、三字合为下卦（笔画和 c+d）
    上卦 = a % 8，下卦 = (c + d) % 8（余 0 → 8）
    动爻 = (a + c + d + T) % 6（余 0 → 6）   ← 取爻当以时加之（通则）
  笔画覆盖：--strokes "字=数,字=数" 手动覆盖字库笔画（覆盖优先于字库值；
    值须 1-60 正整数，非法格式直接 exit 1 且不写日志）。
  变卦=动爻阴阳翻转；互卦=去初爻上爻取中间四爻（「互卦起例」：乾坤无互，互其变卦）。
  时支数 T 用本机 bazi.py 已验证公式 ((hour+1)//2)%12 + 1（子=1…亥=12，
  2026-10-08 修复版；本脚本内联同式，不依赖外部模块）。

笔画数据库 cezi_strokes.json（{"字": 笔画数}，UTF-8，9565 字）：
  来源：GitHub 公开数据集 chanind/hanzi-writer-data v2.0.1（Hanzi Writer 所用数据，
    数据源头为 Make Me a Hanzi 项目，由 Arphic 字体提取）
    仓库：https://github.com/chanind/hanzi-writer-data
    下载：https://registry.npmjs.org/hanzi-writer-data/-/hanzi-writer-data-2.0.1.tgz
    （README 亦指向 jsdelivr CDN: https://cdn.jsdelivr.net/npm/hanzi-writer-data@latest/）
  上游：https://github.com/skishore/makemeahanzi （9000+ 常用简繁汉字笔画矢量数据）
  许可：Arphic Public License（ARPHICPL.TXT），见
    https://raw.githubusercontent.com/chanind/hanzi-writer-data/master/ARPHICPL.TXT
  笔画数 = 每字 JSON 内 strokes 数组长度（即该字笔画顺序路径数）。
  覆盖：GB2312 全部 6763 汉字 100% 命中（含一级 3755 / 二级 3008），总量 9565 ≥ 6000。
  （若网络数据源全部失败的退化方案未启用：本次抓取成功，未做任何静默降级；
    本脚本启动时若数据文件缺失/损坏会显式报错退出，绝不默默换算法。）

用法：
  python3 cezi.py 智 --question "问题"     # 一字占（--question ≤2000 字符，超长/缺值 exit 1 不写日志）
  python3 cezi.py 两字                     # 二字占
  python3 cezi.py 三个字 --question "问"   # 三字占
  python3 cezi.py 智 --time "2026-11-18 21:00"   # 指定起卦时间（默认当前时间）
  python3 cezi.py 西林 --strokes "西=7,林=8" --time "2026-11-19 14:00"
      # 手动笔画覆盖（覆盖优先于字库值；复现《梅花易数》西林寺牌额占书例）
  python3 cezi.py --test                   # 回归测试（不写日志）
输出 JSON（ensure_ascii=False, indent=2）；正常起卦追加一行 divination_log.jsonl。
"""
import os
import json
import random
import sys
from datetime import datetime
from pathlib import Path

STROKES_FILE = Path(__file__).resolve().parent / 'cezi_strokes.json'
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl')

# 先天八卦数 → 卦名：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
TRIGRAM = {1: '乾', 2: '兑', 3: '离', 4: '震', 5: '巽', 6: '坎', 7: '艮', 8: '坤'}

# 六十四卦名表（上卦数, 下卦数）→ 卦名（与 meihua.py 同源，2026-10-08 已验证数据）
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
# 六爻阴阳：字符序 = (下,中,上)，'100' = 初阳二阴三阴
BITS = {1:'111',2:'110',3:'101',4:'100',5:'011',6:'010',7:'001',8:'000'}
INV_BITS = {v: k for k, v in BITS.items()}

_STROKES = None


def load_strokes() -> dict:
    """加载笔画库；缺失/损坏显式报错，不做静默降级。"""
    global _STROKES
    if _STROKES is None:
        try:
            with open(STROKES_FILE, encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            sys.exit(f"笔画库不存在: {STROKES_FILE}（数据集见 docstring，禁止静默降级）")
        except Exception as e:
            sys.exit(f"笔画库损坏: {STROKES_FILE}: {e}")
        if not isinstance(data, dict) or not data:
            sys.exit(f"笔画库格式非法: {STROKES_FILE}")
        _STROKES = data
    return _STROKES


def shichen_num(hour: int) -> int:
    """时支数：子=1…亥=12。公式 ((hour+1)//2)%12，与本机 bazi.py 一致（2026-10-08 修复版）。"""
    return ((hour + 1) // 2) % 12 + 1


def hexagram(upper: int, lower: int, moving: int, extra: dict) -> dict:
    """（上卦数, 下卦数, 动爻）→ 完整卦象：本卦/互卦/变卦。"""
    yao = list(BITS[lower] + BITS[upper])            # [初,二,三,四,五,上]
    yao[moving - 1] = '0' if yao[moving - 1] == '1' else '1'
    b_upper, b_lower = INV_BITS[''.join(yao[3:])], INV_BITS[''.join(yao[:3])]
    # 互卦起例：去初爻上爻，中间四爻分作两卦；乾坤无互，互其变卦
    if NAMES[(upper, lower)] in ('乾为天', '坤为地'):
        hy = BITS[b_lower] + BITS[b_upper]
    else:
        hy = BITS[lower] + BITS[upper]
    hu = NAMES[(INV_BITS[hy[2:5]], INV_BITS[hy[1:4]])]
    out = dict(extra)
    out.update({
        '上卦数': upper, '下卦数': lower,
        '上卦': TRIGRAM[upper], '下卦': TRIGRAM[lower],
        '本卦': NAMES[(upper, lower)],
        '动爻': moving,
        '变卦': NAMES[(b_upper, b_lower)],
        '互卦': hu,
    })
    return out


def strokes_of(chars: str, override: dict = None) -> list:
    """逐字取笔画：--strokes 手动覆盖值优先于字库 cezi_strokes.json。"""
    db = load_strokes()
    ov = override or {}
    out = []
    for ch in chars:
        if ch in ov:
            out.append(ov[ch])
        elif ch in db:
            out.append(db[ch])
        else:
            sys.exit(f"字不在笔画库中: {ch!r}（库收 {len(db)} 字，见 cezi_strokes.json；"
                     f"或用 --strokes \"{ch}=数\" 手动指定笔画）")
    return out


def parse_strokes_override(s: str) -> dict:
    """解析 --strokes "字=数,字=数"（逗号分隔，支持多字）。

    每组须为「单字符=正整数」，值域 1-60；任何非法格式 sys.exit(1)，
    在写日志之前退出，不产生日志行。
    """
    if s is None:
        return {}
    out = {}
    for item in s.split(','):
        item = item.strip()
        if not item or item.count('=') != 1:
            sys.exit(f"--strokes 格式非法: {item!r}（应为 字=数，多组用逗号分隔）")
        k, v = (p.strip() for p in item.split('='))
        if len(k) != 1:
            sys.exit(f"--strokes 键须为单个字符: {k!r}")
        if not (v.isascii() and v.isdigit()):
            sys.exit(f"--strokes 值须为 1-60 正整数: {v!r}（{k}）")
        n = int(v)
        if not 1 <= n <= 60:
            sys.exit(f"--strokes 值须在 1-60: {n}（{k}）")
        out[k] = n
    return out


def qigua(chars: str, dt: datetime, strokes_override: dict = None) -> dict:
    """测字起卦主流程。chars 为 1-3 个汉字；strokes_override 为 --strokes 手动笔画覆盖。"""
    if not 1 <= len(chars) <= 3:
        sys.exit(f"测字需 1-3 个汉字，收到 {len(chars)} 个: {chars!r}")
    ss = strokes_of(chars, strokes_override)
    t = shichen_num(dt.hour)
    total = sum(ss)
    if len(chars) == 1:
        upper, lower = total % 8 or 8, (total + t) % 8 or 8
        moving = (total + t) % 6 or 6
        method = '一字占（总笔画为上卦，加时支数为下卦，卦数并时数总除六取动爻）'
    elif len(chars) == 2:
        upper, lower = ss[0] % 8 or 8, ss[1] % 8 or 8
        moving = total % 6 or 6
        method = '二字占（一字为上卦，一字为下卦；两字总画除六取动爻，不加时——依原书西林寺字画占例）'
    else:
        upper, lower = ss[0] % 8 or 8, (ss[1] + ss[2]) % 8 or 8
        moving = (total + t) % 6 or 6
        method = '三字占（一字为上卦，二字为下卦，合画数加时取爻）'
    extra = {
        '所测之字': chars,
        '笔画数': total,
        '逐字笔画': dict(zip(chars, ss)),
        '起卦时间': dt.isoformat(sep=' ', timespec='minutes'),
        '时辰': ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'][(t - 1) % 12],
        '时支数': t,
        '起卦法': method,
        '问题': None,
    }
    if strokes_override:
        applied = {ch: strokes_override[ch] for ch in chars if ch in strokes_override}
        if applied:
            extra['笔画覆盖'] = applied
    return hexagram(upper, lower, moving, extra)


# ──────────────────────────── 回归测试 ────────────────────────────
def test() -> int:
    fails = []
    counter = {'n': 0}

    def ok(label, cond, detail=''):
        counter['n'] += 1
        print(f"{'✓' if cond else '✗'} {label}" + (f" — {detail}" if detail else ''))
        if not cond:
            fails.append(label)

    # 1) 笔画抽验（出处：《现代汉语通用字表》/《新华字典》笔画数，繁简分别计）
    db = load_strokes()
    expect = {
        # 永=5：永字八法正体五画（《新华字典》）
        '永': 5,
        # 张=7：简体「弓(3)+长(4)」，《现代汉语通用字表》
        '张': 7,
        # 国=8：简体「囗(3)+玉(5)」
        '国': 8,
        # 鑫=24：三金叠字，金 8×3
        '鑫': 24,
        # 李=7：木(4)+子(3)
        '李': 7,
        # 智=12：知(8)+日(4)
        '智': 12,
        # 明=8：日(4)+月(4)
        '明': 8,
        # 春=9：《新华字典》正体九画
        '春': 9,
        # 花=7：艹(3)+化(4)
        '花': 7,
        # 我=7：《新华字典》七画
        '我': 7,
    }
    for ch, n in expect.items():
        got = db.get(ch)
        ok(f"笔画 {ch}={n}", got == n, f"实得 {got}")

    # 2) 数据完整性
    ok("字库规模 ≥6000", len(db) >= 6000, f"{len(db)} 字")
    vals = list(db.values())
    ok("值域 1-60 且全为正整数",
       all(isinstance(v, int) and not isinstance(v, bool) and 1 <= v <= 60 for v in vals),
       f"min={min(vals)} max={max(vals)}")
    raw = STROKES_FILE.read_text(encoding='utf-8')
    dup = []
    json.loads(raw, object_pairs_hook=lambda ps: dup.extend(
        [k for k in {k for k, _ in ps if [x for x, _ in ps].count(k) > 1}] or []) or ps)
    ok("无重复键", len(db) == len(set(db)) and not dup, f"键数 {len(db)}")

    # 3) 算法确定性：同输入跑两次完全一致
    dt = datetime(2026, 11, 18, 21, 0)
    r1, r2 = qigua('智', dt), qigua('智', dt)
    ok("同输入两次结果一致", r1 == r2, json.dumps(r1, ensure_ascii=False)[:60])

    # 4) 余数 0 边界（8/6 整除）：国 8 画 @06:00（时支 4）
    #    上卦 8%8=0→8坤；下卦 (8+4)%8=4震；动爻 (8+4)%6=0→6；本卦地雷复
    rb = qigua('国', datetime(2026, 1, 1, 6, 0))
    ok("整除取坤：上卦=坤", rb['上卦'] == '坤', f"{rb['上卦']}")
    ok("整除取上爻：动爻=6", rb['动爻'] == 6, f"{rb['动爻']}")
    ok("本卦=地雷复", rb['本卦'] == '地雷复', rb['本卦'])
    # 下卦整除：国 8 画 @13:00（时支 8）→ (8+8)%8=0→8坤 → 坤为地，动爻 16%6=4
    rc = qigua('国', datetime(2026, 1, 1, 13, 0))
    ok("下卦整除取坤：本卦=坤为地", rc['下卦'] == '坤' and rc['本卦'] == '坤为地',
       f"{rc['下卦']}/{rc['本卦']}")
    ok("坤为地四爻动→雷地豫", rc['动爻'] == 4 and rc['变卦'] == '雷地豫',
       f"{rc['动爻']}/{rc['变卦']}")

    # 5) 卦名映射完整性：8×8=64，余数 0→8 全覆盖
    ok("六十四卦名表 64 项且唯一", len(NAMES) == 64 and len(set(NAMES.values())) == 64)
    ok("余数0→坤8 映射", TRIGRAM[8] == '坤' and NAMES[(8, 8)] == '坤为地')

    # 6) 随机 10 字起卦：不崩溃且卦名全部在合法表内
    rng = random.Random(42)
    pool = sorted(db)
    sample = rng.sample(pool, 10)
    legal = set(NAMES.values())
    bad = []
    for ch in sample:
        try:
            r = qigua(ch, datetime(2026, 6, 15, 12, 30))
        except SystemExit as e:
            bad.append(f"{ch}:exit:{e}")
            continue
        except Exception as e:
            bad.append(f"{ch}:{type(e).__name__}:{e}")
            continue
        for k in ('本卦', '变卦', '互卦'):
            if r[k] not in legal:
                bad.append(f"{ch}.{k}={r[k]}")
        if not (1 <= r['动爻'] <= 6):
            bad.append(f"{ch}.动爻={r['动爻']}")
    ok(f"随机 10 字起卦合法（{','.join(sample)}）", not bad, '; '.join(bad[:3]))

    # 7) 二字/三字占分支
    r2z = qigua('测字', datetime(2026, 6, 15, 12, 30))   # 测10? 以库值为准，只校结构
    ok("二字占结构完整", all(k in r2z for k in ('上卦', '下卦', '本卦', '动爻', '变卦', '互卦'))
       and r2z['所测之字'] == '测字', r2z['本卦'])
    r3z = qigua('测字占', datetime(2026, 6, 15, 12, 30))
    ok("三字占结构完整", all(k in r3z for k in ('上卦', '下卦', '本卦', '动爻', '变卦', '互卦'))
       and r3z['所测之字'] == '测字占', r3z['本卦'])

    # 8) --strokes 覆盖通道与参数安全项（2026-11-19 验收修复新增）
    cfg = None
    try:
        cfg = parse_args(['西林', '--strokes', '西=7,林=8', '--time', '2026-11-19 14:00'])
    except SystemExit as e:
        ok("--strokes 解析正确", False, f'意外退出: {e.code}')
        cfg = None
    if cfg is not None:
        ok("--strokes 解析正确",
           cfg['chars'] == '西林' and cfg['strokes'] == {'西': 7, '林': 8}
           and cfg['time_str'] == '2026-11-19 14:00',
           json.dumps(cfg['strokes'], ensure_ascii=False))
    # 非法覆盖值必须 exit 1（sys.exit(msg) → 进程退出码 1），且发生在写日志之前
    bad = []
    for c in ('西=0', '西=61', '西=-1', '西=abc', '西=7.5', '西', '=7', '西=7,', ''):
        try:
            parse_strokes_override(c)
            bad.append(f'{c!r}未退出')
        except SystemExit as e:
            if not e.code:
                bad.append(f'{c!r}退出码为0')
    ok("非法覆盖值 exit 1", not bad, '; '.join(bad))
    # 西林寺牌额占复现（原书：山地剥卦，第三爻动，变艮，互见重坤）
    if isinstance(cfg, dict):
        dt_lin = datetime.strptime(cfg['time_str'], '%Y-%m-%d %H:%M')
        r_lin = qigua(cfg['chars'], dt_lin, cfg['strokes'])
    else:
        r_lin = {}
    ok("西林寺覆盖例复现：山地剥·动3·变艮为山·互重坤",
       r_lin.get('本卦') == '山地剥' and r_lin.get('动爻') == 3
       and r_lin.get('变卦') == '艮为山' and r_lin.get('互卦') == '坤为地',
       f"{r_lin.get('本卦')}/动{r_lin.get('动爻')}/{r_lin.get('变卦')}/互{r_lin.get('互卦')}")
    # --question 安全项：缺值 / 超 2000 字符 → exit 1
    try:
        parse_args(['智', '--question'])
        ok("--question 缺值 exit 1", False, '未退出')
    except SystemExit as e:
        ok("--question 缺值 exit 1", bool(e.code), str(e.code))
    try:
        parse_args(['智', '--question', '问' * 2001])
        ok("--question 超2000字符 exit 1", False, '未退出')
    except SystemExit as e:
        ok("--question 超2000字符 exit 1", bool(e.code), str(e.code))

    print(f"\n断言 {counter['n']} 条")
    if fails:
        print(f"失败 {len(fails)} 项 ❌: {fails}")
        return 1
    print("全部通过 ✅")
    return 0


def parse_args(argv: list) -> dict:
    """解析 CLI 参数。缺值 / --question 超长 / --strokes 非法一律 sys.exit(1)，
    且全部发生在写日志之前（负向用例不产生日志行）。"""
    question = time_str = strokes_str = None
    skip = set()
    for flag in ('--question', '--time', '--strokes'):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 >= len(argv) or argv[i + 1] == '' or argv[i + 1].startswith('--'):
                sys.exit(f"{flag} 缺少参数值")
            val = argv[i + 1]
            if flag == '--question':
                question = val
            elif flag == '--time':
                time_str = val
            else:
                strokes_str = val
            skip.update((i, i + 1))
    if question is not None and len(question) > 2000:
        sys.exit(f"--question 超长：{len(question)} 字符，上限 2000")
    strokes = parse_strokes_override(strokes_str)
    args = [a for i, a in enumerate(argv) if i not in skip and not a.startswith('--')]
    if not args:
        sys.exit('用法: cezi.py 汉字 [--question "问题"] [--time "YYYY-MM-DD HH:MM"] '
                 '[--strokes "字=数,字=数"]；或 cezi.py 两字/三字')
    return {'chars': ''.join(args), 'question': question,
            'time_str': time_str, 'strokes': strokes}


def main(argv: list) -> int:
    if '--test' in argv:
        return test()
    cfg = parse_args(argv)
    if cfg['time_str']:
        try:
            dt = datetime.strptime(cfg['time_str'], '%Y-%m-%d %H:%M')
        except ValueError:
            sys.exit(f"时间格式无法解析: {cfg['time_str']!r}，应为 YYYY-MM-DD HH:MM")
    else:
        dt = datetime.now()
    out = qigua(cfg['chars'], dt, cfg['strokes'])
    if cfg['question'] is not None:
        out['问题'] = cfg['question']
    print(json.dumps(out, ensure_ascii=False, indent=2))
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'cezi', 'ts': datetime.now().isoformat(),
                                'result': out}, ensure_ascii=False) + '\n')
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
