from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
import os
import sys
import re
import argparse
import json
import logging
import bisect

import tqdm
import pandas as pd
import networkx as nx


logging.basicConfig(
    level="INFO",
    format=f"[{os.uname()[1].split('.')[0]}]"
           f" %(asctime)s (%(module)s:%(lineno)d) %(levelname)s: %(message)s",
)


# Some talks are just for testing purpose. They should not be included in the
# output.
TALK_ID_BLACKLIST = [
    3,
]

# Finishing conditions of subquests that are related to talks.
FINISH_COND_TALK = [
    "QUEST_CONTENT_COMPLETE_TALK",
    "QUEST_CONTENT_COMPLETE_ANY_TALK",
]

# Reliquary types.
RELIQUARY_TYPE_MAP = {
    "EQUIP_RING": 1,
    "EQUIP_NECKLACE": 2,
    "EQUIP_DRESS": 3,
    "EQUIP_BRACER": 4,
    "EQUIP_SHOES": 5,
}

# Texts containing these tags are not released in the game.
# Note that these tags are collected artificially. We have only done works on
# the simplified Chinese texts. Tags for other languages are absent for now.
UNRELEASED_TAGS = {
    "CHS": [
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
        "（废弃）",
        "(废弃）",
        "（废弃)",
        "(废弃)",
        "此道具废弃",
    ],
}

# These tags appear in subquest descriptions. Subquests containing these tags
# may be skipped if the conditions are already satisfied.
# We should remove these tags from the descriptions.
# Note that these tags are collected artificially. We have only done works on
# the simplified Chinese texts. Tags for other languages are absent for now.
SKIP_TAGS = {
    "CHS": [
        "(跳过)",
    ],
}

# Texts containing these tags are considered as non-existing.
HIDDEN_TAGS = [
    "$HIDDEN",
]

# Some XML tags in the texts.
XML_PATTERNS = [
    (re.compile(r'<color=[^>]*>'), ""),
    (re.compile(r'</color>'), ""),
]

