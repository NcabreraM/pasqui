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

def ask_questions_for_file(file_path, questions):
    """Ask multiple questions about a file."""
    df = load_embeddings(file_path)
    return {question: ask(question, df) for question in questions}

def setup_logging(log_file_path):
    """Setup logging."""
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
    logging.basicConfig(filename=log_file_path, level=logging.INFO)

def list_files_in_directory(directory_path):
    """List all files in a directory."""
    return os.listdir(directory_path)

def create_summaries_out(summaries_out):
    """Ensure summaries output directory exists."""
    os.makedirs(summaries_out, exist_ok=True)

def process_file(file_path, questions, ask_questions_for_file):
    """Process questions for a file and log errors if any."""
    try:
        answers = ask_questions_for_file(file_path, questions)
        logging.info(f"Successfully processed {file_path}")
        return answers
    except Exception as e:
        logging.error(f"Error processing {file_path}: {e}")
        return None

def write_answers_to_file(file_name, answers, questions, headings, summaries_out):
    """Write answers to a text file."""
    try:
        text_output_path = os.path.join(summaries_out, f"{file_name}.txt")
        with open(text_output_path, 'w') as textfile:
            textfile.write(f"Results for {file_name}:\n\n")
            for heading, question in zip(headings, questions):
                answer = answers.get(question, "No answer found")
                textfile.write(f"{heading}: {answer}\n")
        return text_output_path
    except Exception as e:
        logging.error(f"Error writing to file {file_name}: {e}")
        return None

def accumulate_results(file_name, headings, questions, answers, results):
    """Accumulate results in a list."""
    result = {'file_name': file_name}
    for heading, question in zip(headings, questions):
        result[heading] = answers.get(question, "No answer found")
    results.append(result)

def pasqui_summarising(embeddings_dir, summaries_out, questions, headings, log_file_path):
    """Main function to process multiple files."""
    setup_logging(log_file_path)
    files = list_files_in_directory(embeddings_dir)
    create_summaries_out(summaries_out)
    results = []

    for file_name in files:
        file_path = os.path.join(embeddings_dir, file_name)
        answers = process_file(file_path, questions, ask_questions_for_file)
        if answers:
            write_answers_to_file(file_name, answers, questions, headings, summaries_out)
            accumulate_results(file_name, headings, questions, answers, results)

    print("Processing completed. Check the log file for details.")
    return results
