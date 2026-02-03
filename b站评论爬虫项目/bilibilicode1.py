import json
import socket
import time
import urllib.request

# === 修改下面为你自己的 SESSDATA 值（登录 B站网页后在 Cookie 里复制） ===
SESSDATA = "720135ae%2C1767418577%2Ca50e4%2A71CjCzvHKbD1CTgY9nL_ikB7T6orUHCnpmpuN_jsqYGwJa69v13rpMf9mfXWVhEwMmmUcSVkJkOEJuRWNPVTVaUFdCM3AtWS00UmVJN3VENTdwZ2JGTGo0UjZYT2VTd1lLb0xqTjJFa2ZtRDUtTmxJa3BZcUppZjNOclowT2N1WkVFbVl5QVp6T1NBIIEC"  # 替换成你自己的，否则可留空尝试
# 示例（不建议直接使用）：SESSDATA = "xxxxxx==;"

# === 构造请求头 ===
def build_headers():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.bilibili.com/",
    }
    if SESSDATA:
        headers["Cookie"] = f"SESSDATA={SESSDATA}"
    return headers

# === 获取 oid 和视频标题 ===
def get_video_info(bvid, max_retries=3):
    url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    headers = build_headers()
    req = urllib.request.Request(url, headers=headers)

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req) as res:
                data = json.loads(res.read().decode("utf-8"))
                if data["code"] != 0:
                    print("获取视频信息失败")
                    return None, None
                aid = data["data"]["aid"]
                title = data["data"]["title"]
                return aid, title
        except socket.error as e:
            print(f"第 {attempt+1} 次尝试失败：", e)
            time.sleep(2)
        except Exception as e:
            print("请求视频信息出错：", e)
            return None, None
    print("重试失败，退出。")
    return None, None

# === 获取评论（单页） ===
def get_comments(oid, page=1):
    url = f"https://api.bilibili.com/x/v2/reply?type=1&oid={oid}&pn={page}&ps=20&sort=2"
    headers = build_headers()
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as res:
            data = res.read().decode("utf-8")
            result = json.loads(data)
            if result["code"] != 0:
                print(f"请求失败，错误码: {result['code']}")
                return []
            replies = result["data"].get("replies", [])
            if replies is None:
                print("该视频没有评论或评论被关闭")
                return []
            return [(r["member"]["uname"], r["content"]["message"]) for r in replies]
    except Exception as e:
        print("请求评论出错：", e)
        return []

# === 主流程 ===
def crawl_bilibili_comments(bvid, max_pages=30):
    oid, title = get_video_info(bvid)
    if not oid:
        print("❌ 无法获取 oid，退出程序。")
        return

    print(f"\n🎬 视频标题：{title}")
    print(f"🆔 视频 AV号(oid)：{oid}\n")
    all_comments = []

    for page in range(1, max_pages + 1):
        print(f"📄 正在爬取第 {page} 页评论...")
        comments = get_comments(oid, page)
        if not comments:
            print("该页无评论或出错，跳过。")
            continue
        for user, content in comments:
            print(f"{user}: {content}")
            all_comments.append((user, content))
        time.sleep(1)

    # 保存到文件
    filename = f"{title}_comments.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for user, content in all_comments:
            f.write(f"{user}: {content}\n")

    print(f"\n✅ 共爬取 {len(all_comments)} 条评论，已保存到 {filename}")

# === 启动入口 ===
if __name__ == "__main__":
    bvid = input("请输入B站视频的BV号（例如 BV1fK4y1q7Ep）：").strip()
    choice = input("输入0执行爬取，输入1跳过：").strip()

    if choice == '0':
        crawl_bilibili_comments(bvid, max_pages=30)
    elif choice == '1':
        print("已跳过爬取操作")
    else:
        print("无效输入，请输入0或1")
def filter_comments_by_keyword(input_filename, keyword):
    filtered_comments = []

    # 读取原评论文件
    with open(input_filename, "r", encoding="utf-8") as f:
        for line in f:
            if keyword in line:
                filtered_comments.append(line.strip())

    if not filtered_comments:
        print(f"没有找到包含关键词“{keyword}”的评论。")
        return

    # 保存筛选结果到新文件，文件名为关键词.txt
    output_filename = f"{keyword}.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        for comment in filtered_comments:
            f.write(comment + "\n")

    print(f"共筛选出 {len(filtered_comments)} 条评论，已保存到文件：{output_filename}")

