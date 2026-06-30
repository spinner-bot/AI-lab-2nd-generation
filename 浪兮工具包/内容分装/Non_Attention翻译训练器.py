# -*- coding: utf-8 -*-
"""
    Non-Attention翻译训练器（真实数据版）
    ✅ 自动截取多余假维度 ✅ 真实词表加载 ✅ 动态padding ✅ 未知词处理
"""
import os
import json
import time
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# ===================== 固定常量 =====================
HIDDEN_DIM = 512
TRAIN_SPLIT = 0.8
CORPUS_SEP = "\t"
MAX_VOCAB_SIZE = 500000
MAX_SEQ_LEN = 50
PAD_IDX = 0
UNK_IDX = 1
SOS_IDX = 2
EOS_IDX = 3

# UI样式
HIGHLIGHT = "\033[1;32m"
NORMAL = "\033[0m"
BLUE = "\033[94m"
RED = "\033[91m"
DOUBLE_LINE = BLUE + "=" * 70 + NORMAL

# 路径
BASE_ROOT = os.path.abspath(".")
CONFIG_PATH = os.path.join(BASE_ROOT, "数据库", "用户数据", "310001", "config.json")
CORPUS_DIR = os.path.join(BASE_ROOT, "数据库", "资源文件", "平行语料")
VOCAB_DATA_DIR = os.path.join(BASE_ROOT, "数据库", "资源文件", "词表数据")
OUTPUT_DIR = os.path.join(BASE_ROOT, "数据库", "输出结果", "机器翻译", "310002")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 全局变量
src_vocab_name = tgt_vocab_name = corpus_file = None
corpus_is_forward = None
LEARNING_RATE = EPOCHS = BATCH_SIZE = EMBED_DIM = None
SRC_VOCAB_SIZE = TGT_VOCAB_SIZE = None
device = None
train_data = test_data = []


def format_time(seconds):
    total_sec = seconds
    int_sec = int(total_sec)
    ms = round(total_sec - int_sec, 2)
    h = int_sec // 3600
    m = (int_sec % 3600) // 60
    s = int_sec % 60
    if h == 0 and m == 0:
        return f"{s + ms:.2f}s"
    parts = []
    if h > 0:
        parts.append(f"{h}h")
    if m > 0:
        parts.append(f"{m}min")
    parts.append(f"{s}s")
    return "".join(parts)


def get_device():
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats()
    if torch.cuda.is_available():
        print(f"{HIGHLIGHT}✅ CUDA可用 | 显存已清理{NORMAL}")
        print(f"{BLUE}📊 GPU设备型号：{torch.cuda.get_device_name(0)}{NORMAL}")
        total_mem = torch.cuda.get_device_properties(0).total_memory / 1024 ** 3
        print(f"{BLUE}📊 GPU总显存：{total_mem:.2f}G{NORMAL}")
        return torch.device("cuda")
    else:
        raise SystemExit(f"{RED}❌ 必须使用GPU运行！{NORMAL}")


def load_full_config():
    global src_vocab_name, tgt_vocab_name, corpus_file, corpus_is_forward
    global LEARNING_RATE, EPOCHS, BATCH_SIZE, EMBED_DIM, SRC_VOCAB_SIZE, TGT_VOCAB_SIZE

    print(f"{BLUE}📥 读取训练配置...{NORMAL}")
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        src_vocab_name = cfg[0]
        tgt_vocab_name = cfg[1]
        corpus_file = cfg[2]
        corpus_is_forward = cfg[3]
        LEARNING_RATE = float(cfg[4]) if cfg[4] else 0.0001
        EPOCHS = int(cfg[5]) if cfg[5] else 5
        BATCH_SIZE = int(cfg[6]) if cfg[6] else 64
        EMBED_DIM = int(cfg[7]) if cfg[7] else 100
        SRC_VOCAB_SIZE = min(int(cfg[8] or 1200001), MAX_VOCAB_SIZE)
        TGT_VOCAB_SIZE = min(int(cfg[9] or 2000000), MAX_VOCAB_SIZE)

        print(f"{HIGHLIGHT}✅ 配置加载完成{NORMAL}")
        print(f"源词表：{src_vocab_name} | 目标词表：{tgt_vocab_name} | 语料：{corpus_file}")
        print(f"方向：{'正向' if corpus_is_forward else '反向'} | batch size：{BATCH_SIZE}")
        print(f"learning rate：{LEARNING_RATE} | epoch：{EPOCHS} | 向量维度：{EMBED_DIM}")
        return True
    except Exception as e:
        print(f"{RED}❌ 配置加载失败：{str(e)}{NORMAL}")
        return False


