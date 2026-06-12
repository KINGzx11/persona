import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ① 先选这次用哪个记忆文件（不同文件 = 不同的人格/场景）
记忆文件 = input("用哪个记忆文件？(例如 中药.json)：").strip()
if 记忆文件 == "":
    记忆文件 = "记忆.json"        # 什么都不输，就用默认名

# 读一次：把这个柜子打开（没有就开个空柜子）
if os.path.exists(记忆文件):
    档案 = json.load(open(记忆文件, encoding="utf-8"))
else:
    档案 = {}

# ② 循环：可以一条接一条不停地输入情景
while True:
    scene = input("\n说一个情景（直接回车 或 输入 q 退出）：").strip()
    if scene == "" or scene.lower() == "q":
        break                     # 满足条件就跳出循环、结束

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": """你是一个情景分析器。你的任务是把用户输入的情景拆成结构化 JSON。只允许输出 JSON，不要解释，不要 Markdown。JSON 格式如下：
{"object":"对象","relation":"联系","summary":"事件总结","rank":"评价数值"}
如:我去看中医，relation是不管用，object是对象，评价数值是+1，-1"""
            },
            {"role": "user", "content": scene}
        ]
    )

    content = response.choices[0].message.content
    data = json.loads(content)
    print("AI 拆出的卡片：", data)

    # 加：按 object 找格子，把这张卡叠进去
    对象 = data["object"]
    档案.setdefault(对象, []).append(data)

    # 写：每存一张就立刻保存，防止中途退出丢东西
    json.dump(档案, open(记忆文件, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    print(f"已存入「{对象}」，这一格现在有 {len(档案[对象])} 张卡")

print(f"\n结束。所有记忆已保存到 {记忆文件}")