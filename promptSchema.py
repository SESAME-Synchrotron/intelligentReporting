#!/usr/bin/env python3
# promptSchema.py – GPT-2 text-to-SQL for Chinook

import re, sqlite3, torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM, LogitsProcessor

# ── 1.  Prompt blocks ───────────────────────────────────────────────
SCHEMA   = Path("createSampleDB/sqlite3/schema.txt").read_text().strip()
EXAMPLES = Path("createSampleDB/sqlite3/examples.txt").read_text().strip()

# ── 2.  Model & tokenizer ───────────────────────────────────────────
model_name = "trainedGPT2/gpt2-spider-sql-281124"
tok = AutoTokenizer.from_pretrained(model_name)
tok.pad_token = tok.eos_token
lm  = AutoModelForCausalLM.from_pretrained(model_name).to("cuda")

# ── 3.  Allow-list of token IDs (keywords + schema + separators) ────
sql_keywords = [
    "SELECT","FROM","JOIN","WHERE","AND","OR","ON","IN",
    "GROUP","BY","ORDER","LIMIT","ASC","DESC","AS",
    "=","!=","<",">","<=",">=","(",")",",","*",";","."  # note dot
]
# extra = ["\n", ", ", " "]                               # newline, comma-space, bare space
extra = [" Title"]

schema_tokens = re.findall(r"[A-Za-z_]+", SCHEMA)

def ids(word):
    return (tok.encode(word, add_special_tokens=False) +
            tok.encode(" " + word, add_special_tokens=False))

allowed = {i for w in sql_keywords + schema_tokens + extra for i in ids(w)}
ALLOWED = torch.tensor(sorted(i for i in allowed if 0 <= i < tok.vocab_size),
                       dtype=torch.long)

class SafeSQLMask(LogitsProcessor):
    def __init__(self, ids): self.ids = ids
    def __call__(self, _input, scores):
        if self.ids.device != scores.device:
            self.ids = self.ids.to(scores.device)
        m = torch.full_like(scores, float("-inf"))
        m[:, self.ids] = 0
        return scores + m

mask = SafeSQLMask(ALLOWED)

# ── 4.  Prompt helpers ──────────────────────────────────────────────
def prompt_ids(question: str):
    txt = f"{SCHEMA}\n\n{EXAMPLES}\n\n### QUESTION\nQ: {question}\nA:"
    ids = tok(txt).input_ids
    limit = tok.model_max_length - 4
    if len(ids) > limit:
        ids = ids[-limit:]
    ids = torch.tensor(ids).unsqueeze(0).to("cuda")
    att = torch.ones_like(ids)
    return ids, att

# ── 5.  Generate → execute loop ─────────────────────────────────────
def run(question: str, k=12):
    ids, att = prompt_ids(question)
    free = 1023 - ids.size(-1)

    def batch(sample, temp, beams=1):
        out = lm.generate(
            ids, attention_mask=att, pad_token_id=tok.eos_token_id,
            max_new_tokens=free,
            do_sample=sample, temperature=temp, top_p=0.9,
            num_beams=beams, num_return_sequences=(k if sample else 1),
            # logits_processor=[mask],
            logits_processor=[],
        )
        for i, seq in enumerate(out):
            sql = tok.decode(seq[ids.size(-1):]).split("\n")[0].strip()
            if not sql.endswith(";"): sql += ";"
            print(f"[{i}] {sql}")
            try:
                rows = conn.execute(sql).fetchall()
                return sql, rows[:5]
            except sqlite3.DatabaseError:
                continue
        return None

    # low-temperature sampling
    res = batch(True, 0.05)
    if res: return res
    # single greedy attempt
    return batch(False, 0.0)

# ── 6.  Demo ────────────────────────────────────────────────────────
if __name__ == "__main__":
    conn = sqlite3.connect("createSampleDB/sqlite3/Chinook.db")
    sql_rows = run("Show me every album title.")
    if sql_rows:
        sql, rows = sql_rows
        print("\n✔ SQL :", sql)
        print("✔ Rows:", rows)
    else:
        print("\nNo executable SQL – add examples or increase k.")
