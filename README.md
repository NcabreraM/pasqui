
# Pasqui

Pasqui is a Python library created in Google Colab. It is useful to perform serveral functions needed to structure unstructured text. It was created based on my dissertation work at University of Cambridge with the support of chatGPT and Gemini for coding.
Pasqui is designed to handle large amounts of long files, and gracefully deal with errors avoiding repeated processing. It works with both pdfs and docs.

### It has 5 functions.
* pasqui_conveting -> converts pdfs and docs into texts and moves them to a new folder.
* pasqui_embedding -> creates embeddings using cosine similarity.
* pasqui_asks -> creates the topics for the summaries, needed for pasqui_summarising.
* pasqui_summarising -> creates summaries based on customisable topics.
* pasqui_structuring -> creates structured data from unstructured text.

Pasqui requires kor package knowledge and google drive.

Thanks for using Pasqui. This package is dedicated to my doggo, Pasqui! 🐶🐾

## Google Colab Demo  
Run the demo in Google Colab:  
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1BOhuEhxFr-JIVJDLd45YwHBW7HhYWmxg?usp=sharing)

## Installation
```bash
!pip install git+https://github.com/NcabreraM/pasqui.git

