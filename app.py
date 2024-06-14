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

# Mainpage UI
st.title('카카오톡 대화 분석 서비스')
st.markdown('''
가장 최근 대화부터 최대 10만자까지의 대화를 분석합니다.  
이를 통해 나와 상대방의 대화 습관, 심리, 추억 등을 알 수 있습니다.  
''')
custom_css = """
    <style>
        #custom-text {
            background-color: #DFF0D8;
            color: #3C763D;
            font-size: 14px;
            padding-top: 10px;
            padding-bottom: 10px;
            padding-left: 14px;
            padding-right: 20px;
            border-radius: 5px;
            margin-top: -20px;
            margin-bottom: 30px;
        }
    </style>
"""
st.markdown(custom_css, unsafe_allow_html=True)
st.markdown('<p id="custom-text">이 서비스는 카톡 내용을 저장하지 않으니 안심하세요! GPT에게 분석을 요청할 때도 개인정보는 암호화됩니다.</p>', unsafe_allow_html=True)



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

# File Uploader
st.session_state.uploaded_file = st.file_uploader("카카오톡 채팅 내역 업로드", type="txt")
if st.session_state.uploaded_file is not None and st.session_state.file_uploaded is False:
    st.session_state.file_uploaded = True
    handle_button_click("기본 분석", "카카오톡 대화를 입력해주세요. \n 말투, 성격, 추억 등을 먼저 종합적으로 분석해드립니다.", process_file, st.session_state.uploaded_file)

custom_css = """
    <style>
        .custom-margin {
            margin-bottom: 20px;
        }
    </style>
"""

st.markdown(custom_css, unsafe_allow_html=True)
if st.session_state.uploaded_file:
    st.markdown('<div class="custom-margin">' + st.session_state.uploaded_file + '</div>', unsafe_allow_html=True)



available_buttons = [
    ('기본 분석', "카카오톡 대화를 분석하여 관계 리포트를 뽑아드려요", process_file, False),
    ('감정 단어 분석하기', "둘 사이에 어떤 감정 단어가 가장 많이 오고 갔을까요?", module.emotion_donut, False),
    ('월별 추억 돌아보기', "현생에 치여 잊고 살아왔던 둘만의 추억을 돌아봐요", module.monthly_event, False),
    ('전생 관계 분석', "우린 전생에 어떤 사이길래 이렇게 다시 만났을까요?", module.analyze_past_life, False),
    ('랩 가사 작성', "신나는 비트에서 느껴지는 우리의 힙한 관계!", module.write_rap_lyric, True),
    ('기념일 생성', "선배 기념일 만들어주세요! 혹시.. 우리 추억도 같이??", module.create_anniversary, False),
]

# 버튼 UI 구성 및 클릭 처리
cols = st.columns(3)
for idx, (button_name, explanation, process_function, use_response) in enumerate(available_buttons):
    is_clicked = button_name in st.session_state.clicked_buttons
    background_color = "#d3d3d3" if button_name in st.session_state.clicked_buttons else "#f0f0f0"
    button_style = f"background-color: {background_color}; height: 200px; width: 100%; font-size: 20px; border: none text-align: center; white-space: normal;"
    button_label = button_name if button_name not in st.session_state.clicked_buttons else f"{button_name} (완료)"
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

st.markdown("""
    <style>
    div.stButton > button {
        height: 200px;
        width: 100%;
        font-size: 20px;
        font-weight: bold;

    }
    div[data-testid=stSpinner] {
        display: flex;
        align-items: center;
        justify-content: center;
    }
        div[data-testid=stToast] {
        padding: 0 auto;
        margin: 0 auto;
        color: white;
        background: #ff4b4b;
        width: 20%;
        min-width:400px;
    }
    </style>
    """, unsafe_allow_html=True)

