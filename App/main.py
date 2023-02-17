"""Python file to serve as the frontend"""
import streamlit as st
from streamlit_chat import message
import sys
import os

parent_dir = os.path.abspath(os.path.join(os.getcwd(), "../gpt_index"))
sys.path.append(parent_dir)
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "..")))

from gpt_index import GPTPineconeIndex
import openai
import pinecone
import json

ROOT_DIR = os.path.abspath('/Users/sangyhanumasagar/Desktop/Freelancing/Investingdotcom/')

if (os.environ.get("OPENAI_API_KEY") == None):
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, 'config', '.env')) #UPDATE PATH

openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment=os.getenv("PINECONE_ENV"))

# load from disk
pc_index = pinecone.Index("earningsdata")
index_new = GPTPineconeIndex.load_from_disk('../data/indices/Earnings_index_pinecone.json', pinecone_index=pc_index)

# From here down is all the StreamLit UI.
st.set_page_config(page_title="Investing QA Bot", page_icon=":robot:")
st.header("QA Bot: this chatbot will answer questions based on earnings calls")
message('Hi I am Mr.Bot. I will share what I know along with sources for all my answers :)')

if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []
    
if "generated" not in st.session_state and "past" not in st.session_state:
    st.session_state = dict.fromkeys(["generated","past"],[]) 

def get_text():
    input_text = st.text_input("You: ", "Hello, how are you?", key="input")
    return input_text

def get_metadata(user_query):
    gpt3_response = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=f"Extract the company symbol, year and quarter from the query below.\nExample: \"What was Amazon's revenue numbers as reported in the third quarter of 2022?\"\nAnswer: {{'symbol': 'AMZN',  'quarter': 3, 'year': 2022}}\n\n{user_query}\nAnswer:",
                    temperature=0,
                    max_tokens=100,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0
                    )
    string_data = (gpt3_response["choices"][0]["text"].strip())
    if string_data:
        return json.loads(string_data.replace("'", "\"")) 

user_input = get_text()

if user_input:
    query = f"""You are a financial agent designed to answer questions about company earnings calls from the provided data.
The provided data contains companies represented by their S&P symbol (for example, AAPL for Apple, TSLA for TESLA) and their earnings calls for each quarter in the years 2021,2022.
Quarters can be referred to as Q1 for first quarter, Q2 for second quarter, Q3 for third quarter and Q4 for fourth quarter.
It is very important to first match the user query to the relevant company, year and quarter before proceeding to fetch the answers.
With this information, answer the following question: {user_input}"""

    query_metadata = get_metadata(user_input)
    response = index_new.query(query, query_metadata = query_metadata)
    
    source_info = response.source_nodes[0].source_text.split('\n')
    doc, quarter, symbol, FY= source_info[0],source_info[1],source_info[2],source_info[4]
    
    output = f"Answer: {response.response}\nSources: {doc, quarter, symbol, FY}"
    print(response)
    st.session_state['past'].append(user_input)
    st.session_state['generated'].append(output)

if st.session_state["generated"]:

    for i in range(len(st.session_state["generated"]) - 1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")