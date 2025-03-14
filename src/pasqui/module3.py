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
em = "text-embedding-3-small"
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
        model=em,
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
    """Use only the provided information to answer the query, if you don't know the answer return NA"""
    client = get_client()  # Initialize client inside function

    if system_message is None:
        system_message = """
You are Professor Smith, a highly rigorous social sciences professor.
Use only the information of the text I provided to answer the question.
If you don't know the answer, just say that you do not know and return NA.
"""

    user_message = query_message(query, df, model=model, token_budget=token_budget, question=query, introduction=introduction)

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(model=model, messages=messages, temperature=0)
    return response.choices[0].message.content

# ask_questions_for_file remains the same, as the customizable parts are already defined outside.
def pasqui_asks(file_path, questions):
    df = load_embeddings(file_path)
    answers = {}
    for question in questions:
        answer = ask(question, df)
        answers[question] = answer
    return answers

def setup_logging(log_file_path):
    """Ensure the log directory exists and set up logging."""
    log_dir = os.path.dirname(log_file_path)
    os.makedirs(log_dir, exist_ok=True)  # Creates directory if it doesn't exist

    # Set up logging
    logging.basicConfig(filename=log_file_path, level=logging.INFO)
    print(f"Logging set up at {log_file_path}")  # Debug message

def list_files_in_directory(directory_path):
    """List all files in a directory."""
    return os.listdir(directory_path)

# Function to create output directory if it doesn't exist
def create_summaries_out(summaries_out):
    if not os.path.exists(summaries_out):
        os.makedirs(summaries_out)

def process_file(file_path, questions, headings, pasqui_asks):
    try:
        answers = pasqui_asks(file_path, questions)  # Get answers
        logging.info(f"Successfully processed {file_path}")
        return answers  # Ensure it returns answers
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return None

# Function to write answers to a text file
def write_answers_to_file(file_path, answers, questions, headings, summaries_out):
    try:
        # Generate text output file path
        text_output_path = os.path.join(summaries_out, f"{file_path}.txt")

        # Open the text file for writing
        with open(text_output_path, 'w') as textfile:
            textfile.write(f"Results for {file_path}:\n\n")

            # Write each question and its answer to the text file
            for heading, question in zip(headings, questions):
                answer = answers.get(question, "No answer found")
                textfile.write(f"{heading}: {answer}\n")

        return text_output_path
    except Exception as e:
        logging.error(f"Error writing to file {file_path}: {e}")
        return None

# Function to accumulate results in a list
def accumulate_results(file_name, headings, questions, answers, results):
    result = {'file_name': file_name}
    for heading, question in zip(headings, questions):
        answer = answers.get(question, "No answer found")
        result[heading] = answer
    results.append(result)

def pasqui_summarising(embeddings_dir, summaries_out, questions, headings, pasqui_asks, log_file_path):
    # Call the setup_logging function
    setup_logging(log_file_path)

    # List all files in the directory
    files = list_files_in_directory(embeddings_dir)
    print(f"Files found: {files}")  # Debugging step

    # Create output directory if it doesn't exist
    create_summaries_out(summaries_out)

    # List to accumulate results
    results = []

    # Iterate through each file in the directory
    for file_name in files:
        file_path = os.path.join(embeddings_dir, file_name)
        print(f"Processing file: {file_path}")  # Debugging step

        # Process file and get answers
        answers = process_file(file_path, questions, headings, pasqui_asks)

        # Removed incorrect 'done' reference and prevented answers from printing
        # print(f"Generated answers: {answers}")  # Commented out to stop console output

        if answers:  # Only proceed if answers are returned
            base_name = file_name
            write_answers_to_file(base_name, answers, questions, headings, summaries_out)
            accumulate_results(base_name, headings, questions, answers, results)

    return results  # Ensure return is the last statement
