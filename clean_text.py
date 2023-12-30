import copy
import argparse
import json
import re
import tqdm

def filter_unknown_dialogs(data):
    result = {}
    filtered_number = 0
    for key in tqdm.tqdm(data):
        newTalk = []
        for trace in data[key]:
            flag = False
            for dialog in trace:
                if dialog["content"] == "`unknown`":
                    flag = True
                    break
            if not flag:
                newTalk.append(trace)
            else:
                filtered_number += 1
        if len(newTalk) > 0:
            result[key] = newTalk
    stats = {
        "filtered_number": filtered_number,
    }
    return result, stats

UNRELEASED_TAGS = [
    "unreleased",
    "(test)",
    "（test）",
    "（test)",
    "(test）",
    "( test)",
    "（ test）",
    "（ test)",
    "( test）",
    "(test )",
    "（test ）",
    "（test )",
    "(test ）",
]
def filter_unreleased_talks(data):
    result = {}
    filtered_number = 0
    for key in tqdm.tqdm(data):
        newTalk = []
        for trace in data[key]:
            newTrace = []
            for dialog in trace:
                if all([tag not in dialog["content"].lower()
                        for tag in UNRELEASED_TAGS]):
                    newTrace.append(dialog)
                else:
                    filtered_number += 1
            if len(newTrace) > 0:
                newTalk.append(newTrace)
        if len(newTalk) > 0:
            result[key] = newTalk
    stats = {
        "filtered_number": filtered_number,
    }
    return result, stats

XML_PATTERNS = [
    (re.compile(r'<color=[^>]*>'), ""),
    (re.compile(r'</color>'), ""),
]
def remove_xml_tags(data):
    result = {}
    for key in tqdm.tqdm(data):
        newTalk = []
        for trace in data[key]:
            newTrace = []
            for dialog in trace:
                content = dialog["content"]
                for pattern, output in XML_PATTERNS:
                    content = pattern.sub(output, content)
                newDialog = copy.deepcopy(dialog)
                newDialog["content"] = content
                newTrace.append(newDialog)
            newTalk.append(newTrace)
        result[key] = newTalk
    stats = {}
    return result, stats

