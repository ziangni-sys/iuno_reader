"""核对规则的单元测试：python tests/test_check.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from iuno_reader.check import check_sentence  # noqa: E402
from iuno_reader.extract import split_sentences  # noqa: E402
from iuno_reader.glossary import load_hedges  # noqa: E402

H = load_hedges()
T = {"inert": {"zh": ["惰性的"], "note": ""}, "few-shot": {"zh": ["少量示例"], "note": ""},
     "DE": {"zh": ["狄利克雷能量"], "note": ""}}


def codes(en, zh, conf="high"):
    return {f["code"] for f in check_sentence(en, zh, T, H, conf)}


cases = [
    # (英文, 中文, 应该出现的代码, 不应该出现的代码)
    ("Models do not use these representations.", "模型使用这些表示。", {"negation"}, set()),
    ("Models do not use these representations.", "模型没有使用这些表示。", set(), {"negation"}),
    ("We evaluate on 1000 token assignments.", "我们在许多种分配上评估。", {"number"}, set()),
    ("These results suggest that the representations are inert.", "这些结果证明这些表示是惰性的。", {"hedge_strengthened"}, set()),
    ("These results suggest that the representations are inert.", "这些结果表明这些表示是惰性的。", set(), {"hedge_strengthened", "hedge_missing"}),
    ("The representations are largely inert.", "这些表示是惰性的。", {"hedge_missing"}, set()),
    # 只含一个数字或字母的公式写成普通文字算保留；prime 的两种写法等价；数字可以用中文写；复杂公式丢了仍然要标
    ("Llama $3$ $70$B solves it.", "Llama 3 70B 解决了它。", set(), {"math"}),
    ("We set $y^{\\prime}=x$ here.", "这里令 $y'=x$。", set(), {"math"}),
    ("It works in base-10.", "它在十进制下有效。", set(), {"number"}),
    ("We set $y^{\\prime}=x$ here.", "这里令 y=x。", {"math"}, set()),
    ("We use 37 models.", "我们用了三十多个模型。", {"number"}, set()),
    # 被否定的禁用词不算语气加强；没被否定的仍然要标
    ("This suggests, but does not prove, that it fails.", "这表明——但并不证明——它失败了。", set(), {"hedge_mixed", "hedge_strengthened"}),
    ("This suggests that it fails.", "这表明并证明了它失败了。", {"hedge_mixed"}, set()),
    ("The rule maps $s_{i,j}$ to $s_{i+2,j}$.", "该规则把 $s_{i,j}$ 映射到另一个状态。", {"math"}, set()),
    ("We use prefilled responses{fn3} here.", "这里我们使用预填充的回复。", {"placeholder"}, set()),
    ("as shown by Park et al. (2025a).", "如 Park 等人所示。", {"citation"}, set()),
    ("push adjacent words to be similar to one another.", "把相邻的词推得彼此相似。", set(), {"number_word"}),
    ("One might worry that this is wrong.", "有人可能担心这是错的。", set(), {"number_word"}),
    ("The prompt consists of two components.", "提示词由若干部分组成。", {"number_word"}, set()),
    ("We use few-shot examples.", "我们使用 few-shot 例子。", set(), {"term"}),
    ("We use few-shot examples.", "我们使用一些例子。", {"term"}, set()),
    ("It works.", "", {"missing"}, set()),
    # around、about 后面跟着数才是「约」；作介词（周围、以……为中心）不算
    ("We employ a residual connection around each of the two sub-layers.", "我们在两个子层周围各使用一个残差连接。", set(), {"hedge_missing"}),
    ("It attends to a neighborhood centered around the output position.", "它关注以输出位置为中心的邻域。", set(), {"hedge_missing"}),
    ("Training takes around 5 hours.", "训练需要 5 小时。", {"hedge_missing"}, set()),
    ("It uses around half of the budget.", "它用掉一半预算。", {"hedge_missing"}, set()),
    # 带量级、千分位的数换算成万、亿算保留；换算错了仍然要标
    ("The dataset has about 4.5 million sentence pairs.", "该数据集约有 450 万个句子对。", set(), {"number", "hedge_missing"}),
    ("We train on about 40K sentences.", "我们在约 4 万个句子上训练。", set(), {"number"}),
    ("We train on 40 thousand sentences.", "我们在 4 万个句子上训练。", set(), {"number", "number_word"}),
    ("We trained for 100,000 steps.", "我们训练了 10 万步。", set(), {"number"}),
    ("We trained for 100,000 steps.", "我们训练了 100000 步。", set(), {"number"}),
    ("The corpus has 1.2 billion tokens.", "语料有 12 亿个词元。", set(), {"number"}),
    ("The dataset has 4.5 million pairs.", "该数据集有 45 万个句子对。", {"number"}, set()),
    # 禁用词在原文里有对应的英文词（determining →「确定」）不算语气加强；「一定程度」不是「一定」
    ("This suggests that determining compatibility is not easy.", "这表明确定兼容性并不容易。", set(), {"hedge_mixed", "hedge_strengthened"}),
    ("This suggests that it fails.", "这表明它确定会失败。", {"hedge_mixed"}, set()),
    ("The model may help to some extent.", "该模型可能在一定程度上有帮助。", set(), {"hedge_mixed"}),
    ("The model may help.", "该模型一定有帮助。", {"hedge_strengthened"}, set()),
    # 照抄的专名、缩写不算英文词数；整句照抄英文仍然算偏短
    ("We used values of 2.8, 3.7, 6.0 and 9.5 TFLOPS for K80, K40, M40 and P100, respectively.",
     "对于 K80、K40、M40 和 P100，我们分别使用 2.8、3.7、6.0 和 9.5 TFLOPS。", set(), {"too_short"}),
    ("We evaluate the model on many different tasks and datasets here.",
     "We evaluate the model on many different tasks and datasets here.", {"too_short"}, set()),
    # 去掉术语时按整词：术语 DE 不能把 Extended 切开
    ("The Extended Neural GPU [16] is fast.", "Extended Neural GPU [16] 很快。", set(), {"residue"}),
]

fail = 0
for en, zh, must, mustnot in cases:
    got = codes(en, zh)
    ok = must <= got and not (mustnot & got)
    if not ok:
        fail += 1
    print("通过" if ok else "失败", "|", en[:50], "|", zh[:30], "| 得到", sorted(got))

# 分句：编号标签并入下一句；缩写不切
s = split_sentences("1. We introduce a task. Park et al. (2025a) showed this, e.g. on grids. (a) First item here.")
print(s)
assert s[0].startswith("1. We introduce"), s
assert any("et al. (2025a) showed this, e.g. on grids." in x for x in s), s
assert s[-1].startswith("(a) First"), s

print("失败数", fail)
sys.exit(1 if fail else 0)
