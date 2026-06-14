import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

# ── 载入人格文件 ──
net_file = input("用哪个链接网文件？(例如 中药.json)：").strip()
if net_file == "":
    net_file = "记忆.json"
if not net_file.endswith(".json"):
    net_file += ".json"
link_net = json.load(open(net_file, encoding="utf-8")) if os.path.exists(net_file) else {}
print(f"已载入「{net_file}」，{len(link_net)} 个对象：{'、'.join(link_net.keys()) or '（空）'}")


def 保存():
    json.dump(link_net, open(net_file, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def 分析成链接(text):
    """情景 → 多条链接：抽出我此刻评价的所有对象，能对上已知就复用"""
    已知 = "、".join(link_net.keys()) or "（暂无）"
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content":
                '你是人格引擎的情景分析器。情景是「我」第一人称的一句经历。'
                '抽出这条情景里「我」会对之产生态度的【所有】对象，每个对象一条链接。'
                '规则：'
                '1. object 不是「我」、不是说话人本身，而是「我」所评价的外部事物。'
                '2. 优先专有名称/具体实体：有专有名（如「原神」）就别用上位类别词（「游戏」「药」）；指代词（「这个游戏」「它」）回指到具体对象。'
                '3. object 取能独立持有态度的最小单位，去掉修饰、时长、场景（「中药」而非「长期中药治疗」）。'
                '4. 复合体拆成已知原子对象（「中药奶茶店」→「中药」+「奶茶店」）。'
                '5. 本质上就是给定已知对象之一的，必须复用其原名，不要另造近义或复合新名。'
                '6. 每条：relation 是我对该对象的关系/动作，summary 一句话事件，rank 这次留下的倾向（+1 或 -1）。'
                '只输出 JSON 数组：[{"object":"","relation":"","summary":"","rank":"+1 或 -1"}, ...]，不要解释、不要 Markdown。'},
            {"role": "user", "content": f"已知对象（能对上就复用原名）：{已知}\n情景：{text}"}
        ]
    )
    data = json.loads(resp.choices[0].message.content)
    return data if isinstance(data, list) else [data]


def 内化(link):
    link_net.setdefault(link["object"], []).append(link)
    保存()


def 反应(obj, scene, 旧链接):
    """先回溯旧链接：下意识(求和) + 拧巴时进一步"""
    total = sum(int(l["rank"]) for l in 旧链接)
    正 = [l for l in 旧链接 if int(l["rank"]) > 0]
    负 = [l for l in 旧链接 if int(l["rank"]) < 0]
    倾向 = "偏正面" if total > 0 else "偏负面" if total < 0 else "中立/说不清"
    print(f"  【下意识反应】回溯 {len(旧链接)} 条，rank 合计 {total:+d} → {倾向}")

    if not (bool(正) and bool(负) or abs(total) <= 1):
        print("  （倾向明确，下意识就够了）")
        return
    原因 = "正负并存，拧巴" if (正 and 负) else "倾向太弱"
    ctx = "".join(f'- {l["relation"]}：{l["summary"]}（rank {l["rank"]}）\n' for l in 旧链接)
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content":
                "你是人格引擎的反应器。基于某人对一个对象的全部旧链接，用第一人称说出他此刻面对新情景的"
                "反应，含倾向与内心纠结，两三句，口语。"},
            {"role": "user", "content": f"对象：{obj}\n新情景：{scene}\n旧链接：\n{ctx}"}
        ]
    )
    print(f"  【进一步反应】（{原因}）" + resp.choices[0].message.content)


# ── 主循环：情景 → 多条链接 → 逐个反应 → 入库 ──
while True:
    scene = input("\n说一个情景（回车 或 q 退出）：").strip()
    if scene == "" or scene.lower() == "q":
        break

    # ① 情景 → 多条链接
    links = 分析成链接(scene)
    print("\n→ 这条情景涉及：" + "、".join(f"{l['object']}({l['rank']})" for l in links))

    # ② 每个对象先回溯它的旧链接再反应（这条情景还没入库）
    for l in links:
        obj = l["object"]
        旧链接 = list(link_net.get(obj, []))
        print(f"\n· 「{obj}」（{l['relation']} / rank {l['rank']}）")
        if 旧链接:
            反应(obj, scene, 旧链接)
        else:
            print("  （新对象，没有先验，这次只记不反应）")

    # ③ 反应完，所有链接才入库
    for l in links:
        内化(l)

print(f"\n结束。记忆已保存到 {net_file}")
