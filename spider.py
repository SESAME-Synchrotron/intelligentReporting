from datasets import load_dataset
import pandas as pd

ds = load_dataset("KaifengGGG/spider_sql_schema")


first_1000 = ds['train'].select(range(1000))


df = pd.DataFrame(first_1000)[['question', 'query']]


print(df.head())  # Show first few rows


df.to_csv("first_1000_questions_queries.csv", index=False)
