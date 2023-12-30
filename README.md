# GenshinTexts

根据原神的解包文本整理了游戏中大部分对话内容。

## 使用方式

1. 从Dimbreath的仓库（请自行搜索）下载最新游戏解包数据，解压至某一目录。
2. 在当前目录下运行命令行：
```bash
mkdir -p output

# 生成output/data.pkl文件，是从解包数据中提取的中间结果
# 命令参数中的OSRELWin4.1.0_R18121248_S17874799_D18114882目录为解包数据目录，其中应有ExcelBinOutput、BinOutput等目录
python extract.py /path/to/genshin/data/OSRELWin4.1.0_R18121248_S17874799_D18114882 output/data.pkl
# 读入output/data.pkl文件，并生成output/output.json
# 修改"TextMapCHS.json"为其它文件可对应生成其它语言的文本数据
python collect.py output/data.pkl /path/to/genshin/data/OSRELWin4.1.0_R18121248_S17874799_D18114882/ExcelBinOutput/NpcExcelConfigData.json /path/to/genshin/data/OSRELWin4.1.0_R18121248_S17874799_D18114882/TextMap/TextMapCHS.json output/output.json
# 进行文本后处理，清洗文本数据至output/cleaned.json
python clean_text.py output/output.json output/cleaned.json
```

本仓库的脚本在`OSRELWin4.1.0_R18121248_S17874799_D18114882`版本的解包数据上能够运行成功。其他版本可能需要改动。

## 输出数据格式

### 目录和文件结构

使用上节给出的示例命令行运行至`collect.py`时，输出数据保存在`output/output.json`中。由于游戏文本中几乎没有出现`` ` ``字符，故导出文本中以该字符作为特殊含义字符，用于标记。

json文件的第一层dict的键表示该段对话来源，值（列表）为对话内容。该列表中包含对话的多个“路径”，路径之间的差异来源于主角选择的对话选项不同。每个路径为一个列表，包含该路径上对话的全部文本和对应说话人信息。

每句话包含`role`，`roleName`和`content`三个属性。其中：

- `role`为整数（`-1`或自然数），表示说话人的身份ID。`0`表示主角，正整数表示NPC，`-1`表示未知（解包数据中不存在，或者该对话并非从任务对话中提取等异常情形）。但不论提取自何处，主角的`role`字段总是为`0`。
- `roleName`为显示名，即游戏中对话框上方显示的名字。即使`role`为`-1`也可能有显示名。对主角而言，`roleName`为`` `Traveller` ``；对`role`为`-1`且没有显示名的情况，`roleName`为`` `unknown` ``。此外，一些对话是从角色故事等非对话场景生成而来，这种情况被模拟为主角提问，“系统”回答。此处“系统”的`roleName`会被标记为`` `system` ``。可以将`` `system` ``视作对原神世界观全知的特殊角色。
- `content`为对话内容。若说话人为主角，该内容即为对话选项内容。一些句子的对话内容无法从解包数据中提取到，此时`content`内容为`` `unknown` ``。注意`content`中可能包含换行符。

以Python的语法理解此json含义，可表示为

```python
data[source_str][trace_index][sentence_index]["role"]: int
data[source_str][trace_index][sentence_index]["roleName"]: str
data[source_str][trace_index][sentence_index]["content"]: str
```

### 文本后处理

脚本`clean_text.py`用于进行文本后处理，该脚本的输出文件格式与`collect.py`的输出格式完全相同，但输出中将不包含任何具有程序含义的特殊符号，可直接用于语言模型训练等任务。以下介绍游戏文本中出现的特殊文本及脚本中的处理方案。

#### 未知文本

若一段对话中有句子文本为`` `unknown` ``，脚本`clean_text.py`将直接丢弃这段对话。

#### 特殊标记

游戏文本中包含若干特殊标记，主要用于标记该文本是否不应该出现在正式游戏中，例如文本开头出现`(test)`或文本结尾出现`$UNRELEASED`的句子。可以使用脚本`clean_text.py`删除文本中所有含有特殊标记的句子。

#### 修饰符

游戏文本中包含一些XML修饰符（在对话文本中仅有`<color>`，其他文本中还包括`<i>`、`<size>`、`<c1>`、`<c2>`、`<c3>`、`<multi>`），用于修改字体颜色、字号等。可以使用脚本`clean_text.py`删除文本中所有修饰符。

#### 占位符

游戏文本中包含若干种占位符，脚本会将这些占位符替换为合适的文本。占位符两端以`{}`括住，包含称呼占位符的句子以`#`开头，但其它文本并非如此。一些占位符使用`#`添加条件进行了性别区分。此外，有些占位符（包括`{QuestNpcID}`、`{QuestGatherID}`、`{QuestGatherNum}`、`{QuestNpcID2}`、`{ChallengeIndex10}`、`{ChallengeCurrValue10}`）仅用于突发任务（例如蒙德捡苹果）或挑战任务（丹迪限时挑战），包含这些占位符的对话默认会被`clean_text.py`丢弃。

