#!/usr/bin/env python3
"""tarot.py — 塔罗牌抽取（2026-10-08 占卜系统修复工程创建；2026-11-19 补 --test 回归与严格入参对齐安全标准）
随机种子=时间戳并记录在输出里，同一seed可复现同一次抽牌（可追溯）。

用法:
  python3 tarot.py "问什么"              # 单张牌
  python3 tarot.py "问什么" --spread 3   # 过去/现在/未来
  python3 tarot.py "问什么" --seed 123   # 复现指定抽牌
  python3 tarot.py --question "问什么"   # 等价写法（与其余占卜脚本一致）
  python3 tarot.py --test                # 回归测试（不写日志）

口径：牌库=22 张大阿卡纳（本脚本历史口径，56 张小阿卡纳见 tarot_draw.py 的 78 张数据表）；
--spread 越界钳位 1-22（2026-10-08 IndexError 修复保留）；其余非法入参一律 exit 1 且不写日志。
"""
import os
import sys, json, random, time, io, contextlib

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'divination_log.jsonl')
MAX_Q = 2000

MAJOR = ['愚人','魔术师','女祭司','女皇','皇帝','教皇','恋人','战车','力量','隐士',
         '命运之轮','正义','倒吊人','死神','节制','恶魔','高塔','星星','月亮','太阳','审判','世界']

VALUE_FLAGS = ('--spread', '--seed', '--question')
KNOWN_FLAGS = set(VALUE_FLAGS) | {'--test'}


def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


def draw(n, seed):
    rng = random.Random(seed)
    deck = list(range(22))
    rng.shuffle(deck)
    return [{'牌': MAJOR[deck[i]], '正逆': '逆位' if rng.random() < 0.3 else '正位'}
            for i in range(n)]


def parse_spread(v):
    try:
        n = int(v)
    except (TypeError, ValueError):
        die(f"--spread 需要整数（1-22）: {v!r}")
    return max(1, min(n, 22))


def parse_seed(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        die(f"--seed 需要整数: {v!r}")


def validate_question(q):
    if q == '':
        die('问题不能为空')
    if len(q) > MAX_Q:
        die(f'问题超长：{len(q)} 字符，上限 {MAX_Q}')
    return q


def parse_args(argv):
    """显式解析：未知 flag / 缺值 / 冲突 / 超长 → exit 1（写日志之前）。"""
    values = {}
    positionals = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            if a not in KNOWN_FLAGS:
                die(f'未知参数: {a}')
            if a in VALUE_FLAGS:
                if i + 1 >= len(argv) or argv[i + 1].startswith('--'):
                    die(f'{a} 缺少值（后面应跟参数值）')
                values[a] = argv[i + 1]
                i += 2
            else:
                i += 1
        else:
            positionals.append(a)
            i += 1

    if len(positionals) > 1:
        die(f'位置参数过多: {positionals[1:]}（问题只能给一个）')
    if positionals and '--question' in values:
        die('问题不能同时用位置参数和 --question 给出')

    question = values.get('--question')
    if question is None and positionals:
        question = positionals[0]
    if question is not None:
        validate_question(question)

    spread = parse_spread(values['--spread']) if '--spread' in values else 1
    seed = parse_seed(values['--seed']) if '--seed' in values else int(time.time() * 1000)
    return question, spread, seed


def test():
    fails = []

    def ck(name, cond, detail=''):
        print(('✓' if cond else '✗') + f' {name}' + (f' — {detail}' if detail and not cond else ''))
        if not cond:
            fails.append(name)

    def expect_exit1(name, fn, *args):
        buf = io.StringIO()
        try:
            with contextlib.redirect_stderr(buf):
                fn(*args)
            ck(name, False, '未抛 SystemExit')
        except SystemExit as e:
            ck(name, e.code == 1, f'exit={e.code}')

    # 牌库
    ck('大阿卡纳 22 张且无重名', len(MAJOR) == 22 and len(set(MAJOR)) == 22)
    # 确定性
    ck('同 seed 两次抽取完全一致', draw(3, 12345) == draw(3, 12345))
    ck('不同 seed 抽取不同', draw(3, 1) != draw(3, 2))
    # 抽取合法性
    d22 = draw(22, 7)
    ck('22 张全抽不重不漏', sorted(x['牌'] for x in d22) == sorted(MAJOR))
    ck('正逆取值合法', all(x['正逆'] in ('正位', '逆位') for x in draw(5, 3)))
    # 钳位
    ck('spread 钳位 99→22', parse_spread('99') == 22)
    ck('spread 钳位 0→1、-3→1', parse_spread('0') == 1 and parse_spread('-3') == 1)
    ck('spread 3→3', parse_spread('3') == 3)
    # 非法入参全部 exit 1
    expect_exit1('spread 非整数 exit 1', parse_spread, 'abc')
    expect_exit1('seed 非整数 exit 1', parse_seed, 'xyz')
    expect_exit1('未知 flag exit 1', parse_args, ['--foo'])
    expect_exit1('--spread 缺值 exit 1', parse_args, ['--spread'])
    expect_exit1('--seed 缺值 exit 1', parse_args, ['--question', '--foo'])
    expect_exit1('--question 缺值 exit 1', parse_args, ['--question'])
    expect_exit1('问题超 2000 exit 1', parse_args, ['x' * 2001])
    expect_exit1('空问题 exit 1', parse_args, [''])
    expect_exit1('位置参数×2 exit 1', parse_args, ['a', 'b'])
    expect_exit1('位置参数与 --question 冲突 exit 1', parse_args, ['问', '--question', '答'])
    # 逆位概率 p=0.3
    total = 10000
    rev = sum(1 for s in range(total) if draw(1, s)[0]['正逆'] == '逆位')
    ratio = rev / total
    ck(f'逆位概率≈0.30（实测 {ratio:.4f}）', 0.27 <= ratio <= 0.33)
    # 正常解析路径
    q, n, sd = parse_args(['测试问题', '--spread', '3', '--seed', '42'])
    ck('正常解析 question/spread/seed', (q, n, sd) == ('测试问题', 3, 42))
    q2, n2, _ = parse_args(['--question', '2026-11-19', '--spread', '99'])
    ck('--question 形如日期不被当日期解析且钳位', q2 == '2026-11-19' and n2 == 22)

    print()
    print('全部通过 ✅' if not fails else f'失败 {len(fails)} 项 ❌: {fails}')
    return 0 if not fails else 1


if __name__ == '__main__':
    if '--test' in sys.argv:
        sys.exit(test())
    question, n, seed = parse_args(sys.argv[1:])
    out = {'问题': question, 'seed': seed, '牌': draw(n, seed)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'type': 'tarot', 'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
                                'result': out}, ensure_ascii=False) + '\n')
    except Exception:
        pass
