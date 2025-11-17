import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from pathlib import Path
from sql_mask import SQLMask

class SQLGenerator:
    def __init__(self,
                 model_name="gpt2-medium",
                 use_vocab_mask=False,
                 temperature=0.15,
                 k_samples=12):
        self.temperature   = temperature      #  ←  put this line back
        self.k_samples     = k_samples
        self.model_name    = model_name
        self.use_vocab_mask = use_vocab_mask

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token          # silence pad warns

        # ► 40 GB A100 ⇒ hold everything on one GPU ◄
        self.model = (AutoModelForCausalLM
                      .from_pretrained(model_name,
                                       torch_dtype=torch.float16,    # fp16 → 0.7 GB
                                       low_cpu_mem_usage=False)
                      .eval()
                      .to("cuda"))                                   # ← NO meta device

        self.schema   = Path("createSampleDB/sqlite3/schema.txt").read_text().strip()
        self.examples = Path("createSampleDB/sqlite3/examples.txt").read_text().strip()

        self.sql_mask = SQLMask(self.tokenizer, self.schema, use_vocab_mask) if use_vocab_mask else []

    def build_inputs(self, question: str):
        txt  = f"{self.schema}\n\n{self.examples}\n\n### QUESTION\nQ: {question}\nA:"
        ids  = self.tokenizer(txt).input_ids
        ids  = ids[-(self.tokenizer.model_max_length - 4):]          # keep last tokens
        ids  = torch.tensor(ids, device="cuda").unsqueeze(0)         # already on GPU
        attn = torch.ones_like(ids)
        return ids, attn

    def ask_sql(self, question: str):
        ids, attn = self.build_inputs(question)
        max_new   = 1023 - ids.size(-1)

        generations = self.model.generate(
            ids,
            attention_mask=attn,
            max_new_tokens=max_new,
            pad_token_id=self.tokenizer.eos_token_id,
            do_sample=self.temperature > 0,
            temperature=self.temperature,
            top_p=0.9,
            num_return_sequences=self.k_samples,
            logits_processor=self.sql_mask,
        )

        out = []
        for seq in generations:
            sql = self.tokenizer.decode(seq[ids.size(-1):]).split("\n")[0].strip()
            out.append(sql if sql.endswith(";") else sql + ";")
        return out
