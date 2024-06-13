import streamlit as st
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import module
import matplotlib.pyplot as plt
import io
import base64

# 로컬에서만 .env 파일에서 API 키 가져오기
if os.getenv("IS_STREAMLIT_CLOUD") != "true":
    from dotenv import load_dotenv
    load_dotenv() 
    api_key = os.getenv("OPENAI_API_KEY")

# Streamlit 인터페이스 구성
st.title('카카오톡 대화 분석 서비스')
st.markdown('''
가장 최근 대화부터 최대 10만자까지의 대화를 분석합니다.  
이를 통해 나와 상대방의 대화 습관, 심리, 추억 등을 알 수 있습니다.  
카카오톡 내역은 따로 보관하지 않으며, OpenAI사의 GPT에게만 제공됩니다.
''')

# 세션 상태 초기화
if 'clicked_buttons' not in st.session_state:
    st.session_state.clicked_buttons = []
if 'results' not in st.session_state:
    st.session_state.results = []
if 'modal_title' not in st.session_state:
    st.session_state.modal_title = "기본 분석 결과"
if 'modal_content' not in st.session_state:
    st.session_state.modal_content = ""
if 'modal_clicked' not in st.session_state:
    st.session_state.modal_clicked = False
if 'cleaned_content' not in st.session_state:
    st.session_state.cleaned_content = None
if 'combined_chunks' not in st.session_state:
    st.session_state.combined_chunks = ""
if 'combined_responses' not in st.session_state:
    st.session_state.combined_responses = ""
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = True
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
#img_data = None
# 모달 함수 정의
@st.experimental_dialog(st.session_state.modal_title, width="large")
def show_modal():
    if st.session_state.is_loading:
        with st.spinner(text='대화 내용 분석 진행중입니다. 워드클라우드를 확인하며 조금만 기다려주세요!'):
                # 파일 읽기
            file_content = st.session_state.uploaded_file.read().decode("utf-8")
            
            # 시간 정보 제거
            try:
                cleaned_content = module.group_chat_dialogs(file_content)
            except Exception:
                cleaned_content = file_content

            st.session_state.cleaned_content = cleaned_content

            if st.session_state.cleaned_content is not None:
                chunks = module.split_text(st.session_state.cleaned_content)
                st.session_state.combined_chunks = "\n\n".join(chunks)

                words = module.preprocess_text_for_wordcloud(st.session_state.cleaned_content)
                word_frequencies = module.get_word_frequencies(words)

                module.generate_wordcloud(word_frequencies)
                
                # 워드클라우드를 이미지로 변환
                buf = io.BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                img_data = base64.b64encode(buf.read()).decode('utf-8')
                buf.close()

                st.image(f"data:image/png;base64,{img_data}", use_column_width=True)

                # GPT-4 API 요청 병렬 처리
                responses = []
                with ThreadPoolExecutor() as executor:
                    future_to_chunk = {executor.submit(module.gpt_request, chunk): chunk for chunk in chunks}
                    for future in as_completed(future_to_chunk):
                        try:
                            response = future.result()
                            responses.append(response)
                        except Exception as exc:
                            st.error(f"Chunk 처리 중 오류 발생: {exc}")

                # 응답 통합
                st.session_state.combined_responses = "\n\n".join(responses)
                st.session_state.final_result = module.aggregate_responses(st.session_state.combined_responses)
                st.session_state.results.append(("기본 분석","기본 분석입니다.",st.session_state.final_result + f"![워드클라우드](data:image/png;base64,{img_data})"))
                st.session_state.clicked_buttons.append("기본 분석")
                st.session_state.is_loading = False

                # 모달 내용 업데이트
                update_modal_content(f"{st.session_state.results[0][2]}")

    if callable(st.session_state.modal_content):  # additional_result가 함수인지 확인
        st.session_state.modal_content()
    else:
        st.write(f"{st.session_state.modal_content}")
    st.session_state.modal_clicked = False



if st.session_state.modal_clicked:
    show_modal()

def update_modal_content(content):
    st.session_state.modal_content += content
    st.session_state.modal_clicked = True
    st.rerun()

# 파일 처리 함수
def process_file(uploaded_file):
        show_modal()

