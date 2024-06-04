import re
from collections import Counter
from wordcloud import WordCloud
import matplotlib.pyplot as plt

def preprocess_text_for_wordcloud(text):
    cleaned_text = re.sub(r'\[.*?\]', '', text)
    cleaned_text = re.sub(r'\d{4}년 \d{1,2}월 \d{1,2}일 \w요일', '', cleaned_text)
    cleaned_text = re.sub(r'\d{1,2}:\d{1,2}', '', cleaned_text)
    cleaned_text = re.sub(r'\n', ' ', cleaned_text)
    cleaned_text = re.sub(r'[^가-힣\s]', '', cleaned_text)
    words = cleaned_text.split()
    return words

def get_word_frequencies(words):
    counter = Counter(words)
    return counter