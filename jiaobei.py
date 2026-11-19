#!/usr/bin/env python3
"""jiaobei.py — 掷筊（杯筊/圣筊）占卜引擎（2026-11-18 创建）

两枚半月形筊杯，一面平坦（阳面/平）、一面凸起（阴面/凸），掷出看组合：

  圣杯（圣筊/允杯）= 一平一凸（一阴一阳）→ 神明允许、同意，行事会顺利
  笑杯（笑筊）      = 两平面（两阳面）      → 神明一笑、不置可否，问题可能没说清，可重新再掷请示
  阴杯（阴筊/无筊/怒杯/盖杯）= 两凸面（两阴面）→ 神明否定、不宜行事，可重新再掷请示

标准问事流程（可否类），本脚本实现为「三掷组合判定」：
  - 连续掷最多 3 次（MAX_THROWS=3）。依据：维基《掷筊》「礼仪」第 1 条——
    「一般情況下，祈求連續允筊，以三次為限」，即三掷为限，不得无限纠缠。
  - 三掷全圣（三圣杯定）→ 判定「可」；依据：同条「如祈求之事相當慎重，多以連續擲得三次聖筊才算數」。
  - 三掷全阴            → 判定「不可」；依据：阴筊=神明否定（维基「說明」；刘建仁文「陰杯…主凶…是否定的」）。
  - 其余一切混合组合（含任一笑杯、圣阴交杂）→ 判定「需再问」；依据：笑筊「可以重新再擲筊請示神明，
    或再次說清楚自己的祈求」、阴筊「可以重新再擲筊請示」（维基「說明」）；刘建仁文「笑杯…不置可否…
    你需要再問一次」。
  - 随机模拟固定掷满 3 次再按组合判定（与 --manual 的三掷组合判定口径一致）。

概率（两枚独立、各 50/50 时，维基「機率論」）：圣 = 2/4 = 50%，笑 = 1/4 = 25%，阴 = 1/4 = 25%；
连续 n 次全圣概率 = (1/2)^n，故三掷全圣 = 12.5%。本脚本用 random 标准库如实模拟，不做任何加权。

规则出处：
  [1] 维基百科·掷筊（三态名称/含义、三次为限、三圣才算数、概率表）
      https://zh.wikipedia.org/wiki/擲筊
  [2] 劉建仁《臺灣話的語源與理據》·跋杯（puaʔ⊦-pue）──擲珓、求神問卜
      （圣杯=一仰一俯=「是」；阴杯=两俯=「否」；笑杯=两仰=不置可否需再问一次）
      https://taiwanlanguage.wordpress.com/2011/09/19/跋杯（puaʔ⊦-pue）──擲珓、求神問卜/

用法:
  python jiaobei.py                                  # 随机模拟掷筊
  python jiaobei.py --question "明日可行否"           # 带问题（结果与日志均含问题）
  python jiaobei.py --manual "圣,笑,阴"               # 手动输入实掷结果（圣/笑/阴，1~3 个）
  python jiaobei.py --time "2026-11-18 21:00"         # 指定时间（默认当前）
  python jiaobei.py --test                            # 回归测试（固定 seed，不写日志）
输出 JSON（ensure_ascii=False, indent=2）。正常掷筊追加 divination_log.jsonl，写失败不崩溃。
"""
import os
import json
import random
import sys
from datetime import datetime

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl')
MAX_THROWS = 3                       # 三掷为限（出处[1] 礼仪第1条）

# 结果术语表：代码 → 名称/两面形态/含义（出处[1] 說明、出处[2]）
TERMS = {
    '圣': ('圣杯', '一平一凸（一阴一阳）', '允/可行（神明同意，行事顺利）'),
    '笑': ('笑杯', '两平面（两阳面）', '笑而不答/再请示（神明不置可否，问题可能没说清）'),
    '阴': ('阴杯', '两凸面（两阴面）', '不可/再斟酌（神明否定，又称无筊、怒杯、盖杯）'),
}

# --manual 输入别名 → 代码
ALIASES = {
    '圣': '圣', '圣杯': '圣', '圣筊': '圣', '允': '圣', '允杯': '圣', '一阴一阳': '圣', '一平一凸': '圣',
    '笑': '笑', '笑杯': '笑', '笑筊': '笑',
    '阴': '阴', '阴杯': '阴', '阴筊': '阴', '无': '阴', '无筊': '阴', '无杯': '阴',
    '怒杯': '阴', '盖杯': '阴', '两凸': '阴', '两凸面': '阴',
}