脚本对占位符进行了以下处理：

- 当占位符为`{NICKNAME}`时，替换为玩家设置的主角名称（默认替换为`旅行者`，可使用脚本提供的命令行参数修改）。
- 当占位符为`{M#SOMETHING}`或`{F#SOMETHING}`时，根据主角性别决定是否输出为`SOMETHING`。若占位符首项性别与主角相符则输出`SOMETHING`，否则不输出任何内容。
- 当占位符的格式为`{MATEAVATAR#SOMETHING}`或`{PLAYERAVATAR#SOMETHING}`时，`SOMETHING`给出了两种文本选择，需要根据`MATEAVATAR`（血亲的性别）或`PLAYERAVATAR`（主角的性别）的值选择其中一种作为输出文本。变量值为男0、女1。0值时选择第一个文本，1值时选择第二个文本。
- 一种特殊修饰符`{RUBY#[D]SOMETHING}`以占位符的格式出现，用于在文本上方显示小号文字，例如游戏中提及“虚空”时上方出现“阿卡西”。脚本将以下方显示的文字为准，即将该修饰符直接删除。

下表给出了文本中所有称呼占位符，其中仅有`SEXPRO[INFO_MALE_PRONOUN_CUTEBIGBROTHER]`由于难以找到当时剧情留档视频而无法准确复原文本（事实上该占位符使用次数极少），其余推荐替换文本均为游戏中实际使用的文本。

