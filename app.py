import streamlit as st
import openai
from datetime import datetime

# --- 0. 앱 기본 설정 (가장 상단에 위치) ---
st.set_page_config(layout="wide", page_title="할 말은 해야지")

# --- 1. 커스텀 CSS 주입 (디자인 업그레이드) ---
st.markdown("""
<style>
/* 메인 배경 및 폰트 설정 */
.main .block-container {
    max-width: 1100px;
    padding-top: 3rem;
}

/* 제목 스타일 */
h1 {
    color: #FF4B4B;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    font-size: 2.8em !important;
    border-bottom: 2px solid #FF4B4B;
    padding-bottom: 15px;
    margin-bottom: 30px;
}

/* 입력창 스타일 커스텀 */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    background-color: #1e1e1e !important;
    color: white !important;
    border: 1px solid #444 !important;
    border-radius: 10px !important;
}

.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border-color: #FF4B4B !important;
    box-shadow: 0 0 10px rgba(255, 75, 75, 0.2) !important;
}

/* 버튼 스타일 */
.stButton>button {
    width: 100%;
    background-color: #FF4B4B !important;
    color: white !important;
    border: none !important;
    padding: 15px !important;
    font-weight: bold !important;
    border-radius: 12px !important;
    transition: 0.3s !important;
}

.stButton>button:hover {
    background-color: #ff3333 !important;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(255, 75, 75, 0.4);
}

/* 탭 스타일 */
.stTabs [data-baseweb="tab-list"] {
    gap: 10px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    background-color: #262730;
    border-radius: 10px 10px 0 0;
    color: #888;
    padding: 0 20px;
}

.stTabs [aria-selected="true"] {
    background-color: #FF4B4B !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# --- 2. 상태 관리 및 자동 API 설정 ---
if 'history' not in st.session_state:
    st.session_state.history = []

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정 및 기록")
    
    # [중요] Secrets에 등록된 키가 있으면 자동 사용, 없으면 입력받음
    if "OPENAI_API_KEY" in st.secrets:
        st.session_state.api_key = st.secrets["OPENAI_API_KEY"]
        st.success("✅ 시스템 API 키가 연결되었습니다.")
    else:
        st.session_state.api_key = st.text_input("🔑 OpenAI API Key 입력", type="password")
        st.info("관리자 키가 없으면 개인 키를 입력해야 합니다.")

    st.markdown("---")
    st.subheader("📚 최근 기록")
    for item in reversed(st.session_state.history[-5:]):  # 최근 5개만
        with st.expander(f"[{item['time']}] {item['tone']}"):
            st.write(f"**To:** {item['target']}")
            st.caption(item['result'])

# API 클라이언트 초기화
if not st.session_state.api_key:
    st.warning("⚠️ 사이드바에서 API 키를 설정하거나 Secrets에 등록해 주세요.")
    st.stop()

client = openai.OpenAI(api_key=st.session_state.api_key)

# --- 3. 메인 화면 구성 (Tabs 사용) ---
st.title("할 말은 하고 살자")

tab1, tab2 = st.tabs(["📝 메시지 작성", "✨ 변환 결과"])

with tab1:
    with st.form(key='input_form'):
        col1, col2 = st.columns(2)
        with col1:
            tone = st.selectbox("원하는 어투", ["정중하고 예의바르게", "친근하고 캐주얼하게", "격식 있는 비즈니스체", "재치 있는 유머체"])
        with col2:
            strength = st.slider("어투 강도 (1~5)", 1, 5, 3)
            
        col3, col4 = st.columns(2)
        with col3:
            target = st.text_input("받는 사람", placeholder="예: 팀장님, 여자친구, 거래처 담당자")
        with col4:
            situation = st.text_input("상황", placeholder="예: 휴가 신청, 약속 늦음, 거절할 때")
            
        content = st.text_area("변환할 원문 내용", height=150, placeholder="예: 나 내일 아파서 못가")
        must_include = st.text_input("꼭 포함되어야 할 단어 (선택)", placeholder="예: 죄송합니다, 다음 주에 봐요")
        
        submit = st.form_submit_button("🚀 예쁘게 변환하기")

# --- 4. 변환 로직 ---
if submit:
    if not content:
        st.error("내용을 입력해 주세요!")
    else:
        with st.spinner("AI가 가장 적절한 표현을 찾는 중..."):
            try:
                prompt = f"""
                당신은 커뮤니케이션 전문가입니다. 아래 조건에 맞춰 원문을 변환하세요.
                - 대상: {target}
                - 상황: {situation}
                - 어투: {tone} (강도: {strength}/5)
                - 필수 포함 단어: {must_include}
                - 원문: {content}
                
                불필요한 설명 없이 오직 변환된 메시지 내용만 출력하세요.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                result = response.choices[0].message.content
                
                # 결과 저장 및 탭 이동 시뮬레이션
                st.session_state.last_result = result
                st.session_state.history.append({
                    "time": datetime.now().strftime("%H:%M"),
                    "tone": tone,
                    "target": target,
                    "result": result
                })
                
                # 결과 탭에 출력
                with tab2:
                    st.success("완료되었습니다!")
                    st.text_area("최종 메시지 (복사해서 사용하세요)", value=result, height=250)
                    st.balloons()
            except Exception as e:
                st.error(f"오류 발생: {e}")

with tab2:
    if 'last_result' not in st.session_state:
        st.info("변환 버튼을 누르면 이곳에 결과가 나타납니다.")
    else:
        st.text_area("최종 메시지 (복사해서 사용하세요)", value=st.session_state.last_result, height=250, key="result_display")
