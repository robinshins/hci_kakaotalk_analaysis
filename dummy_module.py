import json
from streamlit_apexjs import st_apexcharts
import streamlit as st
import re
import os
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import module
from collections import Counter, defaultdict
from datetime import datetime
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import streamlit.components.v1 as components

import time

WAIT = 3 # wait seconds

def preprocess_text_for_wordcloud(text):
    cleaned_text = re.sub(r'\[.*?\]', '', text)
    cleaned_text = re.sub(r'\d{4}년 \d{1,2}월 \d{1,2}일 \w요일', '', cleaned_text)
    cleaned_text = re.sub(r'\d{1,2}:\d{1,2}', '', cleaned_text)
    cleaned_text = re.sub(r'\n', ' ', cleaned_text)
    cleaned_text = re.sub(r'[^가-힣\s]', '', cleaned_text)
    words = cleaned_text.split()

    stop_words = set(['년', '월', '일', '오전', '오후', '시간', '이모티콘', '나', '너', '난', '아', '좀', '흠', '카카오페이머니는', '온오프라인', '가능해요'])

    name_pattern = re.compile(r'\b[가-힣]{2,3}\b')
    potential_names = [word for word in words if name_pattern.match(word)]
    name_frequencies = Counter(potential_names)

    common_names = {name for name, count in name_frequencies.items() if count > 10}
    words = [word for word in words if word not in common_names and word not in stop_words and len(word) > 1]

    return words



DATE_PATTERN1 = r'(\d{4}년 \d{1,2}월 \d{1,2}일) ((오전|오후)?\s*\d{1,2}:\d{1,2})'   # 2023년 12월 12일 (오전) 4:24   
DATE_PATTERN2 = r'(\d{4}. \d{1,2}. \d{1,2}(.)?) ((오전|오후)?\s*\d{1,2}:\d{1,2})'    # 2023. 10. 1(.) (오전) 4:24
DATE_PATTERN3 = r'(\d{4}/\d{1,2}/\d{1,2}) (\d{1,2}:\d{1,2})'        # 2023/1/12 19:23
DATE_PATTERN4 = r'(\d{4}-\d{1,2}-\d{1,2}) (\d{1,2}:\d{1,2}:\d{1,2})'        # 2024-03-15 14:05:17

DATE_PATTERN_PC_DATE = r'(-*\s*\d{4}년 \d{1,2}월 \d{1,2}일 [월화수목금토일]\s*-*)'  # --------------- 2024년 4월 3일 수요일 ---------------
DATE_PATTERN_PC_MSG = r'\[(.*)\] \[((오전|오후)? \d{1,2}:\d{2})\]' # [홍길동] [오후 10:49]


def get_word_frequencies(words):
    counter = Counter(words)
    return counter

