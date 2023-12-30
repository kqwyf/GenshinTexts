import os
import sys
import json
import tqdm
import pickle
import argparse
from typing import List

talkDirList = [
    os.path.join("BinOutput", "Talk", "ActivityGroup"),
    os.path.join("BinOutput", "Talk", "BlossomGroup"),
    os.path.join("BinOutput", "Talk", "GadgetGroup"),
    os.path.join("BinOutput", "Talk", "NpcGroup"),
]

dialogDirList = [
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
    os.path.join("BinOutput", "Talk", "NpcOther", "3208.json"),
    os.path.join("BinOutput", "Talk", "NpcOther", "4000.json"),
    os.path.join("BinOutput", "Talk", "NpcOther", "4001.json"),
    os.path.join("BinOutput", "Talk", "NpcOther", "4002.json"),
    os.path.join("BinOutput", "Talk", "NpcOther", "4003.json"),
    os.path.join("BinOutput", "Talk", "NpcOther", "4004.json"),
    os.path.join("BinOutput", "Talk", "4c370aaa.json"),
    os.path.join("BinOutput", "Talk", "66c42405.json"),
]

class Talk:
    def __init__(
        self,
        id: int,
        source: str,
        npcId: List[int] = [],
        initDialog: int = -1,
        nextTalks: List[int] = [],
        trusted=True,
        **kwargs
    ):
        self.id = id
        self.npcId = npcId # maybe empty
        self.nextTalks = nextTalks # maybe empty
        self.initDialog = initDialog # -1 means not specified, so we read the
                                     # dialog in the order of the dialogList
        self.source = source
        self.trusted = trusted # If False, it won't corrupt with the same Talk
                               # from another source

    def __eq__(self, __value: object) -> bool:
        return isinstance(__value, Talk) and \
               self.id == __value.id and \
               self.npcId == __value.npcId and \
               self.nextTalks == __value.nextTalks and \
               self.initDialog == __value.initDialog

class Dialog:
    def __init__(
        self,
        id: int,
        talkId: int,
        role: int,
        source: str,
        talkContentTextMapHash: int = -1,
        talkRoleNameTextMapHash: int = -1,
        nextDialogs: List[int] = [],
        trusted=True,
        **kwargs
    ):
        self.id = id
        self.talkId = talkId # -1 means this dialog comes from a quest or the
                             # talkId is missing
        self.role = role # 0 represents player.
                         # -1 means the role field is invalid in the data.
                         # -2 represents narrator.
                         # -3 represents the mate avatar.
        self.talkContentTextMapHash = talkContentTextMapHash # -1 means the
                                                             # field is missing
        self.talkRoleNameTextMapHash = talkRoleNameTextMapHash # -1 means not
                                                               # existing
        self.nextDialogs = nextDialogs # maybe empty
        self.source = source
        self.trusted = trusted # If False, it won't corrupt with the same Talk
                               # from another source.

    def __eq__(self, __value: object) -> bool:
        # We do not check talkId since there is confliction in the original data
        # and it does not mean a lot to us.
        return isinstance(__value, Dialog) and \
               self.id == __value.id and \
               self.role == __value.role and \
               self.talkContentTextMapHash == \
                    __value.talkContentTextMapHash and \
               self.talkRoleNameTextMapHash == \
                    __value.talkRoleNameTextMapHash and \
               self.nextDialogs == __value.nextDialogs

    def update(self, item) -> bool:
        assert self.id == item.id, str(self) + ", " + str(item)
        # We do not check talkId since there is confliction in the original data
        # and it does not mean a lot to us.
        if item.talkId >= 0:
            if self.talkId >= 0 and item.talkId != self.talkId:
                pass
                #return False
            self.talkId = item.talkId
        # we always update role since there is confliction in the original data
        if item.role >= 0:
            #if self.role >= 0 and item.role != self.role:
            #    return False
            self.role = item.role
        if item.talkRoleNameTextMapHash >= 0:
            if self.talkRoleNameTextMapHash >= 0 and \
                    item.talkRoleNameTextMapHash \
                    != self.talkRoleNameTextMapHash:
                return False
            self.talkRoleNameTextMapHash = item.talkRoleNameTextMapHash
        self.nextDialogs = sorted(
                list(set(self.nextDialogs) | set(item.nextDialogs)))
        self.source = item.source + ":" + self.source
        return True

    def __str__(self):
        return f'id: {self.id}, ' \
               f'talkId: {self.talkId}, ' \
               f'role: {self.role}, ' \
               f'talkContentTextMapHash: {self.talkContentTextMapHash}, ' \
               f'talkRoleNameTextMapHash: {self.talkRoleNameTextMapHash}, ' \
               f'nextDialogs: {self.nextDialogs}'

