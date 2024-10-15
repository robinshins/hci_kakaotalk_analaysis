import openai
from openai import OpenAI
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





def get_word_frequencies(words):
    counter = Counter(words)
    return counter

def generate_wordcloud(word_frequencies):
    wordcloud = WordCloud(width=800, height=600, background_color='white', font_path='assets/NanumSquareRoundR.ttf').generate_from_frequencies(word_frequencies)
    plt.figure(figsize=(7, 5))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.show()


def clean_text(text):
    # 날짜를 추출하여 날짜가 변경될 때마다 출력
    lines = text.strip().split('\n')
    current_date = None
    cleaned_lines = []

    for line in lines:
        # 날짜와 시간, 사용자명, 메시지를 분리
        match = re.match(r'(\d{4}/\d{2}/\d{2}) \d{2}:\d{2}, (.+?) : (.+)', line)
        if match:
            date, user, message = match.groups()
            # 날짜가 변경되면 새로운 날짜를 추가
            if date != current_date:
                current_date = date
                cleaned_lines.append(current_date)
            cleaned_lines.append(f"{user} : {message}")

    return "\n".join(cleaned_lines)


def split_text(text, chunk_size=3000, max_chunks=10):
    cleaned_text = clean_text(text)
    # 텍스트를 chunk_size만큼 뒤에서부터나누기
    length = len(cleaned_text)
    # print("텍스트 길이:"+str(length))
    chunks = []
    for i in range(max_chunks):
        start_index = max(0, length - (i + 1) * chunk_size)
        end_index = length - i * chunk_size
        if start_index >= end_index:
            break
        chunks.append(cleaned_text[start_index:end_index])
        if start_index == 0:
            break  # 텍스트의 시작까지 도달하면 종료
    chunks.reverse()  # 뒤에서부터 자른 후 순서를 원래대로 정렬
    #print("청크:"+str(chunks))
    return chunks


def gpt_request(kakao_chat):
    print("gpt_request: ", kakao_chat)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                너는 심리 및 대화 분석 전문가야.
                첨부된 채팅 내역을 바탕으로 대화 참여자들의 말투, 성격, 추억 등을 분석해.
                실제 대화 내역을 그대로 가져와서 상담 참여자가 분석에 대해서 더 공감할 수 있도록 해.
                실제 대화 내역은 [실제 대화 내역]으로 감싸서 표시.
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 : " + kakao_chat,
            },
        ],
    )
    return response.choices[0].message.content

