import openai
from openai import OpenAI
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI()

def get_watch_name(title):
    query = f"""You are given the title of a listing on a watch exchange forum. Extract the watch name that you can use to search up the watch on Ebay. The title is: 
    {title}"""
    messages = [{"role": "user", "content": query}]
    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
    )
    query2 = "Now output just the watch name."
    messages = [{"role": "user", "content": query}, {"role": "assistant", "content": response.choices[0].message.content}, {"role": "user", "content": query2}]
    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
    )
    return response.choices[0].message.content

def get_price(string):
    query = f"""You are given the text of a listing on a watch exchange forum. If there is a price listed, extract the price of the watch as a decimal. Otherwise, output "Not found". The text is: 
    {string}"""
    messages = [{"role": "user", "content": query}]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    try:
        return float(response.choices[0].message.content)
    except:
        return -1

def get_condition(string):
    query = f"""You are given the text of a listing on a watch exchange forum. Output the condition of the watch. The options are "New", "Excellent", "Great", "Good", "Fair". The text is: 
    {string}"""
    messages = [{"role": "user", "content": query}]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    query2 = "Now output just the condition."
    messages = [{"role": "user", "content": query}, {"role": "assistant", "content": response.choices[0].message.content}, {"role": "user", "content": query2}]
    response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
    )
    return response.choices[0].message.content