RULE_TEXT = '三掷为限：三圣=可，三阴=不可，混合（含笑杯/圣阴交杂）=需再问'
SOURCES = [
    'https://zh.wikipedia.org/wiki/擲筊',
    'https://taiwanlanguage.wordpress.com/2011/09/19/跋杯（puaʔ⊦-pue）──擲珓、求神問卜/',
]


def throw_once(rng=None):
    """掷一次（两枚筊杯各 50/50 独立）→ (代码, 面1, 面2)。面：平=阳面, 凸=阴面。"""
    r = rng if rng is not None else random
    a = bool(r.getrandbits(1))       # True=平(阳面), False=凸(阴面)
    b = bool(r.getrandbits(1))
    if a != b:
        code = '圣'
    elif a:
        code = '笑'
    else:
        code = '阴'
    return code, ('平' if a else '凸'), ('平' if b else '凸')


def judge(seq):
    """三掷组合判定 → (判定, 建议)。判定 ∈ 可 / 不可 / 需再问（见 docstring 流程依据）。"""
    if all(x == '圣' for x in seq):
        return '可', '三掷皆圣（三圣杯定），神明允诺，可照所问行事。'
    if all(x == '阴' for x in seq):
        return '不可', '三掷皆阴（阴杯/无筊），神明不允，宜暂止、再斟酌或改期再问。'
    if '笑' in seq:
        return '需再问', '掷中笑杯：神明笑而不答，可能问题没说清；宜把问题问具体后再请示（三掷为限，勿反复纠缠）。'
    return '需再问', '圣阴交杂、结果不一：神明未定，宜拆细问题或择日重新请示（三掷为限）。'


def parse_manual(s):
    """"圣,笑,阴" → ['圣','笑','阴']（支持中英文逗号/顿号，识别别名），非法词抛 ValueError。"""
    parts = [p for p in s.replace('，', ',').replace('、', ',').split(',') if p.strip()]
    out = []
    for p in parts:
        key = p.strip()
        if key not in ALIASES:
            raise ValueError(f"无法识别的掷筊结果: '{key}'，可用: 圣 / 笑 / 阴（或 圣杯/笑杯/阴杯）")
        out.append(ALIASES[key])
    if not out:
        raise ValueError('--manual 为空，格式如: --manual "圣,笑,阴"')
    if len(out) > MAX_THROWS:
        raise ValueError(f'最多 {MAX_THROWS} 次（三掷为限），收到 {len(out)} 个')
    return out


def parse_time(s):
    """'YYYY-MM-DD HH:MM' → datetime，格式错抛 ValueError。"""
    return datetime.strptime(s, '%Y-%m-%d %H:%M')


def build_record(i, code):
    name, faces, meaning = TERMS[code]
    return {'次': i, '代码': code, '结果': name, '两面': faces, '含义': meaning}


def divine(dt, question=None, manual=None):
    """执行一次问事流程 → 输出 dict。manual 给定时按实掷结果判定，否则随机模拟三掷。"""
    if manual is not None:
        codes = list(manual)
        mode = '手动'
    else:
        rng = random.Random()
        codes = [throw_once(rng)[0] for _ in range(MAX_THROWS)]
        mode = '模拟'
    verdict, advice = judge(codes)
    out = {
        '类型': '掷筊',
        '模式': mode,
        '时间': dt.isoformat(sep=' ', timespec='minutes'),
        '问题': question,
        '掷筊': [build_record(i, c) for i, c in enumerate(codes, 1)],
        '组合': ','.join(codes),
        '判定': verdict,
        '规则': RULE_TEXT,
        '建议': advice,
        '规则出处': SOURCES,
    }
    return out


