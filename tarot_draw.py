#!/usr/bin/env python
"""
塔罗牌抽取模块 - 本地随机抽取三张塔罗牌（过去/现在/未来）
包含78张标准塔罗牌数据
"""
import random
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

MAJOR_ARCANA = [
    {"id": 0, "name": "愚者", "element": "风", "upright": "新开始、冒险、天真、自由", "reversed": "鲁莽、冒风险、犹豫不决"},
    {"id": 1, "name": "魔术师", "element": "风", "upright": "创造力、意志力、技巧、自信", "reversed": "操控、欺骗、能力不足"},
    {"id": 2, "name": "女祭司", "element": "水", "upright": "直觉、智慧、神秘、内在声音", "reversed": "忽视直觉、表面化、秘密"},
    {"id": 3, "name": "女皇", "element": "地", "upright": "丰饶、母性、自然、感性", "reversed": "依赖、创造力受阻、过度溺爱"},
    {"id": 4, "name": "皇帝", "element": "火", "upright": "权威、结构、稳定、领导力", "reversed": "专制、僵化、控制欲"},
    {"id": 5, "name": "教皇", "element": "地", "upright": "传统、教导、信仰、指导", "reversed": "叛逆、非传统、自我探索"},
    {"id": 6, "name": "恋人", "element": "风", "upright": "爱情、和谐、关系、选择", "reversed": "不和谐、失衡、价值观冲突"},
    {"id": 7, "name": "战车", "element": "水", "upright": "胜利、意志、决心、前进", "reversed": "失去方向、挫败、缺乏控制"},
    {"id": 8, "name": "力量", "element": "火", "upright": "勇气、内在力量、耐心、温柔", "reversed": "自我怀疑、虚弱、不安全感"},
    {"id": 9, "name": "隐士", "element": "地", "upright": "内省、独处、智慧、指引", "reversed": "孤立、固执、逃避现实"},
    {"id": 10, "name": "命运之轮", "element": "火", "upright": "转变、命运、机遇、循环", "reversed": "坏运气、抗拒改变、不稳定"},
    {"id": 11, "name": "正义", "element": "风", "upright": "公正、真理、因果、责任", "reversed": "不公正、逃避责任、偏见"},
    {"id": 12, "name": "倒吊人", "element": "水", "upright": "牺牲、新视角、放手、等待", "reversed": "拖延、抵制、自我牺牲过度"},
    {"id": 13, "name": "死神", "element": "水", "upright": "结束、转变、放下、重生", "reversed": "抗拒改变、停滞、恐惧"},
    {"id": 14, "name": "节制", "element": "火", "upright": "平衡、耐心、调和、中庸", "reversed": "失衡、过度、缺乏耐心"},
    {"id": 15, "name": "恶魔", "element": "地", "upright": "束缚、欲望、物质、阴影", "reversed": "解脱、觉醒、释放"},
    {"id": 16, "name": "塔", "element": "火", "upright": "突变、破坏、启示、解放", "reversed": "恐惧改变、避免灾难、延迟"},
    {"id": 17, "name": "星星", "element": "风", "upright": "希望、灵感、宁静、信心", "reversed": "失望、缺乏信心、不切实际"},
    {"id": 18, "name": "月亮", "element": "水", "upright": "幻觉、直觉、潜意识、迷惑", "reversed": "释放恐惧、清醒、真相显现"},
    {"id": 19, "name": "太阳", "element": "火", "upright": "快乐、成功、活力、乐观", "reversed": "暂时受挫、过度乐观、延迟成功"},
    {"id": 20, "name": "审判", "element": "火", "upright": "觉醒、更新、反思、召唤", "reversed": "自我怀疑、拒绝反省、错过机会"},
    {"id": 21, "name": "世界", "element": "地", "upright": "完成、整合、成就、圆满", "reversed": "未完成、缺乏闭合、走捷径"},
]

POSITIONS = ["过去", "现在", "未来"]
POSITION_ADVICE = {
    "过去": "审视过去的经历，从中汲取智慧",
    "现在": "关注当下的选择和行动",
    "未来": "展望前景，做好准备迎接变化",
}


def draw_three_cards():
    """随机抽取三张大阿卡纳牌"""
    cards = random.sample(MAJOR_ARCANA, 3)
    result = []
    for i, card in enumerate(cards):
        is_reversed = random.random() < 0.3  # 30%概率逆位
        result.append({
            'position': POSITIONS[i],
            'name': card['name'],
            'number': f"{card['id']:02d}",
            'element': card['element'],
            'reversed': is_reversed,
            'upright_kw': card['upright'],
            'reversed_kw': card['reversed'],
            'deep': f"{'逆位' if is_reversed else '正位'}的{card['name']}暗示着" + (
                card['reversed'] if is_reversed else card['upright']
            ),
            'meaning': POSITION_ADVICE[POSITIONS[i]],
            'advice': f"{'注意避免' if is_reversed else '积极拥抱'}{card['name']}的能量",
        })
    return result