# 최종 결과 통합때만 gpt-4o-mini 사용
def aggregate_responses(combined_responses):
    print("aggregate_responses: ", combined_responses)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 대화 분석 전문가임. 
                아래는 다른 전문가들이 분석한 내용임. 
                겹치는 분석 내용을 우선적으로 포함시키고, 이외에도 흥미로운 내용들이 있다면 추가함.
                대화 참여자들의 말투, 성격, 추억 등을 분석하는 것이 목표이며, 추억은 최대한 많이 포함시키도록 함.
                실제 대화 내역이 포함되도록 하고, 대화 내역은 각색하지 않고 그대로 인용. 이는 리포트를 보는 사람들이 실제 자신의 대화 내용을 확인함으로써, 리포트에 더욱 설득되도록 하기 위함임.
                """,
            },
            {
                "role": "user",
                "content": combined_responses,
            },
            {
                "role": "system",
                "content": """
                각 영역을 ** 등의 기호를 사용해서 구분하지 말고 대괄호안에 주제를 넣는 방식으로 구분.
                최대한 많은 내용을 포함시키도록 하고, 겹치는 내용은 중복해서 포함시키지 않도록 주의.
                분석 내용을 뒷받침 하는 자료로 대화 내역을 그대로 사용함.
                """,
            },
        ],
    )
    return response.choices[0].message.content

def analyze_past_life2(combined_responses):
    a = ""

    return a

def analyze_past_life(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 전생 분석 전문가입니다. 첨부된 채팅 내용 분석 내역을 바탕으로 두 사람이 전생에 어떤 관계였을지 추측하고 이를 재밌는 이야기로 작성해주세요.
                다음은 전생 관계 예시입니다. 예시는 참고할 수 있지만, 분석 내용을 바탕으로 새로운 이야기를 만들어주세요.
                예시 ) 마님과 돌쇠, 엄마와 딸, 반려견과 보호자, 선생님과 제자, 죄수와 간수, 개미와 배짱이, 강아지똥과 민들레씨 등
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 분석 : " + combined_responses,
            },
        ],
    )
    return response.choices[0].message.content

def write_poem(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 시인입니다. 첨부된 채팅 내역 분석을 바탕으로 시를 작성해주세요.
                직접적으로 두 사람의 관계를 언급하지 않으며, 비유적으로 작성.
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 분석 : " + combined_responses,
            },
        ],
    temperature=0.9,
    )
    return response.choices[0].message.content

def create_anniversary(kakao_chat):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 기념일 생성 전문가입니다. 첨부된 채팅 내역을 바탕으로 두 사람에게 의미 있는 기념일을 만들어주세요.
                기념일의 날짜(월/일 형식으로), 이유, 이를 위한 이벤트, 그날 나눴던 대화 등을 포함해주세요.
                그날 나눴던 대화는 각색하지 말고 그대로 인용해주세요.
                대화와 기념일은 서로 잘 어울리도록 만들어주세요.
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 : " + kakao_chat,
            },
        ],
    )
    return response.choices[0].message.content


def monthly_event(kakao_chat):
    print("monthly_event" , kakao_chat)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                유저의 채팅 내역을 바탕으로 각 월의 가장 메인이 되는 이벤트를 명사형으로 추출하고, 그 이벤트에 대한 두 줄 정도의 설명을 작성해주세요.
                분석할 수 있는 모든 달들을 분석해주세요. 연도 구분이 필요하면 연도까지 구분해주세요.
                출력 예시:
                
                [2024년 1월]
                두 사람이 식물원에 가서 식물을 구경했어요.
                식물에 대해서 이야기하기도하고, 저녁에는 스테이크를 먹으며 하루를 마무리했어요.
                00이는 ~~~ 라는 말을 하며 000한 감정을 표현했어요.
                (더 풍성한 내용들 추가)

                [2024년 2월]
                1주년을 기념하여 두 사람이 서로에게 선물을 주고받았어요.
                서로 옷을 선물했는데, 여자분의 옷은 사이즈가 맞지 않아서 교환하는 해프닝이 있었어요.
                (더 풍성한 내용들 추가)

                [2024년 3월]
                .
                .
                .

                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 : " + kakao_chat,
            },
        ],
    )
    return response.choices[0].message.content




def make_quiz(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 퀴즈를 만드는 출제자입니다. 주어진 대화를 보고 두 인물 각각에 대한 정보를 이용한 퀴즈나, 두 인물 간에 있었던
                사건들에 대한 퀴즈를 만들어서 출제합니다.
                퀴즈는 총 세개이며, 주관식 1개 객관식 2개를 출제합니다.
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 분석 : " + combined_responses,
            },
        ],
    )
    return response.choices[0].message.content

def emotion_donut(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 감정 분석가입니다. 대화 내용을 읽으며 각 단락 별로 어떤 감정이 가장 많이 드러나는지 수량을 분석, 분류해 json 형태로 출력하세요.
                기쁨이 약간 좀 더 있는 거로 해줘.
                감정 : ["기쁨", "슬픔", "놀람", "분노", "공포"]
                
                output format : 
                ```json
                {
                    "options" :{
                        "chart": {
                            "toolbar": {
                                "show": False
                            }
                        },

                        "labels": ["기쁨", "슬픔", "놀람", "분노", "공포"]
                        ,
                        "legend": {
                            "show": True,
                            "position": "bottom",
                        }
                    },
                    "series" : [(number of each emotions)]
                }
                ```
                """
                ,
            },
            {
                "role": "user",
                "content": "채팅 내역 분석 : " + combined_responses,
            },
        ],
    )
    result =  response.choices[0].message.content


    result = '\n'.join(result.strip().splitlines()[1:-1])   # remove extras

    data = json.loads(result)

    # Extract 'options' and 'series' from the dictionary
    options = data["options"]
    series = data["series"]

    # Print the resulting Python objects
    # print("options =", options)
    # print("series =", series)

    def gen_chart():
        st_apexcharts(options, series, 'donut', '600', '감정 빈도수')

    return gen_chart


def emotion_donut2(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 감정 분석가입니다. 대화 내용을 읽으며 각 단락 별로 어떤 감정이 가장 많이 드러나는지 수량을 분석, 분류해 json 형태로 출력하세요.
                기쁨이 약간 좀 더 있는 거로 해줘.
                감정 : ["기쁨", "슬픔", "놀람", "분노", "공포"]
                
                output format : 
                ```json
                {
                    "options" :{
                        "chart": {
                            "toolbar": {
                                "show": False
                            }
                        },

                        "labels": ["기쁨", "슬픔", "놀람", "분노", "공포"]
                        ,
                        "legend": {
                            "show": True,
                            "position": "bottom",
                        }
                    },
                    "series" : [(number of each emotions)]
                }
                ```
                """
                ,
            },
            {
                "role": "user",
                "content": "채팅 내역 분석 : " + combined_responses,
            },
        ],
    )
    result =  response.choices[0].message.content


    result = '\n'.join(result.strip().splitlines()[1:-1])   # remove extras

    data = json.loads(result)

    # Extract 'options' and 'series' from the dictionary
    options = data["options"]
    series = data["series"]

    # Print the resulting Python objects
    # print("options =", options)
    # print("series =", series)

    def gen_chart():
        st_apexcharts(options, series, 'donut', '600', '감정 빈도수')

    return gen_chart


def write_rap_lyric(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 국내 최고 힙합 프로듀서이다. 당신은 대화의 내용을 바탕으로 친구와 있었던 특별한 일에 대한 랩 가사를 작성한다.
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 분석 : " + combined_responses,
            },
        ],
    )
    return response.choices[0].message.content
