# 占卜排盘系统 Divination System

一套**可复现、可溯源、带回归测试**的东方/西方占卜排盘工具集，共 10 套方法 + 1 个卦典库，12 个脚本、814 条断言全部内置回归测试。

> 传统文化研究与娱乐参考，不构成任何科学依据或决策建议。

## 方法一览

| 脚本 | 方法 | 说明 |
|---|---|---|
| `meihua.py` | 梅花易数 | 时间/物数/字画起卦，本卦互卦变卦，体用生克 |
| `bazi.py` | 八字排盘 | 四柱/纳音/十神/大运/流年/桃花/红鸾，sxtwl 天文历 |
| `liuren.py` | 大六壬 | 天地盘/四课/三传（九宗门全实现）+ 三传遁干 |
| `liuyao.py` | 六爻纳甲 | 铜钱起卦、八宫世应、六亲六神旬空、动变卦 |
| `qimen.py` | 时家奇门 | 拆补法定局、四盘、值符值使、八门九星八神 |
| `ziwei.py` | 紫微斗数 | 安星法全量、十四主星、生年四化、十二宫大限 |
| `cezi.py` | 测字 | 9565 字笔画库、梅花字占、`--strokes` 古今笔画覆盖 |
| `jiaobei.py` | 掷筊 | 圣/笑/阴三态、三掷为限、概率模拟与手输实掷 |
| `xingpan.py` | 西洋星盘 | JPL 星历十大行星、Placidus 分宫、相位表 |
| `tarot.py` / `tarot_draw.py` | 塔罗 | 大阿卡纳 seed 可复现抽牌 + 三牌解读文本 |
| `gua_data.py` | 卦典库 | 64 卦 384 爻卦辞爻辞（纯数据模块） |

## 环境要求

- Python 3.11+
- `pip install sxtwl`（干支/农历/节气；meihua、bazi、liuren、ziwei 依赖）
- `pip install pyswisseph`（仅 xingpan.py 需要）
- 其余脚本仅用标准库

## 快速开始

```bash
python3 meihua.py "这次合作能不能成"        # 梅花起卦
python3 bazi.py 2000-01-01 13 --gender m   # 八字排盘
python3 liuren.py                          # 六壬起课（当前时间）
python3 liuyao.py --question "项目能否签约"  # 六爻
python3 qimen.py                           # 奇门排盘
python3 ziwei.py "2000-01-01 13:00" --gender f
python3 cezi.py 明 --question "先做还是后做"
python3 jiaobei.py --question "明日出行吉否"
python3 xingpan.py --birth "2000-01-01 13:00"
python3 tarot.py "要不要换工作" --spread 3 --seed 42
```

输出均为 JSON（UTF-8）。带 `--question` 的结果会追加存档到 `divination_log.jsonl`（本地文件，已 gitignore，**只进不出**——归档仅用于事后与现实对答案，起卦解读时不读历史记录）。

## 回归测试（改完必跑）

```bash
for s in meihua bazi liuren tarot tarot_draw gua_data liuyao qimen ziwei cezi jiaobei xingpan; do
  python3 $s.py --test || echo "FAIL $s"
done
```

每个脚本内置黄金锚点（古籍卦例/公开实盘/天文星历值），全绿才可用。合计 814 条断言。

## 数据与出处

| 数据 | 来源 | 许可 |
|---|---|---|
| 卦辞爻辞（gua_data） | [维基文库《周易》王弼本](https://zh.wikisource.org/wiki/周易) | 公有领域 |
| 汉字笔画库（cezi_strokes.json，9565 字） | [hanzi-writer-data](https://github.com/chanind/hanzi-writer-data)（上游 Make Me a Hanzi） | Arphic Public License，见 [LICENSE-hanzi-writer-data.txt](LICENSE-hanzi-writer-data.txt) |
| 六壬真案语料（liuren_real_corpus.json） | 《六壬断案》邵彦和（宋） | 古籍公有领域 |
| 六爻锚点 | [《增删卜易》](https://zh.wikisource.org/wiki/增刪卜易) 维基文库 | 公有领域 |
| 梅花易数算法与字占 | [《梅花易数》卷一](https://zh.wikisource.org/wiki/梅花易數/卷一) 维基文库 | 公有领域 |
| 紫微安星规则 | 《紫微斗数全书》卷二 + [iztro](https://github.com/SylarLong/iztro)（MIT）算例对拍 | 古籍公有领域 / MIT |
| 奇门排盘锚点 | [askqimen](https://www.askqimen.com/)、[qimen-club](https://qimen-club.com/) 公开排盘例 | 公开资料比对 |
| 掷筊规则 | [维基百科·擲筊](https://zh.wikipedia.org/wiki/擲筊) | CC BY-SA |
| 行星位置 | NASA/JPL Horizons 星历 | 公开数据 |

## 目录结构

```
├── meihua.py / bazi.py / liuren.py / liuyao.py / qimen.py
├── ziwei.py / cezi.py / jiaobei.py / xingpan.py
├── tarot.py / tarot_draw.py / gua_data.py
├── cezi_strokes.json          # 9565 字笔画库
├── liuren_real_corpus.json    # 六壬断案真案语料
├── LICENSE-hanzi-writer-data.txt
└── README.md
```
