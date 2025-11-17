import torch
from transformers import LogitsProcessor
import re

class SQLMask(LogitsProcessor):
    def __init__(self, vocab, schema, use_vocab_mask=False):
        self.vocab = vocab
        self.schema = schema
        self.use_vocab_mask = use_vocab_mask
        self.allowed_ids = self.build_allowed_ids() if use_vocab_mask else []

    def build_allowed_ids(self):
        sql_kw = ["SELECT", "FROM", "JOIN", "WHERE", "AND", "OR", "ON", "IN",
                  "GROUP", "BY", "ORDER", "LIMIT", "ASC", "DESC", "AS",
                  "=", "!=", "<", ">", "<=", ">=", "(", ")", ",", "*", ";", "."]
        extras = ["\n", ", ", " "]  # newline, comma-space, space MZ AN_, what else ??
        schema_ids = re.findall(r"[A-Za-z_]+", self.schema)

        def ids(word):
            return (self.vocab.encode(word, add_special_tokens=False) +
                    self.vocab.encode(" " + word, add_special_tokens=False))

        allowed = {i for w in sql_kw + extras + schema_ids for i in ids(w)
                   if 0 <= i < self.vocab.vocab_size}
        return torch.tensor(sorted(allowed), dtype=torch.long)

    def __call__(self, _in, scores):
        if self.allowed_ids.device != scores.device:
            self.allowed_ids = self.allowed_ids.to(scores.device)
        mask = torch.full_like(scores, float("-inf"))
        mask[:, self.allowed_ids] = 0
        return scores + mask
