import streamlit as st
import openai
from datetime import datetime

# --- 1. 앱 초기 설정 및 상태 관리 ---

# 세션 상태(Session State) 초기화: 앱을 껐다가 켜기 전까지 데이터를 유지합니다.
if 'history' not in st.session_state:
    st.session_state.history = []

if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

st.set_page_config(layout="wide", page_title="AI 말투 변환 비서")
st.title("🗣️ AI 말투 변환 및 비서 툴 (Ver 2.0)")

# --- 2. 사이드바 (API Key 및 기록) ---

with st.sidebar:
    st.header("설정 및 기록")
    
    # API Key 입력
    st.session_state.api_key = st.text_input(
        "🔑 OpenAI API Key를 입력하세요", 
        type="password", 
        value=st.session_state.api_key
    )
    
    # API Key 검증 및 클라이언트 초기화
    if st.session_state.api_key:
        try:
            openai.api_key = st.session_state.api_key
            st.success("API 키 입력 완료!")
        except Exception:
            st.error("API 키 형식이 올바르지 않습니다.")
            st.stop()
    else:
        st.info("API Key가 없으면 AI가 작동하지 않습니다.")
        st.stop()

    st.markdown("---")
    st.subheader("최근 변환 기록")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history)):
            st.caption(f"{i+1}. [{item['time']}] {item['tone']} 변환")
            st.markdown(f"**대상:** {item['target']}")
            st.text_area("변환 결과", item['result'], height=100, key=f"hist_{i}")
    else:
        st.caption("아직 기록된 변환이 없습니다.")

# --- 3. 입력 폼 (st.form을 사용하여 '다시 시도' 및 상태 관리) ---

with st.form(key='tone_converter_form'):
    
    st.subheader("1. 변환 옵션 설정")
    col_opt1, col_opt2 = st.columns([2, 1])
    
    with col_opt1:
        # 어투 선택 드롭다운 메뉴
        tone = st.selectbox(
            "📝 변환할 어투를 선택하세요",
            ("존중하고 예의 바르게 (정중체)", "친근하고 캐주얼하게 (평어체)", "비즈니스 공식 메일처럼 (업무체)", "센스 있고 위트있게")
        )
    with col_opt2:
        # 어투 강도 조절 슬라이더
        strength = st.slider(
            "💪 어투 강도 조절 (1:약함 ~ 5:강함)", 
            min_value=1, 
            max_value=5, 
            value=3, 
            step=1
        )

    st.subheader("2. 대화 상황 입력")
    col1, col2 = st.columns(2)
    with col1:
        target = st.text_input("✅ 전달할 사람")
    with col2:
        situation = st.text_input("✅ 상황")

    st.subheader("3. 변환할 내용")
    content = st.text_area(
        "✅ 하고 싶은 말을 편하게 적어주세요 (AI가 이 내용을 변환합니다.)",
        placeholder="몸아파서 그만둔다",
        height=150
    )
    
    must_include_phrases = st.text_input("✨ 필수로 들어갈 말/키워드 (예: 감사했습니다, 3월 10일)", key='keywords')

    uploaded_file = st.file_uploader(
        "🖼️ (선택사항) 대화 캡쳐 사진을 올려주세요. (현재는 텍스트만 처리합니다.)",
        type=['png', 'jpg', 'jpeg']
    )
    
    if uploaded_file is not None:
        st.warning("⚠️ 이미지 인식 기능은 GPT-4o 등 고성능 모델이 필요합니다. 현재는 텍스트 변환만 진행합니다.")

    # 버튼: st.form_submit_button은 '예쁘게 변환하기'와 '다시 시도' 기능을 모두 수행합니다.
    submit_button = st.form_submit_button(label='🚀 예쁘게 변환하기 / 다시 시도')


# --- 4. AI 변환 로직 실행 (버튼 클릭 시) ---
if submit_button:
    
    if not all([target, situation, content]):
        st.error("필수 입력 항목을 모두 채워주세요.")
        st.stop()
    
    # 프롬프트(지시사항) 만들기: 모든 변수를 포함
    prompt = f"""
    당신은 말투 변환 전문가입니다. 주어진 '원문'의 내용을 '상황'과 '대상'에 맞춰서 다음 어투로 수정하세요.
    수정 시, '필수 키워드'를 반드시 포함하고, 어투 강도({strength}/5)를 최대한 반영해야 합니다.
    
    --- 입력 정보 ---
    어투: {tone}
    강도: {strength}
    상황: {situation}
    대상: {target}
    원문: {content}
    필수 키워드: {must_include_phrases if must_include_phrases else "없음"}
    
    --- 출력 규칙 ---
    1. 설명 없이, 수정된 메시지 내용만 바로 출력합니다.
    """
    
    try:
        client = openai.OpenAI(api_key=st.session_state.api_key)
        
        with st.spinner("AI가 머리를 굴리며 최적의 메시지를 작성 중입니다..."):
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "당신은 사용자 의도를 완벽히 파악하여 문장을 가장 적절한 어투로 변환해주는 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7 
            )
        
        # 5. 결과 출력 및 복사 기능
        translated_text = response.choices[0].message.content
        st.success("🎉 변환 완료! 아래 메시지를 복사하여 사용하세요.")
        
        st.text_area(
            "최종 변환 메시지", 
            translated_text, 
            height=250, 
            key='final_output'
        )

        # 6. 기록 저장 (Session State)
        st.session_state.history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "target": target,
            "tone": tone,
            "result": translated_text
        })
        
        # 기록 저장 후 사이드바를 다시 그리도록 페이지를 새로고침 (Streamlit의 일반적인 패턴)
        st.experimental_rerun()


    except openai.AuthenticationError:
        st.error("❌ API 키 오류: OpenAI API Key가 올바르지 않거나 만료되었습니다. 사이드바를 확인해 주세요.")
    except Exception as e:
        # 429 에러 등 기타 오류 처리
        error_msg = str(e)
        if "insufficient_quota" in error_msg:
             st.error("❌ 할당량 부족 오류: OpenAI 크레딧이 부족합니다. 결제 정보를 확인해 주세요.")
        else:
             st.error(f"❌ AI 요청 중 오류가 발생했습니다: {e}")