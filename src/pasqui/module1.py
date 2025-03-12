import os
import pdfplumber
from docx import Document

# Function to ensure output directory exists
def create_output_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

# Function to extract text from PDF files
def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text() or ''
        return text
    except pdfplumber.utils.PDFSyntaxError:
        print(f"Error: Could not process {pdf_path} - Skipping this file.")
        return None

# Function to extract text from DOCX files
def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        text = ''
        for para in doc.paragraphs:
            text += para.text + '\n'
        return text
    except Exception as e:
        print(f"Error: Could not process {docx_path} - {str(e)}")
        return None

# Function to write text to file
def save_text_to_file(text, output_path):
    with open(output_path, 'w') as file:
        file.write(text)

# Function to log errors
def log_error(error_log, message):
    error_log.write(message + '\n')

# Function to process files
def pasqui_converting(input_dir, output_dir, error_log_path):
    create_output_directory(output_dir)

    with open(error_log_path, 'w') as error_log:
        for filename in os.listdir(input_dir):
            file_path = os.path.join(input_dir, filename)

            if filename.endswith('.pdf'):
                extracted_text = extract_text_from_pdf(file_path)
                if extracted_text:
                    output_path = os.path.join(output_dir, filename.replace('.pdf', '.txt'))
                    save_text_to_file(extracted_text, output_path)
                    print(f"Text extracted from {filename} and saved to {output_path}")
                else:
                    log_error(error_log, f"Could not process: {filename}")
                    print(f"Skipping {filename} due to an error.")

            elif filename.endswith('.docx'):
                extracted_text = extract_text_from_docx(file_path)
                if extracted_text:
                    output_path = os.path.join(output_dir, filename.replace('.docx', '.txt'))
                    save_text_to_file(extracted_text, output_path)
                    print(f"Text extracted from {filename} and saved to {output_path}")
                else:
                    log_error(error_log, f"Could not process: {filename}")
                    print(f"Skipping {filename} due to an error.")

            else:
                log_error(error_log, f"Unsupported file type: {filename}")
                print(f"Unsupported file type: {filename}")
