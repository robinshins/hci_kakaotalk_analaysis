import openai
from openai import OpenAI
import json
from streamlit_apexjs import st_apexcharts

def analyze_past_life(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
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
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 시인입니다. 첨부된 채팅 내역 분석을 바탕으로 시를 작성해주세요.
                시에는 두 사람의 관계가 은은하게 담길 수 있도록 해주세요.
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 분석 : " + combined_responses,
            },
        ],
    )
    return response.choices[0].message.content

def create_anniversary(kakao_chat):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
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
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                채팅 내역을 바탕으로 각 월의 가장 메인이 되는 이벤트를 명사형으로 추출하고, 그 이벤트에 대한 두 줄 정도의 설명을 작성해주세요.
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
        model="gpt-4o",
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
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 감정 분석가입니다. 대화 내용을 읽으며 각 단락 별로 어떤 감정이 가장 많이 드러나는지 수량을 분석, 분류해 json 형태로 출력하세요.
                기쁨이 약간 좀 더 있는 거로 해줘.
                감정 : ["기쁨", "슬픔", "놀람", "분노", "공포", "혐오", "중립"]
                
                output format : 
                ```json
                {
                    "options" :{
                        "chart": {
                            "toolbar": {
                                "show": False
                            }
                        },

                        "labels": ["기쁨", "슬픔", "놀람", "분노", "공포", "혐오", "중립"]
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


    print(result)
    result = '\n'.join(result.strip().splitlines()[1:-1])   # remove extras
    print(result)

    data = json.loads(result)

    # Extract 'options' and 'series' from the dictionary
    options = data["options"]
    series = data["series"]

    # Print the resulting Python objects
    print("options =", options)
    print("series =", series)

    def gen_chart():
        st_apexcharts(options, series, 'donut', '600', '감정 빈도수')

    return gen_chart


def write_rap_lyric(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
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
