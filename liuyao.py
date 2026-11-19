#!/usr/bin/env python3
"""liuyao.py — 六爻（纳甲装卦）起卦引擎（2026-11-18 创建）

三枚铜钱起卦（随机模拟，或 --coins 手动输入六爻值），装卦全套：
八宫世应定位、六十四卦纳甲干支、卦宫五行、六亲、六神、旬空、动爻与变卦、用神提示。
日柱干支复用 bazi.py 已验证公式。

用法:
  python3 liuyao.py                            # 当前时间 + 随机三枚铜钱
  python3 liuyao.py 2026-11-18 21:45           # 位置参数指定时间
  python3 liuyao.py --time "2026-11-18 21:45"  # 等价写法（位置参数优先）
  python3 liuyao.py --coins "9,7,7,7,7,7"      # 手动六爻值，初爻→上爻（6老阴 7少阳 8少阴 9老阳）
  python3 liuyao.py --question "问事业"        # 带问存档；--question 的值绝不参与日期解析
  python3 liuyao.py --test                     # 回归测试（不写日志）
输出 JSON（ensure_ascii=False, indent=2）。正常起卦（非 --test）末尾追加一行到
divination_log.jsonl：{"type":"liuyao","ts":iso,"result":{...含问题}}，只进不出，写失败不崩溃。

出处（规则依据，2026-11-18 web_fetch 核对维基文库原文）:
  [1] 《增刪卜易》野鹤老人著·李文辉增删，维基文库:
      总目/录入者增订 https://zh.wikisource.org/wiki/增刪卜易
      卷之一·浑天甲子章第四 https://zh.wikisource.org/wiki/增刪卜易/4
        （乾在內子水寅木辰土，在外午火申金戌土；坎内寅辰午、外申戌子；……兑内巳卯丑、外亥酉未）
      卷之一·六亲歌章第五 https://zh.wikisource.org/wiki/增刪卜易/5
        （乾兑宫金兄、土父、木财、火鬼、水子……震巽木兄、水父、金鬼、火子、土财）
      卷之一·世应章第六 https://zh.wikisource.org/wiki/增刪卜易/6
        （乾为天世在六，天风姤世在初，天山遁世在二，天地否世在三，风地观世在四，山地剥世在五，
          火地晋世在四，火天大有世退在三；隔世爻两位即是应爻）
      卷之一·动变章第七 https://zh.wikisource.org/wiki/增刪卜易/7
        （「○」阳动变阴，「ㄨ」阴动变阳；变出之爻安六亲者仍照正卦而推）
      卷之一·用神章第八 https://zh.wikisource.org/wiki/增刪卜易/8 （财官父兄孙取用规则）
      录入者增订·起六神诀: "甲乙起青龙，丙丁起朱雀，戊日起勾陈，己日起螣蛇，庚辛起白虎，壬癸起元武"
        —— 本脚本六神起例按此诀拆分（戊→勾陈、己→腾蛇、庚辛→白虎、壬癸→玄武）。
          任务书括号里的"戊己勾陈庚辛腾蛇壬癸玄武白虎"是压缩串，末尾白虎无对应日干，
          按权威诀校正为上述六组，覆盖全部 10 日干。
      录入者增订·旬空计算法（甲子旬空戌亥、甲戌旬空申酉、甲申空午未、甲午空辰巳、甲辰空寅卯、甲寅空子丑）
      录入者增订·八純卦納甲圖（八纯卦六爻干支全表，与本脚本 NZHI/NGAN 逐字一致）
  [2] 《卜筮正宗》王洪绪，维基文库（现仅存卷前，正文卷页未录，故未用作锚点）:
      https://zh.wikisource.org/wiki/卜筮正宗
  [3] 纳甲体系本源为汉·京房《京氏易传》；本脚本以 [1] 为直接依据。

黄金锚点（--test 逐条核对，装卦结果含世应纳甲）:
  A. 乾为天 —— 增删卜易·卷之一·八宫图第三 https://zh.wikisource.org/wiki/增刪卜易/3
     （书内原图: 父母戌土世/兄弟申金/官鬼午火/父母辰土应/妻财寅木/子孙子水）
  B. 水天需 之 天水讼 —— 增删卜易·卷之一·动变章第七 https://zh.wikisource.org/wiki/增刪卜易/7
     （书内原图: 需世四爻子孙申金、应初爻妻财子水，动爻1,3,4,6）
  C. 乾为天 之 风天小畜 —— 增删卜易·卷之一·用神元神忌神仇神章第九 https://zh.wikisource.org/wiki/增刪卜易/9
     （辰月戊申日占父近病，书内原图六亲纳甲齐全）
  D. 兑为泽 之 雷水解 —— 增删卜易·卷之一·元神忌神衰旺章第十 https://zh.wikisource.org/wiki/增刪卜易/10
     （酉月辛亥日占求财，书内原图六亲纳甲齐全）
"""
import os
import sys, json, random
from datetime import datetime, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bazi import TG, DZ, GZ, WUXING, SHENG, KE, day_ganzhi  # 复用已验证干支公式

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl')