def load_vocab(vocab_name, max_size, embed_dim_expected):
    """
    读取词表文件，若某词向量维度与 embed_dim_expected 不一致：
      - 若偏大：直接截取到期望维度（丢弃多余假维度）
      - 若偏小：填充0至期望维度（理论上不应发生）
    返回：(word2idx, idx2word, embedding_weights, actual_vocab_size, final_embed_dim)
    """
    vocab_path = os.path.join(VOCAB_DATA_DIR, vocab_name, f"{vocab_name}.txt")
    if not os.path.exists(vocab_path):
        raise FileNotFoundError(f"词表文件不存在：{vocab_path}")

    print(f"{BLUE}📖 加载词表：{vocab_name}{NORMAL}")
    words = []
    vecs = []
    actual_dim = None

    with open(vocab_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f):
            if len(words) >= max_size:
                break
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            word = parts[0]
            # 提取向量部分（跳过词本身，直到遇到非数字）
            vec_strs = []
            for p in parts[1:]:
                try:
                    float(p)
                    vec_strs.append(p)
                except ValueError:
                    break
            if len(vec_strs) == 0:
                continue
            vec = [float(x) for x in vec_strs]

            # 首次确定维度
            if actual_dim is None:
                actual_dim = len(vec)
                if embed_dim_expected is not None and actual_dim != embed_dim_expected:
                    print(f"{BLUE}⚠️ 词表 {vocab_name} 实际维度 {actual_dim} 与配置 {embed_dim_expected} 不符，将使用实际维度{NORMAL}")
                    embed_dim_expected = actual_dim
            # 维度校正：截取或填充
            if len(vec) != embed_dim_expected:
                if len(vec) > embed_dim_expected:
                    vec = vec[:embed_dim_expected]  # 截取多余假维度
                    print(f"{BLUE}⚠️ 词 {word} 向量长度 {len(vec_strs)} > {embed_dim_expected}，已截取{NORMAL}")
                else:
                    # 理论上不会少，但为了鲁棒性填充0
                    vec = vec + [0.0] * (embed_dim_expected - len(vec))
                    print(f"{BLUE}⚠️ 词 {word} 向量长度 {len(vec_strs)} < {embed_dim_expected}，已补0{NORMAL}")
            words.append(word)
            vecs.append(vec)

    if not vecs:
        raise RuntimeError(f"词表 {vocab_name} 无有效向量")

    final_dim = embed_dim_expected if embed_dim_expected is not None else len(vecs[0])
    # 特殊token
    special_tokens = ["<PAD>", "<UNK>", "<SOS>", "<EOS>"]
    word2idx = {token: idx for idx, token in enumerate(special_tokens)}
    idx2word = special_tokens.copy()
    # 特殊向量（零向量）
    special_vecs = [[0.0] * final_dim for _ in special_tokens]

    all_vecs = special_vecs + vecs
    embedding_weights = torch.tensor(all_vecs, dtype=torch.float32)

    for word, vec in zip(words, vecs):
        if word not in word2idx:
            word2idx[word] = len(idx2word)
            idx2word.append(word)

    actual_size = len(word2idx)
    print(f"{HIGHLIGHT}✅ 词表 {vocab_name} 加载完成 | 总词数：{actual_size} | 向量维度：{final_dim}{NORMAL}")
    return word2idx, idx2word, embedding_weights, actual_size, final_dim


def tokenize(sentence):
    """简单分词：含中文则按字符，否则按单词+标点"""
    if any('\u4e00' <= ch <= '\u9fff' for ch in sentence):
        return list(sentence)
    import re
    tokens = re.findall(r'\w+|[^\w\s]', sentence)
    return [t for t in tokens if t.strip()]


def sentence_to_indices(sentence, word2idx, max_len, add_sos_eos=True):
    tokens = tokenize(sentence)
    if len(tokens) > max_len:
        tokens = tokens[:max_len]
    indices = [word2idx.get(token, UNK_IDX) for token in tokens]
    if add_sos_eos:
        indices = [SOS_IDX] + indices + [EOS_IDX]
    return indices


