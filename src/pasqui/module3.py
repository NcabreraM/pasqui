import os
import ast
import logging
import pandas as pd
import numpy as np
import tiktoken
import openai
from scipy import spatial  # For calculating vector similarities
from openai import Client

# Constants
num = 20
gpt = "gpt-4o-mini"
token_budget = 7000 - 500
intro = None

def get_client():
    """Initialize OpenAI client. API key must be set before calling this function."""
    api_key = os.getenv("api_key")  # Get API key from environment
    if not api_key:
        raise ValueError("API key is required but not set. Use os.environ['api_key'] = 'your-key' before calling OpenAI functions.")
    
    return openai.Client(api_key=api_key)  # Initialize client only when needed

def load_embeddings(file_path):
    """Load embeddings from a CSV file."""
    df = pd.read_csv(file_path)
    df['embedding'] = df['embedding'].apply(ast.literal_eval).apply(np.array)
    return df

def strings_ranked_by_relatedness(query, df, top_n=num):
    """Return a list of strings sorted by relatedness."""
    client = get_client()  # Initialize only when needed

    query_embedding_response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=query,
    )
    query_embedding = query_embedding_response.data[0].embedding
    strings_and_relatednesses = [
        (row["text"], 1 - spatial.distance.cosine(query_embedding, row["embedding"]))
        for _, row in df.iterrows()
    ]
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    return strings_and_relatednesses[:top_n]

def num_tokens(text, model=gpt):
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

def query_message(query, df, model, token_budget, question, introduction):
    """Return a message for GPT with relevant source texts."""
    strings = strings_ranked_by_relatedness(query, df)
    message = introduction or ""
    
    for string in strings:
        next_article = f'\n\nSegment:\n{string[0]}'
        if num_tokens(message + next_article + question, model=model) > token_budget:
            break
        else:
            message += next_article
    return message + question

def ask(query, df, model=gpt, token_budget=token_budget, introduction=intro, system_message=None):
    """Answer a query using a dataframe of relevant texts and embeddings."""
    client = get_client()  # Initialize client inside function

    if system_message is None:
        system_message = "You are an AI assistant helping with information retrieval."

    user_message = query_message(query, df, model=model, token_budget=token_budget, question=query, introduction=introduction)

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(model=model, messages=messages, temperature=0)
    return response.choices[0].message.content

# ask_questions_for_file remains the same, as the customizable parts are already defined outside.
def ask_questions_for_file(file_path, questions):
    df = load_embeddings(file_path)
    answers = {}
    for question in questions:
        answer = ask(question, df)
        answers[question] = answer
    return answers

def setup_logging(log_file_path):
    # Ensure the directory for the log file exists
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up logging
    logging.basicConfig(filename=log_file_path, level=logging.INFO)

def list_files_in_directory(directory_path):
    """List all files in a directory."""
    return os.listdir(directory_path)

# Function to create output directory if it doesn't exist
def create_summaries_out(summaries_out):
    if not os.path.exists(summaries_out):
        os.makedirs(summaries_out)

# Function to create output directory if it doesn't exist
def create_summaries_out(summaries_out):
    if not os.path.exists(summaries_out):
        os.makedirs(summaries_out)