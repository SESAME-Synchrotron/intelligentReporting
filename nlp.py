from dotenv import load_dotenv
load_dotenv() ## load all the environemnt variables

import streamlit as st
import os
import sqlite3

import google.generativeai as genai
## Configure Genai Key

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

## Function To Load Google Gemini Model and provide queries as response

def get_gemini_response(question,prompt):
    model=genai.GenerativeModel('gemini-pro')
    response=model.generate_content([prompt[0],question])
    return response.text

## Fucntion To retrieve query from the database

def read_sql_query(sql,db):
    conn=sqlite3.connect(db)
    cur=conn.cursor()
    cur.execute(sql)
    rows=cur.fetchall()
    conn.commit()
    conn.close()
    for row in rows:
        print(row)
    return rows

## Define Your Prompt

prompt1 = [
    """
    you are expert in SQL.
    You are given user text and you should only generate SQL query.
    You should only generate SQL query without any other text.
    Output must consist of **only the SQL query** without any additional explanations, prefixes, or code block formatting (i.e., no \` ```sql \`).

    tables that you should use: album

"""

]

prompt2 = [
    """
    You are a university professor explaining the concept of 'student' in different contexts. 
    Provide a detailed explanation that includes various interpretations of the word 'student' based on their level of education, 
    their role in society, and the challenges they face in modern education.

    Example 1 - Explain the role of a student in a research-oriented education system.
    Example 2 - Discuss the challenges faced by students in online learning environments.

    Make sure your explanation is thorough and covers multiple aspects.
    """
]


prompt3 = [
    """
    Imagine you are writing a short story. The main character is a 'student' who discovers they have special powers. 
    Describe a scene where the student first realizes their powers, focusing on their emotions, the setting, and the reactions of people around them.

    Example 1 - The student is in a classroom when they accidentally move objects with their mind.
    Example 2 - The student is at home when they first notice something unusual about their abilities.

    Make sure the description is vivid and immersive.
    """
]



## Streamlit App

st.set_page_config(page_title="I can Retrieve Any SQL query")
st.header("AI/Gemini App To Retrieve SQL Data")

question=st.text_input("Input: ",key="input")

submit=st.button("SQL generation")
submit2=st.button("University professor")
submit3=st.button("Story writer")

# if submit is clicked
if submit:
    response=get_gemini_response(question,prompt1)
    print("response::: ", response)
    st.header(response)
    response=read_sql_query(response,"Chinook.db")
    st.subheader("The REsponse is: ")
    st.header(response)
    # for row in response:
    #     print(row)
    #     st.header(row)

if submit2:
    response=get_gemini_response(question,prompt2)
    print("response::: ", response)
    st.subheader("The LLM Response is")
    st.header(response)

if submit3:
    response=get_gemini_response(question,prompt3)
    print("response::: ", response)
    st.subheader("The LLM Response is")
    st.header(response)
    # for row in response:
    #     print(row)
    #     st.header(row)
