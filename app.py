import streamlit as st
import openai
import re
import os
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed
import module

# 로컬에서만 .env 파일에서 API 키 가져오기
# if os.getenv("IS_STREAMLIT_CLOUD") != "true":
#     from dotenv import load_dotenv
#     load_dotenv() 
#     api_key = os.getenv("OPENAI_API_KEY")




def clean_text(text):
    # 정규 표현식을 사용하여 날짜 형식을 남기고 시간 형식 제거
    cleaned_text = re.sub(r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}, ', '', text)
    # 쉼표 뒤에 남아 있는 공백 제거
    cleaned_text = re.sub(r',\s+', ', ', cleaned_text)
    # 중복 공백 제거
    cleaned_text = re.sub(r'\s{2,}', ' ', cleaned_text)
    return cleaned_text


def split_text(text, chunk_size=10000, max_chunks=10):
    # 텍스트를 chunk_size만큼 뒤에서부터 나누기
    length = len(text)
    print("텍스트 길이:"+str(length))
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
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 심리 및 대화 분석 전문가입니다. 첨부된 채팅 내역을 바탕으로 대화 참여자들의 말투, 성격, 추억 등을 분석해 주세요. 
                실제 대화들을 적극적으로 인용해서, 상담 참여자가 분석에 대해서 더 공감할 수 있도록 하세요.
                인용은 실제 대화내역을 그대로 인용. 
                """,
            },
            {
                "role": "user",
                "content": "채팅 내역 : " + kakao_chat,
            },
        ],
    )
    return response.choices[0].message.content

# 최종 결과 통합때만 gpt-4o 사용
def aggregate_responses(combined_responses):
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """
                당신은 심리 및 대화 분석 전문가입니다. 아래는 다른 전문가들이 분석한 내용입니다. 이를 종합해서 하나의 리포트로 작성해주세요. 
                실제 대화 내역이 포함되도록 하세요.
                """,
            },
            {
                "role": "user",
                "content": combined_responses,
            },
            {
                "role": "system",
                "content": """
                각 영역을 ** 등의 기호를 사용해서 구분하지 말고 대괄호와 숫자만을 사용해서 구분하세요.
                """,
            },
        ],
    )
    return response.choices[0].message.content

# Streamlit 인터페이스 구성
st.title('카카오톡 대화 분석 서비스')
st.markdown('''
가장 최근 대화부터 최대 10만자까지의 대화를 분석합니다.  
이를 통해 나와 상대방의 대화 습관, 심리, 추억 등을 알 수 있습니다.
''')

# OpenAI API 키 입력 (환경 변수 또는 수동 입력)
# if not api_key:
#     api_key = st.text_input("OpenAI API Key", type="password")

# 파일 업로드   
uploaded_file = st.file_uploader("카카오톡 채팅 내역 업로드", type="txt")

if uploaded_file is not None:
    # 파일 읽기
    file_content = uploaded_file.read().decode("utf-8")
    
    # 시간 정보 제거
    cleaned_content = clean_text(file_content)
    
    chunks = split_text(cleaned_content)
    #청크 개수 확인
    #print("청크 개수:"+str(len(chunks)))
    
    # GPT-4 API 요청 병렬 처리
    if "responses" not in st.session_state:
        responses = []
        with st.spinner("분석 중..."):
            with ThreadPoolExecutor() as executor:
                future_to_chunk = {executor.submit(gpt_request, chunk): chunk for chunk in chunks}
                for future in as_completed(future_to_chunk):
                    try:
                        response = future.result()
                        responses.append(response)
                    except Exception as exc:
                        st.error(f"Chunk 처리 중 오류 발생: {exc}")

        # 응답 통합
        combined_responses = "\n\n".join(responses)
        with st.spinner("리포트 생성중 ..."):
            final_result = aggregate_responses(combined_responses)
    
        # 결과 저장
        st.session_state.responses = responses
        st.session_state.combined_responses = combined_responses
        st.session_state.final_result = final_result
    else:
        responses = st.session_state.responses
        combined_responses = st.session_state.combined_responses
        final_result = st.session_state.final_result

    # 결과 출력
    st.text_area("최종 결과", final_result, height=400)

    
    # 세션 상태 초기화
    if 'clicked_buttons' not in st.session_state:
        st.session_state.clicked_buttons = []
    if 'results' not in st.session_state:
        st.session_state.results = []

    def handle_button_click(button_name, process_function, prompt):
        with st.spinner(f"{button_name} 진행중..."):
            additional_result = process_function(prompt)
        st.session_state.clicked_buttons.append(button_name)
        st.session_state.results.append((button_name, additional_result))
        st.experimental_rerun()  # 버튼 클릭 시 새로고침

    # 추가 분석
    st.markdown('''
    ### 추가 분석 옵션
    아래 버튼 중 하나를 클릭하여 추가 분석을 요청할 수 있습니다:
    ''')

    available_buttons = [
        ('전생에 둘은 무슨 관계였을까?', module.analyze_past_life),
        ('시 작성', module.write_poem),
        ('기념일 생성', module.create_anniversary)
    ]

    # 클릭된 버튼에 해당하는 결과 출력
    for button_name, result in st.session_state.results:
        st.text_area(button_name, result, height=400)

    # 클릭되지 않은 버튼 표시
    for button_name, process_function in available_buttons:
        if button_name not in st.session_state.clicked_buttons:
            if st.button(button_name):
                handle_button_click(button_name, process_function, combined_responses if button_name != '기념일 생성' else "\n\n".join(chunks))