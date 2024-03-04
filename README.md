# GenshinTexts

本项目致力于将《原神》中与剧情和世界观相关的各种文本清洗整理为标准化格式，且替换或滤除文本中一切具有程序含义的字符串（例如根据性别变化的文本）。

**UPDATE: 完全重构了提取逻辑。新增按任务整理的对话顺序关系；新增材料、武器、圣遗物等文本整理；优化代码结构，添加更完善的注释。** 旧版整理脚本见`old_version`目录。

## 免责声明

本项目仅供游戏粉丝学习交流使用，请勿用于任何盈利或非法用途。请勿用于任何违反了您与miHoYo Co., Ltd.所订立的相关协议之用途。

## 🚀脚本，启动！

1. 从[Dimbreath](https://github.com/Dimbreath)的项目获取最新原始数据，解压至某一目录。
2. 修改本项目目录下的run.sh，将其中的路径替换为原始数据所在路径。你也可以修改其它参数以满足你的个性化需求。
3. 在当前目录下运行命令行：
```bash
./run.sh
```
4. 默认会在`exp/v1`目录下输出所有整理结果。

脚本参数一览：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `data_dir` | （必填） | 原始数据路径，脚本以该目录下文件作为输入。该目录下应当包含ExcelBinOutput、BinOutput等目录。 |
| `--output_dir` | exp/output | 输出目录。 |
| `--remove_quest_cycles` | true | 可选值为"true"或"false"。当为"true"时，输出结果中任务间前后关系将不会出现环状依赖。 |
| `--lang` | CHS | 输出结果要使用的语言。支持原始数据中包括的所有语言，即"CHS", "CHT", "DE", "EN", "ES", "FR", "ID", "IT", "JP", "KR", "PT", "RU", "TH", "TR", "VI" |
| `--traveller_sex` | female | 主角性别，会影响部分关于主角及其血亲的文本内容。 |
| `--traveller_name` | 旅行者 | 主角名称。剧情文本中提及主角（旅行者）的部分会被替换为该参数值。 |
| `--mate_name` | （默认为空） | 血亲名称。剧情文本中提及血亲的部分会被替换为该参数值。如果留空，则自动根据主角性别决定。若主角性别为女，则血亲名称自动确定为所选语言中的“空”；若主角性别为男，则血亲名称自动确定为所选语言中的“荧”。 |
| `--wanderer_name` | 流浪者 | 流浪者（原散兵）的名称。剧情中提及改名后的流浪者的部分会被替换为该名称。 |
| `--narrator_name` | \`旁白\` | 剧情中部分文本是以黑屏等形式给出的，没有明确的说话人。这种文本的说话人会使用该参数值确定的名称。默认值使用反引号括住是为了与一般文本相区分。 |
| `--unknown_name` | \`未知\` | 原始数据中缺少部分对话文本的说话人信息，此时会使用该参数值作为这类句子的说话人名称。默认值使用反引号括住是为了与一般文本相区分。 |
| `--unknown_text` | \`未知\` | 原始数据中缺少部分文本内容，此时会使用该参数值替代缺少的内容。默认值使用反引号括住是为了与一般文本相区分。 |
| `--replace_quotes` | true | 可选值为"true"或"false"。当为"true"时，会将所有文本中的直角引号「」替换为弯引号“”。该参数目前仅在语言选择简体中文（CHS）时生效。 |
| `--replace_newline` | true | 可选值为"true"或"false"。原始数据的文本中所有换行符都是经过转义的形式（`\\n`）。当该参数设为"true"时，会将所有转义换行符替换为普通换行符。 |
| `--remove_broken_trace` | false | 可选值为"true"或"false"。原始数据中缺少部分文本内容。当为"true"时，将删除所有缺少部分内容的对话路径。 |
| `--remove_absent_text` | true | 可选值为"true"或"false"。原始数据中缺少部分文本内容。当为"true"时，将删除所有缺少部分内容的文本（在对话中，仅删除缺少文本的单个句子）。若为"false"，将保留这些文本，并将缺少的内容按`--unknown_text`给出的值填充。该参数对`avatar.csv`和`reliquary.csv`无效，该文件中所有缺失字段都会使用`unknown_name`（角色姓名缺失时）或`unknown_text`（其他文本缺失时）填充。 |

本项目在`OSRELWin4.4.0_R20559831_S20338540_D20555221`版本的原始数据上经测试可运行成功。其他版本可能需要改动。

本项目的算法设计不包含随机因素，从而尽可能保证在使用更新版本的数据整理时，旧版本已有的数据在最终整理结果中的结构和命名不会改变。

## 输出数据格式

脚本将输出以下文件：

- `dialog.json`：剧情对话记录。包含每个对话的各种对话路径（对话中选择不同选项而形成不同路径）。
- `quest.json`：章节、任务和子任务的元信息。
- `avatar.csv`：角色语音和角色故事文本。
- `item.csv`：物品名称和简介文本。
- `weapon.csv`：武器名称、简介和故事文本。
- `reliquary.csv`：圣遗物名称、简介和故事文本。

下文以模板和示例形式给出每个文件的格式说明。模板中将包含注释和占位符，其中占位符由尖括号和全大写单词构成。

### dialog.json

`dialog.json`中包含几乎所有对话文本。本项目定义了**source**这一概念用于组织对话内容。如果你希望了解对话文本的组织形式和source的命名规则，可参考附录“关于任务结构与对话命名”。如果你不关心对话来源，可继续浏览下文。

除了常规对话外，角色详情中的角色语音文本（仅对话语音，不包括战斗语音）也保存在`dialog.json`中，以“旅行者问，角色答”的形式组织，问题即是语音标题。角色语音中的特例是旅行者、菲谢尔和白术，这三人的语音中还包含派蒙、奥兹和长生的对话。我们通过检测冒号和换行的方式来切分这些对话，同时用预设的角色名来判断含有冒号的文本到底是否属于特例。目前预设角色名仅限简体中文，不保证其他语言文本的切割正确。对于旅行者和派蒙的特例对话，语音标题不会作为第一句加入到对话中。所有角色语音的source名称格式为`avatar_<AVATAR_ID>_voice_<INDEX>`。

整理过程中，我们还检查了对话的多个选项是否指向相同的下一句。若是，则我们将这些选项合并到对话中。这是因为主角的一句话经常以拆分为多个选项的形式展现。

对每个source而言，存在多种方式遍历全部对话。本项目采用的算法为使用（近似）最少的路径覆盖所有句子。在本文档和程序代码中，我们将对话路径称为trace。关于该算法的详细介绍参见本文附录。

我们保证以`prev_sources`和`next_sources`连接而成的以source为节点的有向图中不包含环。

以下以模板和示例形式介绍`dialog.json`的格式。

模板：

```
{
  "<SOURCE_NAME>": {  # source名称，命名规则详见附录。
    "next_sources": ["<SOURCE_NAME1>", "<SOURCE_NAME2>", ...],  # 按任务顺序，排在该source之后的source列表。列表中多数情况下只有1个source。若列表中包含多个source，则这些source是并列的（通常是因为当前子任务完成后同时开启了多个子任务）。
    "next_sources_optional": ["<SOURCE_NAME1>", "<SOURCE_NAME2>", ...],  # 任务中在完成该source的对话后可以自主进行的其它非必须对话，常见于完成任务后与留在原地的NPC对话。
    "prev_sources": ["<SOURCE_NAME1>", "<SOURCE_NAME2>", ...],  # 按任务顺序，排在该source之前的source列表。该列表与next_sources完全对应。
    "prev_sources_optional": ["<SOURCE_NAME1>", "<SOURCE_NAME2>", ...],  # 任务中在完成该source的对话之前可以自主进行的其它非必须对话，常见于任务进行中可以与部分NPC进行的对话。
    "quest_id": <QUEST_ID>,  # 整数类型，表示该source所属的任务ID，取值范围为正整数或-1。取值为-1时表示该source不属于任何单一任务，常见于大世界常驻NPC的普通对话。
    "subquest_id": <SUBQUEST_ID>,  # 整数类型，表示该source所属的子任务ID，取值范围为正整数或-1。取值为-1时表示该source不属于任何单一子任务，可能是跨越了多个子任务，或者不属于任何任务。
    "traces": [  # 对话路径列表
      [  # 一条对话路径
        {  # 一句对话，即一个dialog
          "role": "<ROLE>",  # 说话人名称，是游戏中实际显示在对话框上方的名字。一些对话数据缺失了这一字段，默认配置下我们会填入“未知”来表示。你可以通过修改调用脚本的命令行参数来改变填入的内容。
          "content": "<CONTENT>"  # 说话内容。一些对话数据缺失了这一字段，默认配置下我们会删除这一句。你可以通过修改调用脚本的命令行参数来决定是否删除该句，或者设定填入的内容。
        },
        ...
      ],
    ]
    ...
  },
  ...
}
```

示例：

```json
{
  "subquest_1012_101214_0": {
    "quest_id": 1012,
    "subquest_id": 101214,
    "prev_sources": [
      "subquest_1012_101213_0"
    ],
    "prev_sources_optional": [
      "quest_1012_5"
    ],
    "next_sources": [
      "subquest_1012_101215_0"
    ],
    "next_sources_optional": [],
    "traces": [
      [
        {
          "role": "莺儿",
          "content": "嗯，水质还不错。"
        },
        {
          "role": "莺儿",
          "content": "接下来就要请你帮忙，去合成台，从霓裳花里提炼出精油了。"
        },
        {
          "role": "莺儿",
          "content": "制造香膏的手法，和炼金的手法大不相同，我来教你吧。要像这样，轻轻地…温柔地握住臼杵…"
        },
        {
          "role": "莺儿",
          "content": "手掌也要注意紧贴，这样才不容易滑脱…"
        },
        {
          "role": "莺儿",
          "content": "然后用你最顺手的节奏搅动…直到霓裳花的汁水…"
        },
        {
          "role": "旅行者",
          "content": "放心，我很在行。"
        },
        {
          "role": "旅行者",
          "content": "好了好了，我明白了…"
        },
        {
          "role": "莺儿",
          "content": "嗯~果然有这方面的天赋，一说就懂。"
        },
        {
          "role": "莺儿",
          "content": "带上这些，到附近的合成台去试试吧？"
        },
        {
          "role": "莺儿",
          "content": "记得，三种都要制作哦。虽然在精油阶段的外形很相似，但制成香膏以后，我会用不同的盒子帮你装好的。"
        }
      ]
    ]
  }
}
```

### quest.json

`quest.json`中包含章节（chapter）、任务（quest）和子任务（subquest）的相关信息。

模板：

```
{
  "chapters": {
    "<CHAPTER_ID>": {
      "group_id": <GROUP_ID>,  # 分组序号。chapter以成组的形式构成更大的单位，例如每个国家的魔神任务chapter各自属于同一group。该字段值可能为-1，表示该chapter不属于任何group。
      "begin_subquest_id": <SUBQUEST_ID>,  # 整数类型，表示起始子任务ID，取值范围为正整数或-1。取值为-1时表示数据中缺失该值。游戏中在该子任务完成时，会在屏幕中央显示章节开始。
      "end_subquest_id": <SUBQUEST_ID>,  # 整数类型，表示最终子任务ID，取值范围为正整数或-1。取值为-1时表示数据中缺失该值。游戏中在该子任务完成时，会在屏幕中央显示章节结束。
      "type": "<QUEST_TYPE>",  # 任务类型，可能取值包括AQ（魔神任务）、EQ（版本活动任务，即每版本的大型活动）、IQ（每日委托任务）、LQ（传说任务）、WQ（世界任务）。
      "number": "<CHAPTER_NUM>",  # 章节号的文字形式。若数据中缺失，将设置为参数`--unknown_text`的值。
      "title": "<CHAPTER_TITLE>",  # chapter标题。若数据中缺失，将设置为参数`--unknown_text`的值。
      "quest_ids": [<QUEST_ID>, ...]  # 所包含的任务ID（整数类型）。
    },
    ...
  },
  "quests": {
    "<QUEST_ID>": {
      "type": "<QUEST_TYPE>",  # 任务类型，可能取值同chapter中的"type"字段。
      "title": "<QUEST_TITLE>",  # 任务标题。若数据中缺失，将设置为参数`--unknown_text`的值。
      "description": "<DESCRIPTION>",  # 任务描述，通常显示在游戏中任务界面的右边。若数据中缺失，将设置为参数`--unknown_text`的值。
      "chapter_id": <CHAPTER_ID>,  # 整数类型，表示所属chapter的ID，取值范围为正整数或-1。取值为-1时表示不属于任何chapter。
      "subquest_ids": [<SUBQUEST_ID>, ...],  # 所包含的子任务的ID（整数类型）。
      "prev_quest_ids": [<QUEST_ID>, ...],  # 上一个任务的ID（整数类型）。有多个ID时表明该任务的前置任务可能有多个并列。该列表可能为空。
      "next_quest_ids": [<QUEST_ID>, ...],  # 下一个任务的ID（整数类型）。有多个ID时表明该任务的后续任务可能有多个并列。该列表可能为空。
    },
    ...
  },
  "subquests": {
    "<SUBQUEST_ID>": {
      "description": "<DESCRIPTION>",  # 子任务描述，通常在开启一个子任务时显示于左上小地图下的任务标题下方。若数据中缺失，将设置为参数`--unknown_text`的值。
      "step_description": "<STEP_DESCRIPTION>",  # 更新任务描述，多数情况下为null。若不为null，表示进行到该子任务时，任务界面的任务描述会更新为该值。
    },
    ...
  }
}
```

示例：

```json

{
  "chapters": {
    "1001": {
      "group_id": 1001,
      "begin_subquest_id": 36301,
      "end_subquest_id": 31101,
      "type": "AQ",
      "number": "序章 第一幕",
      "title": "捕风的异乡人",
      "quest_ids": [
        306,
        307,
        308,
        309,
        311,
        352,
        353,
        354,
        355,
        356,
        357,
        358,
        360,
        363
      ]
    }
  },
  "quests": {
    "306": {
      "type": "AQ",
      "title": "昔日的风",
      "description": "为了消除风魔龙的威胁，你们需要消灭废墟中残留的力量。为此，你前往西风之鹰的庙宇，安柏正在庙宇门口等待你们。",
      "chapter_id": 1001,
      "subquest_ids": [
        30600,
        30601,
        30602,
        30603,
        30604,
        30607,
        30608,
        30609,
        30610,
        30611,
        30612
      ],
      "next_quest_ids": [
        307,
        308
      ]
    }
  },
  "subquests": {
    "35802": {
      "description": "与琴对话",
      "step_description": "你们艰难击退了来袭的风魔龙。来自西风骑士团的凯亚目睹了这一过程，此后，你们受邀前往骑士团总部一叙。代理团长琴早就在总部等待你们，你向她提出想要加入保卫蒙德城的行动。"
    }
  }
}
```

### avatar.csv

`avatar.csv`中包含角色基本信息和故事文本，以csv格式存储。该文件不受参数`--remove_absent_text`影响，所有缺失字段都会使用`--unknown_name`（角色姓名缺失时）或`--unknown_text`（其他文本缺失时）的参数值填充。各列说明如下：

| 列名 | 类型 | 描述 | 示例 |
| --- | --- | --- | --- |
| id | 整数 | 角色id。 | 10000030 |
| name | 字符串 | 角色名称。 | 钟离 |
| description | 字符串 | 角色简要描述，显示在角色“属性”界面右侧好感条下方。 | 被「往生堂」请来的神秘客人，知识渊博，对各种事物都颇有见地。 |
| birth_month | 整数 | 出生月份。 | 12 |
| birth_day | 整数 | 出生日。 | 31 |
| affiliation | 字符串 | 角色所属，显示在角色“资料”界面右侧。 | 璃月港 |
| vision_before | 字符串 | 神之眼属性（变化前）。部分角色的神之眼属性、神之眼名称、命之座名称文本会随着剧情进展而变化，例如钟离。表中所有后缀带有`_before`或`_after`的字段均表示此含义。 | 岩 |
| vision_after | 字符串 | 神之眼属性（变化后）。 | 岩 |
| vision_name_before | 字符串 | 神之眼名称（变化前）。**部分角色的该字段有缺失。** | （缺失。以钟离为例，原则上应当取值“神之眼”） |
| vision_name_after | 字符串 | 神之眼名称（变化后）。**部分角色的该字段有缺失。** | （缺失。以钟离为例，原则上应当取值“神之心”） |
| constellation_before | 字符串 | 命之座名称（变化前）。 | ？？？ |
| constellation_after | 字符串 | 命之座名称（变化后）。 | 岩王帝君座 |
| title | 字符串 | 角色称号，一般在官方立绘中发布。 | 尘世闲游 |
| detail | 字符串 | 角色详细介绍，显示在角色“资料”界面右侧，一般与`description`字段内容相同。 | 被「往生堂」请来的神秘客人，知识渊博，对各种事物都颇有见地。 |
| association | 字符串 | 角色所属国家。截至4.4版本，其可能取值包括"ASSOC_TYPE_MAINACTOR", "ASSOC_TYPE_MONDSTADT", "ASSOC_TYPE_LIYUE", "ASSOC_TYPE_INAZUMA", "ASSOC_TYPE_SUMERU", "ASSOC_TYPE_FONTAINE", "ASSOC_TYPE_FATUI", "ASSOC_TYPE_RANGER"。其中"ASSOC_TYPE_RANGER"仅埃洛伊使用。 | ASSOC_TYPE_LIYUE |
| story_title_1 | 字符串 | 角色故事中第一项的标题。 | 角色详细 |
| story_1 | 字符串 | 角色故事中第一项的内容。 | 在璃月的传统中，「请仙」与「送仙」是同样重要的事。…… |
| story_title_2 | 字符串 | 角色故事中第二项的标题。 | 角色故事1 |
| story_2 | 字符串 | 角色故事中第二项的内容。 | 在璃月，如果一个人对细节特别在意，对某些事物心中…… |
| story_title_3 | 字符串 | 角色故事中第三项的标题。 | 角色故事2 |
| story_3 | 字符串 | 角色故事中第三项的内容。 | 买东西是要砍价的。…… |
| story_title_4 | 字符串 | 角色故事中第四项的标题。 | 角色故事3 |
| story_4 | 字符串 | 角色故事中第四项的内容。 | 钟离是饿不死的。…… |
| story_title_5 | 字符串 | 角色故事中第五项的标题。 | 角色故事4 |
| story_5 | 字符串 | 角色故事中第五项的内容。 | 身为璃月港的缔造者，摩拉克斯在这座商业之城里…… |
| story_title_6 | 字符串 | 角色故事中第六项的标题。 | 角色故事5 |
| story_6 | 字符串 | 角色故事中第六项的内容。 | 作为七神中最古老的一位，「岩王帝君」已经度过了…… |
| story_title_7 | 字符串 | 角色故事中第七项的标题。 | 水产品 |
| story_7 | 字符串 | 角色故事中第七项的内容。 | 魔神战争期间，提瓦特大陆上每一处都燃烧着战火。…… |
| story_title_8 | 字符串 | 角色故事中第八项的标题。 | 神之眼 |
| story_8 | 字符串 | 角色故事中第八项的内容。 | 璃月港这场由钟离自导自演的「送仙」典仪筹备完毕后，…… |

### item.csv

`item.csv`中包含材料、料理等道具的名称和简介，以csv格式存储。各列说明如下：

| 列名 | 类型 | 描述 | 示例 |
| --- | --- | --- | --- |
| id | 整数 | 物品id。 | 101001 |
| name | 字符串 | 物品名称。 | 铁块 |
| description | 字符串 | 材料描述。 | 铁的矿石原石，在拥有相应技能的工匠手中能绽放光采。…… |

### weapon.csv

`weapon.csv`中包含武器的名称、简介和故事文本，以csv格式存储。各列说明如下：

| 列名 | 类型 | 描述 | 示例 |
| --- | --- | --- | --- |
| id | 整数 | 武器id。 | 11101 |
| name | 字符串 | 武器名称。 | 无锋剑 |
| type | 字符串 | 武器类别，可能取值为WEAPON_BOW（弓）、WEAPON_CATALYST（法器）、WEAPON_CLAYMORE（双手剑）、WEAPON_POLE（长柄武器）、WEAPON_SWORD_ONE_HAND（单手剑）。 | WEAPON_SWORD_ONE_HAND |
| rank_level | 整数 | 武器星级，取值范围为1~5。 | 1 |
| description | 字符串 | 武器描述。 | 少年人的梦想、踏上旅途的兴奋——如果这两种珍贵的品质还不够锋利，那就用勇气补足吧。 |
| story | 字符串 | 武器故事。 | 旅途中总是充满了相遇与别离。 <br>始终不会抛弃旅人的忠实旅伴， <br>恐怕只有长剑与远行的梦想了。 |

### reliquary.csv

`reliquary.csv`中包含圣遗物套装的名称，以及各部位的名称、简介和故事文本，以csv格式存储。该文件不受参数`--remove_absent_text`影响，所有缺失字段都会使用`--unknown_name`（套装名或圣遗物名缺失时）或`--unknown_text`（其他文本缺失时）的参数值填充。但对于原本就不存在的部位（例如“祭雷之人”套装仅有理之冠一个部位），对应文本将留空。

原始数据中各部位的英文名称与游戏中看到的名称并不一致（可能是废案），且各部位间有一种与游戏中“花羽沙杯冠”不同的预定义的顺序。其顺序和英文名为：

1. 空之杯：RING
2. 死之羽：NECKLACE
3. 理之冠：DRESS
4. 生之花：BRACER
5. 时之沙：SHOES

为方便整理，我们将按照原始数据中的顺序排列各部位圣遗物。整理后数据的各列说明如下：

| 列名 | 类型 | 描述 | 示例 |
| --- | --- | --- | --- |
| id | 整数 | 圣遗物套装id。 | 10001 |
| set_name | 字符串 | 圣遗物套装名称。 | 行者之心 |
| name_1 | 字符串 | 空之杯名称。若套装中不存在该部位，则留空。 | 异国之盏 |
| description_1 | 字符串 | 空之杯描述。若套装中不存在该部位，则留空。 | 朴素的白瓷酒杯，曾经盈满了欢愉的酒水。 |
| story_1 | 字符串 | 空之杯故事。若套装中不存在该部位，则留空。 | 琴有四弦。…… |
| name_2 | 字符串 | 死之羽名称。若套装中不存在该部位，则留空。 | 归乡之羽 |
| description_2 | 字符串 | 死之羽描述。若套装中不存在该部位，则留空。 | 蓝色的箭羽，其上凝结着旅人消逝远去的眷恋。 |
| story_2 | 字符串 | 死之羽故事。若套装中不存在该部位，则留空。 | 希望被寡情的强权撕裂，重逢的诺言亦化作泡影。…… |
| name_3 | 字符串 | 理之冠名称。若套装中不存在该部位，则留空。 | 感别之冠 |
| description_3 | 字符串 | 理之冠描述。若套装中不存在该部位，则留空。 | 散发着春风气息的柳冠。 |
| story_3 | 字符串 | 理之冠故事。若套装中不存在该部位，则留空。 | 离别的旅人，将这顶柳冠作为最后的纪念，…… |
| name_4 | 字符串 | 生之花名称。若套装中不存在该部位，则留空。 | 故人之心 |
| description_4 | 字符串 | 生之花描述。若套装中不存在该部位，则留空。 | 玉蓝色的小花，花茎上扎着谁人的丝带。 |
| story_4 | 字符串 | 生之花故事。若套装中不存在该部位，则留空。 | 远行而来的旅人，将这朵花佩在胸口。…… |
| name_5 | 字符串 | 时之沙名称。若套装中不存在该部位，则留空。 | 逐光之石 |
| description_5 | 字符串 | 时之沙描述。若套装中不存在该部位，则留空。 | 饱经沧桑的时晷，永远在静默地记录着日月循环。 |
| story_5 | 字符串 | 时之沙故事。若套装中不存在该部位，则留空。 | 追逐命运的旅人，也在追逐着永不停息的光阴。…… |

## 附录

### 关于任务结构与对话命名

原始数据中将句子称为“dialog”，我们的代码（和注释）中在无歧义的前提下也会使用这一概念。另外一些时候我们也会将句子称为“sentence”。

游戏中对话的最小单位为dialog，即游戏中单个对话框或单个选项容纳的内容。游戏通过为每个dialog定义若干个next dialog来将dialog连接在一起构成一个talk。talk并不一定是一段完整的对话，而可能只是对话的一部分。talk之间可能也有连接。

游戏中任务的最小单位为subquest，在本文档中也称为“子任务”，即游戏中通常所说“任务”的每个步骤。当你在游戏中完成一个步骤时，通常你会看到左上角小地图下方显示下一个步骤的标题和说明。若干个subquest构成一个quest（本文档中也称为“任务”），而若干个quest构成一个chapter。例如“浮世浮生千岩间”（魔神任务第一章第一幕）是一个chapter，“辞行久远之躯”（魔神任务第一章第二幕）是另一个chapter。在游戏的任务列表中，你可能会发现一些普通任务和一些有大标题的成组任务，这里的普通任务就是quest，大标题标识的组则是chapter。

本项目定义了source概念作为组织对话的单元。通俗地说，source就是游戏中的一段无中断对话。“无中断”是指从这个source开始到结束，玩家除了点击下一句和选择选项之外没有其它操作的机会。若用数学语言表述，source可以定义为以句子为节点的弱连通有向图，其中存在一个起点集和一个终点集，使得图中每个节点都能够从某个起点到达，且每个节点都能到达某个终点。每个source实际上是若干彼此之间有连接的talk和dialog构成的（我们会将talk拆解成dialog）。在整理数据时，我们首先按照talk和dialog之间的联系建立有向图，然后将该图中每一个弱连通分量作为一个source。

一个source所包含的dialog可能全部来自于同一个subquest，此时我们将该source命名为`subquest_<QUEST_ID>_<SUBQUEST_ID>_<INDEX>`，其中`INDEX`仅用于区别多个来自于同一subquest的source；若并非来自于同一个subquest，但来自于同一个quest，我们将其命名为`quest_<QUEST_ID>_<INDEX>`；若并非来自于同一个quest，我们则按照其构建来源是talk还是dialog命名为`talk_<TALK_ID>`或`dialog_<DIALOG_ID>`，其中的id是构成该source的所有talk或dialog id中最小的一个。


### 关于使用（近似）最少路径覆盖所有句子的算法

算法的整体思路参考了[这篇回答](https://cs.stackexchange.com/questions/107397/fewest-traversals-to-visit-all-vertices-of-dag)。算法实现在`main.py`中`Database._find_covering_traces`方法中，以下简要介绍算法原理。

设我们有一个以句子为节点的有向图，其中共有n个句子。该图有唯一的起点和终点，且每个节点都位于某条从起点到终点的路径上。这个假设不失一般性，因为对于具有多个起点或多个终点的图，我们可以建立一个“总起点”和“总终点”，并将其与所有起点/终点连接；而对于从起点无法到达的节点，我们可以将其看作一个新的起点并连接到“总起点”上。无法到达终点的节点同理。

我们可以利用NetworkX提供的函数`min_cost_flow`来解决这个问题。这一函数在输入的图中寻找最小费用的最大流，同时满足每个节点的流需求（流出节点的流量减去流入节点的流量必须等于一特定值）。如上面引用的回答所述，为了让路径数最小，我们需要让所有路径都流过某一固定的边，同时在这条边上添加费用，从而最小化路径数。由于我们不确定最终的路径数，无法确定起点和终点的流需求，因此需要添加一条从终点到起点的边，让整个图成为一个大环，从而起点和终点的流需求都可以定义为0。此时**几乎**所有流都会流经这条从终点到起点的边，不妨将该边的费用定义为n（总句子数），从而最小化路径数。将费用定义为n而非1的理由将在后文解释。

接下来我们需要保证每个节点都有流经过。为此，我们可以将每个节点v拆成两个节点v1和v2，所有原本指向v的边都指向v1，而所有原本从v出发的边都从v2出发，同时我们加入一条从v1指向v2的边。此时问题转化为每个拆开节点中间的边都必须有流经过。这一问题可以进一步转化为v1和v2的流需求：设置v1的流需求为1（流入比流出多1），v2的流需求为-1（流出比流入多1）即可。

由于句子图中可能包含环（这里并非指我们手动添加的从终点到起点的边构成的环，而是指原本就存在的环），我们在每条从v1到v2的边上都设置费用为1，从而避免算法在环上创建无用的流，同时也尽可能减少句子被重复经过的次数。由于我们设置了每条路径的费用为n，减少一条路径获得的收益足够将全图所有节点经过一次，因此不会出现“为了少经过节点导致路径更多了”的情况。

在上述配置下，算法仍然可能生成不经过“终点->起点”这条边的流。这些流存在于原图中的环内。我们对这些流量使用一种比较暴力的收集方法：检查该环是否与已有的某条路径有重叠。若有，则将这个环直接并入已有路径中，相当于原路径在此多绕了一个圈。若无，则搜索一条从起点到该环的最短路径，这条路径与环相交的第一个节点称为该环的“入口”；以环中“入口”的前一个点作为“出口”，再搜索一条从“出口”到终点的最短路径（这段路径可能仍然会经过环中某些节点）。拼接前半路径、环、后半路径以形成一条新路径加入结果中。

经过以上步骤，我们便得到了近似最少的能覆盖所有句子的路径集合。其中的“近似”发生于最后一步，即创建新路径以容纳不与已有路径相交的环的过程。理论最优的算法会创建尽可能少的路径来经过所有环，而我们使用了一种贪心但实现简便的方式。

如果有将该算法改造为非近似的方案，欢迎提出Issue或Pull Request。

### 关于文本后处理

原始数据的文本中包含大量具有程序含义的字符，通常用于改变文字颜色、根据主角性别显示不同的文本内容等。这里介绍本项目对文本采取的主要后处理步骤。

#### 特殊标记

游戏文本中包含若干特殊标记，主要用于标记该文本是否不应该出现在正式游戏中，例如文本开头出现`(test)`或文本结尾出现`$UNRELEASED`的句子。我们在输出数据中移除了这些句子所在的source。

此外，一些任务标题和描述中会出现`$HIDDEN`。这些任务在游戏中存在，但对应的标题或描述不会显示出来。我们也会将这类文本视作不存在。

#### 修饰符

游戏文本中包含一些XML标签（在对话文本中仅有`<color>`，其他文本中还可能包括`<i>`、`<size>`、`<c1>`、`<c2>`、`<c3>`、`<multi>`等），用于设置字体颜色、字号等。我们在输出数据中移除了所有XML标签。

#### 占位符

游戏文本中包含若干种占位符，我们在输出数据中已经将这些占位符移除或者替换为了合适的文本。

占位符的两端以`{}`括住，包含称呼占位符的句子以`#`开头，但其它文本并非如此。一些占位符使用`#`添加条件进行了性别区分。此外，有些占位符（包括`{QuestNpcID}`、`{QuestGatherID}`、`{QuestGatherNum}`、`{QuestNpcID2}`、`{ChallengeIndex10}`、`{ChallengeCurrValue10}`）仅用于突发任务（例如蒙德捡苹果）或挑战任务（丹迪限时挑战），我们移除了这些句子所在的source。

我们对占位符进行了以下处理：

- 当占位符为`{NICKNAME}`时，替换为玩家设置的主角名称（默认替换为`旅行者`，可通过命令行参数`--traveller_name`修改）。
- 当占位符为`{M#SOMETHING}`或`{F#SOMETHING}`时，根据主角性别决定是否输出为`SOMETHING`。若占位符首项性别与主角相符则输出`SOMETHING`，否则不输出任何内容。可通过命令行参数`--traveller_sex`设定主角性别。
- 当占位符的格式为`{MATEAVATAR#SOMETHING}`或`{PLAYERAVATAR#SOMETHING}`时（我们称为**称呼占位符**），`SOMETHING`给出了两种文本选择，需要根据`MATEAVATAR`（血亲的性别）或`PLAYERAVATAR`（主角的性别）的值选择其中一种作为输出文本。变量值为男0、女1。0值时选择第一个文本，1值时选择第二个文本。
- 一种特殊修饰符`{RUBY#[D]SOMETHING}`以占位符的格式出现，用于在文本上方显示小号文字，例如游戏中提及“虚空”时上方出现“阿卡西”。我们将以下方显示的文字为准，即将该修饰符直接删除。

根据网络上公开的剧情留档视频，下表给出了简体中文文本中所有占位符及其在游戏中实际使用的文本（在“推荐替换文本”一列）。其中仅有`SEXPRO[INFO_MALE_PRONOUN_CUTEBIGBROTHER]`由于难以找到剧情留档视频而无法准确复原文本（事实上该占位符使用次数极少）。由于作者精力所限，本项目仅支持简体中文的称呼占位符替换。

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
| SEXPRO[INFO_FEMALE_PRONOUN_GIRLF] | 女士 | 指控人{PLAYERAVATAR#SEXPRO[INFO_MALE_PRONOUN_BOYC|INFO_FEMALE_PRONOUN_GIRLF]}，我这里有份东西… | 指控人女士，我这里有份东西… |
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

## 致谢

感谢[Dimbreath](https://github.com/Dimbreath)的项目。

本项目参考了[mrzjy的项目](https://github.com/mrzjy/GenshinDialog)的部分源代码和输出结果。非常好项目，使我芙芙旋转。