# ──────────────────────────── 基础表 ────────────────────────────
# 八卦数（梅花易数同序）与卦名：(上卦数, 下卦数) → 六十四卦名
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
NUM = {'乾':1,'兑':2,'离':3,'震':4,'巽':5,'坎':6,'艮':7,'坤':8}
# 六爻阴阳位串（字符序=初→上，'1'阳'0'阴），八卦数→阴阳
BITS = {1:'111',2:'110',3:'101',4:'100',5:'011',6:'010',7:'001',8:'000'}
TRI_BY_BITS = {BITS[n]: name for name, n in NUM.items()}   # '111'→乾 …
CHAR2TRI = {'天':'乾','地':'坤','雷':'震','风':'巽','水':'坎','火':'离','山':'艮','泽':'兑'}

TRI_WX = {'乾':'金','兑':'金','离':'火','震':'木','巽':'木','坎':'水','艮':'土','坤':'土'}
# 纳甲天干：(内卦, 外卦) —— 增删卜易·浑天甲子章第四 / 录入者纳甲歌"乾内甲外壬，三男丙戊庚；坤内乙外癸，三女丁己辛"
NGAN = {'乾':('甲','壬'),'坤':('乙','癸'),'震':('庚','庚'),'巽':('辛','辛'),
        '坎':('戊','戊'),'离':('己','己'),'艮':('丙','丙'),'兑':('丁','丁')}
# 纳甲地支：(内卦三爻, 外卦三爻)，自初爻起 —— 与"八純卦納甲圖"逐字一致
NZHI = {'乾':(('子','寅','辰'),('午','申','戌')),
        '坤':(('未','巳','卯'),('丑','亥','酉')),
        '震':(('子','寅','辰'),('午','申','戌')),
        '巽':(('丑','亥','酉'),('未','巳','卯')),
        '坎':(('寅','辰','午'),('申','戌','子')),
        '离':(('卯','丑','亥'),('酉','未','巳')),
        '艮':(('辰','午','申'),('戌','子','寅')),
        '兑':(('巳','卯','丑'),('亥','酉','未'))}

# 八宫卦序：本宫、一世…五世、游魂、归魂（增删卜易·八宫图第三/世应章第六）
PALACES = [
 ['乾为天','天风姤','天山遁','天地否','风地观','山地剥','火地晋','火天大有'],
 ['坎为水','水泽节','水雷屯','水火既济','泽火革','雷火丰','地火明夷','地水师'],
 ['艮为山','山火贲','山天大畜','山泽损','火泽睽','天泽履','风泽中孚','风山渐'],
 ['震为雷','雷地豫','雷水解','雷风恒','地风升','水风井','泽风大过','泽雷随'],
 ['巽为风','风天小畜','风火家人','风雷益','天雷无妄','火雷噬嗑','山雷颐','山风蛊'],
 ['离为火','火山旅','火风鼎','火水未济','山水蒙','风水涣','天水讼','天火同人'],
 ['坤为地','地雷复','地泽临','地天泰','雷天大壮','泽天夬','水天需','水地比'],
 ['兑为泽','泽水困','泽地萃','泽山咸','水山蹇','地山谦','雷山小过','雷泽归妹'],
]
SHI_XU = ['本宫','一世','二世','三世','四世','五世','游魂','归魂']
SHI_POS = [6, 1, 2, 3, 4, 5, 4, 3]                     # 各宫世爻位（本宫世六，归魂世三）
# 由本宫卦逐位翻爻生成本宫八卦：本宫不动，一至五世翻初…五爻，游魂翻0,1,2,4，归魂翻4
FLIPS = [set(), {0}, {0,1}, {0,1,2}, {0,1,2,3}, {0,1,2,3,4}, {0,1,2,4}, {4}]

# 六神：固定轮转序 + 日干起例（增删卜易·录入者增订·起六神诀）
LIUSHEN = ['青龙','朱雀','勾陈','腾蛇','白虎','玄武']
LIUSHEN_START = {'甲':0,'乙':0,'丙':1,'丁':1,'戊':2,'己':3,'庚':4,'辛':4,'壬':5,'癸':5}

YAO_POS = ['初','二','三','四','五','上']

