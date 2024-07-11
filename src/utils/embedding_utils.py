import openai
import nltk
import spacy
from typing import List, Tuple


# Function to create embeddings
def create_embedding(text: str, model: str, dimensions: int = None) -> List[float]:
    if model == "text-embedding-3-large":
        response = openai.embeddings.create(model=model, input=text, dimensions=dimensions).data[0].embedding
    else:
        response = openai.embeddings.create(model=model, input=text).data[0].embedding[:dimensions]

    return response

# Chunk strategies
def chunk_fixed(sentences: List[str], chunk_size: int) -> List[List[str]]:
    return [sentences[i:i + chunk_size] for i in range(0, len(sentences), chunk_size)]

def chunk_nltk(text: str) -> List[str]:
    nltk.download('punkt')
    return nltk.tokenize.sent_tokenize(text)

def chunk_spacy(text: str) -> List[str]:
    # Load spacy model
    # Make sure you do: python -m spacy download en_core_web_sm
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(text)
    return [sent.text for sent in doc.sents]