def test():
    """回归测试：固定 seed 可复现，不写日志。全过 → 全部通过 ✅ exit 0。"""
    fails = []

    def ok(label, cond, detail=''):
        print(f"{'✓' if cond else '✗'} {label}" + (f" ({detail})" if detail else ''))
        if not cond:
            fails.append(label)

    # ── 1. 单掷概率模拟：10 万次，两枚独立 50/50 → 圣50%/笑25%/阴25% ──
    N = 100000
    rng = random.Random(20261118)
    cnt = {'圣': 0, '笑': 0, '阴': 0}
    for _ in range(N):
        cnt[throw_once(rng)[0]] += 1
    p_sheng, p_xiao, p_yin = cnt['圣'] / N, cnt['笑'] / N, cnt['阴'] / N
    ok('圣杯占比 45%-55%', 0.45 <= p_sheng <= 0.55, f'{p_sheng:.4f}')
    ok('笑杯占比 20%-30%', 0.20 <= p_xiao <= 0.30, f'{p_xiao:.4f}')
    ok('阴杯占比 20%-30%', 0.20 <= p_yin <= 0.30, f'{p_yin:.4f}')

    # ── 2. 三连圣概率：10 万次三掷全圣 ≈ 12.5% ± 2%（(1/2)^3）──
    rng2 = random.Random(20261118)
    hit = 0
    for _ in range(N):
        if all(throw_once(rng2)[0] == '圣' for _ in range(MAX_THROWS)):
            hit += 1
    rate = hit / N
    ok('三掷全圣 ≈12.5%±2%', 0.105 <= rate <= 0.145, f'{rate:.4f}')

    # ── 3. 面组合 → 术语判定（stub 固定两枚筊面）──
    class _Stub:
        def __init__(self, bits):
            self._it = iter(bits)

        def getrandbits(self, n):
            return next(self._it)

    ok('一平一凸=圣杯', throw_once(_Stub([1, 0]))[0] == '圣')
    ok('两平面=笑杯', throw_once(_Stub([1, 1]))[0] == '笑')
    ok('两凸面=阴杯', throw_once(_Stub([0, 0]))[0] == '阴')

    # ── 4. --manual 组合判定（边界：三圣=成、三阴=不成、混合=再问）──
    ok('三圣=可', judge(['圣', '圣', '圣'])[0] == '可')
    ok('三阴=不可', judge(['阴', '阴', '阴'])[0] == '不可')
    ok('混合(圣,笑,阴)=需再问', judge(['圣', '笑', '阴'])[0] == '需再问')
    ok('混合(圣,圣,阴)=需再问', judge(['圣', '圣', '阴'])[0] == '需再问')
    ok('三笑=需再问', judge(['笑', '笑', '笑'])[0] == '需再问')

    # ── 5. --manual 输入解析 ──
    ok('解析 "圣,笑,阴"', parse_manual('圣,笑,阴') == ['圣', '笑', '阴'])
    ok('解析别名+空格+中文逗号', parse_manual(' 圣杯 ， 笑杯 、阴杯 ') == ['圣', '笑', '阴'])
    bad = False
    try:
        parse_manual('圣,阳')
    except ValueError:
        bad = True
    ok('非法词抛 ValueError', bad)

    # ── 6. 确定性：固定 seed 可复现 ──
    r1, r2, r3 = random.Random(42), random.Random(42), random.Random(42)
    seq1 = [throw_once(r1)[0] for _ in range(30)]
    seq2 = [throw_once(r2)[0] for _ in range(30)]
    seq3 = [throw_once(r3)[0] for _ in range(MAX_THROWS)]
    ok('固定 seed 序列可复现', seq1 == seq2)
    ok('固定 seed 前三掷稳定', seq3 == seq1[:MAX_THROWS])

    # ── 7. --time 解析 ──
    ok('--time 解析', parse_time('2026-11-18 21:00') == datetime(2026, 11, 18, 21, 0))
    tbad = False
    try:
        parse_time('2026/11/18 21:00')
    except ValueError:
        tbad = True
    ok('--time 格式错抛 ValueError', tbad)

    print('\n' + ('全部通过 ✅' if not fails else f'失败 {len(fails)} 项 ❌: {fails}'))
    return 0 if not fails else 1


def opt(name):
    """取 --name 的值（无则 None）。"""
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


if __name__ == '__main__':
    if '--test' in sys.argv:
        sys.exit(test())

    question = opt('--question')
    manual_s = opt('--manual')
    time_s = opt('--time')

    if '--question' in sys.argv and question is None:
        print("--question 缺少值（后面应跟问题字符串）", file=sys.stderr)
        sys.exit(1)
    if question is not None and len(question) > 2000:
        print("--question 超过 2000 字符上限", file=sys.stderr)
        sys.exit(1)

    try:
        dt = parse_time(time_s) if time_s is not None else datetime.now()
    except ValueError:
        print(f"时间格式无法解析: '{time_s}'，应为 YYYY-MM-DD HH:MM", file=sys.stderr)
        sys.exit(1)

    manual = None
    if manual_s is not None:
        try:
            manual = parse_manual(manual_s)
        except ValueError as e:
            print(str(e), file=sys.stderr)
            sys.exit(1)

    out = divine(dt, question=question, manual=manual)
    print(json.dumps(out, ensure_ascii=False, indent=2))

    try:                                   # 正常掷筊才写日志；写失败不崩溃
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'jiaobei', 'ts': datetime.now().isoformat(),
                                'result': out}, ensure_ascii=False) + '\n')
    except Exception:
        pass
