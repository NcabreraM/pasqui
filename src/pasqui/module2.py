import os
import pandas as pd
import openai
import tiktoken
from openai import Client
import numpy as np
from scipy import spatial  # for calculating vector similarities for search
from docx import Document
import logging

# Function to return the number of tokens in a string
def num_tokens(text, model=gpt):
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Function to split a string into subsections based on token limits, splitting by sentences
def split_strings_from_subsection(subsection, max_tokens=2000, model=gpt):
    titles, text = subsection
    string = "\n\n".join(titles + [text])

    # Split the string into sentences based on sentence-ending punctuation
    sentences = re.split(r'([.!?])', string)

    # Recombine sentences with their punctuation
    sentences = [sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '') for i in range(0, len(sentences), 2)]

    chunks = []
    current_chunk = ""
    current_token_count = 0

    for sentence in sentences:
        if sentence.strip():  # Ignore empty sentences
            # Calculate token count for the current chunk with the new sentence added
            token_count = num_tokens(current_chunk + sentence, model)

            if current_token_count + token_count <= max_tokens:
                # If adding this sentence doesn't exceed the max token limit, add it to the chunk
                current_chunk += sentence
                current_token_count += token_count
            else:
                # If it exceeds the limit, save the current chunk and start a new one
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_token_count = token_count

    # Add the last chunk if any
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

# Function to generate embeddings for processed sections
def generate_embeddings(processed_sections, embedding_model=em, batch_size=500):
    embeddings = []
    for batch_start in range(0, len(processed_sections), batch_size):
        batch_end = min(batch_start + batch_size, len(processed_sections))
        batch = processed_sections[batch_start:batch_end]
        response = client.embeddings.create(model=embedding_model, input=batch)
        embeddings.extend([e.embedding for e in response.data])
    return embeddings

# Function to process files, create folders if needed, and generate embeddings
def pasqui_embedding(folder_path, output_folder_path, gpt_model=gpt, em_model=em):
    try:
        # Ensure the output folder exists
        os.makedirs(output_folder_path, exist_ok=True)

        # Get the list of text files from the folder
        text_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith(('.txt', '.docx'))]

        # Process each file in the folder
        for file_path in text_files:
            # Load text from file
            with open(file_path, 'r', encoding='utf-8') as file:
                cleaned_text = file.read()

            # Split the text into subsections based on token limits
            subsections = split_strings_from_subsection((["Section"], cleaned_text), model=gpt)

            # Generate embeddings
            embeddings = generate_embeddings(subsections, embedding_model=em_model)

            # Save embeddings to CSV
            df = pd.DataFrame({"text": subsections, "embedding": embeddings})
            output_file_path = f"{output_folder_path}/{file_path.split('/')[-1].replace('.txt', '.csv')}"
            df.to_csv(output_file_path, index=False)
            print(f"Saved embeddings to {output_file_path}")

    except Exception as e:
        print(f"Error processing files in {folder_path}: {e}")