if __name__ == "__main__":
    input_file = input("请输入爬取的评论txt文件名（带后缀，如 BV1fK4y1q7Ep_comments.txt）：").strip()
    keyword = input("请输入你想筛选的关键词：").strip()

    filter_comments_by_keyword(input_file, keyword)

    import torch
    import torch.nn as nn
    import torch.optim as optim
    from tqdm import tqdm
    import jieba
    import os

    # === 步骤 1：加载并分词文本，结合自定义词典提升分词准确率 ===
    from collections import Counter


    def build_custom_dict(words, top_k=5000):
        counter = Counter(words)
        common_words = counter.most_common(top_k)
        dict_filename = "custom_dict.txt"
        with open(dict_filename, "w", encoding="utf-8") as f:
            for word, freq in common_words:
                # 词频设定为整数，越大优先级越高，调整时可根据实际情况调节
                f.write(f"{word} {freq}\n")
        return dict_filename


    def load_text(filename):
        with open(filename, "r", encoding="utf-8") as f:
            text = f.read()

        # 初次切分统计词频，生成自定义词典
        init_words = list(jieba.cut(text))
        dict_file = build_custom_dict(init_words, top_k=5000)
        jieba.load_userdict(dict_file)  # 加载自定义词典后分词更准确

        improved_words = list(jieba.cut(text))
        return improved_words


    # === 步骤 2：构建词表 ===
    def build_vocab(words):
        vocab = sorted(set(words))
        stoi = {w: i for i, w in enumerate(vocab)}
        itos = {i: w for w, i in stoi.items()}
        return stoi, itos


    # === 步骤 3：构建数据集 ===
    def create_dataset(words, stoi, seq_len=20):
        X, Y = [], []
        for i in range(len(words) - seq_len):
            x_seq = words[i:i + seq_len]
            y_seq = words[i + 1:i + seq_len + 1]
            X.append([stoi[w] for w in x_seq])
            Y.append([stoi[w] for w in y_seq])
        return torch.tensor(X), torch.tensor(Y)


    # === 步骤 4：Transformer 语言模型 ===
    class TransformerLM(nn.Module):
        def __init__(self, vocab_size, embed_size=256, nhead=4, nhid=512, nlayers=4, dropout=0.1, max_len=512):
            super().__init__()
            self.embed = nn.Embedding(vocab_size, embed_size)
            self.pos_embed = nn.Embedding(max_len, embed_size)
            encoder_layer = nn.TransformerEncoderLayer(embed_size, nhead, nhid, dropout, batch_first=True)
            self.transformer = nn.TransformerEncoder(encoder_layer, nlayers)
            self.fc = nn.Linear(embed_size, vocab_size)

        def forward(self, src):
            bsz, seq_len = src.size()
            pos = torch.arange(seq_len, device=src.device).unsqueeze(0).expand(bsz, -1)
            x = self.embed(src) + self.pos_embed(pos)
            mask = nn.Transformer.generate_square_subsequent_mask(seq_len).to(src.device)
            out = self.transformer(x, mask=mask)
            return self.fc(out)


    # === 步骤 5：训练模型（保存并加载最佳模型）===
    def train_model(model, X, Y, device, epochs=20, batch_size=64, save_path="best_transformer_lm.pth"):
        model = model.to(device)
        X, Y = X.to(device), Y.to(device)

        optimizer = optim.Adam(model.parameters(), lr=3e-4)
        loss_fn = nn.CrossEntropyLoss()

        best_loss = float('inf')

        for epoch in range(epochs):
            model.train()
            total_loss = 0
            pbar = tqdm(range(0, len(X), batch_size), desc=f"Epoch {epoch + 1}")
            for i in pbar:
                xb = X[i:i + batch_size]
                yb = Y[i:i + batch_size]

                optimizer.zero_grad()
                pred = model(xb)
                loss = loss_fn(pred.view(-1, pred.size(-1)), yb.view(-1))
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                pbar.set_postfix(loss=total_loss / ((i // batch_size) + 1))

            avg_loss = total_loss / (len(X) / batch_size)
            print(f"✅ Epoch {epoch + 1} 完成，Loss: {avg_loss:.4f}")

            # 保存最佳模型
            if avg_loss < best_loss:
                best_loss = avg_loss
                torch.save(model.state_dict(), save_path)
                print(f"💾 新最佳模型已保存，Loss: {best_loss:.4f}")


    # === 步骤 6：生成文本（加载最佳模型）===
    def generate(model, stoi, itos, start_words=["这"], length=50, device='cpu', temperature=1.0, load_path=None):
        if load_path:
            model.load_state_dict(torch.load(load_path, map_location=device))
        model = model.to(device)
        model.eval()

        input_seq = torch.tensor([[stoi.get(w, 0) for w in start_words]], dtype=torch.long).to(device)
        result = start_words.copy()

        with torch.no_grad():
            for _ in range(length):
                output = model(input_seq)
                last_logits = output[0, -1] / temperature
                prob = torch.softmax(last_logits, dim=0)
                idx = torch.multinomial(prob, 1).item()
                result.append(itos[idx])
                input_seq = torch.cat([input_seq, torch.tensor([[idx]], device=device)], dim=1)

        return ''.join(result)


    # === 主程序入口 ===

    if __name__ == "__main__":
        filename = input("请输入评论文本文件名（如 BVxxxx_comments.txt）：").strip()
        if not filename or not os.path.isfile(filename):
            print("❌ 文件不存在")
            exit(1)

        words = load_text(filename)
        if len(words) < 30:
            print("❌ 文本太短，无法训练")
            exit(1)

        stoi, itos = build_vocab(words)
        X, Y = create_dataset(words, stoi, seq_len=20)

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 当前使用设备: {device}")

        model = TransformerLM(len(stoi))
        print(f"📦 模型总参数量: {sum(p.numel() for p in model.parameters() if p.requires_grad)}")

        save_path = "best_transformer_lm.pth"

        # === 是否使用已有模型 ===
        if os.path.exists(save_path):
            choice = input("是否使用已保存的最佳模型生成评论？(y/n)：").strip().lower()
        else:
            choice = 'n'  # 没有模型文件时自动训练

        if choice == 'y':
            print("📂 加载已保存的最佳模型用于生成...")
        else:
            print("🎯 开始训练模型...")
            train_model(model, X, Y, device, epochs=30, save_path=save_path)

        print("\n📝 === 生成评论示例 ===")
        for _ in range(20):
            print("👉", generate(model, stoi, itos, start_words=["这"], length=50, device=device,
                                temperature=0.8, load_path=save_path))
