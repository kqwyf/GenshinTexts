import os
import pickle
import copy
import json
import tqdm
import argparse

from extract import Talk, Dialog

TRAVELLER_AVATAR_IDS = [10000005, 10000007]
PAIMON_NPC_ID = 1005
PAIMON_NAME_HASH = 1356475093

# system questions and answers (using variable name of the textmap hash)
SYSTEM_TALKS = [
    {
        "question": "%s属于哪里？",
        "answer": "%s",
        "args": ["avatarNative"],
    },
    {
        "question": "%s使用哪种元素力？",
        "answer": "%s",
        "args": ["avatarVisionBefor"],
    },
    {
        "question": "%s的命之座是？",
        "answer": "%s",
        "args": ["avatarConstellationBefor"],
    },
    {
        "question": "%s的称号是？",
        "answer": "%s",
        "args": ["avatarTitle"],
    },
    {
        "question": "用一句话介绍%s？",
        "answer": "%s",
        "args": ["avatarDetail"],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 0, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 1, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 2, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 3, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 4, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 5, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 6, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 7, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 8, 1)],
    },
    {
        "question": "讲一些%s的故事？",
        "answer": "%s",
        "args": [("story", 9, 1)],
    },
]

talkDict = {}
dialogDict = {}
dialogDictsByTalkId = {}

def getAttr(obj, key):
    if not (isinstance(key, tuple) or isinstance(key, list)):
        return obj[key] if key in obj else None
    if len(key) == 1:
        return obj[key[0]] if key[0] in obj else None
    return getAttr(obj[key[0]], key[1:]) if key[0] in obj else None

def addResult(stack, results):
    if len(stack) > 0:
        results.append(copy.deepcopy(stack))
        if len(results) > 500:
            return False
    return True

def findFirstDialogs(dialogDict, dialogsWithParent):
    for dialog in dialogDict.values():
        for id in dialog.nextDialogs:
            dialogsWithParent.add(id)
    return [dialog.id for dialog in dialogDict.values() if dialog.id not in dialogsWithParent]

def dfsTalk(talk, results, isPlayer, stack, talkSet, dialogSet, n):
    # stack structure: [(role, talkRoleNameTextMapHash, talkContentTextMapHash), ...]
    if n > 10000:
        return False
    talkSet.add(talk.id)
    if talk.initDialog != -1 and talk.initDialog in dialogDict:
        if talk.initDialog not in dialogSet:
            dfsDialog(dialogDict[talk.initDialog], results, isPlayer, talk.nextTalks, stack, talkSet, dialogSet, n + 1)
        else:
            if not addResult(stack, results):
                return False
    elif talk.id in dialogDictsByTalkId:
        firstDialogs = findFirstDialogs(dialogDictsByTalkId[talk.id], set())
        if len(firstDialogs) > 0:
            flag = False
            for dialogId in firstDialogs:
                if dialogId not in dialogDict:
                    flag = True
                elif dialogId not in dialogSet:
                    flag = True
                    dfsDialog(dialogDict[dialogId], results, isPlayer, talk.nextTalks, stack, talkSet, dialogSet, n + 1)
            if not flag:
                if not addResult(stack, results):
                    return False
    else:
        if not addResult(stack, results):
            return False
    talkSet.remove(talk.id)
    return True

