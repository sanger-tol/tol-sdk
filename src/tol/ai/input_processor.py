# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import nltk
import string
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
 
# Download essential datasets and models
nltk.download('punkt')  # Tokenizers for sentence and word tokenization
nltk.download('stopwords')  # List of common stop words
nltk.download('wordnet')  # WordNet lexical database for lemmatization
nltk.download('punkt_tab')


class InputProcessor:
    """
    Base class for boards models.
    """

    def __init__(self) -> None:
        pass
    
    def process_text(self, text: str) -> str:
        tokenized_text = self._tokenize_text(text)
        filtered_text = self._remove_stopwords(tokenized_text)
        stemmed_text = self._lemmatize_words(filtered_text)
        
        
    def _tokenize_text(self, text: str) -> list[str]:
        cleaned_text = ''.join(char for char in text if char not in string.punctuation)
        # Word Tokenization
        words = word_tokenize(cleaned_text)
        return words
    
    def _remove_stopwords(self, words: list) -> list[str]:
        # Load NLTK's stopwords list
        stop_words = set(stopwords.words('english'))
        
        # Filter out stop words
        filtered_words = [word for word in words if word.lower() not in stop_words]
        return filtered_words
    
    def _lemmatize_words(self, words: list) -> list[str]:
        # Initialize the Lemmatizer
        lemmatizer = WordNetLemmatizer()
        
        # Lemmatize each word
        lemmatized_words = [lemmatizer.lemmatize(word, pos='v') for word in words]
        print("Lemmatized Words:", lemmatized_words)