# Placeholders.
# Note that these replacements are collected artificially. We have only done
# works on the simplified Chinese texts. Tags for other languages are absent for
# now.
PLACEHOLDERS = {
    "CHS": {
        "SEXPRO": {
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
            "INFO_FEMALE_PRONOUN_GIRLF": "女士",
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
            "INFO_FEMALE_PRONOUN_Twins2Female":
                "这种花自我苏醒便戴在我的头上。",
        },
    },
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

# In simplified Chinese, the quotes could be replaced by a more usual version.
QUOTE_MAPPINGS = {
    "CHS": {
        "「": "“",
        "」": "”",
        "『": "‘",
        "』": "’",
    }
}

# Special npc ids and avatar ids.
NPC_ID_AETHER = 1025
NPC_ID_LUMINE = 1026
AVATAR_ID_AETHER = 10000005
AVATAR_ID_LUMINE = 10000007
AVATAR_ID_FISCHL = 10000031
AVATAR_ID_BAIZHU = 10000082

# Avatars for testing purpose. They are not released in the game.
AVATAR_ID_BLACKLIST = [10000001]

# Possible characters to appear in the voice texts.
# For now only simplified Chinese is supported.
NAMES_IN_VOICE_TEXT = {
    "CHS": ["{NICKNAME}", "派蒙", "菲谢尔", "奥兹", "白术","长生"],
}

@dataclass(eq=False)
class Talk:
    """
    For convenience of comparing talks from different sources.
    """
    id: int
    source: str  # Only used in logging.
    npc_id: List[int]  # Maybe empty.
    init_dialog: int  # -1 means not specified, so we read the dialog in the
                      # order of the dialogList.
    next_talks: List[int]  # Maybe empty.
    prev_talks: List[int]  # Maybe empty.
    begin_cond_comb: bool  # True for AND, False for OR.
    begin_cond: List[Tuple[int, str]]  # The talk will only be triggered after
                                       # these conditions are satisfied.
                                       # The tuple stores (subquest_id, cond)
                                       # where the cond value represents:
                                       # 2: in progress
                                       # 3: finished
                                       # 4: failed
                                       # There are also other values in the
                                       # original data, but we do not care about
                                       # them.
    trusted: bool  # If False, it won't corrupt with the same Talk from another
                   # source.

    def __eq__(self, __value: object) -> bool:
        # We do not check prev_talks since it is set after all talks are read.
        return isinstance(__value, Talk) and \
               self.id == __value.id and \
               self.npc_id == __value.npc_id and \
               self.next_talks == __value.next_talks and \
               self.init_dialog == __value.init_dialog and \
               self.begin_cond_comb == __value.begin_cond_comb and \
               self.begin_cond == __value.begin_cond


@dataclass(eq=False)
class Dialog:
    """
    For convenience of comparing dialogs from different sources.
    """
    id: int
    talk_id: int  # -1 means this dialog comes from a quest or the talkId is
                  # missing.
    role: int  # 0 represents player.
               # -1 means the role field is invalid in the data.
               # -2 represents the narrator.
               # -3 represents the mate avatar.
    source: str  # Only used in logging.
    talk_content_text_map_hash: int  # -1 means the field is missing.
    talk_role_name_text_map_hash: int  # -1 means not existing.
    next_dialogs: List[int]  # Maybe empty.
    trusted: bool  # If False, it won't corrupt with the same Dialog from
                   # another source.

    def __eq__(self, __value: object) -> bool:
        # We do not check talkId since there is confliction in the original data
        # and it does not mean a lot to us.
        return isinstance(__value, Dialog) and \
               self.id == __value.id and \
               self.role == __value.role and \
               self.talk_content_text_map_hash == \
                    __value.talk_content_text_map_hash and \
               self.talk_role_name_text_map_hash == \
                    __value.talk_role_name_text_map_hash and \
               self.next_dialogs == __value.next_dialogs

    def update(self, item: "Dialog") -> bool:
        """
        Merge two dialogs of the same id from different sources.
        """
        assert self.id == item.id, str(self) + ", " + str(item)
        # We do not check talkId since there is confliction in the original data
        # and it does not mean a lot to us.
        if item.talk_id >= 0:
            if self.talk_id >= 0 and item.talk_id != self.talk_id:
                pass
                #return False
            self.talk_id = item.talk_id
        # We always update role since there is confliction in the original data.
        if item.role >= 0:
            #if self.role >= 0 and item.role != self.role:
            #    return False
            self.role = item.role
        if item.talk_role_name_text_map_hash >= 0:
            if (
                self.talk_role_name_text_map_hash >= 0 and
                item.talk_role_name_text_map_hash
                    != self.talk_role_name_text_map_hash
            ):
                return False
            self.talk_role_name_text_map_hash = \
                    item.talk_role_name_text_map_hash
        self.next_dialogs = sorted(
                list(set(self.next_dialogs) | set(item.next_dialogs)))
        self.source = item.source + ":" + self.source
        return True

    def __str__(self):
        return f'id: {self.id}, ' \
               f'talkId: {self.talk_id}, ' \
               f'role: {self.role}, ' \
               f'talk_content_text_map_hash: ' \
               f'{self.talk_content_text_map_hash}, ' \
               f'talk_role_name_text_map_hash: ' \
               f'{self.talk_role_name_text_map_hash}, ' \
               f'next_dialogs: {self.next_dialogs}'


@dataclass
class SubQuest:
    id: int  # Sub quest id.
    order: int  # Order in this quest.
    desc_text_map_hash: int  # Description of the sub quest. -1 means not
                             # presented.
    step_desc_text_map_hash: int  # -1 means not presented.
    talk_ids: List[int]  # List of talk ids. Finishing any talks in this will
                         # complete the sub quest. -1 means any talks
                         # (finishCond == "QUEST_CONTENT_COMPLETE_ANY_TALK").
                         # An empty list indicates that this subquest is not
                         # related to talks.


@dataclass
class Quest:
    id: int
    type: str  # AQ: archon quest
               # EQ: event quest
               # IQ: intrust quest
               # LQ: legend quest
               # WQ: world quest
    title_text_map_hash: int  # -1 means not presented.
    desc_text_map_hash: int  # -1 means not presented.
    suggest_track_main_quest_list: List[int]
    chapter_id: int  # -1 means not presented.
    sub_quests: List[int]  # Sub quest ids. May be empty.
                           # Only sub quests with finishCond ==
                           # "QUEST_CONTENT_COMPLETE_TALK" or
                           # "QUEST_CONTENT_COMPLETE_ANY_TALK" will be
                           # collected here.
    talks: List[int]  # List of talk ids this quest contains.
    next_quests: List[int]  # According to suggest_track_main_quest_list, the
                            # possible successors of this quest.
    prev_quests: List[int]  # The inverse of next_quests.


@dataclass
class Chapter:
    id: int
    group_id: int  # Chapters are grouped. May be -1.
    begin_quest_id: int  # Starting subquest id. In the game, the chapter
                         # beginning UI is shown when this quest finishes. May
                         # be -1.
    end_quest_id: int  # Ending subquest id. In the game, the chapter ending UI
                       # is shown when this quest finishes. May be -1.
    chapter_num_text_map_hash: int  # Chapter number text. -1 means absent.
    chapter_title_text_map_hash: int  # Chapter title.
    chapter_image_title_text_map_hash: int  # Chapter image title.
    quest_type: str  # Same as Quest's types. i.e. AQ, EQ, IQ, LQ or WQ.
    quests: List[int]  # All quest ids of this chapter.


@dataclass
class Avatar:
    id: int
    name_text_map_hash: int  # Avatar name.
    desc_text_map_hash: int  # Avatar description.
    # The below hashes may be -1, which means not presented.
    info_birth_month: int  # Birthday month.
    info_birth_day: int  # Birthday day.
    native_text_map_hash: int  # Affiliation.
    vision_befor_text_map_hash: int  # Vision.
    vision_after_text_map_hash: int  # Vision.
    vision_name_befor_text_map_hash: int  # Vision name.
    vision_name_after_text_map_hash: int  # Vision name.
    constellation_befor_text_map_hash: int  # Constellation.
    constellation_after_text_map_hash: int  # Constellation.
    title_text_map_hash: int  # Title.
    detail_text_map_hash: int  # Avatar detail.
    assoc_type: Optional[str]  # Association. May be None.
                            # Possible values: "ASSOC_TYPE_MAINACTOR",
                            # "ASSOC_TYPE_MONDSTADT", "ASSOC_TYPE_LIYUE",
                            # "ASSOC_TYPE_INAZUMA", "ASSOC_TYPE_SUMERU",
                            # "ASSOC_TYPE_FONTAINE", "ASSOC_TYPE_FATUI",
                            # "ASSOC_TYPE_RANGER", where "RANGER" is for Aloy.
    voice_texts: List[Tuple[int, int, int]]  # Texts from avatar voice list.
                                             # Tuple structure:
                                             # (type, title, content).
                                             # Type 1: Chat
                                             # Type 2: Battle
    stories: List[Tuple[int, int]]  # Avatar's stories.
                                    # Tuple structure: (title, content).


@dataclass
class Item:
    id: int
    name_text_map_hash: int  # Item name.
    desc1_text_map_hash: int  # Item description.
    desc2_text_map_hash: int  # An alternative item description.


@dataclass
class Weapon:
    id: int
    type: str  # Weapon type. Possible values: WEAPON_BOW, WEAPON_CATALYST,
               # WEAPON_CLAYMORE, WEAPON_POLE, WEAPON_SWORD_ONE_HAND.
    rank_level: int  # 1~5 stars.  -1 means not existing.
    name_text_map_hash: int  # Weapon name.
    desc_text_map_hash: int  # Weapon description.


@dataclass
class ReliquarySet:
    id: int
    set_name_text_map_hash: int  # Reliquary set name.
    name_text_map_hashs: List[Optional[int]]  # Reliquary names. None means the
                                              # corresponding part does not
                                              # exist.
    desc_text_map_hashs: List[Optional[int]]  # Reliquary descriptions. None
                                              # means the corresponding part
                                              # does not exist.


@dataclass
class Source:
    """
    'Source' is a concept defined by our project. A source is a set of dialogs
    that have connections among them. In the game, a source contains the dialogs
    between two user-controllable states.
    """
    name: str
    order: int  # Order in the original quest. Two sources with the same order
                # are branches of the story.
                # `order` may be not consecutive.
                # -1 means that this source does not belongs to any quest, or
                # this source is not a necessary part in the quest.
    quest_id: int  # Id of the original quest. -1 means not belonging to any.
    subquest_id: int  # Id of the original subquest. Ditto for -1.
    talk_ids: Optional[Set[int]]  # Talks belonging to this source. None means
                                  # this source is built from dialogs rather
                                  # than talks.
    dialog_ids: Set[int]  # Dialogs belonging to this source.
    traces: List[List[int]]  # List of traces. Each trace is a list of dialog
                             # ids representing a possible dialog path through
                             # the story lines.
                             # We do not iterate all possible traces and store
                             # them here. Instead, we design an algorithm to
                             # find a minimum number of traces that can cover
                             # all the dialogs in this source.
    next_sources: List[str]  # Sources taking place after the current source.
    next_sources_optional: List[str]  # Ditto, but are triggered optionally.
    prev_sources: List[str]  # Sources taking place before the current source.
    prev_sources_optional: List[str]  # Ditto, but are triggered optionally.


class Database:
    talk_dict: Dict[int, Talk] = {}
    dialog_dict: Dict[int, Dialog] = {}
    quest_dict: Dict[int, Quest] = {}
    subquest_dict: Dict[int, SubQuest] = {}
    chapter_dict: Dict[int, Chapter] = {}
    avatar_dict: Dict[int, Avatar] = {}
    item_dict: Dict[int, Item] = {}
    weapon_dict: Dict[int, Weapon] = {}
    reliquary_set_dict: Dict[int, ReliquarySet] = {}
    source_dict: Dict[str, Source] = {}
    npc_name_map: Dict[int, str] = {}
    text_map: Dict[int, str] = {}
    readable_dict: Dict[str, str] = {}

    talk2quest: Dict[int, int] = {}
    talk2subquest: Dict[int, int] = {}
    subquest2quest: Dict[int, int] = {}
    quest2sources: Dict[int, List[str]] = {}
    subquest2sources: Dict[int, List[str]] = {}

    def add_talk(self, item, path):
        if "id" not in item:
            # Deal with some special cases. These may be different for every
            # version of game data.
            if "JOLEJEFDNJJ" in item:
                item["id"] = item["JOLEJEFDNJJ"]
                item["initDialog"] = item["FBALOFKGJKN"]
                item["trusted"] = False
            elif "CCFPGAKINNB" in item:
                item["id"] = item["CCFPGAKINNB"]
                if "FMFFELFBBJN" not in item and "initDialog" not in item:
                    # Talks without initDialog are useless.
                    return
                item["initDialog"] = item["FMFFELFBBJN"]
                if "JDOFKFPHIDC" in item and "npcId" not in item:
                    item["npcId"] = item["JDOFKFPHIDC"]
                if "EECDLICEMBF" in item and "nextTalks" not in item:
                    item["nextTalks"] = item["EECDLICEMBF"]
                if "KHBAFFEPLFB" in item and "beginCondComb" not in item:
                    item["beginCondComb"] = item["KHBAFFEPLFB"]
                if "AFNAENENCBB" in item and "beginCond" not in item:
                    item["beginCond"] = item["AFNAENENCBB"]
                    for subitem in item["beginCond"]:
                        if "_type" in subitem:
                            subitem["type"] = subitem["_type"]
                        if "_param" in subitem:
                            subitem["param"] = subitem["_param"]
                item["trusted"] = False
            else:
                # Cannot resolve.
                logging.error(f'Key "id" not exists in some item of {path} . '
                              f'Item detail:\n{str(item)}')
                exit(1)
        talk_id = item["id"]
        if talk_id in TALK_ID_BLACKLIST:
            return
        # Add talk to the talk_dict.
        begin_cond_comb = (
            "beginCondComb" in item and item["beginCondComb"] == "LOGIC_AND"
        )
        begin_cond = []
        for subitem in item.get("beginCond", []):
            if (
                subitem.get("type", None) == "QUEST_COND_STATE_EQUAL" and
                "param" in subitem and
                len(subitem["param"]) >= 2 and
                subitem["param"][0].isdigit() and
                subitem["param"][1] in ["2", "3"]  # We only count these values.
            ):
                begin_cond.append((int(subitem["param"][0]),
                                   subitem["param"][1]))
        talk_item = Talk(
            id=item["id"],
            source=path,
            npc_id=item.get("npcId", []),
            init_dialog=item.get("initDialog", -1),
            next_talks=item.get("nextTalks", []),
            prev_talks=[],
            begin_cond_comb=begin_cond_comb,
            begin_cond=begin_cond,
            trusted=item.get("trusted", True),
        )
        if talk_id not in self.talk_dict:
            self.talk_dict[talk_id] = talk_item
        else:
            # There is a talk with the same id. Determine whether to replace it.
            if not talk_item == self.talk_dict[talk_id] and talk_item.trusted:
                if self.talk_dict[talk_id].trusted:
                    logging.error(f'Talk {talk_id} differs between {path} and '
                                  f'{self.talk_dict[talk_id].source}')
                    exit(1)
                else:
                    self.talk_dict[talk_id] = talk_item

    def add_dialog(self, item, talk_id, path):
        # In DialogExcelConfigData.json, "GFLDJMJKIKE" is the id field.
        if "id" not in item and "GFLDJMJKIKE" not in item:
            # Deal with some special cases. These may be different for every
            # version of game data.
            if "CCFPGAKINNB" in item:
                item["id"] = item["CCFPGAKINNB"]
                if "FNNPCGIAELE" in item:
                    item["nextDialogs"] = item["FNNPCGIAELE"]
                if "HJLEMJIGNFE" in item:
                    item["talkRole"] = item["HJLEMJIGNFE"]
                    if "_type" in item["talkRole"]:
                        item["talkRole"]["type"] = item["talkRole"]["_type"]
                    if "_id" in item["talkRole"]:
                        item["talkRole"]["id"] = item["talkRole"]["_id"]
                if "BDOKCLNNDGN" in item:
                    item["talkContentTextMapHash"] = item["BDOKCLNNDGN"]
                item["trusted"] = False
            elif "JOLEJEFDNJJ" in item:
                item["id"] = item["JOLEJEFDNJJ"]
                if "CLMNEDLMAJL" in item:
                    item["nextDialogs"] = item["CLMNEDLMAJL"]
                if "IFAOOKCBDGD" in item:
                    item["talkRole"] = item["IFAOOKCBDGD"]
                    if "_type" in item["talkRole"]:
                        item["talkRole"]["type"] = item["talkRole"]["_type"]
                    if "_id" in item["talkRole"]:
                        item["talkRole"]["id"] = item["talkRole"]["_id"]
                if "EMKCOIBADBJ" in item:
                    item["talkContentTextMapHash"] = item["EMKCOIBADBJ"]
                if "EIKACHBNBMJ" in item:
                    item["talkRoleNameTextMapHash"] = item["EIKACHBNBMJ"]
                item["trusted"] = False
            else:
                logging.error(f'Key "id" not exists in some item of {path} . '
                              f'Item detail:\n{str(item)}')
                exit(1)
        elif "GFLDJMJKIKE" in item:
            item["id"] = item["GFLDJMJKIKE"]
        if "talkRole" not in item:
            logging.error(f'Invalid dialog {item["id"]} in {path}')
            exit(1)
        # Add dialog to the dialog_dict.
        dialog_id = item["id"]
        if (
            "talkShowType" in item and
            item["talkShowType"] == "TALK_SHOW_FORCE_SELECT"
        ):
            role = 0
        elif (
            "talkRole" not in item or
            "type" not in item["talkRole"] or
            "id" not in item["talkRole"] or (
                item["talkRole"]["type"] in ["TALK_ROLE_NPC",
                                             "TALK_ROLE_GADGET"] and
                not item["talkRole"]["id"].isnumeric()
            )
        ):
            role = -1
        else:
            role = (
                0 if item["talkRole"]["type"] == "TALK_ROLE_PLAYER" else
                -2 if item["talkRole"]["type"] in [
                    "TALK_ROLE_BLACK_SCREEN",
                    "TALK_ROLE_NEED_CLICK_BLACK_SCREEN",
                    "TALK_ROLE_CONSEQUENT_BLACK_SCREEN",
                    "TALK_ROLE_CONSEQUENT_NEED_CLICK_BLACK_SCREEN",
                ] else
                -3 if item["talkRole"]["type"] == "TALK_ROLE_MATE_AVATAR" else
                int(item["talkRole"]["id"])
            )
        dialog_item = Dialog(
            id=item["id"],
            talk_id=talk_id,
            role=role,
            source=path,
            talk_content_text_map_hash=item.get("talkContentTextMapHash", -1),
            talk_role_name_text_map_hash=
                item.get("talkRoleNameTextMapHash", -1),
            next_dialogs=item.get("nextDialogs", []),
            trusted=item.get("trusted", True),
        )
        if dialog_item.id in dialog_item.next_dialogs:
            dialog_item.next_dialogs.remove(dialog_item.id)  # remove self-loop
        if dialog_id not in self.dialog_dict:
            self.dialog_dict[dialog_id] = dialog_item
        else:
            # There is a dialog with the same id. Try to merge them or to
            # replace it.
            if (
                not dialog_item == self.dialog_dict[dialog_id] and
                dialog_item.trusted
            ):
                if self.dialog_dict[dialog_id].trusted:
                    # Try to merge them.
                    if not self.dialog_dict[dialog_id].update(dialog_item):
                        logging.error(
                            f'Dialog {dialog_id} differs between {path} and '
                            f'{self.dialog_dict[dialog_id].source} :\n'
                            f'{self.dialog_dict[dialog_id]}\n{dialog_item}'
                        )
                        exit(1)
                else:
                    self.dialog_dict[dialog_id] = dialog_item

    def add_quest(self, data, path):
        if "id" not in data:
            # Deal with some special cases. These may be different for every
            # version of game data.
            def update(item, real_key, obfused_key, default=None):
                if real_key not in item:
                    if obfused_key not in item:
                        if default is None:
                            return False
                        item[real_key] = default
                    else:
                        item[real_key] = item[obfused_key]
                return True
            if "CCFPGAKINNB" in data:
                data["id"] = data["CCFPGAKINNB"]
                update(data, "type", "JNMCHAGDLOL")
                update(data, "titleTextMapHash", "HLAINHJACPJ")
                update(data, "descTextMapHash", "CJBHOPEAEPN")
                update(data, "chapterId", "FLCLAPBOOHF")
                update(data, "subQuests", "POJOCEPJPAL")
                for item in data["subQuests"]:
                    update(item, "subId", "OHGOECEBPJM")
                    update(item, "order", "NKCPJODPKPO")
                    update(item, "descTextMapHash", "CJBHOPEAEPN")
                    update(item, "finishCond", "AODHOADLAJC")
                    for cond_item in item["finishCond"]:
                        update(cond_item, "type", "JNMCHAGDLOL")
                        update(cond_item, "param", "OBKNOBNIEGC")
                update(data, "talks", "PCNNNPLAEAI")
        if "suggestTrackMainQuestList" not in data:
            data["suggestTrackMainQuestList"] = []
        talks = []
        if "talks" in data:
            for item in data["talks"]:
                self.add_talk(item, path)
                talks.append(item["id"])
        subquest_ids = []
        if "subQuests" in data:
            for item in data["subQuests"]:
                # Finishing any talks in this list will complete the sub quest.
                talk_ids = []
                for cond_item in item.get("finishCond", []):
                    if cond_item["type"] == "QUEST_CONTENT_COMPLETE_TALK":
                        talk_ids.append(cond_item["param"][0])  # The talk id.
                    elif cond_item["type"] == "QUEST_CONTENT_COMPLETE_ANY_TALK":
                        talk_ids.append(-1)
                subquest_item = SubQuest(
                    id=item["subId"],
                    order=item["order"],
                    desc_text_map_hash=item.get("descTextMapHash", -1),
                    step_desc_text_map_hash=item.get("stepDescTextMapHash", -1),
                    talk_ids=talk_ids,
                )
                self.subquest_dict[item["subId"]] = subquest_item
                subquest_ids.append(item["subId"])
        quest_item = Quest(
            id=data["id"],
            # If type not presented, it is an archon quest.
            type=data.get("type", "AQ"),
            title_text_map_hash=data.get("titleTextMapHash", -1),
            desc_text_map_hash=data.get("descTextMapHash", -1),
            suggest_track_main_quest_list=data["suggestTrackMainQuestList"],
            chapter_id=data.get("chapterId", -1),
            sub_quests=subquest_ids,
            talks=talks,
            next_quests=[],  # Fill it later.
            prev_quests=[],  # Ditto.
        )
        self.quest_dict[data["id"]] = quest_item

    def add_chapter(self, item):
        assert len(self.quest_dict) > 0, \
            "This step should be run after quests being collected."
        assert len(self.subquest_dict) > 0, \
            "This step should be run after subquests being collected."
        if "beginQuestId" in item:
            assert item["beginQuestId"] in self.subquest_dict, item["id"]
        if "endQuestId" in item:
            assert item["endQuestId"] in self.subquest_dict, item["id"]
        quests = [
            quest_id for quest_id, quest in self.quest_dict.items()
            if quest.chapter_id == item["id"]
        ]
        chapter_item = Chapter(
            id=item["id"],
            group_id=item.get("groupId", -1),
            begin_quest_id=item.get("beginQuestId", -1),
            end_quest_id=item.get("endQuestId", -1),
            chapter_num_text_map_hash=item["chapterNumTextMapHash"],
            chapter_title_text_map_hash=item["chapterTitleTextMapHash"],
            chapter_image_title_text_map_hash=
                item["chapterImageTitleTextMapHash"],
            # If type not presented, it is an archon quest.
            quest_type=item.get("questType", "AQ"),
            quests=quests,
        )
        self.chapter_dict[item["id"]] = chapter_item

    def collect_avatar_info(self, avatar_info, fetter_info, fetters,
                            fetter_story):
        """
        Collect avatars' information.
        Thanks to [mrzjy's work](https://github.com/mrzjy/GenshinDialog).
        """
        avatar_temp_dict = {}

        for info in avatar_info:
            avatar_id = info["id"]
            avatar_name = info["nameTextMapHash"]
            avatar_desc = info["descTextMapHash"]
            avatar_temp_dict[avatar_id] = {
                "name": avatar_name,
                "desc": avatar_desc,
                "infoBirthMonth": -1,
                "infoBirthDay": -1,
                "avatarNative": -1,
                "avatarVisionBefor": -1,
                "avatarVisionAfter": -1,
                "avatarVisionNameBefor": -1,
                "avatarVisionNameAfter": -1,
                "avatarConstellationBefor": -1,
                "avatarConstellationAfter": -1,
                "avatarTitle": -1,
                "avatarDetail": -1,
                "avatarAssocType": None,
                "voice_texts": [],
                "stories": [],
            }

        for info in fetter_info:
            avatar_id = info["avatarId"]
            if avatar_id not in avatar_info:
                continue
            avatar_temp_dict[avatar_id]["avatarAssocType"] = \
                info["avatarAssocType"]
            for field, value in info.items():
                if "TextMapHash" in field or "Birth" in field:
                    field = field.replace("TextMapHash", "")
                    avatar_temp_dict[avatar_id][field] = value
            avatar_temp_dict[avatar_id]["avatarVisionNameBefor"] = \
                info["AMOCIMEIEOG"]
            avatar_temp_dict[avatar_id]["avatarVisionNameAfter"] = \
                info["DOEBOFLEBLL"]

        for info in fetters:
            avatar_id = info["avatarId"]
            avatar_temp_dict[avatar_id]["voice_texts"].append((
                info["type"],
                info["voiceTitleTextMapHash"],
                info["voiceFileTextTextMapHash"],
            ))

        for info in fetter_story:
            avatar_id = info["avatarId"]
            avatar_temp_dict[avatar_id]["stories"].append((
                info["storyTitleTextMapHash"],
                info["storyContextTextMapHash"],
            ))

        for avatar_id, info in avatar_temp_dict.items():
            assert "infoBirthMonth" in info, avatar_id
            self.avatar_dict[avatar_id] = Avatar(
                id=avatar_id,
                name_text_map_hash=info["name"],
                desc_text_map_hash=info["desc"],
                info_birth_month=info["infoBirthMonth"],
                info_birth_day=info["infoBirthDay"],
                native_text_map_hash=info["avatarNative"],
                vision_befor_text_map_hash=info["avatarVisionBefor"],
                vision_after_text_map_hash=info["avatarVisionAfter"],
                vision_name_befor_text_map_hash=info["avatarVisionNameBefor"],
                vision_name_after_text_map_hash=info["avatarVisionNameAfter"],
                constellation_befor_text_map_hash=\
                    info["avatarConstellationBefor"],
                constellation_after_text_map_hash=\
                    info["avatarConstellationAfter"],
                title_text_map_hash=info["avatarTitle"],
                detail_text_map_hash=info["avatarDetail"],
                assoc_type=info["avatarAssocType"],
                voice_texts=info["voice_texts"],
                stories=info["stories"],
            )

    def collect_item_info(self, material_info, material_codex):
        name_dict = {}  # key: id, value: name_hash
        desc1_dict = {}  # key: id, value: description_hash
        desc2_dict = {}  # key: id, value: description_hash
        for item in material_info:
            if "id" not in item:
                continue
            name_dict[item["id"]] = item.get("nameTextMapHash", -1)
            desc1_dict[item["id"]] = item.get("descTextMapHash", -1)
        for item in material_codex:
            if "materialId" not in item:
                continue
            desc2_dict[item["materialId"]] = item.get("descTextMapHash", -1)
        for item_id in sorted(set(name_dict.keys() | desc2_dict.keys())):
            self.item_dict[item_id] = Item(
                id=item_id,
                name_text_map_hash=name_dict.get(item_id, -1),
                desc1_text_map_hash=desc1_dict.get(item_id, -1),
                desc2_text_map_hash=desc2_dict.get(item_id, -1),
            )

    def collect_weapon_info(self, weapon_info):
        for item in weapon_info:
            assert "rankLevel" in item and 1 <= item["rankLevel"] <= 5
            self.weapon_dict[item["id"]] = Weapon(
                id=item["id"],
                type=item["weaponType"],
                rank_level=item["rankLevel"],
                name_text_map_hash=item["nameTextMapHash"],
                desc_text_map_hash=item["descTextMapHash"],
            )

    def collect_reliquary_info(
        self, reliquary_info, reliquary_set_info, equip_affix_info,
    ):
        attr_map = {}  # key: id, value: (type, name hash, description hash)
        set_name_dict = {}  # key: equip_affix_id, value: set name
        for item in reliquary_info:
            if "id" not in item:
                continue
            attr_map[item["id"]] = (item["equipType"],
                                    item["nameTextMapHash"],
                                    item["descTextMapHash"])
        for item in equip_affix_info:
            if "id" not in item:
                continue
            set_name_dict[item["id"]] = item["nameTextMapHash"]

        for item in reliquary_set_info:
            if "setId" not in item or "EquipAffixId" not in item:
                continue
            set_id = item["setId"]
            equip_affix_id = item["EquipAffixId"]
            name_hashs = [None for _ in range(5)]
            desc_hashs = [None for _ in range(5)]
            for reliq_id in item["containsList"]:
                equip_type, name_hash, desc_hash = attr_map[reliq_id]
                index = RELIQUARY_TYPE_MAP[equip_type] - 1
                name_hashs[index] = name_hash
                desc_hashs[index] = desc_hash
            self.reliquary_set_dict[set_id] = ReliquarySet(
                id=set_id,
                set_name_text_map_hash=set_name_dict[equip_affix_id],
                name_text_map_hashs=name_hashs,  # type: ignore
                desc_text_map_hashs=desc_hashs,  # type: ignore
            )

    def collect_prev_talks(self):
        """
        Collect the previous talk ids for each talk.
        """
        for talk_id, talk in self.talk_dict.items():
            for next_talk_id in talk.next_talks:
                self.talk_dict[next_talk_id].prev_talks.append(talk_id)

    def clean_data(self):
        """
        Fix some errors and remove some non-existing stuffs.
        """
        # Clean dialogs' next_dialogs.
        for dialog in self.dialog_dict.values():
            dialog.next_dialogs = [
                dialog_id for dialog_id in dialog.next_dialogs
                          if dialog_id in self.dialog_dict
            ]

        # Clean talks containing non-existing dialogs.
        dialog_set_dict = {}  # talk_id: set([dialog_id1, dialog_id2, ...])
        def dfs(dialog_id, dialog_set, talk_id):
            dialog_set.add(dialog_id)
            if dialog_id not in self.dialog_dict:
                return False
            result = True
            for next_id in self.dialog_dict[dialog_id].next_dialogs:
                if next_id not in dialog_set:
                    if not dfs(next_id, dialog_set, talk_id):
                        result = False
            return result
        broken_talk_set = set()
        for talk_id, talk in self.talk_dict.items():
            dialog_set_dict[talk_id] = set()
            if not dfs(talk.init_dialog, dialog_set_dict[talk_id], talk_id):
                broken_talk_set.add(talk_id)
        for talk_id in broken_talk_set:
            self.talk_dict.pop(talk_id)
            for dialog_id in dialog_set_dict[talk_id]:
                if dialog_id in self.dialog_dict:
                    self.dialog_dict.pop(dialog_id)
        for talk in self.talk_dict.values():
            talk.next_talks = [
                talk_id for talk_id in talk.next_talks
                        if talk_id not in broken_talk_set
            ]
            talk.prev_talks = [
                talk_id for talk_id in talk.prev_talks
                        if talk_id not in broken_talk_set
            ]
        for subquest in self.subquest_dict.values():
            subquest.talk_ids = [
                talk_id for talk_id in subquest.talk_ids
                        if talk_id not in broken_talk_set
            ]
        for quest in self.quest_dict.values():
            quest.talks = [
                talk_id for talk_id in quest.talks
                        if talk_id not in broken_talk_set
            ]

        # Clean talks containing non-existing subquests as conditions.
        for talk in self.talk_dict.values():
            talk.begin_cond = [
                (subquest_id, value) for subquest_id, value in talk.begin_cond
                                     if subquest_id in self.subquest_dict
            ]

        # Clean some non-existing quest ids.
        for quest in self.quest_dict.values():
            quest.suggest_track_main_quest_list = [
                quest_id for quest_id in quest.suggest_track_main_quest_list
                         if quest_id in self.quest_dict
            ]

        # Fix some unknown roles that could be inferred.
        for dialog in self.dialog_dict.values():
            if all(
                self.dialog_dict[dialog_id].role != -1
                for dialog_id in dialog.next_dialogs
            ):
                continue
            # If any of the next dialog has role of player, then all the next
            # dialogs should be the player's.
            if any(
                self.dialog_dict[dialog_id].role == 0
                for dialog_id in dialog.next_dialogs
            ):
                for dialog_id in dialog.next_dialogs:
                    self.dialog_dict[dialog_id].role = 0

        return len(broken_talk_set)

    def connect_quests(self, remove_quest_cycles: bool):
        """
        Fill the `prev_quests` and `next_quests` fields of the quests.
        If remove_quest_cycles is True, remove some connections among the
        quests to avoid cycles in the quest graph.
        """
        if not remove_quest_cycles:
            logging.info("Connecting quests.")
            for quest_id, quest in self.quest_dict.items():
                for next_quest_id in quest.suggest_track_main_quest_list:
                    self.quest_dict[next_quest_id].prev_quests.append(quest_id)
                    quest.next_quests.append(next_quest_id)
            return

        logging.info("Connecting quests while removing cycles.")
        # To remove the cycles, first build the quest graph.
        graph = nx.DiGraph()
        for quest_id, quest in self.quest_dict.items():
            for next_quest_id in quest.suggest_track_main_quest_list:
                graph.add_edge(quest_id, next_quest_id)

        # Deal with it per component. This greatly reduces computations.
        components = list(nx.weakly_connected_components(graph))

        for component in tqdm.tqdm(components):
            # Iteratively remove an edge from a cycle to break it.
            # There seems to be no smart strategies to break the cycles. To keep
            # the algorithm deterministic, we always remove an in-edge of the
            # node with the minimum id in the first cycle sorted in alphabetical
            # order. The in-edge is from the predecessors (in the cycle) with
            # the maximum id.
            while True:
                cycles = []
                for cycle in nx.simple_cycles(graph.subgraph(component)):
                    index_min = min(range(len(cycle)), key=lambda x: cycle[x])
                    cycles.append(cycle[index_min:] + cycle[:index_min])
                if len(cycles) == 0:
                    break
                nodes_in_cycle = set(sum(cycles, []))
                victim = sorted(cycles)[0][0]
                prev_victim = min(
                    graph.predecessors(victim),
                    key=lambda node: (node not in nodes_in_cycle, node)
                )
                graph.remove_edge(prev_victim, victim)

        # Now connect them.
        for quest_id, next_quest_id in graph.edges():
            self.quest_dict[next_quest_id].prev_quests.append(quest_id)
            self.quest_dict[quest_id].next_quests.append(next_quest_id)

    def build_sources(self):
        """
        Build the source infos and find a minimum number of traces that covers
        all the sentences in each source.
        """
        logging.info("Building sources and covering traces.")

        # Group the talks into sources.
        self._collect_sources_from_talks()
        source_names_talk = set(self.source_dict.keys())
        graphs_dict_talk = {
            source_name: self._build_dialog_graph_from_talks(
                self.source_dict[source_name].talk_ids
            ) for source_name in source_names_talk
        }
        for source_name in source_names_talk:
            self.source_dict[source_name].dialog_ids.update(
                graphs_dict_talk[source_name].nodes
            )

        # Ditto for dialogs.
        dialog_ids_in_talks = set.union(*[
            self.source_dict[source_name].dialog_ids
            for source_name in source_names_talk
        ])
        self._collect_sources_from_dialogs(dialog_ids_in_talks)
        graphs_dict_dialog = {
            source_name: self._build_dialog_graph_from_dialogs(
                self.source_dict[source_name].dialog_ids
            ) for source_name in self.source_dict
            if source_name not in source_names_talk
        }

        # Merge the player's lines that are splitted into options.
        graphs_dict = {**graphs_dict_talk, **graphs_dict_dialog}
        for graph in graphs_dict.values():
            self._reorder_player_lines_(graph)

        # Find the traces.
        for source_name in tqdm.tqdm(self.source_dict):
            preferred_starts = [
                self.talk_dict[talk_id].init_dialog
                for talk_id in
                    self.source_dict[source_name].talk_ids  # type: ignore
            ] if self.source_dict[source_name].talk_ids is not None else []
            start_set, end_set = self._find_start_end(
                graphs_dict[source_name], preferred_starts
            )
            self.source_dict[source_name].traces = self._find_covering_traces(
                graphs_dict[source_name], start_set, end_set
            )
            if len(self.source_dict[source_name].traces) == 0:
                print(source_name)

    def _collect_sources_from_talks(self):
        """
        Collect sources from talks, each representing possible paths among the
        talks.
        """
        # Find connected talk graphs (components).
        graph = nx.DiGraph()
        graph.add_nodes_from(self.talk_dict.keys())
        for talk_id in self.talk_dict:
            talk = self.talk_dict[talk_id]
            graph.add_edges_from([(talk_id, next_talk_id)
                                  for next_talk_id in talk.next_talks])
        components = list(nx.weakly_connected_components(graph))

        # Determine the belonging subquest/quest of each talk (if any).
        talk_ids_rest = set()  # Talks belonging to multiple quests.
        for quest_id, quest in self.quest_dict.items():
            for talk_id in quest.talks:
                # This asserts that each talk belongs to one quest only.
                assert (
                    talk_id not in self.talk2quest or
                    self.talk2quest[talk_id] == quest_id
                ), f'{talk_id}, {self.talk2quest[talk_id]}, {quest_id}'
                self.talk2quest[talk_id] = quest_id
        self.subquest2quest = {
            subquest_id: quest_id
            for quest_id, quest in self.quest_dict.items()
            for subquest_id in quest.sub_quests
        }
        for quest_id, quest in self.quest_dict.items():
            for subquest_id in quest.sub_quests:
                subquest = self.subquest_dict[subquest_id]
                for talk_id in subquest.talk_ids:
                    # Note that here the talk_id may have not appeared in
                    # talk2quest.
                    if talk_id < 0 or talk_id in talk_ids_rest:
                        continue
                    if (
                        talk_id in self.talk2quest and
                        self.talk2quest[talk_id] != quest_id
                    ):
                        # Talks belonging to some quest should not be assigned
                        # to subquests belonging to other quests.
                        continue
                    if (
                        talk_id in self.talk2subquest and
                        self.subquest2quest[self.talk2subquest[talk_id]] != \
                            quest_id
                    ):
                        # The talk belongs to multiple quests. It should not be
                        # assigned to any quest.
                        self.talk2subquest.pop(talk_id)
                        if talk_id in self.talk2quest:
                            self.talk2quest.pop(talk_id)
                        talk_ids_rest.add(talk_id)
                        continue
                    # Now there remain two cases:
                    # 1. The talk belongs to no subquest for now.
                    # 2. The talk belongs to a subquest of the current quest.
                    # Let's assign the talk to the subquest with the minimum
                    # order.
                    if talk_id not in self.talk2subquest:
                        self.talk2subquest[talk_id] = subquest_id
                        assert (
                            talk_id not in self.talk2quest or
                            self.talk2quest[talk_id] == quest_id
                        ), f'{talk_id}, {self.talk2quest[talk_id]}, {quest_id}'
                        self.talk2quest[talk_id] = quest_id
                    else:
                        subquest_id_old = self.talk2subquest[talk_id]
                        order_old = self.subquest_dict[subquest_id_old].order
                        if subquest.order < order_old:
                            self.talk2subquest[talk_id] = subquest_id

        # Determine the source name and the order of each component.
        subquest_sizes = {}  # subquest_id: #compoments belonging to it.
        quest_sizes = {}  # quest_id: #compoments belonging to it.
        for component in components:
            subquests_belonging_to = set(
                self.talk2subquest[talk_id]
                for talk_id in component if talk_id in self.talk2subquest
            )
            quests_belonging_to = set(
                self.talk2quest[talk_id]
                for talk_id in component if talk_id in self.talk2quest
            )
            if len(subquests_belonging_to) == 1:
                # This component belongs to a certain subquest.
                subquest_id = next(iter(subquests_belonging_to))
                if subquest_id not in subquest_sizes:
                    subquest_sizes[subquest_id] = 0
                source_name = (
                    f'subquest_{self.subquest2quest[subquest_id]}_{subquest_id}'
                    f'_{subquest_sizes[subquest_id]}'
                )
                self.source_dict[source_name] = Source(
                    name=source_name,
                    order=self.subquest_dict[subquest_id].order,
                    quest_id=self.subquest2quest[subquest_id],
                    subquest_id=subquest_id,
                    talk_ids=component,
                    dialog_ids=set(),
                    traces=[],
                    next_sources=[],
                    next_sources_optional=[],
                    prev_sources=[],
                    prev_sources_optional=[],
                )
                subquest_sizes[subquest_id] += 1
            elif len(quests_belonging_to) == 1:
                # This component belongs to a certain quest.
                quest_id = next(iter(quests_belonging_to))
                if quest_id not in quest_sizes:
                    quest_sizes[quest_id] = 0
                orders_all = [
                    self.subquest_dict[subquest_id].order
                    for subquest_id in subquests_belonging_to
                ]
                source_name = f'quest_{quest_id}_{quest_sizes[quest_id]}'
                self.source_dict[source_name] = Source(
                    name=source_name,
                    # Use the minimum order of the related subquests as the
                    # order of this source.
                    # There may be no talk belonging to some subquest.
                    order=min(orders_all) if len(orders_all) > 0 else -1,
                    quest_id=quest_id,
                    subquest_id=-1,
                    talk_ids=component,
                    dialog_ids=set(),
                    traces=[],
                    next_sources=[],
                    next_sources_optional=[],
                    prev_sources=[],
                    prev_sources_optional=[],
                )
                quest_sizes[quest_id] += 1
            else:
                # This component belongs to no quest or multiple quests.
                # This indicates that this component either:
                # - is relatively independent to other talks.
                # - contains most related talks from different quests inside
                # this single component.
                # So we do not assign an order to it. i.e. setting it to -1.
                # The source name is randomly (but deterministicly) selected.
                source_name = f'talk_{sorted(component)[0]}'
                self.source_dict[source_name] = Source(
                    name=source_name,
                    order=-1,
                    quest_id=-1,
                    subquest_id=-1,
                    talk_ids=component,
                    dialog_ids=set(),
                    traces=[],
                    next_sources=[],
                    next_sources_optional=[],
                    prev_sources=[],
                    prev_sources_optional=[],
                )

    def _collect_sources_from_dialogs(self, dialog_ids_in_talks):
        """
        Collect sources from dialogs, each representing possible paths among the
        dialogs.
        Here we omit dialogs that already exist in talks.
        """
        # Find connected dialog graphs (components).
        graph = nx.DiGraph()
        dialog_ids = set(self.dialog_dict.keys()) - set(dialog_ids_in_talks)
        graph.add_nodes_from(dialog_ids)
        for dialog_id in dialog_ids:
            dialog = self.dialog_dict[dialog_id]
            graph.add_edges_from([(dialog_id, next_dialog_id)
                                  for next_dialog_id in dialog.next_dialogs])
        components = list(nx.weakly_connected_components(graph))

        # Collect them into source_dict.
        for component in components:
            source_name = f'dialog_{sorted(component)[0]}'
            self.source_dict[source_name] = Source(
                name=source_name,
                order=-1,
                quest_id=-1,
                subquest_id=-1,
                talk_ids=None,
                dialog_ids=component,
                traces=[],
                next_sources=[],
                next_sources_optional=[],
                prev_sources=[],
                prev_sources_optional=[],
            )

    def _build_dialog_graph_from_talks(self, talk_ids):
        """
        Returns a networkx.DiGraph.
        """
        graph = nx.DiGraph()
        graph.add_nodes_from([self.talk_dict[talk_id].init_dialog
                              for talk_id in talk_ids])
        graph_talk = nx.DiGraph()
        for talk_id in talk_ids:
            for next_talk_id in self.talk_dict[talk_id].next_talks:
                graph_talk.add_edge(talk_id, next_talk_id)
        def dfs(dialog_id, visited, end_set_dialog):
            visited.add(dialog_id)
            if len(self.dialog_dict[dialog_id].next_dialogs) == 0:
                end_set_dialog.add(dialog_id)
            for next_id in self.dialog_dict[dialog_id].next_dialogs:
                graph.add_edge(dialog_id, next_id)
                if next_id not in visited:
                    dfs(next_id, visited, end_set_dialog)
        for talk_id in talk_ids:
            visited = set()
            end_set_dialog = set()
            dfs(self.talk_dict[talk_id].init_dialog, visited, end_set_dialog)
            for dialog_id in end_set_dialog:
                for next_talk_id in self.talk_dict[talk_id].next_talks:
                    graph.add_edge(dialog_id,
                                   self.talk_dict[next_talk_id].init_dialog)
        return graph

    def _build_dialog_graph_from_dialogs(self, dialog_ids):
        """
        Returns a networkx.DiGraph.
        """
        graph = nx.DiGraph()
        graph.add_nodes_from(dialog_ids)
        def dfs(dialog_id, visited):
            visited.add(dialog_id)
            for next_id in self.dialog_dict[dialog_id].next_dialogs:
                graph.add_edge(dialog_id, next_id)
                if next_id not in visited:
                    dfs(next_id, visited)
        visited = set()
        for dialog_id in dialog_ids:
            if dialog_id in visited:
                continue
            dfs(dialog_id, visited)
        return graph

    def _reorder_player_lines_(self, graph):
        """
        In Genshin Impact, sometimes a line of the player will be broken into
        multiple options, while the choice won't affect the later lines. We
        rearrange these sentences so they form a correct dialog.
        Before:
        1. npc line 1
        2. player option 1 | player option 2
        3. npc line 2
        After:
        1. npc line 1
        2. player option 1
        3. player option 2
        4. npc line 2

        This method accepts a dialog graph (as networkx.DiGraph) as input and
        reorder the nodes inplace.
        """
        for node in graph.nodes:
            neighbors = self.dialog_dict[node].next_dialogs
            if (
                len(neighbors) < 2 or
                not all(self.dialog_dict[neighbor].role == 0
                        for neighbor in neighbors) or
                not all(len(self.dialog_dict[neighbor].next_dialogs) == 1
                        for neighbor in neighbors)
            ):
                continue
            next_dialog_id = self.dialog_dict[neighbors[0]].next_dialogs[0]
            if not all(
                self.dialog_dict[neighbor].next_dialogs[0] == next_dialog_id
                for neighbor in neighbors
            ):
                continue
            for neighbor in neighbors[:-1]:
                # In case when:
                # 1->3, 1->4, 3->5, 4->5
                # 2->3, 2->4
                # We'll first remove 3->5 when processing node 1, and we'll try
                # removing 3->5 again when processing node 2. That's why we
                # check has_edge here.
                if graph.has_edge(neighbor, next_dialog_id):
                    graph.remove_edge(neighbor, next_dialog_id)
            for i in range(1, len(neighbors)):
                # Ditto.
                if graph.has_edge(node, neighbors[i]):
                    graph.remove_edge(node, neighbors[i])
                graph.add_edge(neighbors[i - 1], neighbors[i])

    def _find_start_end(self, graph, preferred_starts):
        """
        Find starting and ending nodes in the graph.
        The result is guaranteed that there exists a path from one of the
        starting nodes to any node in the graph. Also, there exists a path from
        any node to one of the ending nodes.
        Returns a set of starting nodes and a set of ending nodes.
        """
        start_set = set()
        end_set = set()
        for node in graph.nodes:
            if graph.in_degree(node) == 0:
                start_set.add(node)
            if graph.out_degree(node) == 0:
                end_set.add(node)

        # In some graphs with loops, maybe the start_set is empty or there are
        # some nodes that cannot be reached from the starting nodes. Ditto for
        # ending nodes.
        # We iteratively add starting and ending nodes until all nodes are
        # reachable from the starting nodes and can reach one of the ending
        # nodes.
        ancestors = set.union(
            set(),  # For cases where end_set is empty.
            *[nx.ancestors(graph, node) for node in end_set]
        ) | end_set
        descendants = set.union(
            set(),  # For cases where start_set is empty.
            *[nx.descendants(graph, node) for node in start_set]
        ) | start_set
        preferred_starts = [
            node for node in preferred_starts if node not in descendants
        ]
        while (
            len(ancestors) < len(graph.nodes) or
            len(descendants) < len(graph.nodes)
        ):
            new_start_node = None
            if len(descendants) < len(graph.nodes):
                if len(preferred_starts) > 0:
                    # Try the preferred starting nodes first.
                    new_start_node = preferred_starts[0]
                else:
                    # Add a starting node by finding the node with the largest
                    # out degree. This is inspired by the fact that most loop
                    # dialogs start with a sentence with many options.
                    subgraph = graph.subgraph(set(graph.nodes) - descendants)
                    new_start_node = max(
                        subgraph.nodes,
                        # When out_degrees equal, choose the one with minimum
                        # dialog id.
                        key=lambda node: (graph.out_degree(node), -node)
                    )
                start_set.add(new_start_node)
                descendants.add(new_start_node)
                descendants.update(nx.descendants(graph, new_start_node))
                preferred_starts = [
                    node for node in preferred_starts if node not in descendants
                ]
            if len(ancestors) < len(graph.nodes):
                subgraph = graph.subgraph(set(graph.nodes) - ancestors)
                if (
                    new_start_node is not None and
                    new_start_node in subgraph.nodes
                ):
                    # If it is impossible for the new starting node to reach any
                    # ending nodes, the new starting node must be in a loop.
                    # Thus we add its predecessors as new ending nodes.
                    predecessors = subgraph.predecessors(new_start_node)
                    end_set.update(predecessors)
                    for new_end_node in predecessors:
                        ancestors.add(new_end_node)
                        ancestors.update(nx.ancestors(graph, new_end_node))
                else:
                    # In this case, we claim that the node with the maximum
                    # degree is possibly an ending node. This is because a node
                    # with a large degree is possibly the joint node of multiple
                    # loops.
                    new_end_node = max(
                        subgraph.nodes,
                        key=lambda node: (graph.degree(node), node)
                    )
                    end_set.add(new_end_node)
                    ancestors.add(new_end_node)
                    ancestors.update(nx.ancestors(graph, new_end_node))
        return start_set, end_set

    def _find_covering_traces(self, graph, start_set, end_set):
        """
        Find the minimal set of traces covering all the dialogs by reducing the
        problem to a minimum-cost flow problem.
        The NetworkX library provides a method `min_cost_flow` for it.
        Reference: https://cs.stackexchange.com/questions/107397/fewest-traversals-to-visit-all-vertices-of-dag
        A detailed explanation could be found in README.md .

        Returns a list of lists. Each sub-list contains a trace, that is, a
        sequence of dialog ids.
        """
        # 1. Build the auxiliary graph.
        # Since we need to split each node v into v1 and v2, we use the original
        # node label (a positive integer) to represent v1, while use the
        # negative label to represent v2.
        g = nx.DiGraph()
        assert all(node > 0 for node in graph.nodes)
        # 1.1. Split the nodes.
        for node in graph.nodes:
            g.add_node(node, demand=1)
            g.add_node(-node, demand=-1)
            g.add_edge(node, -node, weight=1)
        # 1.2. Add the original edges.
        for u, v in graph.edges:
            g.add_edge(-u, v)
        # 1.3. Add edges related to the super starting and ending nodes.
        for node in start_set:
            g.add_edge("start", node)
        for node in end_set:
            g.add_edge(-node, "end")
        g.add_edge("end", "start", weight=len(graph.nodes))

        # 2. Calculate the minimum cost flow.
        flow_dict = nx.min_cost_flow(g)

        # 3. Extract the covering traces.
        traces = []
        for i in range(flow_dict["end"]["start"]):
            trace = []
            node = "start"
            while node != "end":
                node_next = max(
                    flow_dict[node].keys(),
                    key=lambda suc: (flow_dict[node][suc],
                                     # Add a second item to the tuple to make
                                     # the result deterministic.
                                     suc if suc != "end" else 0)
                )
                assert node_next == "end" or node_next > 0  # We'll skip the
                                                            # negative node.
                # We do not delete the zeroed items in order to invoke max()
                # without considering corner cases.
                flow_dict[node][node_next] -= 1
                if node_next == "end":
                    break
                else:
                    trace.append(node_next)
                    flow_dict[node_next][-node_next] -= 1
                    node = -node_next  # Skip the edge in the splitted node.
            traces.append(trace)
        flow_dict["end"]["start"] = 0

        # 4. Deal with the loops.
        # 4.1. Collect the loops.
        loops = []
        for node_start in flow_dict:
            if node_start in ["start", "end"]:
                continue
            if node_start > 0:  # Skip the edge in the splitted node.
                continue
            while True:
                node_next = max(
                    flow_dict[node_start].keys(),
                    key=lambda suc: (flow_dict[node_start][suc],
                                     suc if suc != "end" else 0)
                )
                if flow_dict[node_start][node_next] == 0:
                    # There is no more loops containing this node.
                    break
                # Collect a loop.
                loop = [-node_start]
                flow_dict[-node_start][node_start] -= 1
                node = node_start
                assert (
                    node < 0 and
                    node_next not in ["start", "end"] and
                    node_next > 0
                )
                while node_next != -node_start:
                    assert flow_dict[node][node_next] > 0
                    flow_dict[node][node_next] -= 1
                    loop.append(node_next)
                    flow_dict[node_next][-node_next] -= 1
                    node = -node_next  # Skip the edge in the splitted node.
                    node_next = max(
                        flow_dict[node].keys(),
                        key=lambda suc: (flow_dict[node][suc],
                                         suc if suc != "end" else 0)
                    )
                flow_dict[node][node_next] -= 1
                loops.append(loop)
        # 4.2. Merge the loops into existing traces, or create new traces to
        # cover the loops.
        node2trace = {}
        for i, trace in enumerate(traces):
            for node in trace:
                node2trace[node] = i  # We do not care about the sharing nodes.
        for loop in loops:
            trace_i = None
            for node in loop:
                if node in node2trace:
                    trace_i = node2trace[node]
                    break
            if trace_i is not None:
                # Merge into an existing trace.
                trace = traces[trace_i]
                entrance_i = None
                loop_node_set = set(loop)
                for node_i, node in enumerate(trace):
                    if node in loop_node_set:
                        entrance_i = node_i
                        break
                assert entrance_i is not None
                entrance_loc = loop.index(trace[entrance_i])
                traces[trace_i] = (
                    trace[:entrance_i] + loop[entrance_loc:] +
                    loop[:entrance_loc] + trace[entrance_i:]
                )
            else:
                # Create a new trace.
                # Directly exploit the input graph to do our business. Recover
                # it later.
                # 1. Find the first half path.
                assert "start" not in graph.nodes and "end" not in graph.nodes
                for node in start_set:
                    graph.add_edge("start", node)
                for node in loop:
                    graph.add_edge(node, "end")
                path1 = nx.shortest_path(graph, "start", "end")[1:-1]
                assert len(path1) == 1 or path1[-2] not in loop
                entrance_loc = loop.index(path1[-1])
                graph.remove_node("start")
                graph.remove_node("end")
                # 2. Find the second half path.
                exit_loc = (entrance_loc - 1 + len(loop)) % len(loop)
                for node in end_set:
                    graph.add_edge(node, "end")
                path2 = nx.shortest_path(graph, loop[exit_loc], "end")[1:-1]
                graph.remove_node("end")
                # 3. Concatenate them.
                traces.append(
                    path1 + loop[entrance_loc + 1:] + loop[:entrance_loc] +
                    path2
                )
                # 4. Update node2trace.
                for node in traces[-1]:
                    node2trace[node] = len(traces) - 1
        return traces

    def connect_sources(self):
        """
        Fill the `prev_sources`, `prev_sources_optional`, `next_sources` and
        `next_sources_optional` fields of the sources.
        """
        logging.info("Building connections among the sources.")
        # We arrange the sources by the order numbers.
        sources = {
            # The inner dict has key as order and value as list of source names.
            quest_id: {} for quest_id in self.quest_dict
        }
        sources_before = {quest_id: {} for quest_id in self.quest_dict}  # ditto
        sources_after = {quest_id: {} for quest_id in self.quest_dict}  # ditto

        # Collect the sources with a pre-assigned order.
        for source_name, source in self.source_dict.items():
            if source.order < 0 or source.quest_id < 0:
                continue
            sources[source.quest_id].setdefault(source.order, []).append(
                source_name
            )

        # As for other sources belonging to some quest but not having an order,
        # arrange them by the beginning conditions of the talks belonging to
        # them.
        for source_name, source in self.source_dict.items():
            if source.order >= 0 or source.quest_id < 0:
                continue
            begin_conds = [
                (self.talk_dict[talk_id].begin_cond_comb,
                 self.talk_dict[talk_id].begin_cond)
                for talk_id in source.talk_ids  # type: ignore
                if len(self.talk_dict[talk_id].begin_cond) > 0
            ]
            if len(begin_conds) == 0:
                # No beginning conditions means this source could be triggered
                # at the very first of the quest.
                sources_before[source.quest_id].setdefault(0, []).append(
                    source_name
                )
                continue

            # Sum all the conditions into a range representing the valid
            # locations of the source.
            # The endpoint of the range is defined as (order: int, bias: int),
            # where `bias` is an additional field to indicate whether the
            # endpoint is after the subquest of this order. The value range is
            # {-1, 0, 1}. For example, if we have range_start == (3, -1) and
            # range_end == (5, False), then placing the source BEFORE the order
            # 3 subquest is valid, but placing it AFTER the order 5 subquest is
            # invalid. This is because range_start is BEFORE order 3, and
            # range_end is BEFORE order 5.
            range_start = (0, -1)  # (order, bias)
            range_end = (sys.maxsize, 1)  # ditto
            for begin_cond_comb, begin_cond in begin_conds:
                if len(begin_cond) == 0:
                    continue
                if begin_cond_comb:  # LOGIC_AND
                    range_start_tmp = (0, -1)
                    range_end_tmp = (sys.maxsize, 1)
                    for subquest_id, cond_value in begin_cond:
                        subquest_order = self.subquest_dict[subquest_id].order
                        assert subquest_order >= 0, subquest_id
                        if cond_value == "2":
                            range_start_tmp = max(range_start_tmp,
                                                  (subquest_order, -1))
                            range_end_tmp = min(range_end_tmp,
                                                (subquest_order, -1))
                        elif cond_value in ["3", "4"]:
                            range_start_tmp = max(range_start_tmp,
                                                  (subquest_order, 1))
                        else:
                            raise NotImplementedError(f'value: {cond_value}')
                else:  # LOGIC_OR
                    range_start_tmp = (sys.maxsize, 1)
                    range_end_tmp = (0, -1)
                    for subquest_id, cond_value in begin_cond:
                        subquest_order = self.subquest_dict[subquest_id].order
                        assert subquest_order >= 0, subquest_id
                        if cond_value == "2":
                            range_start_tmp = min(range_start_tmp,
                                                  (subquest_order, -1))
                            range_end_tmp = max(range_end_tmp,
                                                (subquest_order, -1))
                        elif cond_value in ["3", "4"]:
                            range_start_tmp = min(range_start_tmp,
                                                  (subquest_order, 1))
                        else:
                            raise NotImplementedError(f'value: {cond_value}')
                range_start = max(range_start, range_start_tmp)
                range_end = min(range_end, range_end_tmp)

            # If the range is valid, place the source at the earliest location.
            # Otherwise, place it at the end.
            if range_start <= range_end:
                if range_start[1] == -1:
                    sources_before[source.quest_id].setdefault(
                        range_start[0], []
                    ).append(source_name)
                else:
                    sources_after[source.quest_id].setdefault(
                        range_start[0], []
                    ).append(source_name)
            else:
                sources_after[source.quest_id].setdefault(
                    sys.maxsize, []
                ).append(source_name)

        # Fill the `prev_sources`, `prev_sources_optional`, `next_sources` and
        # `next_sources_optional` fields.
        for quest_id in self.quest_dict:
            srcs = sources[quest_id]
            if len(srcs) == 0:
                continue
            orders = sorted(srcs.keys())
            for o1, o2 in zip(orders[:-1], orders[1:]):
                for s1 in srcs[o1]:
                    for s2 in srcs[o2]:
                        self.source_dict[s1].next_sources.append(s2)
                        self.source_dict[s2].prev_sources.append(s1)
            srcs_b = sources_before[quest_id]
            srcs_a = sources_after[quest_id]
            for order, src_list in srcs_b.items():
                loc = bisect.bisect_left(orders, order)
                if loc < len(orders):
                    for source_name in srcs[orders[loc]]:
                        self.source_dict[source_name].prev_sources_optional\
                            .extend(src_list)
                else:
                    for source_name in srcs[orders[-1]]:
                        self.source_dict[source_name].next_sources_optional\
                            .extend(src_list)
            for order, src_list in srcs_a.items():
                loc = bisect.bisect_right(orders, order) - 1
                if loc >= 0:
                    for source_name in srcs[orders[loc]]:
                        self.source_dict[source_name].next_sources_optional\
                            .extend(src_list)
                else:
                    for source_name in srcs[orders[0]]:
                        self.source_dict[source_name].prev_sources_optional\
                            .extend(src_list)

        # Finally, connect the sources across quests.
        for quest_id, quest in self.quest_dict.items():
            if quest_id not in sources or len(sources[quest_id]) == 0:
                continue
            srcs = sources[quest_id]
            last_source_ids = srcs[max(srcs.keys())]
            for next_quest_id in quest.next_quests:
                if (
                    next_quest_id not in sources or
                    len(sources[next_quest_id]) == 0
                ):
                    continue
                srcs_next = sources[next_quest_id]
                for s1 in last_source_ids:
                    for s2 in srcs_next[min(srcs_next.keys())]:
                        self.source_dict[s1].next_sources.append(s2)
                        self.source_dict[s2].prev_sources.append(s1)

    def load_text_map(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            text_map = json.load(f)
        self.text_map = {int(key): value for key, value in text_map.items()}

    def load_npc_name(self, filepath):
        assert len(self.text_map) > 0, \
            "TextMap must be loaded before exporting the dialogs."
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            if (
                "nameTextMapHash" in item and
                item["nameTextMapHash"] in self.text_map and
                len(self.text_map[item["nameTextMapHash"]]) > 0
            ):
                self.npc_name_map[item["id"]] = \
                    self.text_map[item["nameTextMapHash"]]

    def load_readable(self, source_dir):
        for filename in os.listdir(source_dir):
            if not filename.endswith(".txt"):
                continue
            readable_name = filename[:-4]
            with open(
                os.path.join(source_dir, filename), "r", encoding="utf-8"
            ) as f:
                self.readable_dict[readable_name] = f.read()

    def export_dialogs(
        self,
        filepath: str,
        lang: str,
        traveller_sex: str,
        traveller_name: str,
        mate_name: str,
        wanderer_name: str,
        narrator_name: str,
        unknown_name: str,
        unknown_text: str,
        replace_quotes: bool,
        replace_newline: bool,
        remove_broken_trace: bool,
        remove_absent_text: bool,
    ):
        assert len(self.text_map) > 0, \
            "TextMap must be loaded before exporting the dialogs."

        result = {}

        # Export dialogs.
        logging.info(f'Exporting dialogs to {filepath}')
        valid_source_names = set()
        for source_name, source in tqdm.tqdm(self.source_dict.items()):
            source_item = {}
            source_item["quest_id"] = source.quest_id
            source_item["subquest_id"] = source.subquest_id
            source_item["prev_sources"] = source.prev_sources
            source_item["prev_sources_optional"] = source.prev_sources_optional
            source_item["next_sources"] = source.next_sources
            source_item["next_sources_optional"] = source.next_sources_optional
            traces_item = []
            for trace in source.traces:
                trace_item = []
                for dialog_id in trace:
                    dialog = self.dialog_dict[dialog_id]
                    role_name_hash = dialog.talk_role_name_text_map_hash
                    content_hash = dialog.talk_content_text_map_hash
                    # Determine the role.
                    if dialog.role == 0:
                        role = traveller_name
                    elif dialog.role == -2:
                        role = narrator_name
                    elif dialog.role == -3:
                        role = mate_name
                    elif dialog.role in [12947, 1065, 9075, 9547]:
                        role = wanderer_name
                    elif (
                        role_name_hash in self.text_map and
                        len(self.text_map[role_name_hash]) > 0
                    ):
                        role = self.text_map[role_name_hash]
                    elif dialog.role > 0 and dialog.role in self.npc_name_map:
                        role = self.npc_name_map[dialog.role]
                    else:
                        role = unknown_name
                    # Determine the content.
                    if (
                        content_hash in self.text_map and
                        len(self.text_map[content_hash]) > 0
                    ):
                        content = self.text_map[content_hash]
                    elif not remove_absent_text:
                        content = unknown_text
                    else:
                        content = None
                    # Filter out absent sentences.
                    if content is None:
                        if remove_broken_trace:
                            break
                        continue
                    # Filter out unreleased dialogs.
                    if (
                        lang in UNRELEASED_TAGS and
                        (
                            any([tag in content.lower()
                                 for tag in UNRELEASED_TAGS[lang]]) or
                            any([tag in role.lower()
                                 for tag in UNRELEASED_TAGS[lang]])
                        )
                    ):
                        break
                    # Remove XML tags.
                    for pattern, target in XML_PATTERNS:
                        content = pattern.sub(target, content)
                    # Filter out challenge quest dialogs.
                    if any(
                        pattern in content
                        for pattern in QUEST_PLACEHOLDER_PATTERNS
                    ):
                        break
                    # Replace placeholders.
                    content = self._replace_placeholders(
                        content, lang, traveller_sex, traveller_name,
                        wanderer_name
                    )
                    # Replace quotes to a more usual version.
                    if replace_quotes and lang in QUOTE_MAPPINGS:
                        for quote, target in QUOTE_MAPPINGS[lang].items():
                            role = role.replace(quote, target)
                            content = content.replace(quote, target)
                    # Replace escaped newline characters.
                    if replace_newline:
                        content = content.replace('\\n', "\n")
                    # Drop empty sentences.
                    if len(content) == 0:
                        continue
                    trace_item.append({
                        "role": role,
                        "content": content,
                    })
                else:
                    if len(trace_item) > 0:
                        traces_item.append(trace_item)
            source_item["traces"] = traces_item
            if len(traces_item) > 0:
                result[source_name] = source_item
                valid_source_names.add(source_name)

        # Remove invalid sources from prev_sources and next_sources.
        logging.info(f'Removing invalid sources.')
        for source_item in tqdm.tqdm(result.values()):
            source_item["prev_sources"] = [
                s for s in source_item["prev_sources"]
                if s in valid_source_names
            ]
            source_item["prev_sources_optional"] = [
                s for s in source_item["prev_sources_optional"]
                if s in valid_source_names
            ]
            source_item["next_sources"] = [
                s for s in source_item["next_sources"]
                if s in valid_source_names
            ]
            source_item["next_sources_optional"] = [
                s for s in source_item["next_sources_optional"]
                if s in valid_source_names
            ]

        # Export avatar voice texts.
        logging.info(f'Exporting avatar voice texts to {filepath}')
        traveller_id_ignore = (
            AVATAR_ID_LUMINE if traveller_sex == "male" else
            AVATAR_ID_AETHER
        )
        for avatar_id, avatar in tqdm.tqdm(self.avatar_dict.items()):
            # Not track dialogs from the traveller of the other sex.
            if avatar_id == traveller_id_ignore:
                continue
            # Get the avatar's name.
            if avatar.name_text_map_hash not in self.text_map:
                if remove_absent_text:
                    continue
                else:
                    avatar_name = unknown_name
            else:
                avatar_name = self.text_map[avatar.name_text_map_hash]
            for i, (voice_type, topic_hash, content_hash) in enumerate(
                avatar.voice_texts
            ):
                if voice_type == 2:
                    # We do not collect the battle voices.
                    continue
                # Get the texts.
                if (
                    topic_hash in self.text_map and
                    len(self.text_map[topic_hash]) > 0 and
                    content_hash in self.text_map and
                    len(self.text_map[content_hash]) > 0
                ):
                    topic = self.text_map[topic_hash]
                    content = self.text_map[content_hash]
                elif not remove_absent_text:
                    topic = self.text_map.get(topic_hash, unknown_text)
                    content = self.text_map.get(content_hash, unknown_text)
                else:
                    continue
                # Filter out unreleased dialogs.
                if (
                    lang in UNRELEASED_TAGS and
                    (
                        any([tag in topic.lower()
                             for tag in UNRELEASED_TAGS[lang]]) or
                        any([tag in content.lower()
                             for tag in UNRELEASED_TAGS[lang]])
                    )
                ):
                    continue
                # Remove XML tags.
                for pattern, target in XML_PATTERNS:
                    content = pattern.sub(target, content)
                # Replace placeholders. Do not replace the traveller's name here
                # because we need it when dealing with dialogs in the voice
                # text.
                content = self._replace_placeholders(
                    content, lang, traveller_sex, "{NICKNAME}", wanderer_name
                )
                # Drop empty sentences.
                if len(content) == 0:
                    continue
                source_item = {
                    "quest_id": -1,
                    "subquest_id": -1,
                    "prev_sources": [],
                    "prev_sources_optional": [],
                    "next_sources": [],
                    "next_sources_optional": [],
                }
                # Deal with the special cases where there are other characters
                # in the dialog.
                if (
                    avatar_id in [AVATAR_ID_AETHER, AVATAR_ID_LUMINE,
                                  AVATAR_ID_FISCHL, AVATAR_ID_BAIZHU] and
                    (
                        lang not in NAMES_IN_VOICE_TEXT and
                        (
                            # There is a colon in the first line.
                            ": " in content.split("\\n")[0] or
                            "：" in content.split("\\n")[0]
                        )
                    ) or (
                        lang in NAMES_IN_VOICE_TEXT and
                        any(
                            # There is a character's line in the first line.
                            content.split("\\n")[0].startswith(f'{name}: ') or
                            content.split("\\n")[0].startswith(f'{name}：')
                            for name in NAMES_IN_VOICE_TEXT[lang]
                        )
                    )
                ):
                    trace = self._split_voice_text(content, traveller_name)
                    if avatar_id not in [AVATAR_ID_AETHER, AVATAR_ID_LUMINE]:
                        trace = [{
                            "role": traveller_name,
                            "content": topic,
                        }] + trace
                else:
                    trace = [
                        {
                            "role": traveller_name,
                            "content": topic,
                        }, {
                            "role": avatar_name,
                            "content": content,
                        },
                    ]
                # Post-process the dialogs in the trace.
                for dialog in trace:
                    # Replace the traveller's name.
                    dialog["content"] = dialog["content"].replace(
                        "{NICKNAME}", traveller_name
                    )
                    # Replace quotes to a more usual version.
                    if replace_quotes and lang in QUOTE_MAPPINGS:
                        for quote, target in QUOTE_MAPPINGS[lang].items():
                            dialog["role"] = dialog["role"].replace(
                                quote, target
                            )
                            dialog["content"] = dialog["content"].replace(
                                quote, target
                            )
                    # Replace escaped newline characters. We do this in
                    # post-processing because the newline character should be
                    # consistent when splitting the content for special cases.
                    if replace_newline:
                        dialog["content"] = dialog["content"].replace(
                            '\\n', "\n"
                        )
                source_item["traces"] = [trace]
                result[f'avatar_{avatar_id}_voice_{i}'] = source_item

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def _replace_placeholders(
        self,
        content: str,
        lang: str,
        traveller_sex: str,
        traveller_name: str,
        wanderer_name: str,
    ):
        for match in RUBY_PATTERN.findall(content):
            content = content.replace("{RUBY#[D]" + match + "}", "")
        if not content.startswith("#"):
            return content
        sex = {
            "PLAYERAVATAR": int(traveller_sex == "female"),
            "MATEAVATAR": int(traveller_sex == "male"),
        }
        for placeholder in PLACEHOLDER_PATTERN.findall(content):
            if "#" in placeholder:
                first, second = placeholder.split("#")
                if first in ["PLAYERAVATAR", "MATEAVATAR"]:
                    assert second.endswith("]"), second
                    category, choices_str = second[:-1].split("[")
                    target = [
                        PLACEHOLDERS[lang][category][choice]
                        for choice in choices_str.split("|")
                    ][sex[first]]
                elif (
                    (first == "M" and traveller_sex == "male") or
                    (first == "F" and traveller_sex == "female")
                ):
                    target = second
                else:
                    assert first in ["M", "F"], first
                    target = ""
            elif placeholder in ["REALNAME[ID(1)|HOSTONLY(true)]",
                                 "REALNAME[ID(1)]"]:  # Wanderer
                target = wanderer_name
            else:
                assert placeholder == "NICKNAME", content
                target = traveller_name
            content = content.replace("{" + placeholder + "}", target)
        content = content[1:]  # Remove the leading '#'.
        return content

    def _split_voice_text(self, text, traveller_name, names_in_voice_text=None):
        """
        Split the voice text where there are multiple people in the dialog.
        This method requires:
        1. The first line of the text must have a colon in it. This enables us
        to parse a sentence of multiple lines. A colon in the first line of the
        text guarantees that each sentence in the dialog must belong to a
        speaker.
        2. The newline characters in the text are escaped.
        """
        trace = []
        for turn in text.split("\\n"):
            if len(turn) == 0:
                continue
            turn = turn.replace(": ", "：")
            assert "：" in turn or len(trace) > 0
            splits = turn.split("：")
            if (
                len(splits) == 1 or
                (
                    names_in_voice_text is not None and
                    splits[0] not in names_in_voice_text
                )
            ):
                # This line is not a new sentence, but follows the previous one.
                assert len(trace) > 0
                trace[-1] = {
                    "role": trace[-1]["role"],
                    "content": trace[-1]["content"] + turn,
                }
                continue
            role = turn[:len(splits[0])].strip()
            content = turn[len(splits[0]) + 1:].strip()
            trace.append({
                "role": role.replace("{NICKNAME}", traveller_name),
                "content": content,
            })
        return trace

    def export_quests(
        self,
        filepath: str,
        lang: str,
        traveller_sex: str,
        traveller_name: str,
        wanderer_name: str,
        unknown_text: str,
        replace_quotes: bool,
        replace_newline: bool,
    ):
        logging.info(f'Exporting quests to {filepath}')

        chapters = {}
        chapter_ids = sorted(self.chapter_dict.keys())
        for chapter_id in chapter_ids:
            chapter = self.chapter_dict[chapter_id]
            number = self.text_map.get(chapter.chapter_num_text_map_hash,
                                       unknown_text)
            title = self.text_map.get(chapter.chapter_title_text_map_hash,
                                      unknown_text)
            # Filter out unreleased chapters.
            if (
                lang in UNRELEASED_TAGS and
                (
                    any([
                        tag in number.lower() for tag in UNRELEASED_TAGS[lang]]
                    ) or
                    any([tag in title.lower() for tag in UNRELEASED_TAGS[lang]])
                )
            ):
                continue
            # Hide texts containing hidden tags.
            if any(tag in number for tag in HIDDEN_TAGS):
                number = unknown_text
            if any(tag in title for tag in HIDDEN_TAGS):
                title = unknown_text
            # Remove XML tags.
            for pattern, target in XML_PATTERNS:
                number = pattern.sub(target, number)
                title = pattern.sub(target, title)
            # Replace placeholders.
            number = self._replace_placeholders(
                number, lang, traveller_sex, traveller_name, wanderer_name
            )
            title = self._replace_placeholders(
                title, lang, traveller_sex, traveller_name, wanderer_name
            )
            # Replace quotes to a more usual version.
            if replace_quotes and lang in QUOTE_MAPPINGS:
                for quote, target in QUOTE_MAPPINGS[lang].items():
                    number = number.replace(quote, target)
                    title = title.replace(quote, target)
            # Replace escaped newline characters.
            if replace_newline:
                number = number.replace('\\n', "\n")
                title = title.replace('\\n', "\n")
            # Collect related info.
            chapters[str(chapter_id)] = {
                "group_id": chapter.group_id,
                "begin_subquest_id": chapter.begin_quest_id,
                "end_subquest_id": chapter.end_quest_id,
                "type": chapter.quest_type,
                "number": number,
                "title": title,
                "quest_ids": sorted(chapter.quests),
            }

        quests = {}
        quest_ids = sorted(self.quest_dict.keys())
        valid_quest_ids = set()
        for quest_id in quest_ids:
            quest = self.quest_dict[quest_id]
            title = self.text_map.get(quest.title_text_map_hash, unknown_text)
            description = self.text_map.get(quest.desc_text_map_hash,
                                            unknown_text)
            # Filter out unreleased quests.
            if (
                lang in UNRELEASED_TAGS and
                (
                    any([tag in description.lower()
                         for tag in UNRELEASED_TAGS[lang]]) or
                    any([tag in title.lower() for tag in UNRELEASED_TAGS[lang]])
                )
            ):
                continue
            # Hide texts containing hidden tags.
            if any(tag in title for tag in HIDDEN_TAGS):
                title = unknown_text
            if any(tag in description for tag in HIDDEN_TAGS):
                description = unknown_text
            # Remove XML tags.
            for pattern, target in XML_PATTERNS:
                title = pattern.sub(target, title)
                description = pattern.sub(target, description)
            # Replace placeholders.
            title = self._replace_placeholders(
                title, lang, traveller_sex, traveller_name, wanderer_name
            )
            description = self._replace_placeholders(
                description, lang, traveller_sex, traveller_name, wanderer_name
            )
            # Replace quotes to a more usual version.
            if replace_quotes and lang in QUOTE_MAPPINGS:
                for quote, target in QUOTE_MAPPINGS[lang].items():
                    title = title.replace(quote, target)
                    description = description.replace(quote, target)
            # Replace escaped newline characters.
            if replace_newline:
                title = title.replace('\\n', "\n")
                description = description.replace('\\n', "\n")
            # Collect related info.
            quests[str(quest_id)] = {
                "type": quest.type,
                "title": title,
                "description": description,
                "chapter_id": quest.chapter_id,
                "subquest_ids": sorted(quest.sub_quests),
                "prev_quest_ids": sorted(quest.prev_quests),
                "next_quest_ids": sorted(quest.next_quests),
            }
            valid_quest_ids.add(quest_id)

        subquests = {}
        subquest_ids = sorted(self.subquest_dict.keys())
        valid_subquest_ids = set()
        for subquest_id in subquest_ids:
            subquest = self.subquest_dict[subquest_id]
            description = self.text_map.get(subquest.desc_text_map_hash,
                                            unknown_text)
            # None for the step_description is intended, which indicates the
            # quest description is not updated here.
            step_description = self.text_map.get(
                subquest.step_desc_text_map_hash, None
            )
            # Filter out unreleased quests.
            if (
                lang in UNRELEASED_TAGS and
                (
                    any([tag in description.lower()
                         for tag in UNRELEASED_TAGS[lang]]) or
                    (
                        step_description is not None and
                        any([tag in step_description.lower()
                             for tag in UNRELEASED_TAGS[lang]])
                    )
                )
            ):
                continue
            # Remove the skipping tags.
            if lang in SKIP_TAGS:
                for tag in SKIP_TAGS[lang]:
                    description = description.replace(tag, "")
            # Hide texts containing hidden tags.
            if any(tag in description for tag in HIDDEN_TAGS):
                description = unknown_text
            if step_description is not None:
                if any(tag in step_description for tag in HIDDEN_TAGS):
                    step_description = None
            # Remove XML tags.
            for pattern, target in XML_PATTERNS:
                description = pattern.sub(target, description)
                if step_description is not None:
                    step_description = pattern.sub(target, step_description)
            # Replace placeholders.
            description = self._replace_placeholders(
                description, lang, traveller_sex, traveller_name, wanderer_name
            )
            if step_description is not None:
                step_description = self._replace_placeholders(
                    step_description, lang, traveller_sex, traveller_name,
                    wanderer_name
                )
            # Replace quotes to a more usual version.
            if replace_quotes and lang in QUOTE_MAPPINGS:
                for quote, target in QUOTE_MAPPINGS[lang].items():
                    description = description.replace(quote, target)
                    if step_description is not None:
                        step_description = step_description.replace(
                            quote, target
                        )
            # Replace escaped newline characters.
            if replace_newline:
                description = description.replace('\\n', "\n")
                if step_description is not None:
                    step_description = step_description.replace('\\n', "\n")
            # Collect related info.
            subquests[str(subquest_id)] = {
                "description": description,
                "step_description": step_description,
            }
            valid_subquest_ids.add(subquest_id)

        # Remove invalid quests and subquests.
        for quest_item in quests.values():
            quest_item["subquest_ids"] = [
                s for s in quest_item["subquest_ids"] if s in valid_subquest_ids
            ]
            quest_item["prev_quest_ids"] = [
                s for s in quest_item["prev_quest_ids"] if s in valid_quest_ids
            ]
            quest_item["next_quest_ids"] = [
                s for s in quest_item["next_quest_ids"] if s in valid_quest_ids
            ]

        result = {
            "chapters": chapters,
            "quests": quests,
            "subquests": subquests,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    def export_avatars(
        self,
        filepath,
        lang: str,
        traveller_sex: str,
        traveller_name: str,
        wanderer_name: str,
        unknown_name: str,
        unknown_text: str,
        replace_quotes: bool,
        replace_newline: bool,
    ):
        logging.info(f'Exporting avatars\' info to {filepath}')

        def get(text_hash, default_text=unknown_text):
            if text_hash not in self.text_map:
                return default_text
            text = self.text_map[text_hash]
            # Remove XML tags.
            for pattern, target in XML_PATTERNS:
                text = pattern.sub(target, text)
            # Replace placeholders.
            text = self._replace_placeholders(
                text, lang, traveller_sex, traveller_name, wanderer_name
            )
            # Replace quotes to a more usual version.
            if replace_quotes and lang in QUOTE_MAPPINGS:
                for quote, target in QUOTE_MAPPINGS[lang].items():
                    text = text.replace(quote, target)
            # Replace escaped newline characters.
            if replace_newline:
                text = text.replace('\\n', "\n")
            return text

        def list_get(l, index, default):
            return l[index] if len(l) > index else default

        traveller_id_ignore = (
            AVATAR_ID_LUMINE if traveller_sex == "male" else
            AVATAR_ID_AETHER
        )
        result = [{
            "id": avatar.id,
            "name": get(avatar.name_text_map_hash, unknown_name),
            "description": get(avatar.desc_text_map_hash),
            "birth_month": avatar.info_birth_month,
            "birth_day": avatar.info_birth_day,
            "affiliation": get(avatar.native_text_map_hash),
            "vision_before": get(avatar.vision_befor_text_map_hash),
            "vision_after": get(avatar.vision_after_text_map_hash),
            "vision_name_before": get(avatar.vision_name_befor_text_map_hash),
            "vision_name_after": get(avatar.vision_name_after_text_map_hash),
            "constellation_before": get(
                avatar.constellation_befor_text_map_hash
            ),
            "constellation_after": get(
                avatar.constellation_after_text_map_hash
            ),
            "title": get(avatar.title_text_map_hash),
            "detail": get(avatar.detail_text_map_hash),
            "association": avatar.assoc_type,
            "story_title_1": get(list_get(avatar.stories, 0, (-1, -1))[0]),
            "story_1": get(list_get(avatar.stories, 0, (-1, -1))[1]),
            "story_title_2": get(list_get(avatar.stories, 1, (-1, -1))[0]),
            "story_2": get(list_get(avatar.stories, 1, (-1, -1))[1]),
            "story_title_3": get(list_get(avatar.stories, 2, (-1, -1))[0]),
            "story_3": get(list_get(avatar.stories, 2, (-1, -1))[1]),
            "story_title_4": get(list_get(avatar.stories, 3, (-1, -1))[0]),
            "story_4": get(list_get(avatar.stories, 3, (-1, -1))[1]),
            "story_title_5": get(list_get(avatar.stories, 4, (-1, -1))[0]),
            "story_5": get(list_get(avatar.stories, 4, (-1, -1))[1]),
            "story_title_6": get(list_get(avatar.stories, 5, (-1, -1))[0]),
            "story_6": get(list_get(avatar.stories, 5, (-1, -1))[1]),
            "story_title_7": get(list_get(avatar.stories, 6, (-1, -1))[0]),
            "story_7": get(list_get(avatar.stories, 6, (-1, -1))[1]),
            "story_title_8": get(list_get(avatar.stories, 7, (-1, -1))[0]),
            "story_8": get(list_get(avatar.stories, 7, (-1, -1))[1]),
        } for avatar in tqdm.tqdm(self.avatar_dict.values())
          if avatar.id != traveller_id_ignore and
             avatar.id not in AVATAR_ID_BLACKLIST]
        df = pd.DataFrame.from_dict(result)
        df.to_csv(filepath, index=False)

    def export_items(
        self,
        filepath,
        lang: str,
        unknown_name: str,
        unknown_text: str,
        replace_quotes: bool,
        replace_newline: bool,
        remove_absent_text: bool,
    ):
        logging.info(f'Exporting items\' info to {filepath}')

        def get(text_hash, alternative_hash=None, default_text=unknown_text):
            if text_hash not in self.text_map and alternative_hash is not None:
                text_hash = alternative_hash
            if text_hash not in self.text_map:
                return default_text
            text = self.text_map[text_hash]
            # Remove XML tags.
            for pattern, target in XML_PATTERNS:
                text = pattern.sub(target, text)
            # Replace quotes to a more usual version.
            if replace_quotes and lang in QUOTE_MAPPINGS:
                for quote, target in QUOTE_MAPPINGS[lang].items():
                    text = text.replace(quote, target)
            # Replace escaped newline characters.
            if replace_newline:
                text = text.replace('\\n', "\n")
            return text

        result = [
            {
                "id": item_id,
                "name": get(item.name_text_map_hash, default_text=unknown_name),
                "description": get(item.desc1_text_map_hash,
                                   item.desc2_text_map_hash),
            }
            for item_id, item in self.item_dict.items()
            # Remove items with absent texts.
            if not remove_absent_text or (
                item.name_text_map_hash in self.text_map and (
                    item.desc1_text_map_hash in self.text_map or
                    item.desc2_text_map_hash in self.text_map
                )
            )
        ]
        # Filter out absent or unreleased items.
        result_filtered = []
        for item in result:
            if (
                lang in UNRELEASED_TAGS and
                (
                    any([tag in item["name"].lower()
                         for tag in UNRELEASED_TAGS[lang]]) or
                    any([tag in item["description"].lower()
                         for tag in UNRELEASED_TAGS[lang]])
                )
            ):
                continue
            result_filtered.append(item)
        df = pd.DataFrame.from_dict(result_filtered)
        df.to_csv(filepath, index=False)

    def export_weapons(
        self,
        filepath,
        lang: str,
        unknown_name: str,
        unknown_text: str,
        replace_quotes: bool,
        replace_newline: bool,
        remove_absent_text: bool,
    ):
        logging.info(f'Exporting weapons\' info to {filepath}')

        def post_process(text):
            # Remove XML tags.
            for pattern, target in XML_PATTERNS:
                text = pattern.sub(target, text)
            # Replace quotes to a more usual version.
            if replace_quotes and lang in QUOTE_MAPPINGS:
                for quote, target in QUOTE_MAPPINGS[lang].items():
                    text = text.replace(quote, target)
            # Replace escaped newline characters.
            if replace_newline:
                text = text.replace('\\n', "\n")
            # Remove leading and trailing newline characters and trim
            # consecutive empty lines.
            text = re.sub(r'\n{2,}', '\n\n', text.strip())
            return text

        result = [
            {
                "id": weapon.id,
                "name":
                    unknown_name
                    if weapon.name_text_map_hash not in self.text_map
                    else post_process(self.text_map[weapon.name_text_map_hash]),
                "type": weapon.type,
                "rank_level": weapon.rank_level,
                "description":
                    unknown_text
                    if weapon.desc_text_map_hash not in self.text_map
                    else post_process(self.text_map[weapon.name_text_map_hash]),
                "story":
                    unknown_text
                    if f'Weapon{weapon.id}' not in self.readable_dict
                    else post_process(self.readable_dict[f'Weapon{weapon.id}']),
            }
            for weapon in self.weapon_dict.values()
            # Remove weapons with absent texts.
            if not remove_absent_text or (
                weapon.name_text_map_hash in self.text_map and
                weapon.desc_text_map_hash in self.text_map and
                f'Weapon{weapon.id}' in self.readable_dict
            )
        ]
        # Filter out unreleased weapons.
        result_filtered = []
        for item in result:
            if (
                lang in UNRELEASED_TAGS and
                (
                    any([tag in item["name"].lower()
                         for tag in UNRELEASED_TAGS[lang]]) or
                    any([tag in item["description"].lower()
                         for tag in UNRELEASED_TAGS[lang]])
                )
            ):
                continue
            result_filtered.append(item)
        df = pd.DataFrame.from_dict(result_filtered)
        df.to_csv(filepath, index=False)

    def export_reliquaries(
        self,
        filepath,
        lang: str,
        unknown_name: str,
        unknown_text: str,
        replace_quotes: bool,
        replace_newline: bool,
    ):
        logging.info(f'Exporting reliquaries\' info to {filepath}')

        def post_process(text):
            # Remove XML tags.
            for pattern, target in XML_PATTERNS:
                text = pattern.sub(target, text)
            # Replace quotes to a more usual version.
            if replace_quotes and lang in QUOTE_MAPPINGS:
                for quote, target in QUOTE_MAPPINGS[lang].items():
                    text = text.replace(quote, target)
            # Replace escaped newline characters.
            if replace_newline:
                text = text.replace('\\n', "\n")
            # Remove leading and trailing newline characters and trim
            # consecutive empty lines.
            text = re.sub(r'\n{2,}', '\n\n', text.strip())
            return text

        def get(text_hash, default=unknown_text):
            if text_hash is None:
                return None
            elif text_hash in self.text_map:
                return post_process(self.text_map[text_hash])
            return default

        result = [{
            "id": reliquary_set.id,
            "set_name": get(reliquary_set.set_name_text_map_hash, unknown_name),
            "name_1": get(reliquary_set.name_text_map_hashs[0], unknown_name),
            "description_1": get(reliquary_set.desc_text_map_hashs[0],
                                 unknown_text),
            "story_1":
                "" if reliquary_set.name_text_map_hashs[0] is None else
                unknown_text
                if f'Relic{reliquary_set.id}_1' not in self.readable_dict
                else post_process(
                    self.readable_dict[f'Relic{reliquary_set.id}_1']
                ),
            "name_2": get(reliquary_set.name_text_map_hashs[1], unknown_name),
            "description_2": get(reliquary_set.desc_text_map_hashs[1],
                                 unknown_text),
            "story_2":
                "" if reliquary_set.name_text_map_hashs[1] is None else
                unknown_text
                if f'Relic{reliquary_set.id}_2' not in self.readable_dict
                else post_process(
                    self.readable_dict[f'Relic{reliquary_set.id}_2']
                ),
            "name_3": get(reliquary_set.name_text_map_hashs[2], unknown_name),
            "description_3": get(reliquary_set.desc_text_map_hashs[2],
                                 unknown_text),
            "story_3":
                "" if reliquary_set.name_text_map_hashs[2] is None else
                unknown_text
                if f'Relic{reliquary_set.id}_3' not in self.readable_dict
                else post_process(
                    self.readable_dict[f'Relic{reliquary_set.id}_3']
                ),
            "name_4": get(reliquary_set.name_text_map_hashs[3], unknown_name),
            "description_4": get(reliquary_set.desc_text_map_hashs[3],
                                 unknown_text),
            "story_4":
                "" if reliquary_set.name_text_map_hashs[3] is None else
                unknown_text
                if f'Relic{reliquary_set.id}_4' not in self.readable_dict
                else post_process(
                    self.readable_dict[f'Relic{reliquary_set.id}_4']
                ),
            "name_5": get(reliquary_set.name_text_map_hashs[4], unknown_name),
            "description_5": get(reliquary_set.desc_text_map_hashs[4],
                                 unknown_text),
            "story_5":
                "" if reliquary_set.name_text_map_hashs[4] is None else
                unknown_text
                if f'Relic{reliquary_set.id}_5' not in self.readable_dict
                else post_process(
                    self.readable_dict[f'Relic{reliquary_set.id}_5']
                ),
        } for reliquary_set in self.reliquary_set_dict.values()]
        # Filter out unreleased reliquaries.
        result_filtered = []
        for item in result:
            if (
                lang in UNRELEASED_TAGS and
                (
                    any(
                        any([
                            item[key] is not None and tag in item[key].lower()
                            for tag in UNRELEASED_TAGS[lang]
                        ]) for key in [
                            "set_name", "name_1", "description_1", "name_2",
                            "description_2", "name_3", "description_3",
                            "name_4", "description_4", "name_5", "description_5"
                        ]
                    )
                )
            ):
                continue
            result_filtered.append(item)
        df = pd.DataFrame.from_dict(result_filtered)
        df.to_csv(filepath, index=False)


def main(args):
    global database

    # Directories containing all the talks and dialogs.
    talk_dir_list = [
        os.path.join("BinOutput", "Talk", "ActivityGroup"),
        os.path.join("BinOutput", "Talk", "BlossomGroup"),
        os.path.join("BinOutput", "Talk", "GadgetGroup"),
        os.path.join("BinOutput", "Talk", "NpcGroup"),
    ]
    dialog_dir_list = [
        os.path.join("BinOutput", "Talk", "Activity"),
        os.path.join("BinOutput", "Talk", "Blossom"),
        os.path.join("BinOutput", "Talk", "Coop"),
        os.path.join("BinOutput", "Talk", "FreeGroup"),
        os.path.join("BinOutput", "Talk", "Gadget"),
        os.path.join("BinOutput", "Talk", "Npc"),
        os.path.join("BinOutput", "Talk", "NpcOther"),
        os.path.join("BinOutput", "Talk"),
    ]
    blacklist = [
        os.path.join("BinOutput", "Talk", "NpcGroup", "22.json"),
        os.path.join("BinOutput", "Talk", "NpcGroup", "23.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "1702.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "1712.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "1713.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "2231.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "2232.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "3208.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "4000.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "4001.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "4002.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "4003.json"),
        os.path.join("BinOutput", "Talk", "NpcOther", "4004.json"),
        os.path.join("BinOutput", "Talk", "4c370aaa.json"),
        os.path.join("BinOutput", "Talk", "66c42405.json"),
    ]
    quest_talk_dir = os.path.join(args.data_dir, "BinOutput", "Talk", "Quest")
    quest_dir = os.path.join(args.data_dir, "BinOutput", "Quest")

    # Collect talk files.
    talk_file_list = [
        os.path.join(args.data_dir, "ExcelBinOutput",
                     "TalkExcelConfigData.json"),
        os.path.join(args.data_dir, "ExcelBinOutput",
                     "RqTalkExcelConfigData.json"),
    ]
    for d in talk_dir_list:
        for f in os.listdir(os.path.join(args.data_dir, d)):
            if not f.endswith(".json"):
                continue
            if os.path.join(d, f) in blacklist:
                continue
            talk_file_list.append(os.path.join(args.data_dir, d, f))

    # Collect dialog files.
    dialog_file_list = [
        os.path.join(args.data_dir, "ExcelBinOutput",
                     "DialogExcelConfigData.json")
    ]
    for d in dialog_dir_list:
        for f in os.listdir(os.path.join(args.data_dir, d)):
            if not f.endswith(".json"):
                continue
            if os.path.join(d, f) in blacklist:
                continue
            dialog_file_list.append(os.path.join(args.data_dir, d, f))

    # Collect files containing talks in quests.
    quest_talk_file_list = []
    for f in os.listdir(quest_talk_dir):
        if os.path.join("BinOutput", "Talk", "Quest", f) in blacklist:
            continue
        quest_talk_file_list.append(os.path.join(quest_talk_dir, f))

    # Collect quest files.
    quest_file_list = []
    for f in os.listdir(quest_dir):
        if os.path.join("BinOutput", "Quest", f) in blacklist:
            continue
        quest_file_list.append(os.path.join(quest_dir, f))

    database = Database()

    # Parse talk files.
    logging.info("Parsing talk files.")
    for path in tqdm.tqdm(talk_file_list):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "talks" in data:
                data = data["talks"]
            # Then deal with some special cases where the field names are
            # obfusecated.
            elif (
                # I'm not sure what the field "JEMDGACPOPC" is, but it seems
                # like a kind of unique identifier.
                "JEMDGACPOPC" in data
            ):
                data = data["DMIMNILOLKP"]  # "DMIMNILOLKP" is "talks".
            elif (
                # "JDOFKFPHIDC" is "npcId".
                "JDOFKFPHIDC" in data
            ):
                data = data["PCNNNPLAEAI"]  # "PCNNNPLAEAI" is "talks"
            else:  # a single talk item
                data = [data]
        for item in data:
            database.add_talk(item, path)

    # Parse dialog files.
    logging.info("Parsing dialog files.")
    for path in tqdm.tqdm(dialog_file_list):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Special blacklist cases.
        if isinstance(data, dict) and \
                len(data) == 2 and \
                set(data.keys()) == set(["talkId", "type"]):
            continue
        if isinstance(data, dict):
            if "talkId" in data:
                talkId = data["talkId"]
            # Then deal with some special cases where the field names are
            # obfusecated.
            elif "FEOACBMDCKJ" in data:
                talkId = data["FEOACBMDCKJ"]
                if "AAOAAFLLOJI" not in data and "dialogList" not in data:
                    # Files without dialogList are useless.
                    continue
                data = data["AAOAAFLLOJI"]
            elif "PBAEPDPNKEJ" in data:
                talkId = data["PBAEPDPNKEJ"]
                if "KJNKFMPAGAA" not in data and "dialogList" not in data:
                    # Files without dialogList are useless.
                    continue
                data = data["KJNKFMPAGAA"]
            else:
                logging.info(f'Ignoring {path} since it seems not a dialog '
                             'file.')
                continue
        else:
            assert isinstance(data, list)
            if (
                len(data) > 0 and
                "id" not in data[0] and
                "GFLDJMJKIKE" not in data[0]
            ):
                logging.info(f'Ignoring {path} since it seems not a dialog '
                             'file.')
                continue
            talkId = -1
        if isinstance(data, dict):
            if "dialogList" in data:
                data = data["dialogList"]
            else: # a single dialog item
                data = [data]
        for item in data:
            database.add_dialog(item, talkId, path)

    # Parse quest talk files (possibly containing talks and/or dialogs).
    logging.info("Parsing quest talk files.")
    for path in tqdm.tqdm(quest_talk_file_list):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "talks" in data:
            for item in data["talks"]:
                database.add_talk(item, path)
        if "dialogList" in data:
            for item in data["dialogList"]:
                database.add_dialog(item, -1, path)

    # Parse quest files.
    logging.info("Parsing quest files.")
    for path in tqdm.tqdm(quest_file_list):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        database.add_quest(data, path)

    # Parse chapter files.
    logging.info("Parsing chapter files.")
    with open(
        os.path.join(
            args.data_dir, "ExcelBinOutput", "ChapterExcelConfigData.json"
        ), "r", encoding="utf-8"
    ) as f:
        data = json.load(f)
        for item in data:
            database.add_chapter(item)

    # Parse avatar info.
    logging.info("Parsing avatar files.")
    with open(os.path.join(
        args.data_dir, "ExcelBinOutput", "AvatarExcelConfigData.json"
    ), "r", encoding="utf-8") as file_avatar_info, \
    open(os.path.join(
        args.data_dir, "ExcelBinOutput", "FetterInfoExcelConfigData.json"
    ), "r", encoding="utf-8") as file_fetter_info, \
    open(os.path.join(
        args.data_dir, "ExcelBinOutput", "FettersExcelConfigData.json"
    ), "r", encoding="utf-8") as file_fetters, \
    open(os.path.join(
        args.data_dir, "ExcelBinOutput", "FetterStoryExcelConfigData.json"
    ), "r", encoding="utf-8") as file_fetter_story:
        avatar_info = json.load(file_avatar_info)
        fetter_info = json.load(file_fetter_info)
        fetters = json.load(file_fetters)
        fetter_story = json.load(file_fetter_story)
        database.collect_avatar_info(
            avatar_info, fetter_info, fetters, fetter_story
        )

    # Parse item info.
    logging.info("Parsing item info.")
    with open(os.path.join(
        args.data_dir, "ExcelBinOutput", "MaterialExcelConfigData.json"
    ), "r", encoding="utf-8") as file_material_info, \
    open(os.path.join(
        args.data_dir, "ExcelBinOutput", "MaterialCodexExcelConfigData.json"
    ), "r", encoding="utf-8") as file_material_codex_info:
        material_info = json.load(file_material_info)
        material_codex_info = json.load(file_material_codex_info)
        database.collect_item_info(material_info, material_codex_info)

    # Parse weapon info.
    logging.info("Parsing weapon info.")
    with open(os.path.join(
        args.data_dir, "ExcelBinOutput", "WeaponExcelConfigData.json"
    ), "r", encoding="utf-8") as file_weapon_info:
        weapon_info = json.load(file_weapon_info)
        database.collect_weapon_info(weapon_info)

    # Parse reliquary info.
    logging.info("Parsing reliquary info.")
    with open(os.path.join(
        args.data_dir, "ExcelBinOutput", "ReliquaryExcelConfigData.json"
    ), "r", encoding="utf-8") as file_reliquary_info, \
    open(os.path.join(
        args.data_dir, "ExcelBinOutput", "ReliquarySetExcelConfigData.json"
    ), "r", encoding="utf-8") as file_reliquary_set_info, \
    open(os.path.join(
        args.data_dir, "ExcelBinOutput", "EquipAffixExcelConfigData.json"
    ), "r", encoding="utf-8") as file_equip_affix_info:
        reliquary_info = json.load(file_reliquary_info)
        reliquary_set_info = json.load(file_reliquary_set_info)
        equip_affix_info = json.load(file_equip_affix_info)
        database.collect_reliquary_info(
            reliquary_info, reliquary_set_info, equip_affix_info
        )

    # Collect prev_talks for each talk.
    database.collect_prev_talks()

    # Remove talks containing non-existing dialogs.
    num_talks = len(database.talk_dict)
    num_talks_dropped = database.clean_data()
    logging.info(f'Dropped {num_talks_dropped}/{num_talks} talks because some '
                 'dialogs of these talks are absent.')

    # Build the connections among the quests.
    database.connect_quests(args.remove_quest_cycles == "true")

    # Build the sources, while find a minimum number of traces for each source
    # that cover all the dialogs.
    database.build_sources()

    # Build the connections among the sources.
    database.connect_sources()

    # Load texts.
    database.load_text_map(
        os.path.join(args.data_dir, "TextMap", f'TextMap{args.lang}.json')
    )
    database.load_npc_name(
        os.path.join(args.data_dir, "ExcelBinOutput", "NpcExcelConfigData.json")
    )
    database.load_readable(os.path.join(args.data_dir, "Readable", args.lang))

    mate_name = args.mate_name
    if mate_name is None:
        mate_name = (
            database.npc_name_map[NPC_ID_AETHER]
            if args.traveller_sex == "female" else
            database.npc_name_map[NPC_ID_LUMINE]
        )

    # Export all the output files.
    os.makedirs(args.output_dir, exist_ok=True)
            
    database.export_dialogs(
        filepath=os.path.join(args.output_dir, "dialog.json"),
        lang=args.lang,
        traveller_sex=args.traveller_sex,
        traveller_name=args.traveller_name,
        mate_name=mate_name,
        wanderer_name=args.wanderer_name,
        narrator_name=args.narrator_name,
        unknown_name=args.unknown_name,
        unknown_text=args.unknown_text,
        replace_quotes=args.replace_quotes == "true",
        replace_newline=args.replace_newline == "true",
        remove_broken_trace=args.remove_broken_trace == "true",
        remove_absent_text=args.remove_absent_text == "true",
    )

    database.export_quests(
        filepath=os.path.join(args.output_dir, "quest.json"),
        lang=args.lang,
        traveller_sex=args.traveller_sex,
        traveller_name=args.traveller_name,
        wanderer_name=args.wanderer_name,
        unknown_text=args.unknown_text,
        replace_quotes=args.replace_quotes == "true",
        replace_newline=args.replace_newline == "true",
    )

    database.export_avatars(
        filepath=os.path.join(args.output_dir, "avatar.csv"),
        lang=args.lang,
        traveller_sex=args.traveller_sex,
        traveller_name=args.traveller_name,
        wanderer_name=args.wanderer_name,
        unknown_name=args.unknown_name,
        unknown_text=args.unknown_text,
        replace_quotes=args.replace_quotes == "true",
        replace_newline=args.replace_newline == "true",
    )

    database.export_items(
        filepath=os.path.join(args.output_dir, "item.csv"),
        lang=args.lang,
        unknown_name=args.unknown_name,
        unknown_text=args.unknown_text,
        replace_quotes=args.replace_quotes == "true",
        replace_newline=args.replace_newline == "true",
        remove_absent_text=args.remove_absent_text == "true",
    )

    database.export_weapons(
        filepath=os.path.join(args.output_dir, "weapon.csv"),
        lang=args.lang,
        unknown_name=args.unknown_name,
        unknown_text=args.unknown_text,
        replace_quotes=args.replace_quotes == "true",
        replace_newline=args.replace_newline == "true",
        remove_absent_text=args.remove_absent_text == "true",
    )

    database.export_reliquaries(
        filepath=os.path.join(args.output_dir, "reliquary.csv"),
        lang=args.lang,
        unknown_name=args.unknown_name,
        unknown_text=args.unknown_text,
        replace_quotes=args.replace_quotes == "true",
        replace_newline=args.replace_newline == "true",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_dir", type=str,
        help="Directory containing the extracted game data.")
    parser.add_argument(
        "--output_dir", type=str, default="exp/output",
        help="The output directory.")
    parser.add_argument(
        "--remove_quest_cycles", choices=["true", "false"], default="true",
        help="Whether remove some connections among the quests to avoid cycles."
        "Default to true.")
    parser.add_argument(
        "--lang", type=str, default="CHS", choices=[
            "CHS", "CHT", "DE", "EN", "ES", "FR", "ID", "IT", "JP", "KR", "PT",
            "RU", "TH", "TR", "VI",
        ],
        help="The language of the outputted text.")
    parser.add_argument(
        "--traveller_sex", choices=["male", "female"], default="female",
        help="Traveller's sex. Determines some contents of the text.")
    parser.add_argument(
        "--traveller_name", type=str, default="旅行者",
        help="Traveller's name to be filled into the placeholders in the text.")
    parser.add_argument(
        "--mate_name", type=str, default=None,
        help="Traveller's mate's name to be filled into the placeholders in "
        "the text.")
    parser.add_argument(
        "--wanderer_name", type=str, default="流浪者",
        help="Wanderer (Scaramouche)'s name to be filled into the placeholders "
        "in the text.'")
    parser.add_argument(
        "--narrator_name", type=str, default="`旁白`",
        help="The narrator's name to be used with texts on blackscreen, etc.")
    parser.add_argument(
        "--unknown_name", type=str, default="`未知`",
        help="A special name to indicate that the speaker's name is absent in "
        "the input data.")
    parser.add_argument(
        "--unknown_text", type=str, default="`未知`",
        help="A special string to indicate that the text is absent in the "
        "input data.")
    parser.add_argument(
        "--replace_quotes", choices=["true", "false"], default="true",
        help="Whether replace the quote characters to the more usual version."
        "Default to true.")
    parser.add_argument(
        "--replace_newline", choices=["true", "false"], default="true",
        help="Whether replace the escaped newline characters to the unescaped "
        "version. Default to true.")
    parser.add_argument(
        "--remove_broken_trace", choices=["true", "false"], default="false",
        help="Whether remove traces with absent content. Default to false.")
    parser.add_argument(
        "--remove_absent_text", choices=["true", "false"], default="true",
        help="Whether remove the absent text. Default to true. If false, they "
        "will be replaced by the value of the argument `unknown_text`.")
    args = parser.parse_args()
    main(args)