def dfsDialog(dialog, results, isPlayer, nextTalks, stack, talkSet, dialogSet, n):
    # stack structure: [(role, talkRoleNameTextMapHash, talkContentTextMapHash), ...]
    if n > 10000:
        return False
    dialogSet.add(dialog.id)
    stack.append((0 if isPlayer else dialog.role, dialog.talkRoleNameTextMapHash, dialog.talkContentTextMapHash))
    if len(dialog.nextDialogs) > 0:
        flag = False
        for nextId in dialog.nextDialogs:
            if nextId in dialogDict and nextId not in dialogSet:
                flag = True
                dfsDialog(dialogDict[nextId], results, len(dialog.nextDialogs) > 1, nextTalks, stack, talkSet, dialogSet, n + 1)
        if not flag:
            if not addResult(stack, results):
                return False
    elif len(nextTalks) > 0:
        flag = False
        for nextId in nextTalks:
            if nextId in talkDict and nextId not in talkSet:
                flag = True
                dfsTalk(talkDict[nextId], results, len(nextTalks) > 1, stack, talkSet, dialogSet, n + 1)
        if not flag:
            if not addResult(stack, results):
                return False
    else:
        if not addResult(stack, results):
            return False
    stack.pop()
    dialogSet.remove(dialog.id)
    return True

def bfs(obj):
    results = []

    # bfs queue. this queue do not pop items
    q = [(obj, int(-1), int(-1))] # (current talk/dialog, previous item in queue, parent talk (only for dialogs to obtain nextTalks))

    talkSet = set()
    dialogSet = set()
    if isinstance(obj, Talk):
        talkSet.add(obj.id)
    else:
        dialogSet.add(obj.id)

    def addItem(prevId, nextId, itemSet, itemDict, parentId):
        itemSet.add(nextId)
        q.append((itemDict[nextId], prevId, parentId))
        if len(q) > 1000000:
            return False
        return True

    def generateResult(index):
        result = []
        obj, prevIndex, _ = q[index]
        if isinstance(obj, Dialog):
            if prevIndex >= 0:
                prev, _, prevParentId = q[prevIndex]
                isPlayer = (isinstance(prev, Dialog) and len(prev.nextDialogs) > 1) or \
                           (isinstance(prev, Talk) and prevParentId != -1 and \
                            len(talkDict[prevParentId].nextTalks) > 0)
            else:
                isPlayer = False
            result.append((0 if isPlayer else obj.role, obj.talkRoleNameTextMapHash, obj.talkContentTextMapHash))
        while prevIndex >= 0:
            obj, prevIndex, _ = q[prevIndex]
            if isinstance(obj, Dialog):
                if prevIndex >= 0:
                    prev, _, prevParentId = q[prevIndex]
                    isPlayer = (isinstance(prev, Dialog) and len(prev.nextDialogs) > 1) or \
                               (isinstance(prev, Talk) and prevParentId != -1 and \
                                len(talkDict[prevParentId].nextTalks) > 0)
                else:
                    isPlayer = False
                result.append((0 if isPlayer else obj.role, obj.talkRoleNameTextMapHash, obj.talkContentTextMapHash))
        return result[::-1]

    i = 0
    while i < len(q):
        obj, _, parentId = q[i]
        flag = False # whether there is any further searching paths
        if isinstance(obj, Talk):
            if obj.initDialog != -1 and obj.initDialog in dialogDict:
                if obj.initDialog not in dialogSet:
                    flag = True
                    if not addItem(i, obj.initDialog, dialogSet, dialogDict, obj.id):
                        return None
            elif obj.id in dialogDictsByTalkId:
                firstDialogs = findFirstDialogs(dialogDictsByTalkId[obj.id], set())
                for dialogId in firstDialogs:
                    if dialogId in dialogDict and dialogId not in dialogSet:
                        flag = True
                        if not addItem(i, dialogId, dialogSet, dialogDict, obj.id):
                            return None
        else:
            if len(obj.nextDialogs) > 0:
                for nextId in obj.nextDialogs:
                    if nextId in dialogDict and nextId not in dialogSet:
                        flag = True
                        if not addItem(i, nextId, dialogSet, dialogDict, parentId):
                            return None
            else:
                for nextId in talkDict[parentId].nextTalks:
                    if nextId in talkDict and nextId not in talkSet:
                        flag = True
                        if not addItem(i, nextId, talkSet, talkDict, parentId):
                            return None
        if not flag:
            results.append(generateResult(i))
        i += 1
    return results

