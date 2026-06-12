import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 选要读的链接网文件
net_file = input("读哪个链接网文件？(例如 中药.json)：").strip()
link_net = json.load(open(net_file, encoding="utf-8"))

# 选要总结的对象
obj = input("总结哪个对象？(例如 中药)：").strip()
links = link_net[obj]            # 这个对象身上挂着的全部链接

# ① 把每条链接的 rank 转成数字，加总
total = 0
for link in links:
    total += int(link["rank"])

print(f"\n「{obj}」共有 {len(links)} 条链接，rank 合计 = {total}")

# ② 把所有链接拼成一段文字，喂给解说员
context = ""
for link in links:
    context += f'- {link["relation"]}：{link["summary"]}（rank {link["rank"]}）\n'

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": """你是人格引擎的解说员。下面是某人关于一个对象的全部链接（每条链接 = 一次经历留下的 relation + 评价 rank），以及 rank 合计。
请用第三人称总结他此刻对这个对象的整体态度：偏好还是偏恶、是否矛盾拧巴，并说出为什么。两三句，简洁。"""
        },
        {
            "role": "user",
            "content": f"对象：{obj}\nrank 合计：{total}\n链接：\n{context}"
        }
    ]
)

print("\n【总叙事】")
print(response.choices[0].message.content)