# 用神提示（增删卜易·用神章第八 / 八宫图第三 / 月将章第十六 / 动变章第七）
YONGSHEN = {
  "取用总则": "自占吉凶以世爻为用神；占他人、代人占事以应爻为用神（增删卜易·八宫图第三、用神章第八）",
  "父母": "占父母、祖父母及父母同辈亲长、师长、妻父母、仆占主人；天地、城池、宅舍、舟车、衣服、雨具、文书、章奏、契约——一切庇护我身者，以父母爻为用神",
  "官鬼": "占功名、官府、雷霆鬼神、女占夫、乱臣贼盗邪祟；一切拘束我身者，以官鬼爻为用神",
  "妻财": "占妻妾、婢仆、役使之人；货财、珠宝、仓库、金银买卖等使用之财物，以妻财爻为用神",
  "兄弟": "占兄弟姐妹、族中兄弟、姑姨妹夫、结拜兄弟以兄弟爻为用神；兄弟乃劫财之神，占财以此为阻、占谋以此为阻神",
  "子孙": "占子孙、女婿、侄甥、门生、医药、僧道、兵卒、六畜禽兽以子孙爻为用神；子孙为福德、解忧、制鬼之神，诸事见之为喜，独占功名忌之",
  "两现": "用神两现：一动一静取动者；俱动俱静择其旺者（增删卜易·八宫图第三）",
  "不现": "卦无用神：查伏神（飞伏神章第二十八）；月将章第十六云'卦无用神即以月建为用神，不必寻伏神也'",
  "六亲定法": "六亲按卦宫五行与爻支五行的生克定：同我兄弟、生我父母、我生子孙、我克妻财、克我官鬼（六亲歌章第五）",
  "变卦六亲": "变出之爻安六亲者仍照正卦（本卦宫五行）而推，不按变卦自身宫（动变章第七）",
}

SOURCES = [
  "纳甲干支：《增删卜易》卷之一·浑天甲子章第四 https://zh.wikisource.org/wiki/增刪卜易/4",
  "八宫世应：《增删卜易》卷之一·世应章第六 https://zh.wikisource.org/wiki/增刪卜易/6",
  "六亲：《增删卜易》卷之一·六亲歌章第五 https://zh.wikisource.org/wiki/增刪卜易/5",
  "动变：《增删卜易》卷之一·动变章第七 https://zh.wikisource.org/wiki/增刪卜易/7",
  "用神：《增删卜易》卷之一·用神章第八 https://zh.wikisource.org/wiki/增刪卜易/8",
  "六神起例：《增删卜易》录入者增订·起六神诀 https://zh.wikisource.org/wiki/增刪卜易",
  "旬空：《增删卜易》录入者增订·旬空计算法 https://zh.wikisource.org/wiki/增刪卜易",
  "锚点A 乾为天：https://zh.wikisource.org/wiki/增刪卜易/3",
  "锚点B 水天需之天水讼：https://zh.wikisource.org/wiki/增刪卜易/7",
  "锚点C 乾为天之风天小畜：https://zh.wikisource.org/wiki/增刪卜易/9",
  "锚点D 兑为泽之雷水解：https://zh.wikisource.org/wiki/增刪卜易/10",
]


# ──────────────────────────── 卦象基础 ────────────────────────────
def trigram_of_gua(name: str) -> str:
    """卦名→上卦八卦名：'乾为天'→乾，'天风姤'→天→乾"""
    if '为' in name:
        return name[0]
    return CHAR2TRI[name[0]]


def gua_bits(name: str):
    """卦名→(下卦, 上卦)八卦名。'天风姤'=天(上)+风(下)+名，故下卦在 name[1]"""
    if '为' in name:
        t = name[0]
        return t, t
    return CHAR2TRI[name[1]], CHAR2TRI[name[0]]


def name_from_bits(bits) -> str:
    """6位阴阳串(初→上)→卦名"""
    lower, upper = ''.join(bits[:3]), ''.join(bits[3:])
    return NAMES[(NUM[TRI_BY_BITS[upper]], NUM[TRI_BY_BITS[lower]])]


def build_palace_info():
    """按翻爻规则从八纯卦生成八宫八卦 → {卦名: {宫,宫五行,世序,世爻,应爻,列表名}}"""
    info = {}
    for pnames in PALACES:
        p_tri = trigram_of_gua(pnames[0])               # 纯卦上下同卦
        p_bits = list(BITS[NUM[p_tri]] * 2)           # 纯卦 = 下卦 + 上卦（6爻）
        for k, listed in enumerate(pnames):
            bb = p_bits[:]
            for i in FLIPS[k]:
                bb[i] = '0' if bb[i] == '1' else '1'
            computed = name_from_bits(bb)
            info[computed] = {
                '宫': p_tri + '宫', '宫五行': TRI_WX[p_tri],
                '世序': SHI_XU[k], '世爻': SHI_POS[k],
                '应爻': (SHI_POS[k] + 2) % 6 + 1,       # 应世隔二爻
                '列表名': listed, '宫索引': PALACES.index(pnames), '位索引': k,
            }
    return info


PALACE_INFO = build_palace_info()


