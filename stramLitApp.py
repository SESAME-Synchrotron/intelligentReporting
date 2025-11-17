import streamlit as st
import sqlparse
from transformers import pipeline
import torch

import pandas as pd

from st_aggrid import AgGrid, GridOptionsBuilder


# from similarityCheckerFAISS import SimilaritySearcher
from sqlQueryAgent import SQLQueryAgent
from sqlCoder import SQLGenerator


# @st.cache_resource(show_spinner="Loading GPT-2…")
# def load_gpt2_model(device: int, model_name: str, tokenizer_name: str):
#     return pipeline(
#         "text-generation",
#         model=model_name,
#         tokenizer=tokenizer_name,
#         device=device,
#     )


@st.cache_resource(show_spinner="Loading SQLCoder-7B-2 …")
def load_sqlcoder() -> SQLGenerator:
    """Load the 7-B model once per session (4-bit)."""
    return SQLGenerator(use_vocab_mask=False)


class IntelligentReportingAgentApp:
    def __init__(self, examples_csv: str):
        self.model_name: str | None = None
        self.acc_hw: str | None = None
        self.use_rag: bool = False

        # model handles
        self.generator = None
        self.sql_agent: SQLQueryAgent | None = None
        self.sqlcoder: SQLGenerator | None = None

        self.question: str = ""

        # RAG
        # self.searcher = SimilaritySearcher(useGpu=False)
        # self.searcher.parseExamplesCsv(examples_csv)
        # self.searcher.buildIndex()

    def run(self):
        self._render_header()
        self._sidebar()
        self._handle_model_selection()
        self._main_content()

    def _render_header(self):
        st.title("👋 Intelligent Reporting Agent")

    def _sidebar(self):
        st.sidebar.title("Settings")
        self.model_name = st.sidebar.selectbox(
            "Select a model:",
            (
                # "GPT2",
                # "GPT2-Tuned 1K",
                # "GPT2-Tuned 3K",
                # "GPT2-Tuned 6K",
                # "GPT2-Tuned 7K",
                # "GPT2-Tuned 10K",
                # "GPT2-Tuned 281K",
                # "GPT2-Medium",
                "SQLCoder-7B",
            ),
        )
        self.acc_hw = st.sidebar.selectbox("Compute device:", ("GPU", "CPU"))
        self.use_rag = st.sidebar.checkbox(
            "Use Retrieval-Augmented (RAG)", value=False
        )


    def _handle_model_selection(self):
        device = 0 if (self.acc_hw == "GPU" and torch.cuda.is_available()) else -1
        # base = "trainedGPT2/gpt2-spider-sql-{}"

        # # --- plain GPT-2 
        # if self.model_name == "GPT2":
        #     self.generator = load_gpt2_model(device, "gpt2", "gpt2")
        #     self.sqlcoder = self.sql_agent = None
        #     return

        # # --- GPT-2 fine-tunes 
        # if self.model_name and self.model_name.startswith("GPT2-Tuned"):
        #     n = int(self.model_name.split()[-1].replace("K", "000"))
        #     model_path = base.format(n)
        #     self.generator = load_gpt2_model(device, model_path, model_path)
        #     self.sqlcoder = self.sql_agent = None
        #     return

        # # --- GPT-2-Medium 
        # if self.model_name == "GPT2-Medium":
        #     if self.sql_agent is None:
        #         self.sql_agent = SQLQueryAgent()   # loads lazily
        #     self.generator = self.sqlcoder = None
        #     self.use_rag = False
        #     return

        # --- SQLCoder-7B-2 
        if self.model_name == "SQLCoder-7B":
            if self.sqlcoder is None:
                self.sqlcoder = load_sqlcoder()
            self.generator = self.sql_agent = None
            self.use_rag = False
            return

    # ---------------- main UI panel -------------------------------------- #
    def _main_content(self):
        self.question = st.text_input("Ask your question:")

        if not st.button("Generate report"):
            return

        # ---------- SQLCoder branch --------------------------------------
        if self.model_name == "SQLCoder-7B":
            if self.sqlcoder is None or not self.question:
                st.warning("Please enter a question and wait for the model to load.")
                return
            with st.spinner("Generating SQL with SQLCoder-7B-2…"):
                # sql = self.sqlcoder.ask_sql(self.question)
                sql = self.sqlcoder.ask_sql(self.question)[0]
                # st.code(sql, language="sql")
                cols, rows = self.sqlcoder.executeSQL(sql)
            if rows is None:
                st.error("Query failed or returned no data.")
                sql_formatted = sqlparse.format(
                sql,
                reindent=True,
                keyword_case="upper"
                )
                st.code(sql_formatted, language="sql")
                st.stop()
            df = pd.DataFrame(rows, columns=cols)
            st.subheader("Generated SQL:")
            sql_formatted = sqlparse.format(
                sql,
                reindent=True,
                keyword_case="upper"
            )

            st.code(sql_formatted, language="sql")

            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_default_column(
                filterable=True, sortable=True, resizable=True
            )
            gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=30)
            grid_opts = gb.build()

            st.subheader("Query results")
            AgGrid(
                df,
                gridOptions=grid_opts,
                enable_enterprise_modules=False,
                allow_unsafe_jscode=False,
                fit_columns_on_grid_load=True,
                height=400
            )
            return

        # # ---------- GPT-2-Medium branch ----------------------------------
        # if self.model_name == "GPT2-Medium":
        #     if self.sql_agent is None or not self.question:
        #         st.warning("Please enter a question and wait for the model to load.")
        #         return
        #     with st.spinner("Generating SQL with GPT-2-Medium…"):
        #         sql, rows = self.sql_agent.ask_sql(self.question)
        #     if sql:
        #         st.subheader("Generated SQL (GPT-2-Medium):")
        #         st.code(sql, language="sql")
        #         st.subheader("Query results:")
        #         st.write(rows)
        #     else:
        #         st.warning("No executable SQL query generated.")
        #     return

        # ---------- GPT-2 / fine-tunes branch ----------------------------
        if self.generator is None or not self.question:
            st.warning("Please enter a question and ensure the model is loaded.")
            return

       

        with st.spinner("Generating answer with GPT-2…"):
            output = self.generator(
                prompt,
                max_new_tokens=250,
                temperature=0.1,
                top_k=30,
                top_p=0.8,
                repetition_penalty=1.5,
                num_return_sequences=1,
            )

        st.subheader("GPT-2 says:")
        st.write(output[0]["generated_text"])

    # ---------- helper: RAG prompt --------------------------------------- #
    # def _build_prompt_for_gpt2(self, question: str) -> str:
    #     examples = self.searcher.retrieve(question, topK=3)
    #     few_shot = "\n\n".join(
    #         f"### Example\nQuestion: {q}\nSQL Query: {sql}" for q, sql in examples
    #     )
    #     return f"{few_shot}\n\n### Now question:\n{question}\n### SQL Query:\n"


# ------------------------- CLI entry-point ----------------------------- #
if __name__ == "__main__":
    app = IntelligentReportingAgentApp("RAG_Chinook.csv")
    app.run()