| 占位符 | 推荐替换文本 | 文本示例 - 替换前 | 文本示例 - 替换后 |
| --- | --- | --- | --- |
| NICKNAME | 旅行者 | 唔嗯…当然，{NICKNAME}的战力是很强的。 | 唔嗯…当然，旅行者的战力是很强的。 |
| M | （女主时删除，男主时替换） | 关于我的{M#妹妹}{F#哥哥}… | 关于我的妹妹… |
| F | （男主时删除，女主时替换） | 关于我的{M#妹妹}{F#哥哥}… | 关于我的哥哥… |
| SEXPRO[INFO_FEMALE_PRONOUN_AUNT] | 阿姨 | 知道了。对不起。黄毛{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_UNCLE\|INFO_FEMALE_PRONOUN_AUNT]} | 知道了。对不起。黄毛阿姨。 |
| SEXPRO[INFO_MALE_PRONOUN_UNCLE] | 叔叔 | 知道了。对不起。黄毛{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_UNCLE\|INFO_FEMALE_PRONOUN_AUNT]}。 | 知道了。对不起。黄毛叔叔。 |
| SEXPRO[INFO_FEMALE_PRONOUN_BIGSISTER] | 大姐姐 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BIGBROTHER\|INFO_FEMALE_PRONOUN_BIGSISTER]}，要玩手鞠吗？ | 大姐姐，要玩手鞠吗？ |
| SEXPRO[INFO_MALE_PRONOUN_BIGBROTHER] | 大哥哥 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BIGBROTHER\|INFO_FEMALE_PRONOUN_BIGSISTER]}，要玩手鞠吗？ | 大哥哥，要玩手鞠吗？ |
| SEXPRO[INFO_FEMALE_PRONOUN_BROTHER] | 哥哥 | 你的{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_SISTER\|INFO_FEMALE_PRONOUN_BROTHER]}，好像和「深渊」… | 你的哥哥，好像和「深渊」… |
| SEXPRO[INFO_MALE_PRONOUN_SISTER] | 妹妹 | 你的{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_SISTER\|INFO_FEMALE_PRONOUN_BROTHER]}，好像和「深渊」… | 你的妹妹，好像和「深渊」… |
| SEXPRO[INFO_FEMALE_PRONOUN_CUTEBIGSISTER] | 大捷洁 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_CUTEBIGBROTHER\|INFO_FEMALE_PRONOUN_CUTEBIGSISTER]}，呢也不过…过风画节呀？ | 大捷洁，呢也不过…过风画节呀？ |
| SEXPRO[INFO_MALE_PRONOUN_CUTEBIGBROTHER] | 大葛格（未经验证） | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_CUTEBIGBROTHER\|INFO_FEMALE_PRONOUN_CUTEBIGSISTER]}，呢也不过…过风画节呀？ | 大葛格，呢也不过…过风画节呀？ |
| SEXPRO[INFO_FEMALE_PRONOUN_GIRLA] | 老妹 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYA\|INFO_FEMALE_PRONOUN_GIRLA]}，冒昧问一下。你身边飘着的这个小东西，多少钱可以卖？ | 老妹，冒昧问一下。你身边飘着的这个小东西，多少钱可以卖？ |
| SEXPRO[INFO_MALE_PRONOUN_BOYA] | 小哥 | 「朋友」？请问这位{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYA\|INFO_FEMALE_PRONOUN_GIRLC]}，混的是哪条道？ | 「朋友」？请问这位小哥，混的是哪条道？ |
| SEXPRO[INFO_FEMALE_PRONOUN_GIRLB] | 姑娘 | 哈哈，你很懂嘛，{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYA\|INFO_FEMALE_PRONOUN_GIRLB]}！在这个日子许愿的话，帝君和仙人们都会保佑你的。 | 哈哈，你很懂嘛，姑娘！在这个日子许愿的话，帝君和仙人们都会保佑你的。 |
| SEXPRO[INFO_FEMALE_PRONOUN_GIRLC] | 小姐 | 咦？这位{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYA\|INFO_FEMALE_PRONOUN_GIRLC]}，你是来光顾「猫尾酒馆」的吗？ | 咦？这位小姐，你是来光顾「猫尾酒馆」的吗？ |
| SEXPRO[INFO_MALE_PRONOUN_BOYC] | 先生 | 哎哟，是您呐！我亲爱的好{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYC\|INFO_FEMALE_PRONOUN_GIRLC]}，准是一阵好风送您过来的。 | 哎哟，是您呐！我亲爱的好先生，准是一阵好风送您过来的。 |
| SEXPRO[INFO_FEMALE_PRONOUN_GIRLD] | 公主 | …原来如此，深渊教团里有一位「{MATEAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYD\|INFO_FEMALE_PRONOUN_GIRLD]}」，主导了腐化特瓦林的计划？ | …原来如此，深渊教团里有一位「公主」，主导了腐化特瓦林的计划？ |
| SEXPRO[INFO_MALE_PRONOUN_BOYD] | 王子 | …原来如此，深渊教团里有一位「{MATEAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYD\|INFO_FEMALE_PRONOUN_GIRLD]}」，主导了腐化特瓦林的计划？ | …原来如此，深渊教团里有一位「王子」，主导了腐化特瓦林的计划？ |
| SEXPRO[INFO_FEMALE_PRONOUN_BOYD] | 王子 | 「{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_GIRLD\|INFO_FEMALE_PRONOUN_BOYD]}」殿下。 | 「王子」殿下。 |
| SEXPRO[INFO_MALE_PRONOUN_GIRLD] | 公主 | 「{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_GIRLD\|INFO_FEMALE_PRONOUN_BOYD]}」殿下。 | 「公主」殿下。 |
| SEXPRO[INFO_FEMALE_PRONOUN_GIRLE] | 小姑娘 | 哈哈，{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYE\|INFO_FEMALE_PRONOUN_GIRLE]}，跟你们在一起的，可是名震蒙德的大探险家斯坦利啊！ | 哈哈，小姑娘，跟你们在一起的，可是名震蒙德的大探险家斯坦利啊！ |
| SEXPRO[INFO_MALE_PRONOUN_BOYE] | 小伙子 | 哈哈，{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYE\|INFO_FEMALE_PRONOUN_GIRLE]}，跟你们在一起的，可是名震蒙德的大探险家斯坦利啊！ | 哈哈，小伙子，跟你们在一起的，可是名震蒙德的大探险家斯坦利啊！ |
| SEXPRO[INFO_FEMALE_PRONOUN_GIRL] | 少女 | 实在不愧于骑士团超新星{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOY\|INFO_FEMALE_PRONOUN_GIRL]}之名。 | 实在不愧于骑士团超新星少女之名。 |
| SEXPRO[INFO_MALE_PRONOUN_BOY] | 少年 | 实在不愧于骑士团超新星{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOY\|INFO_FEMALE_PRONOUN_GIRL]}之名。 | 实在不愧于骑士团超新星少年之名。 |
| SEXPRO[INFO_FEMALE_PRONOUN_HEROINE] | 女一号 | 当然！当然！您可是我心中永远的{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_HERO\|INFO_FEMALE_PRONOUN_HEROINE]}！ | 当然！当然！您可是我心中永远的女一号！ |
| SEXPRO[INFO_MALE_PRONOUN_HERO] | 男一号 | 当然！当然！您可是我心中永远的{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_HERO\|INFO_FEMALE_PRONOUN_HEROINE]}！ | 当然！当然！您可是我心中永远的男一号！ |
| SEXPRO[INFO_FEMALE_PRONOUN_HE] | 他 | 这…这究竟是怎么回事？！戴因也知道{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_SHE\|INFO_FEMALE_PRONOUN_HE]}的名字！ | 这…这究竟是怎么回事？！戴因也知道他的名字！ |
| SEXPRO[INFO_MALE_PRONOUN_SHE] | 她 | 这…这究竟是怎么回事？！戴因也知道{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_SHE\|INFO_FEMALE_PRONOUN_HE]}的名字！ | 这…这究竟是怎么回事？！戴因也知道她的名字！ |
| SEXPRO[INFO_FEMALE_PRONOUN_KONG] | 空 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_YING\|INFO_FEMALE_PRONOUN_KONG]}。我们又见面了。 | 空。我们又见面了。 |
| SEXPRO[INFO_MALE_PRONOUN_YING] | 荧 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_YING\|INFO_FEMALE_PRONOUN_KONG]}。我们又见面了。 | 荧。我们又见面了。 |
| SEXPRO[INFO_FEMALE_PRONOUN_SHE] | 她 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_HE\|INFO_FEMALE_PRONOUN_SHE]}不是已经来了船上，要和我们一起庆祝了吗？ | 她不是已经来了船上，要和我们一起庆祝了吗？ |
| SEXPRO[INFO_MALE_PRONOUN_HE] | 他 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_HE\|INFO_FEMALE_PRONOUN_SHE]}不是已经来了船上，要和我们一起庆祝了吗？ | 他不是已经来了船上，要和我们一起庆祝了吗？ |
| SEXPRO[INFO_FEMALE_PRONOUN_SISANDSIS] | 两位姐姐 | 谢谢{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BROANDSIS\|INFO_FEMALE_PRONOUN_SISANDSIS]}！ | 谢谢两位姐姐！ |
| SEXPRO[INFO_MALE_PRONOUN_BROANDSIS] | 哥哥姐姐 | 谢谢{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BROANDSIS\|INFO_FEMALE_PRONOUN_SISANDSIS]}！ | 谢谢哥哥姐姐！ |
| SEXPRO[INFO_FEMALE_PRONOUN_SISTERA] | 姐姐 | 下次，就换{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BROTHER\|INFO_FEMALE_PRONOUN_SISTERA]}再来和小冥一起玩吧。 | 下次，就换姐姐再来和小冥一起玩吧。 |
| SEXPRO[INFO_FEMALE_PRONOUN_SISTER] | 妹妹 | 这个啊。以前，我们有一个那菈朋友。那菈法留纳。{MATEAVATAR#SEXPRO[INFO_MALE_PRONOUN_HE\|INFO_FEMALE_PRONOUN_SHE]}说，{MATEAVATAR#SEXPRO[INFO_MALE_PRONOUN_HE\|INFO_FEMALE_PRONOUN_SHE]}有一个「{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BROTHER\|INFO_FEMALE_PRONOUN_SISTER]}」。 | 这个啊。以前，我们有一个那菈朋友。那菈法留纳。{MATEAVATAR#SEXPRO[INFO_MALE_PRONOUN_HE\|INFO_FEMALE_PRONOUN_SHE]}说，{MATEAVATAR#SEXPRO[INFO_MALE_PRONOUN_HE\|INFO_FEMALE_PRONOUN_SHE]}有一个「妹妹」。 |
| SEXPRO[INFO_FEMALE_PRONOUN_XIAGIRL] | 女侠 | 有这位{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_XIABOY\|INFO_FEMALE_PRONOUN_XIAGIRL]}相助，所幸无恙。 | 有这位女侠相助，所幸无恙。 |
| SEXPRO[INFO_MALE_PRONOUN_XIABOY] | 少侠 | 有这位{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_XIABOY\|INFO_FEMALE_PRONOUN_XIAGIRL]}相助，所幸无恙。 | 有这位少侠相助，所幸无恙。 |
| SEXPRO[INFO_FEMALE_PRONOUN_YING] | 荧 | 但不用急，{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BROTHER\|INFO_FEMALE_PRONOUN_YING]}。我有足够的时间来等你。 | 但不用急，荧。我有足够的时间来等你。 |
| SEXPRO[INFO_MALE_PRONOUN_BROTHER] | 哥哥 | 但不用急，{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BROTHER\|INFO_FEMALE_PRONOUN_YING]}。我有足够的时间来等你。 | 但不用急，哥哥。我有足够的时间来等你。 |
| SEXPRO[INFO_MALE_PRONOUN_Twins2Male] | 这也是我妹妹头上的花。 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_Twins2Male\|INFO_FEMALE_PRONOUN_Twins2Female]} | 这也是我妹妹头上的花。 |
| SEXPRO[INFO_FEMALE_PRONOUN_Twins2Female] | 这种花自我苏醒便戴在我的头上。 | {PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_Twins2Male\|INFO_FEMALE_PRONOUN_Twins2Female]} | 这种花自我苏醒便戴在我的头上。 |