def addTalk(item, path, talkDict):
    if "id" not in item:
        # Deal with some special cases.
        if "JOLEJEFDNJJ" in item and item["JOLEJEFDNJJ"] in [6800002, 80045]:
            item["id"] = item["JOLEJEFDNJJ"]
            item["initDialog"] = item["FBALOFKGJKN"]
            item["trusted"] = False
        else:
            # Cannot resolve.
            print(f'ERROR: Key "id" not exists in some item of {path} . ' \
                  f'Item detail:\n{str(item)}', file=sys.stderr)
            exit(1)
    talkId = item["id"]
    talkItem = Talk(**item, source=path)
    if talkId not in talkDict:
        talkDict[talkId] = talkItem
    else:
        if not talkItem == talkDict[talkId] and talkItem.trusted:
            if talkDict[talkId].trusted:
                print(f'ERROR: Talk {talkId} differs between {path} and ' \
                      f'{talkDict[talkId].source}', file=sys.stderr)
                exit(1)
            else:
                talkDict[talkId] = talkItem

def addDialog(item, talkId, path, dialogDict):
    # In DialogExcelConfigData.json, "GFLDJMJKIKE" is the id field.
    if "id" not in item and "GFLDJMJKIKE" not in item:
        # Deal with some special cases.
        if "JOLEJEFDNJJ" in item and \
                item["JOLEJEFDNJJ"] in [680000201, 680000202, 8004501, 8004502,
                                        8004503]:
            item["id"] = item["JOLEJEFDNJJ"]
            if "CLMNEDLMAJL" in item:
                item["nextDialogs"] = item["CLMNEDLMAJL"]
            if "IFAOOKCBDGD" in item:
                item["talkRole"] = item["IFAOOKCBDGD"]
            if "EMKCOIBADBJ" in item:
                item["talkContentTextMapHash"] = item["EMKCOIBADBJ"]
            item["trusted"] = False
        else:
            print(f'ERROR: Key "id" not exists in some item of {path} . ' \
                  f'Item detail:\n{str(item)}', file=sys.stderr)
            exit(1)
    elif "GFLDJMJKIKE" in item:
        item["id"] = item["GFLDJMJKIKE"]
    if "talkRole" not in item:
        print(f'ERROR: Invalid dialog {item["id"]} in {path}', file=sys.stderr)
        exit(1)
    dialogId = item["id"]
    if "talkRole" not in item or \
            "type" not in item["talkRole"] or \
            "id" not in item["talkRole"] or \
            (
                item["talkRole"]["type"] != "TALK_ROLE_PLAYER" and \
                not item["talkRole"]["id"].isnumeric()
            ):
        role = -1
    else:
        role = 0 if item["talkRole"]["type"] == "TALK_ROLE_PLAYER" else \
               int(item["talkRole"]["id"])
    dialogItem = Dialog(**item, talkId=talkId, role=role, source=path)
    if dialogId not in dialogDict:
        dialogDict[dialogId] = dialogItem
    else:
        if not dialogItem == dialogDict[dialogId] and dialogItem.trusted:
            if dialogDict[dialogId].trusted:
                # try to merge them
                if not dialogDict[dialogId].update(dialogItem):
                    print(f'ERROR: Dialog {dialogId} differs between {path} '
                          f'and {dialogDict[dialogId].source}', file=sys.stderr)
                    print(str(dialogDict[dialogId]))
                    print(str(dialogItem))
                    exit(1)
            else:
                dialogDict[dialogId] = dialogItem