def generate_summary(cards):
    """根据三张牌生成综合解读"""
    names = [f"{c['position']}位的{c['name']}({'逆' if c['reversed'] else '正'}位)" for c in cards]
    themes = []
    for c in cards:
        kw = c['reversed_kw'] if c['reversed'] else c['upright_kw']
        themes.append(kw.split('、')[0])

    summary = f"今日三张牌分别是{', '.join(names)}。"
    summary += f"整体能量围绕着{'、'.join(themes)}展开。"
    summary += "建议保持开放心态，顺应变化中的机遇。"

    actions = [
        f"关注{cards[1]['name']}牌带来的当下启示",
        f"从{cards[0]['name']}牌中汲取过去的经验",
        f"为{cards[2]['name']}牌预示的未来做好准备",
    ]

    affirmation = f"我接纳{cards[1]['name']}的智慧，在变化中保持平衡与信心。"

    return summary, actions[:3], affirmation


def draw_three_cards_text():
    """抽取三张牌并返回文本格式"""
    cards = draw_three_cards()
    summary, actions, affirmation = generate_summary(cards)

    lines = []
    for card in cards:
        rev = "🔄 逆位" if card['reversed'] else "✨ 正位"
        lines.append(f"🎴 {card['position']}：{card['name']} {rev}")
        lines.append(f"  编号：{card['number']}　元素：{card['element']}")
        lines.append(f"  正位关键词：{card['upright_kw']}")
        lines.append(f"  逆位关键词：{card['reversed_kw']}")
        lines.append(f"  深度解读：{card['deep']}")
        lines.append(f"  位置含义：{card['meaning']}")
        lines.append(f"  单牌建议：{card['advice']}")
        lines.append("")

    lines.append(f"✨ 综合解读：{summary}")
    lines.append("")
    lines.append("💡 今日行动建议：")
    for i, a in enumerate(actions, 1):
        lines.append(f"  {i}. {a}")
    lines.append("")
    lines.append(f"🌟 今日肯定语：{affirmation}")

    return cards, "\n".join(lines)


def test():
    """回归测试（2026-11-19 占卜系统补齐轮添加）。--test 时运行，不产牌不写日志。"""
    import random as _random
    fails = []

    def ck(name, cond, detail=''):
        print(('✓' if cond else '✗') + f' {name}' + (f' — {detail}' if detail and not cond else ''))
        if not cond:
            fails.append(name)

    # 数据表
    ids = [c['id'] for c in MAJOR_ARCANA]
    names = [c['name'] for c in MAJOR_ARCANA]
    ck('大阿卡纳 22 张 id 0-21 无重复', len(MAJOR_ARCANA) == 22 and sorted(ids) == list(range(22)))
    ck('牌名无重复', len(set(names)) == 22)
    ck('每张牌四要素齐全（id/name/element/正逆关键词）',
       all(c.get('element') and c.get('upright') and c.get('reversed') for c in MAJOR_ARCANA))
    ck('位置表 过去/现在/未来', POSITIONS == ['过去', '现在', '未来'])
    ck('位置建议覆盖全部位置', set(POSITION_ADVICE) == set(POSITIONS))
    # 抽牌
    _random.seed(42)
    a = draw_three_cards()
    _random.seed(42)
    b = draw_three_cards()
    ck('同 seed 三张牌完全一致', a == b)
    ck('三张牌互不重复', len({c['name'] for c in a}) == 3)
    need = {'position', 'name', 'number', 'element', 'reversed',
            'upright_kw', 'reversed_kw', 'deep', 'meaning', 'advice'}
    ck('单牌字段齐全', all(need <= set(c) for c in a))
    ck('编号两位格式', all(len(c['number']) == 2 and c['number'].isdigit() for c in a))
    # 解读生成
    summary, actions, affirmation = generate_summary(a)
    ck('综合解读为非空字符串', isinstance(summary, str) and len(summary) > 10)
    ck('行动建议恰 3 条', isinstance(actions, list) and len(actions) == 3)
    ck('肯定语为非空字符串', isinstance(affirmation, str) and len(affirmation) > 5)
    cards_t, text = draw_three_cards_text()
    ck('文本输出含综合解读与建议', '综合解读' in text and '行动建议' in text and len(cards_t) == 3)
    # 逆位概率 p=0.3（3000 次三张牌 = 9000 张）
    _random.seed(20261119)
    n_rev = sum(1 for _ in range(3000) for c in draw_three_cards() if c['reversed'])
    ratio = n_rev / 9000
    ck(f'逆位概率≈0.30（实测 {ratio:.4f}）', 0.27 <= ratio <= 0.33)

    print()
    print('全部通过 ✅' if not fails else f'失败 {len(fails)} 项 ❌: {fails}')
    return 0 if not fails else 1


if __name__ == "__main__":
    import sys
    if '--test' in sys.argv:
        sys.exit(test())
    cards, text = draw_three_cards_text()
    print(text)
