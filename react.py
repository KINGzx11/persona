import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ① 选人格文件，把链接网读进内存
net_file = input("用哪个链接网文件？(例如 中药.json)：").strip()
if net_file == "":
    net_file = "记忆.json"
link_net = json.load(open(net_file, encoding="utf-8")) if os.path.exists(net_file) else {}


def 认出对象(scene):
    """从情景里抽出主要对象（本段只取对象，不写回）"""
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content":
                '你是情景分析器。只输出 JSON，不要解释，不要 Markdown。'
                '格式：{"object":"对象"}。object 是这条情景主要关于的那个对象。'},
            {"role": "user", "content": scene}
        ]
    )
    return json.loads(resp.choices[0].message.content)["object"]


def 进一步反应(obj, scene, links):
    """拧巴时，把具体链接喂给反应器，做更细的反应"""
    context = ""
    for link in links:
        context += f'- {link["relation"]}：{link["summary"]}（rank {link["rank"]}）\n'
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content":
                "你是人格引擎的反应器。下面是某人关于一个对象的全部旧链接"
                "（每条=一次经历留下的 relation+评价）。他现在又遇到一个关于这个对象的新情景。"
                "请基于这些旧链接，用第一人称说出他此刻的反应——包含倾向，以及内心的纠结"
                "（若正负链接并存）。两三句，口语，别罗列链接。"},
            {"role": "user", "content":
                f"对象：{obj}\n新情景：{scene}\n我对它的旧链接：\n{context}"}
        ]
    )
    return resp.choices[0].message.content


# ② + ③ 主循环：回溯 + 反应
while True:
    scene = input("\n说一个情景（回车 或 q 退出）：").strip()
    if scene == "" or scene.lower() == "q":
        break

    obj = 认出对象(scene)
    links = link_net.get(obj, [])
    print(f"\n→ 这条情景关于「{obj}」")

    # 新对象：桶是空的，没有先验可回溯
    if not links:
        print("（新对象，记忆里还没有它的链接，暂时无从反应）")
        continue

    # 下意识反应：纯算术，看 rank 总和（不调 AI）
    total = sum(int(l["rank"]) for l in links)
    正 = [l for l in links if int(l["rank"]) > 0]
    负 = [l for l in links if int(l["rank"]) < 0]
    倾向 = "偏正面" if total > 0 else "偏负面" if total < 0 else "中立/说不清"
    print(f"【下意识反应】回溯到 {len(links)} 条链接，rank 合计 {total:+d} → {倾向}")

    # 触发进一步反应的条件：正负并存(拧巴) 或 倾向太弱(≈0)
    拧巴 = bool(正) and bool(负)
    弱倾向 = abs(total) <= 1
    if 拧巴 or 弱倾向:
        原因 = "正负链接并存，拧巴" if 拧巴 else "倾向太弱，下意识给不出准话"
        print(f"【需要进一步】（{原因}）")
        print("【进一步反应】" + 进一步反应(obj, scene, links))
    else:
        print("（倾向明确，下意识就够了，不深想）")

print("\n结束。本段只做回溯+反应，没有改动记忆。")
