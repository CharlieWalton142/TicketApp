from openai import OpenAI
import streamlit as st

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)

response = client.responses.create(
    model="gpt-5.5",
    input="Write one sentence about software testing."
)

print(response.output_text)