def get_avatar_info(repo):
    avatar_info = {}

    with open(os.path.join(repo, "ExcelBinOutput/AvatarExcelConfigData.json"),
              "r", encoding="utf-8") as f:
        infoList = json.load(f)
        for info in infoList:
            avatar_name = info["nameTextMapHash"]
            avatar_desc = info["descTextMapHash"]
            avatar_id = info["id"]
            avatar_info[avatar_id] = {
                "name": avatar_name,
                "desc": avatar_desc,
                "sayings": [],
                "story": [],
            }

    with open(
            os.path.join(repo, "ExcelBinOutput/FetterInfoExcelConfigData.json"),
            "r", encoding="utf-8") as f:
        infoList = json.load(f)
        for info in infoList:
            avatar_id = info["avatarId"]
            if avatar_id not in avatar_info:
                continue
            for field, value in info.items():
                if "TextMapHash" in field or "Birth" in field:
                    field = field.replace("TextMapHash", "")
                    avatar_info[avatar_id][field] = value

    with open(os.path.join(repo, "ExcelBinOutput/FettersExcelConfigData.json"),
              "r", encoding="utf-8") as f:
        infoList = json.load(f)
        for info in infoList:
            avatar_id = info["avatarId"]
            avatar_info[avatar_id]["sayings"].append((
                info["voiceTitleTextMapHash"],
                info["voiceFileTextTextMapHash"],
            ))

    with open(os.path.join(repo,
                           "ExcelBinOutput/FetterStoryExcelConfigData.json"),
              "r", encoding="utf-8") as f:
        infoList = json.load(f)
        for info in infoList:
            avatar_id = info["avatarId"]
            avatar_info[avatar_id]["story"].append((
                info["storyTitleTextMapHash"],
                info["storyContextTextMapHash"],
            ))

    return avatar_info

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_dir",
        type=str,
    )
    parser.add_argument(
        "output_path",
        type=str,
    )
    args = parser.parse_args()
    dataDir = args.data_dir
    outputPath = args.output_path

    talkFileList = [
        os.path.join(dataDir, "ExcelBinOutput", "TalkExcelConfigData.json"),
        os.path.join(dataDir, "ExcelBinOutput", "RqTalkExcelConfigData.json"),
    ]
    for d in talkDirList:
        for f in os.listdir(os.path.join(dataDir, d)):
            if not f.endswith(".json"):
                continue
            if os.path.join(d, f) in blacklist:
                continue
            talkFileList.append(os.path.join(dataDir, d, f))

    dialogFileList = [os.path.join(dataDir, "ExcelBinOutput",
                                   "DialogExcelConfigData.json")]
    for d in dialogDirList:
        for f in os.listdir(os.path.join(dataDir, d)):
            if not f.endswith(".json"):
                continue
            if os.path.join(d, f) in blacklist:
                continue
            dialogFileList.append(os.path.join(dataDir, d, f))

    questFileList = []
    for f in os.listdir(os.path.join(dataDir, "BinOutput", "Talk", "Quest")):
        if os.path.join("BinOutput", "Talk", "Quest", f) in blacklist:
            continue
        questFileList.append(os.path.join(dataDir, "BinOutput", "Talk", "Quest",
                                          f))

    talkDict = {}
    dialogDict = {}

    # Parse talk files.
    print("Parsing talk files.")
    for path in tqdm.tqdm(talkFileList):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            if "talks" in data:
                data = data["talks"]
            elif "JEMDGACPOPC" in data and \
                    data["JEMDGACPOPC"] in [38001, 53001]: # special cases
                data = data["DMIMNILOLKP"]
            else: # a single talk item
                data = [data]
        for item in data:
            addTalk(item, path, talkDict)

    # Parse dialog files.
    print("Parsing dialog files.")
    for path in tqdm.tqdm(dialogFileList):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # special blacklist cases.
        if isinstance(data, dict) and \
                len(data) == 2 and \
                set(data.keys()) == set(["talkId", "type"]):
            continue
        if isinstance(data, dict):
            if "talkId" in data:
                talkId = data["talkId"]
            elif "PBAEPDPNKEJ" in data and \
                    data["PBAEPDPNKEJ"] in [6800002, 80045]: # special cases
                talkId = data["PBAEPDPNKEJ"]
                data = data["KJNKFMPAGAA"]
            else:
                print(f'ERROR: Key "talkId" not exists in {path}',
                      file=sys.stderr)
                exit(1)
        else:
            assert isinstance(data, list)
            talkId = -1
        if isinstance(data, dict):
            if "dialogList" in data:
                data = data["dialogList"]
            else: # a single dialog item
                data = [data]
        for item in data:
            addDialog(item, talkId, path, dialogDict)

    # Parse quest files (possibly containing talks and/or dialogs).
    print("Parsing quest files.")
    for path in tqdm.tqdm(questFileList):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "talks" in data:
            for item in data["talks"]:
                addTalk(item, path, talkDict)
        if "dialogList" in data:
            for item in data["dialogList"]:
                addDialog(item, -1, path, dialogDict)

    # Parse avatar info.
    # Thanks to mrzjy's work.
    avatarInfo = get_avatar_info(dataDir)

    print("Saving to " + outputPath)
    with open(outputPath, "wb") as f:
        pickle.dump((talkDict, dialogDict, avatarInfo), f)

    print("Num talks: " + str(len(talkDict)))
    print("Num dialogs: " + str(len(dialogDict)))

if __name__ == "__main__":
    main()

