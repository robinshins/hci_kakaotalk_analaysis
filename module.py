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
