import openai
from openai import OpenAI


def analyze_past_life(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 전생 분석 전문가입니다. 첨부된 채팅 내용 분석 내역을 바탕으로 두 사람이 전생에 어떤 관계였을지 추측하고 이를 재밌는 이야기로 작성해주세요.
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
                당신은 기념일 작가입니다. 첨부된 채팅 내역을 바탕으로 두 사람에게 의미 있는 기념일을 만들어주세요.
                기념일의 날짜, 이유, 이를 위한 이벤트, 그날 나눴던 대화 등을 포함해주세요.
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 : " + kakao_chat,
            },
        ],
    )
    return response.choices[0].message.content