PLACEHOLDERS = {
    "SEXPRO" : {
        "INFO_FEMALE_PRONOUN_AUNT": "阿姨",
        "INFO_MALE_PRONOUN_UNCLE": "叔叔",
        "INFO_FEMALE_PRONOUN_BIGSISTER": "大姐姐",
        "INFO_MALE_PRONOUN_BIGBROTHER": "大哥哥",
        "INFO_FEMALE_PRONOUN_BROTHER": "哥哥",
        "INFO_MALE_PRONOUN_SISTER": "妹妹",
        "INFO_FEMALE_PRONOUN_CUTEBIGSISTER": "大捷洁",
        "INFO_MALE_PRONOUN_CUTEBIGBROTHER": "大葛格（未经验证）",
        "INFO_FEMALE_PRONOUN_GIRLA": "老妹",
        "INFO_MALE_PRONOUN_BOYA": "小哥",
        "INFO_FEMALE_PRONOUN_GIRLB": "姑娘",
        "INFO_FEMALE_PRONOUN_GIRLC": "小姐",
        "INFO_MALE_PRONOUN_BOYC": "先生",
        "INFO_FEMALE_PRONOUN_GIRLD": "公主",
        "INFO_MALE_PRONOUN_BOYD": "王子",
        "INFO_FEMALE_PRONOUN_BOYD": "王子",
        "INFO_MALE_PRONOUN_GIRLD": "公主",
        "INFO_FEMALE_PRONOUN_GIRLE": "小姑娘",
        "INFO_MALE_PRONOUN_BOYE": "小伙子",
        "INFO_FEMALE_PRONOUN_GIRL": "少女",
        "INFO_MALE_PRONOUN_BOY": "少年",
        "INFO_FEMALE_PRONOUN_HEROINE": "女一号",
        "INFO_MALE_PRONOUN_HERO": "男一号",
        "INFO_FEMALE_PRONOUN_HE": "他",
        "INFO_MALE_PRONOUN_SHE": "她",
        "INFO_FEMALE_PRONOUN_KONG": "空",
        "INFO_MALE_PRONOUN_YING": "荧",
        "INFO_FEMALE_PRONOUN_SHE": "她",
        "INFO_MALE_PRONOUN_HE": "他",
        "INFO_FEMALE_PRONOUN_SISANDSIS": "两位姐姐",
        "INFO_MALE_PRONOUN_BROANDSIS": "哥哥姐姐",
        "INFO_FEMALE_PRONOUN_SISTERA": "姐姐",
        "INFO_FEMALE_PRONOUN_SISTER": "妹妹",
        "INFO_FEMALE_PRONOUN_XIAGIRL": "女侠",
        "INFO_MALE_PRONOUN_XIABOY": "少侠",
        "INFO_FEMALE_PRONOUN_YING": "荧",
        "INFO_MALE_PRONOUN_BROTHER": "哥哥",
        "INFO_MALE_PRONOUN_Twins2Male": "这也是我妹妹头上的花。",
        "INFO_FEMALE_PRONOUN_Twins2Female": "这种花自我苏醒便戴在我的头上。",
    }
}
PLACEHOLDER_PATTERN = re.compile(r'\{([^}]*)\}')
RUBY_PATTERN = re.compile(r'\{RUBY#\[D\]([^}]*)\}')
QUEST_PLACEHOLDER_PATTERNS = [
    "{QuestNpcID}",
    "{QuestGatherID}",
    "{QuestGatherNum}",
    "{QuestNpcID2}",
    "{ChallengeIndex10}",
    "{ChallengeCurrValue10}",
]
def replace_placeholders(data, traveller_sex, traveller_name, wanderer_name):
    result = {}
    sex = {
        "PLAYERAVATAR": int(traveller_sex == "female"),
        "MATEAVATAR": int(traveller_sex == "male"),
    }
    num_placeholders = 0
    for key in tqdm.tqdm(data):
        newTalk = []
        for trace in data[key]:
            newTrace = []
            quest_flag = False
            for dialog in trace:
                content = dialog["content"]
                for quest_placeholder in QUEST_PLACEHOLDER_PATTERNS:
                    if quest_placeholder in content:
                        quest_flag = True
                        break
                if quest_flag:
                    break
                newDialog = copy.deepcopy(dialog)
                if content.startswith("#"):
                    for placeholder in PLACEHOLDER_PATTERN.findall(content):
                        num_placeholders += 1
                        if "#" in placeholder:
                            first, second = placeholder.split("#")
                            if first in ["PLAYERAVATAR", "MATEAVATAR"]:
                                assert second.endswith("]"), second
                                category, choices_str = second[:-1].split("[")
                                output = [PLACEHOLDERS[category][choice]
                                          for choice in \
                                          choices_str.split("|")][sex[first]]
                            elif (first == "M" and traveller_sex == "male") or \
                               (first == "F" and traveller_sex == "female"):
                                output = second
                            else:
                                assert first in ["M", "F"], first
                                output = ""
                        elif placeholder in ["REALNAME[ID(1)|HOSTONLY(true)]",
                                             "REALNAME[ID(1)]"]: # Wanderer
                            output = wanderer_name
                        else:
                            assert placeholder == "NICKNAME", content
                            output = traveller_name
                        content = content.replace("{" + placeholder + "}",
                                                  output)
                    content = content[1:] # Remove '#' at the beginning
                for match in RUBY_PATTERN.findall(content):
                    num_placeholders += 1
                    content = content.replace("{RUBY#[D]" + match + "}", "")
                newDialog = copy.deepcopy(dialog)
                newDialog["content"] = content
                newTrace.append(newDialog)
            if not quest_flag:
                newTalk.append(newTrace)
        result[key] = newTalk
    stats = {
        "num_placeholders": num_placeholders,
    }
    return result, stats

def filter_empty_traces(data):
    result = {}
    filtered_number = 0
    for key in tqdm.tqdm(data):
        newTalk = []
        for trace in data[key]:
            newTrace = []
            for dialog in trace:
                if len(dialog["content"]) > 0:
                    newTrace.append(dialog)
            if len(newTrace) > 0:
                newTalk.append(newTrace)
            else:
                filtered_number += 1
        if len(newTalk) > 0:
            result[key] = newTalk
    stats = {
        "filtered_number": filtered_number,
    }
    return result, stats

