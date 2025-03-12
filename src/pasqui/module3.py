import re
import hashlib
import pandas as pd
import ast
from scipy import spatial  # for calculating vector similarities for search
from scipy.spatial import distance
import os
import pandas as pd
import openai
import tiktoken
from openai import Client
import numpy as np
from scipy import spatial  # for calculating vector similarities for search
from docx import Document
import logging

def load_embeddings(file_path):
    df = pd.read_csv(file_path)
    df['embedding'] = df['embedding'].apply(ast.literal_eval).apply(np.array)  # Apply ast.literal_eval to convert strings to lists and then np.array to convert to np array
    return df

def strings_ranked_by_relatedness(
    query: str,
    df: pd.DataFrame,
    relatedness_fn=lambda x, y: 1 - spatial.distance.cosine(x, y),
    top_n: int = num
) -> tuple[list[str], list[float]]:
    """Returns a list of strings and relatednesses, sorted from most related to least."""
    query_embedding_response = client.embeddings.create(
        model=em,
        input=query,
    )
    query_embedding = query_embedding_response.data[0].embedding
    strings_and_relatednesses = [
        (row["text"], relatedness_fn(query_embedding, row["embedding"]))
        for i, row in df.iterrows()
    ]
    # Sort by relatedness and return the top n results
    strings_and_relatednesses.sort(key=lambda x: x[1], reverse=True)
    return strings_and_relatednesses[:top_n] # Return the list of strings and relatednesses

def num_tokens(text: str, model: str = gpt) -> int:
    """Return the number of tokens in a string."""
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))
# Refactored query_message function
def query_message(query: str, df: pd.DataFrame, model: str, token_budget: int, question: str, introduction: str) -> str:
    """Return a message for GPT, with relevant source texts pulled from a dataframe."""
    strings = strings_ranked_by_relatedness(query, df)
    message = introduction
    for string in strings:
        next_article = f'\n\nSegment:\n{string}'
        if num_tokens(message + next_article + question, model=model) > token_budget:
            break
        else:
            message += next_article
    return message + question


def ask(query: str, df: pd.DataFrame, model: str = gpt, token_budget: int = token_budget, print_message: bool = print, introduction: str = intro, system_message: str = None, user_message: str = None) -> str:
    """Answer a query using a dataframe of relevant texts and embeddings."""
    
    # Use the default system message if none is provided
    if system_message is None:
        system_message = syst_message
    
    if user_message is None:
        user_message = query_message(query, df, model=model, token_budget=token_budget, question=query, introduction=introduction)

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]

    response = client.chat.completions.create(model=model, messages=messages, temperature=0)
    response_message = response.choices[0].message.content
    return response_message

# ask_questions_for_file remains the same, as the customizable parts are already defined outside.
def ask_questions_for_file(file_path, questions):
    df = load_embeddings(file_path)
    answers = {}
    for question in questions:
        answer = ask(question, df)
        answers[question] = answer
    return answers

# Setup logging function
def setup_logging(log_file_path):
    # Ensure the directory for the log file exists
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Set up logging
    logging.basicConfig(filename=log_file_path, level=logging.INFO)

# Function to list all files in a directory
def list_files_in_directory(directory_path):
    return os.listdir(directory_path)

# Function to create output directory if it doesn't exist
def create_summaries_out(summaries_out):
    if not os.path.exists(summaries_out):
        os.makedirs(summaries_out)

# Function to process questions for each file
def process_file(file_path, questions, headings, ask_questions_for_file):
    try:
        # Process questions for the current file
        answers = ask_questions_for_file(file_path, questions)
        _ = answers

        # Log success
        logging.info(f"Successfully processed {file_path}")

        return None
    except Exception as e:
        # Log the error
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

# Main function to orchestrate the processing
def pasqui_summarising(embeddings_dir, summaries_out, questions, headings, ask_questions_for_file, log_file_path):
    # Call the setup_logging function
    setup_logging(log_file_path)

    # List all files in the directory
    files = list_files_in_directory(embeddings_dir)

    # Create output directory if it doesn't exist
    create_summaries_out(summaries_out)

    # List to accumulate results
    results = []

    # Iterate through each file in the directory
    for file_name in files:
        file_path = os.path.join(embeddings_dir, file_name)

        # Process file and get answers
        answers = process_file(file_path, questions, headings, ask_questions_for_file)
        if answers:
            # Write the answers to a text file
            write_answers_to_file(file_name, answers, questions, headings, summaries_out)

            # Append results
            accumulate_results(file_name, headings, questions, answers, results)

    print("Processing completed. Check the log file for details.")
    return results


