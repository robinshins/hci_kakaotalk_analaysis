import json
from streamlit_apexjs import st_apexcharts
import openai
from openai import OpenAI


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