def load_corpus_and_convert(src_word2idx, tgt_word2idx):
    global train_data, test_data
    start = time.time()
    print(f"{BLUE}📚 加载平行语料并转换为索引...{NORMAL}")
    corpus_path = os.path.join(CORPUS_DIR, corpus_file)
    pairs_raw = []

    with open(corpus_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(CORPUS_SEP)
            if len(parts) != 2:
                continue
            if corpus_is_forward:
                src_sent, tgt_sent = parts[0], parts[1]
            else:
                src_sent, tgt_sent = parts[1], parts[0]
            if not src_sent or not tgt_sent:
                continue
            pairs_raw.append((src_sent, tgt_sent))

    src_indices_list, tgt_indices_list = [], []
    for src_sent, tgt_sent in pairs_raw:
        src_idx = sentence_to_indices(src_sent, src_word2idx, MAX_SEQ_LEN, add_sos_eos=True)
        tgt_idx = sentence_to_indices(tgt_sent, tgt_word2idx, MAX_SEQ_LEN, add_sos_eos=True)
        if len(src_idx) <= 1 or len(tgt_idx) <= 1:
            continue
        src_indices_list.append(src_idx)
        tgt_indices_list.append(tgt_idx)

    split_idx = int(len(src_indices_list) * TRAIN_SPLIT)
    train_data = list(zip(src_indices_list[:split_idx], tgt_indices_list[:split_idx]))
    test_data = list(zip(src_indices_list[split_idx:], tgt_indices_list[split_idx:]))

    print(f"{HIGHLIGHT}✅ 语料转换完成 | 耗时：{format_time(time.time() - start)}")
    print(f"总句对：{len(src_indices_list)} | 训练：{len(train_data)} | 测试：{len(test_data)}")
    return True


class TranslationDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        src_seq, tgt_seq = self.data[idx]
        return torch.tensor(src_seq, dtype=torch.long), torch.tensor(tgt_seq, dtype=torch.long)


def collate_fn(batch):
    src_seqs, tgt_seqs = zip(*batch)
    src_padded = torch.nn.utils.rnn.pad_sequence(src_seqs, batch_first=True, padding_value=PAD_IDX)
    tgt_padded = torch.nn.utils.rnn.pad_sequence(tgt_seqs, batch_first=True, padding_value=PAD_IDX)
    return src_padded, tgt_padded


class Encoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, pretrained_weights=None):
        super().__init__()
        if pretrained_weights is not None:
            self.embedding = nn.Embedding.from_pretrained(pretrained_weights, freeze=True)
        else:
            self.embedding = nn.Embedding(vocab_size, embed_dim)
            self.embedding.requires_grad_(False)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)

    def forward(self, x):
        x = self.embedding(x)
        _, (hidden, cell) = self.lstm(x)
        return hidden, cell


class Decoder(nn.Module):
    def __init__(self, vocab_size, embed_dim, hidden_dim, pretrained_weights=None):
        super().__init__()
        if pretrained_weights is not None:
            self.embedding = nn.Embedding.from_pretrained(pretrained_weights, freeze=True)
        else:
            self.embedding = nn.Embedding(vocab_size, embed_dim)
            self.embedding.requires_grad_(False)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, vocab_size)

    def forward(self, x, hidden, cell):
        x = self.embedding(x)
        out, (hidden, cell) = self.lstm(x, (hidden, cell))
        return self.fc(out), hidden, cell


class Seq2Seq(nn.Module):
    def __init__(self, encoder, decoder):
        super().__init__()
        self.encoder = encoder
        self.decoder = decoder

    def forward(self, src, tgt):
        hidden, cell = self.encoder(src)
        output, _, _ = self.decoder(tgt[:, :-1], hidden, cell)
        return output


def build_model(src_embed_weights, tgt_embed_weights):
    start = time.time()
    print(f"{BLUE}🤖 初始化模型（加载预训练词向量）...{NORMAL}")
    with torch.device("cuda"):
        enc = Encoder(SRC_VOCAB_SIZE, EMBED_DIM, HIDDEN_DIM, pretrained_weights=src_embed_weights)
        dec = Decoder(TGT_VOCAB_SIZE, EMBED_DIM, HIDDEN_DIM, pretrained_weights=tgt_embed_weights)
        model = Seq2Seq(enc, dec)
    print(f"{HIGHLIGHT}✅ 模型初始化完成 | 耗时：{format_time(time.time() - start)}")
    return model