def xunkong(day_gz: str):
    """旬空：按日柱所在旬取缺失的两个地支（增删卜易·旬空计算法）"""
    i = GZ.index(day_gz)
    used = {g[1] for g in GZ[(i // 10) * 10:(i // 10) * 10 + 10]}
    return [z for z in DZ if z not in used]


def liushen_seq(day_gan: str):
    """六神自初爻起的六位序列（起六神诀）"""
    s = LIUSHEN_START[day_gan]
    return [LIUSHEN[(s + i) % 6] for i in range(6)]


def liuqin(palace_wx: str, line_wx: str) -> str:
    """六亲：卦宫五行 vs 爻支五行（六亲歌章第五）"""
    if line_wx == palace_wx:
        return '兄弟'
    if SHENG[palace_wx] == line_wx:
        return '子孙'
    if SHENG[line_wx] == palace_wx:
        return '父母'
    if KE[palace_wx] == line_wx:
        return '妻财'
    return '官鬼'                                   # KE[line]==palace 爻克宫


def random_coins():
    """三枚铜钱随机模拟：字=3(阳) 背=2(阴)，六次每次三枚求和 → 6/7/8/9"""
    return [sum(random.choice((2, 3)) for _ in range(3)) for _ in range(6)]


def parse_coins(s: str):
    """'6,7,8,9,8,7' → [6,7,8,9,8,7]（初爻→上爻）"""
    try:
        vals = [int(x.strip()) for x in s.split(',') if x.strip() != '']
    except ValueError:
        raise CliError(f"--coins 只能是逗号分隔的整数: '{s}'")
    if len(vals) != 6:
        raise CliError(f"--coins 需要 6 个值（初爻→上爻），收到 {len(vals)} 个")
    bad = [v for v in vals if v not in (6, 7, 8, 9)]
    if bad:
        raise CliError(f"--coins 只能是 6/7/8/9（老阴/少阳/少阴/老阳），非法值: {bad}")
    return vals


# ──────────────────────────── 装卦 ────────────────────────────
def build_lines(gua: str, palace_wx: str, day_gan: str, coins=None, with_liushen=True):
    """逐爻装卦：爻支/纳甲干/六亲/六神/世应/动变标记。coins=None 时只标静。"""
    lo, hi = gua_bits(gua)
    seq = liushen_seq(day_gan) if with_liushen else [None] * 6
    info = PALACE_INFO[gua]
    out = []
    for i in range(6):
        tri = lo if i < 3 else hi
        side = 0 if i < 3 else 1
        gan, zhi = NGAN[tri][side], NZHI[tri][side][i % 3]
        bit = BITS[NUM[tri]][i % 3]                   # 本爻在本卦中的阴阳位
        yinyang = (('阳' if coins[i] in (7, 9) else '阴') if coins is not None
                   else ('阳' if bit == '1' else '阴'))
        item = {
            '爻位': YAO_POS[i], '序': i + 1, '阴阳': yinyang,
            '爻支': zhi, '纳甲干': gan, '纳甲': gan + zhi,
            '六亲': liuqin(palace_wx, WUXING[zhi]),
            '世应': '世' if info['世爻'] == i + 1 else ('应' if info['应爻'] == i + 1 else ''),
        }
        if with_liushen:
            item['六神'] = seq[i]
        if coins is not None:
            c = coins[i]
            item['标记'] = '老阳动→变阴' if c == 9 else ('老阴动→变阳' if c == 6 else '静')
        out.append(item)
    return out


def zhuanggua(coins, dt: datetime, mode: str) -> dict:
    """三枚铜钱装卦主流程。coins: 6个值(初→上, 6/7/8/9)"""
    day_gz = day_ganzhi(dt.date())
    day_gan = day_gz[0]
    bits = ['1' if c in (7, 9) else '0' for c in coins]
    name = name_from_bits(bits)
    info = PALACE_INFO[name]
    moving = [i + 1 for i, c in enumerate(coins) if c in (6, 9)]

    bian_name, bian_info, bian_lines = None, None, []
    if moving:
        b2 = bits[:]
        for n in moving:                              # 翻第 n 爻 = 索引 n-1
            i = n - 1
            b2[i] = '0' if b2[i] == '1' else '1'
        bian_name = name_from_bits(b2)
        bian_info = PALACE_INFO[bian_name]
        # 变卦六亲仍照正卦（本卦宫五行）而推 —— 动变章第七
        bian_lines = build_lines(bian_name, info['宫五行'], day_gan,
                                 coins=None, with_liushen=False)

    return {
        '占法': '六爻（纳甲装卦）',
        '起卦时间': dt.isoformat(sep=' ', timespec='minutes'),
        '日干支': day_gz, '日干': day_gan,
        '旬空': xunkong(day_gz),
        '六神起例': f"{day_gan}日起{LIUSHEN[LIUSHEN_START[day_gan]]}于初爻",
        '起卦方式': mode, '钱币值': list(coins),
        '本卦': {'卦名': name, '卦宫': info['宫'], '宫五行': info['宫五行'],
                 '世序': info['世序'], '世爻': info['世爻'], '应爻': info['应爻']},
        '动爻': moving,
        '变卦': (None if bian_name is None else
                 {'卦名': bian_name, '卦宫': bian_info['宫'], '宫五行': bian_info['宫五行'],
                  '世序': bian_info['世序'], '世爻': bian_info['世爻'], '应爻': bian_info['应爻']}),
        '逐爻': build_lines(name, info['宫五行'], day_gan, coins=coins, with_liushen=True),
        '变卦逐爻': bian_lines,
        '用神提示': YONGSHEN,
        '出处': SOURCES,
    }


# ──────────────────────────── CLI ────────────────────────────
class CliError(Exception):
    pass


def parse_dt(s: str):
    """'YYYY-MM-DD HH:MM' / 'YYYY-MM-DD' → datetime；返回 (dt, 是否带时分)"""
    s = s.strip()
    for fmt, has_time in (('%Y-%m-%d %H:%M', True), ('%Y-%m-%d %H:%M:%S', True),
                          ('%Y-%m-%d', False)):
        try:
            return datetime.strptime(s, fmt), has_time
        except ValueError:
            continue
    raise CliError(f"时间格式无法解析: '{s}'，应为 YYYY-MM-DD HH:MM")


def parse_cli(argv):
    """解析命令行。--question 的值绝不当日期解析（从位置参数中剔除）。"""
    opts = {'test': False, 'question': None, 'coins': None, 'dt': None,
            'time_arg': None, 'positional': []}
    i, skip = 0, set()
    while i < len(argv):
        a = argv[i]
        if a == '--test':
            opts['test'] = True
        elif a == '--question':
            if i + 1 >= len(argv):
                raise CliError("--question 缺少值（后面应跟问题字符串）")
            opts['question'] = argv[i + 1]
            if len(opts['question']) > 2000:
                raise CliError("--question 超过 2000 字符上限")
            skip.add(i + 1)
            i += 1
        elif a == '--coins':
            if i + 1 >= len(argv):
                raise CliError("--coins 需要 6,7,8,9,8,7 形式的值")
            opts['coins'] = parse_coins(argv[i + 1])
            i += 1
        elif a == '--time':
            if i + 1 >= len(argv) or argv[i + 1] == '':
                raise CliError("--time 需要 'YYYY-MM-DD HH:MM'（不能为空）")
            opts['time_arg'] = argv[i + 1]
            i += 1
        elif a.startswith('--'):
            raise CliError(f"未知参数: {a}")
        elif i not in skip:
            opts['positional'].append(a)
        i += 1

    # 时间：位置参数优先，其次 --time，最后当前时间
    if opts['positional']:
        if len(opts['positional']) > 2:
            raise CliError(f"位置参数过多: {opts['positional']}（只接受 'YYYY-MM-DD HH:MM'）")
        joined = ' '.join(opts['positional'])
        dt, has_time = parse_dt(joined)
        if not has_time:
            print("注意：只给了日期未给时间，按 00:00 起卦", file=sys.stderr)
        opts['dt'] = dt
    elif opts['time_arg']:
        dt, has_time = parse_dt(opts['time_arg'])
        if not has_time:
            print("注意：--time 只给了日期未给时间，按 00:00 起卦", file=sys.stderr)
        opts['dt'] = dt
    else:
        opts['dt'] = datetime.now()
    return opts


# ──────────────────────────── 回归测试 ────────────────────────────
# 《增删卜易》六亲歌章第五 原文（按宫五行×爻支五行）
BOOK_LIUQIN = {
 '金': {'金':'兄弟','土':'父母','木':'妻财','火':'官鬼','水':'子孙'},
 '水': {'水':'兄弟','火':'妻财','土':'官鬼','金':'父母','木':'子孙'},
 '土': {'土':'兄弟','火':'父母','木':'官鬼','水':'妻财','金':'子孙'},
 '火': {'火':'兄弟','水':'官鬼','土':'子孙','木':'父母','金':'妻财'},
 '木': {'木':'兄弟','水':'父母','金':'官鬼','火':'子孙','土':'妻财'},
}


def test():
    fails = []
    def eq(label, got, want):
        ok = got == want
        print(f"{'✓' if ok else '✗'} {label}: {got!r}" + ("" if ok else f" ≠ {want!r}"))
        if not ok:
            fails.append(label)

    DT = datetime(2026, 1, 1, 12, 0)

    # ── 锚点A：乾为天（增删卜易·八宫图第三 /3，原图"父母戌土世…子孙子水"）──
    a = zhuanggua([7] * 6, DT, 'test')
    eq("锚点A 卦名", a['本卦']['卦名'], '乾为天')
    eq("锚点A 卦宫", a['本卦']['卦宫'], '乾宫')
    eq("锚点A 宫五行", a['本卦']['宫五行'], '金')
    eq("锚点A 世序", a['本卦']['世序'], '本宫')
    eq("锚点A 世爻", a['本卦']['世爻'], 6)
    eq("锚点A 应爻", a['本卦']['应爻'], 3)
    eq("锚点A 纳甲", [l['纳甲'] for l in a['逐爻']],
       ['甲子','甲寅','甲辰','壬午','壬申','壬戌'])
    eq("锚点A 六亲", [l['六亲'] for l in a['逐爻']],
       ['子孙','妻财','父母','官鬼','兄弟','父母'])
    eq("锚点A 世应标注", [l['世应'] for l in a['逐爻']], ['','','应','','','世'])
    eq("锚点A 全静无变卦", (a['动爻'], a['变卦'], a['变卦逐爻']), ([], None, []))

    # ── 锚点B：水天需之天水讼（增删卜易·动变章第七 /7 原图）──
    b = zhuanggua([9, 7, 9, 6, 7, 6], DT, 'test')
    eq("锚点B 卦名", b['本卦']['卦名'], '水天需')
    eq("锚点B 卦宫/世序", (b['本卦']['卦宫'], b['本卦']['世序']), ('坤宫', '游魂'))
    eq("锚点B 世爻/应爻", (b['本卦']['世爻'], b['本卦']['应爻']), (4, 1))
    eq("锚点B 纳甲", [l['纳甲'] for l in b['逐爻']],
       ['甲子','甲寅','甲辰','戊申','戊戌','戊子'])
    eq("锚点B 六亲", [l['六亲'] for l in b['逐爻']],
       ['妻财','官鬼','兄弟','子孙','兄弟','妻财'])
    eq("锚点B 动爻", b['动爻'], [1, 3, 4, 6])
    eq("锚点B 变卦", b['变卦']['卦名'], '天水讼')
    eq("锚点B 变卦纳甲", [l['纳甲'] for l in b['变卦逐爻']],
       ['戊寅','戊辰','戊午','壬午','壬申','壬戌'])
    eq("锚点B 变卦六亲(照正卦坤宫)", [l['六亲'] for l in b['变卦逐爻']],
       ['官鬼','兄弟','父母','父母','子孙','兄弟'])

    # ── 锚点C：辰月戊申日占父近病 乾为天之风天小畜（增删卜易·用神章第九 /9）──
    c = zhuanggua([7, 7, 7, 9, 7, 7], DT, 'test')
    eq("锚点C 动爻", c['动爻'], [4])
    eq("锚点C 变卦", c['变卦']['卦名'], '风天小畜')
    eq("锚点C 变卦纳甲", [l['纳甲'] for l in c['变卦逐爻']],
       ['甲子','甲寅','甲辰','辛未','辛巳','辛卯'])
    eq("锚点C 变卦六亲(照正卦乾宫)", [l['六亲'] for l in c['变卦逐爻']],
       ['子孙','妻财','父母','父母','官鬼','妻财'])

    # ── 锚点D：酉月辛亥日占求财 兑为泽之雷水解（增删卜易·元神忌神衰旺章第十 /10）──
    d = zhuanggua([9, 7, 8, 7, 9, 8], DT, 'test')     # 兑110 110：1,5爻阳动，3,6爻阴静
    eq("锚点D 卦名/宫/世序", (d['本卦']['卦名'], d['本卦']['卦宫'], d['本卦']['世序']),
       ('兑为泽', '兑宫', '本宫'))
    eq("锚点D 世爻/应爻", (d['本卦']['世爻'], d['本卦']['应爻']), (6, 3))
    eq("锚点D 纳甲", [l['纳甲'] for l in d['逐爻']],
       ['丁巳','丁卯','丁丑','丁亥','丁酉','丁未'])
    eq("锚点D 六亲", [l['六亲'] for l in d['逐爻']],
       ['官鬼','妻财','父母','子孙','兄弟','父母'])
    eq("锚点D 动爻", d['动爻'], [1, 5])
    eq("锚点D 变卦", d['变卦']['卦名'], '雷水解')
    eq("锚点D 变卦六亲(照正卦兑宫)", [l['六亲'] for l in d['变卦逐爻']],
       ['妻财','父母','官鬼','官鬼','兄弟','父母'])

    # ── 世应章第六：乾宫八卦世位原文明列 ──
    eq("世应章 乾宫八世位", [PALACE_INFO[n]['世爻'] for n in PALACES[0]],
       [6, 1, 2, 3, 4, 5, 4, 3])
    eq("世应章 乾宫八应位(隔二)", [PALACE_INFO[n]['应爻'] for n in PALACES[0]],
       [3, 4, 5, 6, 1, 2, 1, 6])

    # ── 64 卦纳甲表全覆盖无重复 ──
    eq("64卦表 项数", len(PALACE_INFO), 64)
    eq("64卦表 名称全集=六十四卦名", sorted(PALACE_INFO), sorted(NAMES.values()))
    eq("64卦表 构造名与宫表列名逐一一致",
       [(n, PALACE_INFO[n]['列表名']) for n in PALACE_INFO
        if n != PALACE_INFO[n]['列表名']], [])
    bad_yy = []
    for n in sorted(PALACE_INFO):
        lo, hi = gua_bits(n)
        yang_tri = {'乾', '震', '坎', '艮'}            # 四阳卦
        for i in range(6):
            tri = lo if i < 3 else hi
            zhi = NZHI[tri][0 if i < 3 else 1][i % 3]
            gan = NGAN[tri][0 if i < 3 else 1]
            yin_yang_tri = '阳' if tri in yang_tri else '阴'
            if (DZ.index(zhi) % 2 == 0) != (yin_yang_tri == '阳'):
                bad_yy.append((n, i + 1, '支', zhi))
            if (TG.index(gan) % 2 == 0) != (yin_yang_tri == '阳'):
                bad_yy.append((n, i + 1, '干', gan))
    eq("64卦 纳甲干支全表阴阳相配", bad_yy, [])
    eq("64卦 纳甲干支全部合法(干∈十干, 支∈十二支)",
       all(l['纳甲干'] in TG and l['爻支'] in DZ
           for n in PALACE_INFO
           for l in build_lines(n, PALACE_INFO[n]['宫五行'], '甲')), True)

    # ── 八宫世应规则自洽（每宫：本宫+一至五世+游魂+归魂）──
    for pi, pnames in enumerate(PALACES):
        eq(f"宫{pi+1}({trigram_of_gua(pnames[0])}宫) 世位链",
           [PALACE_INFO[n]['世爻'] for n in pnames], SHI_POS)
        eq(f"宫{pi+1} 翻爻构造=表列",
           [n for n in pnames if PALACE_INFO[n]['列表名'] != n], [])
        eq(f"宫{pi+1} 本宫纯卦(上下同)", gua_bits(pnames[0])[0] == gua_bits(pnames[0])[1], True)
        eq(f"宫{pi+1} 归魂下卦返宫卦",
           gua_bits(pnames[7])[0] == trigram_of_gua(pnames[0]), True)
        eq(f"宫{pi+1} 世序名链", [PALACE_INFO[n]['世序'] for n in pnames], SHI_XU)

    # ── 六神 6 日干组全验证（起六神诀）──
    eq("六神 固定轮转序", LIUSHEN, ['青龙','朱雀','勾陈','腾蛇','白虎','玄武'])
    expect0 = {'甲':'青龙','乙':'青龙','丙':'朱雀','丁':'朱雀','戊':'勾陈',
               '己':'腾蛇','庚':'白虎','辛':'白虎','壬':'玄武','癸':'玄武'}
    for g in TG:
        seq = liushen_seq(g)
        eq(f"六神 {g}日起初爻", seq[0], expect0[g])
        eq(f"六神 {g}日六位轮转", seq,
           [LIUSHEN[(LIUSHEN_START[g] + i) % 6] for i in range(6)])
    # 整卦输出里的六神（取一个甲子日、一个己日）
    dd = date(2026, 1, 1)
    while day_ganzhi(dd) != '甲子':
        dd = date.fromordinal(dd.toordinal() + 1)
    o1 = zhuanggua([7] * 6, datetime(dd.year, dd.month, dd.day, 12, 0), 'test')
    eq("六神 甲子日整卦(青龙→玄武)", [l['六神'] for l in o1['逐爻']],
       ['青龙','朱雀','勾陈','腾蛇','白虎','玄武'])
    dd2 = date(2026, 1, 1)
    while day_ganzhi(dd2)[0] != '己':
        dd2 = date.fromordinal(dd2.toordinal() + 1)
    o2 = zhuanggua([7] * 6, datetime(dd2.year, dd2.month, dd2.day, 12, 0), 'test')
    eq("六神 己日初爻腾蛇", o2['逐爻'][0]['六神'], '腾蛇')

    # ── 旬空：60 甲子抽验 + 全量 ──
    for gz, want in (('甲子', ['戌','亥']), ('甲戌', ['申','酉']), ('甲申', ['午','未']),
                     ('甲午', ['辰','巳']), ('甲辰', ['寅','卯']), ('甲寅', ['子','丑'])):
        eq(f"旬空 {gz}", xunkong(gz), want)
    def brute(gz):
        i = GZ.index(gz); s = (i // 10) * 10
        have = {g[1] for g in GZ[s:s + 10]}
        return [z for z in DZ if z not in have]
    eq("旬空 60甲子全量=旬内缺失两支", [g for g in GZ if xunkong(g) != brute(g)], [])

    # ── 动爻与变卦（翻第 n 爻 = 索引 n-1，硬编码期望值防错位）──
    expect_flip = ['天风姤', '天火同人', '天泽履', '风天小畜', '火天大有', '泽天夬']
    for n, want in enumerate(expect_flip, 1):
        coins = [7] * 6
        coins[n - 1] = 9
        r = zhuanggua(coins, DT, 'test')
        eq(f"变卦 乾为天爻{n}动", r['变卦']['卦名'], want)
    eq("变卦 全静无变", zhuanggua([7] * 6, DT, 'test')['变卦'], None)
    eq("变卦 六爻全动→坤为地", zhuanggua([9] * 6, DT, 'test')['变卦']['卦名'], '坤为地')
    eq("变卦 老阴动变阳(6→阳)", zhuanggua([6] + [7] * 5, DT, 'test')['逐爻'][0]['标记'],
       '老阴动→变阳')
    eq("变卦 老阳动变阴(9→阴)", zhuanggua([9] + [7] * 5, DT, 'test')['逐爻'][0]['标记'],
       '老阳动→变阴')
    eq("动爻 索引n-1(爻2动≠爻1动)",
       (zhuanggua([7, 9, 7, 7, 7, 7], DT, 'test')['变卦']['卦名'],
        zhuanggua([9, 7, 7, 7, 7, 7], DT, 'test')['变卦']['卦名']),
       ('天火同人', '天风姤'))

    # ── 六亲歌（增删卜易·六亲歌章第五）原文 vs 通用公式 ──
    eq("六亲歌 五宫×五行全对",
       [(p, w) for p in BOOK_LIUQIN for w in BOOK_LIUQIN[p]
        if liuqin(p, w) != BOOK_LIUQIN[p][w]], [])

    # ── 随机铜钱合法性 ──
    rc = random_coins()
    eq("随机 6爻且取值合法", (len(rc) == 6 and all(v in (6, 7, 8, 9) for v in rc)), True)
    ro = zhuanggua(rc, DT, 'test')
    eq("随机 阴阳与币值一致",
       all(l['阴阳'] == ('阳' if c in (7, 9) else '阴')
           for l, c in zip(ro['逐爻'], rc)), True)

    # ── 日柱：60日整轮 + sxtwl 交叉验证 ──
    ds = [date.fromordinal(date(2026, 3, 1).toordinal() + i) for i in range(60)]
    eq("日柱 60日走完一整轮",
       [day_ganzhi(x) for x in ds], GZ[GZ.index(day_ganzhi(ds[0])):] +
       GZ[:GZ.index(day_ganzhi(ds[0]))])
    try:
        import sxtwl
        bad = []
        for x in ds:
            y = sxtwl.fromSolar(x.year, x.month, x.day).getDayGZ()
            if day_ganzhi(x) != TG[y.tg] + DZ[y.dz]:
                bad.append((str(x), day_ganzhi(x), TG[y.tg] + DZ[y.dz]))
        eq("日柱 与sxtwl天文历60日交叉一致", bad, [])
    except Exception as e:
        eq("日柱 sxtwl交叉", f"sxtwl不可用: {e}", None)

    # ── CLI：--question 绝不参与日期解析 ──
    o = parse_cli(['--question', '六爻加装自检'])
    eq("CLI 仅有--question", (o['question'], o['dt'] is not None), ('六爻加装自检', True))
    o = parse_cli(['--question', '2026-01-02 03:04'])
    eq("CLI 问题形如日期也不解析",
       (o['question'], len(o['positional']), o['dt'] == datetime(2026, 1, 2, 3, 4)),
       ('2026-01-02 03:04', 0, False))
    o = parse_cli(['--question', '问事', '2026-01-02', '03:04'])
    eq("CLI 问题在前+位置时间",
       (o['question'], o['dt']), ('问事', datetime(2026, 1, 2, 3, 4)))
    o = parse_cli(['2026-01-02', '03:04', '--question', '问事'])
    eq("CLI 问题在后+位置时间",
       (o['question'], o['dt']), ('问事', datetime(2026, 1, 2, 3, 4)))
    o = parse_cli(['2026-05-06 07:08'])
    eq("CLI 单参数含空格时间", o['dt'], datetime(2026, 5, 6, 7, 8))
    o = parse_cli(['--time', '2026-05-06 07:08'])
    eq("CLI --time", o['dt'], datetime(2026, 5, 6, 7, 8))
    o = parse_cli(['--time', '2026-05-06 07:08', '2027-01-01', '11:11'])
    eq("CLI 位置参数优先于--time", o['dt'], datetime(2027, 1, 1, 11, 11))
    eq("CLI --coins 解析", parse_coins('6,7,8,9,8,7'), [6, 7, 8, 9, 8, 7])
    for bad_args in ('6,7', '6,7,8,9,8,10', 'a,b,c,d,e,f'):
        try:
            parse_coins(bad_args)
            eq(f"CLI --coins 非法拒绝 '{bad_args}'", '未拒绝', 'CliError')
        except CliError:
            eq(f"CLI --coins 非法拒绝 '{bad_args}'", 'CliError', 'CliError')
    try:
        parse_cli(['2026-13-45 99:99'])
        eq("CLI 非法时间拒绝", '未拒绝', 'CliError')
    except CliError:
        eq("CLI 非法时间拒绝", 'CliError', 'CliError')

    print("\n" + ("全部通过 ✅" if not fails else f"失败 {len(fails)} 项 ❌: {fails}"))
    return 0 if not fails else 1


if __name__ == '__main__':
    try:
        opts = parse_cli(sys.argv[1:])
    except CliError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)
    if opts['test']:
        sys.exit(test())
    coins = opts['coins'] if opts['coins'] else random_coins()
    mode = '--coins手动指定' if opts['coins'] else '三枚铜钱随机模拟'
    out = zhuanggua(coins, opts['dt'], mode)
    out['问题'] = opts['question']
    print(json.dumps(out, ensure_ascii=False, indent=2))
    try:
        with open(LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'liuyao', 'ts': datetime.now().isoformat(),
                                'result': out}, ensure_ascii=False) + '\n')
    except Exception:
        pass
