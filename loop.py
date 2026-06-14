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
    """情景 → 一条链接"""
    resp = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content":
                '你是情景分析器。把输入客观拆成一条链接，只输出 JSON，不要解释、不要 Markdown。'
                '格式：{"object":"对象","relation":"联系","summary":"事件总结","rank":"+1 或 -1"}。'},
            {"role": "user", "content": text}
        ]
    )
    return json.loads(resp.choices[0].message.content)


def 内化(link):
    link_net.setdefault(link["object"], []).append(link)
    保存()


def 反应(obj, scene, 旧链接):
    """先回溯旧链接：下意识(求和) + 拧巴时进一步"""
    total = sum(int(l["rank"]) for l in 旧链接)
    正 = [l for l in 旧链接 if int(l["rank"]) > 0]
    负 = [l for l in 旧链接 if int(l["rank"]) < 0]
    倾向 = "偏正面" if total > 0 else "偏负面" if total < 0 else "中立/说不清"
    print(f"【下意识反应】回溯 {len(旧链接)} 条，rank 合计 {total:+d} → {倾向}")

    if not (bool(正) and bool(负) or abs(total) <= 1):
        print("（倾向明确，下意识就够了）")
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
    print(f"【进一步反应】（{原因}）" + resp.choices[0].message.content)


# ── 主循环：情景 → 链接 → 反应 → 入库 ──
while True:
    scene = input("\n说一个情景（回车 或 q 退出）：").strip()
    if scene == "" or scene.lower() == "q":
        break

    # ① 情景 → 链接（拿到对象）
    link = 分析成链接(scene)
    obj = link["object"]
    print(f"\n→ 这条情景关于「{obj}」（{link['relation']} / rank {link['rank']}）")

    # ② 反应先回溯该对象旧链接（这条情景还没入库）
    旧链接 = list(link_net.get(obj, []))
    if 旧链接:
        反应(obj, scene, 旧链接)
    else:
        print("（新对象，没有先验，这次只记不反应）")

    # ③ 反应完，情景才入库
    内化(link)

print(f"\n结束。记忆已保存到 {net_file}")