def train_model(model, train_loader):
    total_train_start = time.time()
    print(f"{BLUE}🚀 开始训练（混合精度）...{NORMAL}")

    scaler = torch.amp.GradScaler('cuda')
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)
    optimizer = torch.optim.Adam(
        list(model.encoder.lstm.parameters()) +
        list(model.decoder.lstm.parameters()) +
        list(model.decoder.fc.parameters()),
        lr=LEARNING_RATE
    )

    for epoch in range(EPOCHS):
        epoch_start = time.time()
        model.train()
        epoch_loss = 0.0

        for src, tgt in train_loader:
            src, tgt = src.to(device), tgt.to(device)
            optimizer.zero_grad()

            with torch.amp.autocast('cuda', dtype=torch.float16):
                output = model(src, tgt)
                target = tgt[:, 1:].contiguous().view(-1)
                loss = criterion(output.reshape(-1, TGT_VOCAB_SIZE), target)

            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            epoch_loss += loss.item()

        epoch_time = time.time() - epoch_start
        avg_loss = epoch_loss / len(train_loader)
        print(f"{HIGHLIGHT}▶ 第 {epoch + 1}/{EPOCHS} 轮 | 耗时：{format_time(epoch_time)} | 损失：{avg_loss:.4f}")

    total_time = time.time() - total_train_start
    print(f"{HIGHLIGHT}✅ 训练完成 | 总耗时：{format_time(total_time)}{NORMAL}")


def test_model(model, test_loader):
    start = time.time()
    print(f"{BLUE}🧪 测试集评估...{NORMAL}")
    model.eval()
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)
    total_loss = 0.0

    with torch.no_grad(), torch.amp.autocast('cuda', dtype=torch.float16):
        for src, tgt in test_loader:
            src, tgt = src.to(device), tgt.to(device)
            output = model(src, tgt)
            target = tgt[:, 1:].contiguous().view(-1)
            loss = criterion(output.reshape(-1, TGT_VOCAB_SIZE), target)
            total_loss += loss.item()

    avg_loss = total_loss / len(test_loader)
    print(f"{HIGHLIGHT}✅ 测试完成 | 测试损失：{avg_loss:.4f} | 耗时：{format_time(time.time() - start)}{NORMAL}")


def save_model(model):
    start = time.time()
    print(f"{BLUE}💾 保存模型...{NORMAL}")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(OUTPUT_DIR, f"non_attention_{timestamp}.pth")
    torch.save({
        "encoder": model.encoder.state_dict(),
        "decoder": model.decoder.state_dict(),
        "config": {
            "src_vocab_size": SRC_VOCAB_SIZE,
            "tgt_vocab_size": TGT_VOCAB_SIZE,
            "embed_dim": EMBED_DIM,
            "hidden_dim": HIDDEN_DIM
        }
    }, save_path)
    print(f"{HIGHLIGHT}🎉 模型保存成功！\n路径：{save_path} | 耗时：{format_time(time.time() - start)}{NORMAL}")


def start_trainer(run_app):
    total_start = time.time()
    print(DOUBLE_LINE)
    print(f"{HIGHLIGHT}    Non-Attention 翻译训练器（自动截取假维度版）     {NORMAL}")
    print(DOUBLE_LINE)

    print(f"{HIGHLIGHT}🔧 打开翻译训练配置器...{NORMAL}")
    run_app("310001")

    if not load_full_config():
        return

    global device, SRC_VOCAB_SIZE, TGT_VOCAB_SIZE, EMBED_DIM
    device = get_device()

    # 加载源词表（维度自适应）
    src_word2idx, _, src_embed_weights, src_size, src_dim = load_vocab(
        src_vocab_name, MAX_VOCAB_SIZE, EMBED_DIM
    )
    tgt_word2idx, _, tgt_embed_weights, tgt_size, tgt_dim = load_vocab(
        tgt_vocab_name, MAX_VOCAB_SIZE, EMBED_DIM
    )

    if src_dim != tgt_dim:
        print(f"{RED}❌ 源词表维度({src_dim})与目标词表维度({tgt_dim})不一致，无法训练！{NORMAL}")
        return

    SRC_VOCAB_SIZE, TGT_VOCAB_SIZE, EMBED_DIM = src_size, tgt_size, src_dim

    if not load_corpus_and_convert(src_word2idx, tgt_word2idx):
        return

    train_dataset = TranslationDataset(train_data)
    test_dataset = TranslationDataset(test_data)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn, pin_memory=True)

    model = build_model(src_embed_weights, tgt_embed_weights).to(device)

    train_model(model, train_loader)
    test_model(model, test_loader)
    save_model(model)

    print(f"\n{BLUE}ℹ️ 进入文件资源管理系统，可预览{NORMAL}")
    input(f"{HIGHLIGHT}请按回车键继续...{NORMAL}")
    if run_app is not None:
        run_app("110002")

    print(DOUBLE_LINE)
    print(f"{HIGHLIGHT}✅ 全部任务完成！总耗时：{format_time(time.time() - total_start)}")
    print(DOUBLE_LINE)


if __name__ == "__main__":
    start_trainer(None)