def handle_button_click(button_name, explanation, process_function, prompt):
    if button_name == "기본 분석" and st.session_state.file_uploaded:
        process_function(prompt)
    if not prompt:
        st.toast("카카오톡 대화를 먼저 입력하세요")
        return
    if button_name in st.session_state.clicked_buttons:
        # 이미 실행한 결과가 있으면 그 결과를 모달에 표시
        result_index = st.session_state.clicked_buttons.index(button_name)
        st.session_state.modal_content = st.session_state.results[result_index][2]
        st.session_state.modal_title = button_name
        st.session_state.modal_clicked = True
    else:
        additional_result = process_function(prompt)
        st.session_state.clicked_buttons.append(button_name)
        st.session_state.results.append((button_name, explanation, additional_result))
        st.session_state.modal_title = button_name
        st.session_state.modal_content = additional_result
        st.session_state.modal_clicked = True
    st.rerun()

# 파일 업로드   
st.session_state.uploaded_file = st.file_uploader("카카오톡 채팅 내역 업로드", type="txt")
if st.session_state.uploaded_file is not None and st.session_state.file_uploaded is False:
    st.session_state.file_uploaded = True
    handle_button_click("기본 분석", "카카오톡 대화를 입력해주세요. \n 말투, 성격, 추억 등을 먼저 종합적으로 분석해드립니다.", process_file, st.session_state.uploaded_file)


# 버튼들 정의
available_buttons = [
    ('기본 분석', "카카오톡 대화를 입력해주세요. \n 말투, 성격, 추억 등을 먼저 종합적으로 분석해드립니다.", process_file, False),
    ('전생 관계 분석', "전생에 어떤 관계였을지 소설 형태로 작성해줍니다. \n 과연 전생에 어떤 인연이 있었길래 이렇게 또 만났을까요?", module.analyze_past_life, False),
    ('시 작성', "우리의 관계로 작성해보는 시 \n 로맨틱한 시일까요 슬픈 시일까요?", module.write_poem, True),
    ('랩 가사 작성', "신나는 박자감과 느껴보는 우리의 힙한 관계", module.write_rap_lyric, True),
    ('기념일 생성', "모든 사람들이 챙기는 기념일 말고!! \n 우리만의 특별한 기념일을 만들어보세요", module.create_anniversary, False),
    ('월별 추억 돌아보기', "현생에 치여 살던 우리 \n 잊고 있던 과거의 추억들을 한번 살펴봐요", module.monthly_event, False),
    ('감정 단어 분석하기', "너는 너무 부정적이야. 데이터로 보여줄테니 반성해 \n 라고 외치고 싶을 때", module.emotion_donut, False),
]

# 버튼 UI 구성 및 클릭 처리
cols = st.columns(3)
for idx, (button_name, explanation, process_function, use_response) in enumerate(available_buttons):
    is_clicked = button_name in st.session_state.clicked_buttons
    background_color = "#d3d3d3" if button_name in st.session_state.clicked_buttons else "#f0f0f0"
    button_style = f"background-color: {background_color}; height: 200px; width: 100%; font-size: 20px; border: none;"
    button_label = button_name if button_name not in st.session_state.clicked_buttons else f"{button_name}(완료)"
    button_explanation = explanation if button_name not in st.session_state.clicked_buttons else "클릭해서 결과를 확인하세요"

    with cols[idx % 3]:
        if st.button(f"### {button_label}\n {button_explanation}"):
            if button_name in st.session_state.clicked_buttons:
                result_index = st.session_state.clicked_buttons.index(button_name)
                st.session_state.modal_content = st.session_state.results[result_index][2]
                st.session_state.modal_title = button_name
                st.session_state.modal_clicked = True
                st.rerun()
            else:
                with st.spinner(f"{button_name} 진행중..."):
                    if use_response:
                        handle_button_click(button_name, explanation, process_function, st.session_state.combined_responses)
                    else:
                        handle_button_click(button_name, explanation, process_function, st.session_state.combined_chunks)


# CSS 스타일로 버튼 크기 조정
st.markdown("""
    <style>
    div.stButton > button {
        height: 200px;
        width: 100%;
        font-size: 20px;
    }
    div[data-testid=stSpinner] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    div[data-testid=stToast] {
        padding: 0 auto;
        margin: 0 auto;
        background-color: #0D33B3;
        width: 20%;
    }
    </style>
    """, unsafe_allow_html=True)
