# sqlcoder_agent.py
import threading
from pathlib import Path
from typing import List, Optional
import sqlite3

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    LogitsProcessorList,
    TextIteratorStreamer,
)

from sql_mask import SQLMask
import streamlit as st


class SQLGenerator:
    """
    Text-to-SQL generator backed by Defog SQLCoder-7B-2 (4-bit NF4).
    """

    def __init__(
        self,
        model_name: str = "defog/sqlcoder-7b-2",
        use_vocab_mask: bool = True,
        temperature: float = 0.0,
        num_beams: int = 4,
        top_p: float = 0.9,
    ):
        self.temperature = temperature
        self.num_beams = num_beams
        self.top_p = top_p
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        bnb_cfg = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
        )
        self.model = (
            AutoModelForCausalLM.from_pretrained(
                model_name, quantization_config=bnb_cfg, device_map="auto"
            )
            .eval()
        )

        #  prompt scaffolding --> MZ to change this to SUP DB 
        self.schema = Path("createSampleDB/sqlite3/schema.txt").read_text().strip()
        self.examples = Path("createSampleDB/sqlite3/examples.txt").read_text().strip()
        self.db_path="createSampleDB/sqlite3/Chinook.db"

        # -------- SQL-aware logits mask -------------------------------------
        if use_vocab_mask:
            mask = SQLMask(self.tokenizer, self.schema)

            # 🔧 FIX: convert list → tensor so .device exists
            if isinstance(mask.allowed_ids, list):
                mask.allowed_ids = torch.tensor(
                    mask.allowed_ids, dtype=torch.long, device=self.model.device
                )

            self.sql_mask: Optional[LogitsProcessorList] = LogitsProcessorList([mask])
        else:
            self.sql_mask = None

        # -------- context window --------------------------------------------
        self.max_ctx = (
            getattr(self.model.config, "max_position_embeddings", None)
            or getattr(self.model.config, "n_positions", None)
            or self.tokenizer.model_max_length
        )

    # --------------------------------------------------------------------- #
    def _build_inputs(self, question: str) -> torch.Tensor:
        prompt = (
            f"### Database schema\n{self.schema}\n\n"
            f"### Examples\n{self.examples}\n\n"
            f"### Task\nWrite ONE valid SQLite query that answers the question.\n\n"
            f"### Question\n{question}\n\n### Answer\n"
        )
        ids = self.tokenizer(prompt).input_ids
        ids = ids[-(self.max_ctx - 256) :]            # leave room for output
        return torch.tensor(ids, device=self.model.device).unsqueeze(0)

    # --------------------------------------------------------------------- #
    def ask_sql(
        self,
        question: str,
        k_return: int = 1,
        stream: bool = False,
    ) -> List[str]:
        """Return up to k_return SQL strings (always ending in ‘;’)."""
        input_ids = self._build_inputs(question)
        max_new = min(self.max_ctx - input_ids.size(-1), 128)

        gen_kwargs = dict(
            input_ids=input_ids,
            max_new_tokens=max_new,
            pad_token_id=self.tokenizer.eos_token_id,
            eos_token_id=[self.tokenizer.eos_token_id],
            logits_processor=self.sql_mask,
            num_return_sequences=self.num_beams if self.temperature == 0 else k_return,
        )
        if self.temperature > 0:
            gen_kwargs.update(
                do_sample=True, top_p=self.top_p, temperature=self.temperature
            )
        else:
            gen_kwargs.update(do_sample=False, num_beams=self.num_beams)

        # -------- optional live streaming -----------------------------------
        if stream:
            streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True)
            gen_kwargs["streamer"] = streamer
            threading.Thread(
                target=self.model.generate, kwargs=gen_kwargs, daemon=True
            ).start()
            partial = ""
            for token_text in streamer:
                partial += token_text
                st.empty()
                st.code(partial, language="sql")

        # -------- standard generation ---------------------------------------
        with torch.inference_mode():
            sequences = self.model.generate(**gen_kwargs)

        results: List[str] = []
        for seq in sequences:
            text = self.tokenizer.decode(seq[input_ids.size(-1) :])
            results.append(text.split(";")[0].strip() + ";")
            if len(results) >= k_return:
                break
        return results
    def executeSQL(self, sql):
        self.conn = sqlite3.connect(self.db_path)
        try:
            conn = sqlite3.connect(self.db_path)
            cur  = conn.execute(sql)
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            return cols, rows
        except sqlite3.DatabaseError:
            pass
        return None, None