## 附录

附录中总结分析解包数据时部分值得记录的经验。

### 关于talkRole

对话中的`talkRole`的`type`字段取值共有如下几种：

- `TALK_ROLE_NPC`：最常见的type之一，表示这句话来自NPC。
- `TALK_ROLE_PLAYER`：最常见的type之一，表示这句话来自主角（游戏中通常表现为选项）。
- `TALK_ROLE_BLACK_SCREEN`：这句话会以黑屏形式出现，通常是旁白。出现这种type时id通常为空。
- `TALK_ROLE_NEED_CLICK_BLACK_SCREEN`：黑屏形式，但需要点击来到达下一句话。出现这种type时id通常为空。
- `TALK_ROLE_CONSEQUENT_BLACK_SCREEN`：游戏中的表现效果似乎与`TALK_ROLE_BLACK_SCREEN`一致。
- `TALK_ROLE_CONSEQUENT_NEED_CLICK_BLACK_SCREEN`：游戏中的表现效果似乎与`TALK_ROLE_NEED_CLICK_BLACK_SCREEN`一致。
- `TALK_ROLE_GADGET`：游戏中的表现效果似乎与`TALK_ROLE_NPC`一致，且id通常有值，不需要特殊处理。
- `TALK_ROLE_MATE_AVATAR`：这句话来自血亲，例如“我们终将重逢。”“但不用急，荧。我有足够的时间来等你。”。出现这种type时id通常为空。

## 致谢

本仓库参考了[mrzjy的项目](https://github.com/mrzjy/GenshinDialog)的部分源代码和输出结果。

