import streamlit as st
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import module
# import dummy_module as module
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
if 'selected_button' not in st.session_state:
    st.session_state.selected_button = None
if 'results' not in st.session_state:
    st.session_state.results = {}
if 'modal_clicked' not in st.session_state:
    st.session_state.modal_clicked = False
if 'cleaned_content' not in st.session_state:
    st.session_state.cleaned_content = None
if 'combined_chunks' not in st.session_state:
    st.session_state.combined_chunks = ""
if 'combined_responses' not in st.session_state:
    st.session_state.combined_responses = ""
if 'final_result' not in st.session_state:
    st.session_state.final_result = ""
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False
if 'is_loading' not in st.session_state:
    st.session_state.is_loading = False
if 'uploaded_file' not in st.session_state:
    st.session_state.uploaded_file = None
if 'wordcloud_img' not in st.session_state:
    st.session_state.wordcloud_img = None

#img_data = None
def create_wordcloud():
    # 파일 읽기
    file_content = st.session_state.uploaded_file.read().decode("utf-8")
    
    # 시간 정보 제거
    try:
        cleaned_content = module.group_chat_dialogs(file_content)
    except Exception:
        cleaned_content = file_content

    chunks = module.split_text(cleaned_content)
    st.session_state.cleaned_content = cleaned_content
    st.session_state.combined_chunks = "\n\n".join(chunks)

    words = module.preprocess_text_for_wordcloud(cleaned_content)
    word_frequencies = module.get_word_frequencies(words)

    module.generate_wordcloud(word_frequencies)
    
    # 워드클라우드를 이미지로 변환
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    img_data = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()

    st.session_state.wordcloud_img = img_data

def basic_analyze(combined_responses):
    # GPT-4 API 요청 병렬 처리
    responses = []
    with ThreadPoolExecutor() as executor:
        chunks = module.split_text(st.session_state.cleaned_content)
        future_to_chunk = {executor.submit(module.gpt_request, chunk): chunk for chunk in chunks}
        for future in as_completed(future_to_chunk):
            try:
                response = future.result()
                responses.append(response)
            except Exception as exc:
                st.error(f"Chunk 처리 중 오류 발생: {exc}")

    # 응답 통합
    st.session_state.combined_responses = "\n\n".join(responses)

    final_result = module.aggregate_responses(st.session_state.combined_responses)
    st.session_state.final_result = final_result
    print("basic analyze done")
    return final_result


# 모달 함수 정의
@st.experimental_dialog("Title" if st.session_state.selected_button is None else st.session_state.selected_button[0], width="large")
def show_modal():

    (button_name, explanation, process_function, source)  = st.session_state.selected_button

    modal_content = "Content"

    if st.session_state.wordcloud_img is None:
        with st.spinner(f'워드클라우드를 생성중입니다!'):
            create_wordcloud()


    if button_name in st.session_state.clicked_buttons:
        # 이미 실행한 결과가 있으면 그 결과를 모달에 표시
        modal_content = st.session_state.results[button_name][1]
        st.session_state.is_loading = False
    else:
        st.session_state.is_loading = True
        with st.spinner(f'{button_name} 진행중입니다. 조금만 기다려주세요!'):
            st.image(f"data:image/png;base64,{st.session_state.wordcloud_img}", use_column_width=True)
            result = process_function(source)
            st.session_state.results[button_name]=(explanation, result)
            st.session_state.clicked_buttons.append(button_name)
            modal_content = result
            st.rerun()

    if callable(modal_content):  # additional_result가 함수인지 확인
        modal_content()
    else:
        st.write(f"{modal_content}")







def handle_button_click(button):
    st.session_state.selected_button = button
    # if not st.session_state.is_loading:
    #     st.session_state.modal_clicked = True

# 버튼들 정의
available_buttons = [
    ('기본 분석', "카카오톡 대화를 입력해주세요. \n 말투, 성격, 추억 등을 먼저 종합적으로 분석해드립니다.", basic_analyze, st.session_state.combined_responses),
    ('전생 관계 분석', "전생에 어떤 관계였을지 소설 형태로 작성해줍니다. \n 과연 전생에 어떤 인연이 있었길래 이렇게 또 만났을까요?", module.analyze_past_life, st.session_state.combined_responses),
    # ('시 작성', "우리의 관계로 작성해보는 시 \n 로맨틱한 시일까요 슬픈 시일까요?", module.write_poem, True),
    ('랩 가사 작성', "신나는 박자감과 느껴보는 우리의 힙한 관계", module.write_rap_lyric, st.session_state.final_result),
    ('기념일 생성', "모든 사람들이 챙기는 기념일 말고!! \n 우리만의 특별한 기념일을 만들어보세요", module.create_anniversary, st.session_state.combined_responses),
    ('월별 추억 돌아보기', "현생에 치여 살던 우리 \n 잊고 있던 과거의 추억들을 한번 살펴봐요", module.monthly_event, st.session_state.combined_responses),
    ('감정 단어 분석하기', "너는 너무 부정적이야. 데이터로 보여줄테니 반성해 \n 라고 외치고 싶을 때", module.emotion_donut, st.session_state.combined_responses),
]

# 파일 업로드   
st.session_state.uploaded_file = st.file_uploader("카카오톡 채팅 내역 업로드", type="txt")
if st.session_state.uploaded_file is not None and st.session_state.file_uploaded is False:
    st.session_state.file_uploaded = True
    handle_button_click(available_buttons[0])
    st.session_state.modal_clicked=True

elif st.session_state.uploaded_file is None:
    st.session_state.file_uploaded = False




# 버튼 UI 구성 및 클릭 처리
cols = st.columns(3)
for idx, button in enumerate(available_buttons):
    (button_name, explanation, process_function, use_response) = button
    is_clicked = button_name in st.session_state.clicked_buttons
    background_color = "#d3d3d3" if is_clicked else "#f0f0f0"
    button_style = f"background-color: {background_color}; height: 200px; width: 100%; font-size: 20px; border: none;"
    button_label = button_name if not is_clicked else f"{button_name}(완료)"
    button_explanation = explanation if not is_clicked else "클릭해서 결과를 확인하세요"

    with cols[idx % 3]:
        def on_click_clicked():
            print("trying : "+button_name)
            

        if st.button(f"### {button_label}\n {button_explanation}"):
            if st.session_state.file_uploaded :
                handle_button_click(button)
            else:
                st.toast("카카오톡 대화를 먼저 입력하세요")


st.markdown("""
    <style>
    .centered-button {
        display: flex;
        justify-content: center;
        align-items: center;
        position: fixed;
        bottom: 20px;
        width: 100%;
    }
    .centered-button a {
        background-color: #794BDB;
        color: white;
        padding: 14px 25px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        border-radius: 15px 15px 0px 15px;
    }
    .centered-button a:hover {
        background-color: #6C43C4;
    }
    </style>
    <div class="centered-button">
        <a href="https://forms.gle/ysV2jzyU352BcmDx5" target="_blank">사용 후기 남기기 🥰</a>
    </div>
""", unsafe_allow_html=True)

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
        color: white;
        background: #ff4b4b;
        width: 20%;
        min-width:400px;
    }
    </style>
    """, unsafe_allow_html=True)

if st.session_state.modal_clicked:
    show_modal()