def generate_wordcloud(word_frequencies):
    wordcloud = WordCloud(width=800, height=600, background_color='white', font_path='assets/NanumSquareRoundR.ttf').generate_from_frequencies(word_frequencies)
    plt.figure(figsize=(7, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()




# obsolete
def clean_text(text):
    # 정규 표현식을 사용하여 날짜 형식을 남기고 시간 형식 제거
    cleaned_text = re.sub(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}, ', '', text)
    # 쉼표 뒤에 남아 있는 공백 제거
    cleaned_text = re.sub(r',\s+', ', ', cleaned_text)
    # 중복 공백 제거
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
    return cleaned_text

def group_chat_dialogs(chat):
    chat_lines = chat.strip().split('\n')
    date_pattern = None

        # find which pattern fits by trying various patterns
    for line in chat_lines:
        if date_pattern is None:
            if re.match(DATE_PATTERN1, line):
                date_pattern = DATE_PATTERN1
                break
            elif re.match(DATE_PATTERN2, line):
                date_pattern = DATE_PATTERN2
                break
            elif re.match(DATE_PATTERN3, line):
                date_pattern = DATE_PATTERN3
                break
            elif re.match(DATE_PATTERN4, line):
                date_pattern = DATE_PATTERN4
                break
            elif re.match(DATE_PATTERN_PC_DATE, line):
                date_pattern = DATE_PATTERN_PC_DATE
                break

    print('found pattern : '+ date_pattern)

    if date_pattern == DATE_PATTERN_PC_DATE:
        return parse_chat_pc(chat_lines)
    else:
        return parse_chat_mobile(chat_lines,date_pattern)


def parse_chat_mobile(chat_lines, date_pattern):
    grouped_chats = defaultdict(list)
    current_date = None
    current_time = None
    for line in chat_lines:
        # Check for date line
        date_match = re.match(date_pattern, line)
        if date_match:
            if current_date != date_match.group(1):
                current_date = date_match.group(1)
                # grouped_chats[current_date].append(current_date)

            if current_time != date_match.group(2):
                current_time = date_match.group(2)
                grouped_chats[current_date].append('\n'+current_time)

        elif current_date is None:
            # pass headers
            continue
        else:
            # continuous line from prvious chat line.
            grouped_chats[current_date].append(line)
            continue


        # Parse each chat line
        chat_match = re.match(date_pattern + r',?\s*(.*)\s*[:,]\s*(.*)', line)
        if chat_match:
            date_part, time_part, speaker, message = None, None, None, None
            if len(chat_match.groups()) == 5:
                # no ampm
                date_part, am_pm, time_part, speaker, message = chat_match.groups()
            elif len(chat_match.groups()) == 4:
                # no ampm
                date_part, time_part, speaker, message = chat_match.groups()
            else:
                # headers
                continue
            grouped_chats[current_date].append(f"{speaker}: {message}")
        
        
    result = []

    for date, messages in grouped_chats.items():
        result.append(f"{date}")
        result.extend(messages)
        result.append("")  # for new line between different dates
    print(result)
    return "\n".join(result)


def parse_chat_pc(chat_lines):
    grouped_chats = defaultdict(list)
    current_date = None
    current_time = None
    for line in chat_lines:
        # Check for date line
        date_match = re.match(DATE_PATTERN_PC_DATE, line)
        date_match_msg = re.match(DATE_PATTERN_PC_MSG, line)

        if date_match:
            if current_date != date_match.group(1):
                current_date = date_match.group(1)
                # continue to next lines
                continue

        if date_match_msg:
            if current_time != date_match_msg.group(2):
                current_time = date_match_msg.group(2)
                grouped_chats[current_date].append('\n'+current_time)

        elif current_date is None:
            # pass headers
            continue
        else:
            # continuous line from prvious chat line.
            grouped_chats[current_date].append(line)
            continue


        # Parse each chat line
        chat_match = re.match(DATE_PATTERN_PC_MSG + r'\s*(.*)', line)
        if chat_match:
            speaker, time_part, message = None, None, None
            if len(chat_match.groups()) == 4:
                # ampm
                speaker, am_pm, time_part, message = chat_match.groups()
            elif len(chat_match.groups()) == 3:
                # no ampm
                speaker, time_part, message = chat_match.groups()
            else:
                # headers
                continue
            grouped_chats[current_date].append(f"{speaker}: {message}")
        
        
    result = []

    for date, messages in grouped_chats.items():
        result.append(f"{date}")
        result.extend(messages)
        result.append("")  # for new line between different dates
    
    return "\n".join(result)


def split_text(text, chunk_size=10000, max_chunks=10):
    # 텍스트를 chunk_size만큼 뒤에서부터 나누기
    length = len(text)
    # print("텍스트 길이:"+str(length))
    chunks = []
    for i in range(max_chunks):
        start_index = max(0, length - (i + 1) * chunk_size)
        end_index = length - i * chunk_size
        if start_index >= end_index:
            break
        chunks.append(text[start_index:end_index])
        if start_index == 0:
            break  # 텍스트의 시작까지 도달하면 종료
    chunks.reverse()  # 뒤에서부터 자른 후 순서를 원래대로 정렬
    #print("청크:"+str(chunks))
    return chunks


def gpt_request(kakao_chat):
    print("running dummy gpt_request")
    time.sleep(WAIT)
    return "Dummy Response"

# 최종 결과 통합때만 gpt-4o 사용
def aggregate_responses(combined_responses):
    print("running dummy aggregate_response")
    time.sleep(WAIT)
    return "Dummy Aggregated Response"

def analyze_past_life2(combined_responses):
    time.sleep(WAIT)
    return ""

def analyze_past_life(combined_responses):
    print("running dummy analyze_past_life")
    time.sleep(WAIT)
    return "Dummy Past Life"
    

def write_poem(combined_responses):
    print("running dummy write_poem")
    time.sleep(WAIT)
    return "Dummy Poem"

def create_anniversary(kakao_chat):
    print("running dummy create_anniversary")
    time.sleep(WAIT)
    return "Dummy Anniverary"


def monthly_event(kakao_chat):
    print("running dummy monthly_event")
    time.sleep(WAIT)
    return "Dummy Monthly Event"
    




def make_quiz(combined_responses):
    print("running dummy make_quiz")
    time.sleep(WAIT)
    return "Dummy Quiz"

def emotion_donut(combined_responses):
    print("running dummy emotion_donut")
    time.sleep(WAIT)

    options = {'chart': {'toolbar': {'show': False}}, 'labels': ['기쁨', '슬픔', '놀람', '분노', '공포', '혐오', '중립'], 'legend': {'show': True, 'position': 'bottom'}}
    series = [300, 50, 120, 80, 10, 20, 150]
    
    def gen_chart():
        st_apexcharts(options, series, 'donut', '600', '감정 빈도수')

    return gen_chart


def write_rap_lyric(combined_responses):
    print("running dummy write_rap_lyric")
    time.sleep(WAIT)
    return "Dummy Rap Lyric"