def replace_character_names(data, traveller_name, mate_name, wanderer_name,
                            system_name, narrator_name, unknown_name):
    result = {}
    for key in tqdm.tqdm(data):
        newTalk = []
        for trace in data[key]:
            newTrace = []
            for dialog in trace:
                if dialog["roleName"] == "`system`":
                    newDialog = copy.deepcopy(dialog)
                    newDialog["roleName"] = system_name
                elif dialog["role"] == 0:
                    newDialog = copy.deepcopy(dialog)
                    newDialog["roleName"] = traveller_name
                elif dialog["role"] == -1 or dialog["roleName"] == "`unknown`":
                    newDialog = copy.deepcopy(dialog)
                    newDialog["roleName"] = unknown_name
                elif dialog["role"] == -2:
                    newDialog = copy.deepcopy(dialog)
                    newDialog["roleName"] = narrator_name
                elif dialog["role"] == -3:
                    newDialog = copy.deepcopy(dialog)
                    newDialog["roleName"] = mate_name
                elif dialog["role"] in [12947, 1065, 9075, 9547,]:
                    newDialog = copy.deepcopy(dialog)
                    newDialog["roleName"] = wanderer_name
                else:
                    newDialog = dialog
                newTrace.append(newDialog)
            newTalk.append(newTrace)
        result[key] = newTalk
    stats = {}
    return result, stats

def replace_newline_characters(data):
    result = {}
    for key in tqdm.tqdm(data):
        newTalk = []
        for trace in data[key]:
            newTrace = []
            for dialog in trace:
                newDialog = copy.deepcopy(dialog)
                newDialog["content"] = dialog["content"].replace('\\n', "\n")
                newTrace.append(newDialog)
            newTalk.append(newTrace)
        result[key] = newTalk
    stats = {}
    return result, stats

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_file",
        type=str,
    )
    parser.add_argument(
        "output_file",
        type=str,
    )
    parser.add_argument(
        "--traveller_sex",
        choices=["male", "female"],
        default="female",
    )
    parser.add_argument(
        "--traveller_name",
        type=str,
        default="旅行者",
    )
    parser.add_argument(
        "--mate_name",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--wanderer_name",
        type=str,
        default="流浪者",
    )
    parser.add_argument(
        "--system_name",
        type=str,
        default="ADMIN",
    )
    parser.add_argument(
        "--narrator_name",
        type=str,
        default="旁白",
    )
    parser.add_argument(
        "--unknown_name",
        type=str,
        default="未知",
    )
    parser.add_argument(
        "--not_replace_newline",
        action="store_true",
    )
    args = parser.parse_args()

    if args.mate_name is None:
        args.mate_name = "空" if args.traveller_sex == "female" else "荧"

    with open(args.input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f'Filtering talks containing unknown content.')
    data, stats = filter_unknown_dialogs(data)
    print(f'Filtered {stats["filtered_number"]} traces containing unknown '
          'content.')

    print(f'Filtering dialogs containing UNRELEASED or test tags.')
    data, stats = filter_unreleased_talks(data)
    print(f'Filtered {stats["filtered_number"]} dialogs containing UNRELEASED '
          'or test tags.')

    print(f'Removing XML tags.')
    data, stats = remove_xml_tags(data)
    print(f'Removed XML tags.')

    print(f'Replacing placeholders.')
    data, stats = replace_placeholders(data, args.traveller_sex,
                                       args.traveller_name, args.wanderer_name)
    print(f'Replaced {stats["num_placeholders"]} placeholders.')

    print(f'Filtering empty traces.')
    data, stats = filter_empty_traces(data)
    print(f'Filtered {stats["filtered_number"]} empty traces.')

    print(f'Replacing characters\' names.')
    data, stats = replace_character_names(
        data, args.traveller_name, args.mate_name, args.wanderer_name,
        args.system_name, args.narrator_name, args.unknown_name,
    )
    print(f'Replaced characters\' names.')

    if not args.not_replace_newline:
        print(f'Replacing newline characters.')
        data, stats = replace_newline_characters(data)
        print(f'Replaced newline characters.')

    print("Saving to json...")
    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, sort_keys=True, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()