def splitTalkWithPaimon(text, paimonName):
    result = []
    for turn in text.split("\\n"):
        splits = turn.replace(": ", "：").split("：")
        spkName, content = turn[:len(splits[0])].strip(), turn[len(splits[0]) + 1:].strip()
        result.append({
            "role": 0 if "{NICKNAME}" in spkName else PAIMON_NPC_ID,
            "roleName": spkName.replace("{NICKNAME}", "`Traveller`") if "{NICKNAME}" in spkName else paimonName,
            "content": "#" + content,
        })
    return result

def main():
    global talkDict, dialogDict, dialogDictsByTalkId, textMap

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "data_path",
        type=str,
    )
    parser.add_argument(
        "npc_map_path",
        type=str,
    )
    parser.add_argument(
        "text_map_path",
        type=str,
    )
    parser.add_argument(
        "output_path",
        type=str,
    )
    parser.add_argument(
        "--traveller_sex",
        choices=["male", "female"],
        default="female",
    )
    args = parser.parse_args()

    dataPath = args.data_path
    npcMapPath = args.npc_map_path
    textMapPath = args.text_map_path
    outputPath = args.output_path

    textMap = {}
    with open(textMapPath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for key in data:
            textMap[int(key)] = data[key]

    npcNameMap = {}
    with open(npcMapPath, "r", encoding="utf-8") as f:
        data = json.load(f)
        for item in data:
            if "nameTextMapHash" in item and item["nameTextMapHash"] in textMap and len(textMap[item["nameTextMapHash"]]) > 0:
                npcNameMap[item["id"]] = textMap[item["nameTextMapHash"]]

    with open(dataPath, "rb") as f:
        talkDict, dialogDict, avatarInfo = pickle.load(f)
    for id in talkDict:
        talkDict[id].used = False
    for id in dialogDict:
        dialogDict[id].used = False
    dialogDictsByTalkId = {}
    for dialog in dialogDict.values():
        if dialog.talkId != -1:
            if dialog.talkId not in dialogDictsByTalkId:
                dialogDictsByTalkId[dialog.talkId] = {}
            dialogDictsByTalkId[dialog.talkId][dialog.id] = dialog

    talksWithParent = set()
    dialogsWithParent = set()
    for talk in talkDict.values():
        dialogsWithParent.add(talk.initDialog)
        for id in talk.nextTalks:
            talksWithParent.add(id)
    firstTalks = [talk.id for talk in talkDict.values() if talk.id not in talksWithParent]
    firstDialogs = findFirstDialogs(dialogDict, dialogsWithParent)

    dfsCount = 0
    bfsCount = 0

    finalResults = {}

    print("Processing talks.")
    for id in tqdm.tqdm(firstTalks):
        results = []
        dfsCount += 1
        if not dfsTalk(talkDict[id], results, False, [], set(), set(), 0):
            dfsCount -= 1
            bfsCount += 1
            results = bfs(talkDict[id])
            assert results is not None, id
        finalResults[f'talk_{id}'] = []
        for result in results:
            finalDialog = []
            for role, talkRoleNameTextMapHash, talkContentTextMapHash in result:
                if role == 0:
                    roleName = "`Traveller`"
                elif talkRoleNameTextMapHash in textMap and len(textMap[talkRoleNameTextMapHash]) > 0:
                    roleName = textMap[talkRoleNameTextMapHash]
                elif role > 0 and role in npcNameMap:
                    roleName = npcNameMap[role]
                else:
                    roleName = "`unknown`"
                if talkContentTextMapHash in textMap and len(textMap[talkContentTextMapHash]) > 0:
                    content = textMap[talkContentTextMapHash]
                else:
                    content = "`unknown`"
                finalDialog.append({"role": role, "roleName": roleName, "content": content})
            finalResults[f'talk_{id}'].append(finalDialog)

    print("Processing dialogs.")
    for id in tqdm.tqdm(firstDialogs):
        results = []
        dfsCount += 1
        if not dfsDialog(dialogDict[id], results, False, [], [], set(), set(), 0):
            dfsCount -= 1
            bfsCount += 1
            results = bfs(dialogDict[id])
            assert results is not None, id
        finalResults[f'dialog_{id}'] = []
        for result in results:
            finalDialog = []
            for role, talkRoleNameTextMapHash, talkContentTextMapHash in result:
                if role == 0:
                    roleName = "`Traveller`"
                elif talkRoleNameTextMapHash in textMap and len(textMap[talkRoleNameTextMapHash]) > 0:
                    roleName = textMap[talkRoleNameTextMapHash]
                elif role > 0 and role in npcNameMap:
                    roleName = npcNameMap[role]
                else:
                    roleName = "`unknown`"
                if talkContentTextMapHash in textMap and len(textMap[talkContentTextMapHash]) > 0:
                    content = textMap[talkContentTextMapHash]
                else:
                    content = "`unknown`"
                finalDialog.append({"role": role, "roleName": roleName, "content": content})
            finalResults[f'dialog_{id}'].append(finalDialog)

    print("Processing avatar infos")
    travellerId = 10000005 if args.traveller_sex == "male" else 10000007
    paimonName = textMap[PAIMON_NAME_HASH]
    for avatarId, info in tqdm.tqdm(avatarInfo.items()):
        for i, sayings in enumerate(info["sayings"]):
            topic, content = sayings
            if avatarId in TRAVELLER_AVATAR_IDS:
                # only track dialogs from the traveller of chosen sex
                if avatarId == travellerId:
                    if content not in textMap:
                        continue
                    content_text = textMap[content]
                    if not (("{NICKNAME}：" in content_text or "{NICKNAME}:" in content_text) and ("派蒙：" in content_text or "派蒙:" in content_text)):
                        continue # skip traveller's skill voices
                    trace = splitTalkWithPaimon(content_text, paimonName)
                    finalResults[f'avatar_{avatarId}_sayings_{i + 1}'] = [trace]
            else:
                if topic not in textMap or content not in textMap:
                    continue
                finalResults[f'avatar_{avatarId}_sayings_{i + 1}'] = [[
                    {
                        "role": 0,
                        "roleName": "`Traveller`",
                        "content": textMap[topic],
                    },
                    {
                        "role": -1, # we only know the avatarId, not the npcId
                        "roleName": textMap[info["name"]] if info["name"] in textMap else "`unknown`",
                        "content": textMap[content],
                    },
                ]]
        # add other info as talks
        avatarName = textMap[info["name"]] if info["name"] in textMap else "`unknown`"
        if avatarId in TRAVELLER_AVATAR_IDS:
            avatarName = "{NICKNAME}" # will be replaced later in clean_text.py
        for i, item in enumerate(SYSTEM_TALKS):
            args = [getAttr(info, key) for key in item["args"]]
            args_text = [textMap[item] if item in textMap else None for item in args]
            if all(args):
                finalResults[f'avatar_{avatarId}_system_{i + 1}'] = [[
                    {
                        "role": 0,
                        "roleName": "`Traveller`",
                        "content": "#" + item["question"] % avatarName,
                    },
                    {
                        "role": -1,
                        "roleName": "`system`",
                        "content": item["answer"] % tuple(args_text),
                    },
                ]]

    print("Saving to json...")
    with open(outputPath, "w", encoding="utf-8") as f:
        json.dump(finalResults, f, sort_keys=True, indent=2, ensure_ascii=False)

    print(f'Talks as beginning: {len(firstTalks)}')
    print(f'Dialogs as beginning: {len(firstDialogs)}')
    print(f'dfsCount: {dfsCount}')
    print(f'bfsCount: {bfsCount}')

if __name__ == "__main__":
    main()

