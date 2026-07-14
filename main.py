import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as qs
from plotly.subplots import make_subplots
import google.generativeai as genai
import os

# 1. 페이지 기본 설정 및 디자인 테마 적용
st.set_page_config(
    layout="wide",
    page_title="Performance Dashboard for Senior AE",
    page_icon="📊"
)

# 프리미엄 UI 스타일링을 위한 Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 폰트 및 기본 스크롤바 디자인 */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    /* 사이드바 스타일 정의 (가독성 높은 폰트 대비) */
    section[data-testid="stSidebar"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #38BDF8 !important;
    }
    
    /* KPI 카드 커스텀 디자인 (가독성 높은 대비) */
    .kpi-container {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .kpi-card {
        background-color: #1E293B;
        border: 1px solid #475569;
        border-radius: 12px;
        padding: 20px;
        flex: 1 1 calc(25% - 15px);
        min-width: 220px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        transition: transform 0.2s, border-color 0.2s, background-color 0.2s;
    }
    
    .kpi-card:hover {
        transform: translateY(-2px);
        border-color: #38BDF8;
        background-color: #0F172A;
    }
    
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 700;
        color: #CBD5E1; /* 더 밝은 색으로 가독성 향상 */
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: #FFFFFF; /* 완전한 흰색으로 수치 가독성 극대화 */
        margin-bottom: 4px;
    }
    
    .kpi-sub {
        font-size: 0.75rem;
        color: #38BDF8; /* 밝은 스카이블루 */
        font-weight: 600;
    }
    
    /* 메인 타이틀 장식 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(to right, #38BDF8, #818CF8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 1rem;
        color: #94A3B8; /* 조금 더 밝은 회색으로 서브타이틀 가독성 보완 */
        margin-bottom: 25px;
    }
</style>
""", unsafe_allow_html=True)

# 2. 데이터 로딩 및 캐싱 (에러 가드레일 포함)
@st.cache_data
def load_data():
    file_path = 'raw_data.tsv'
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"'{file_path}' 파일을 찾을 수 없습니다. 경로를 확인해 주세요.")
    
    # UTF-16 인코딩으로 데이터 로드
    df = pd.read_csv(file_path, sep='\t', encoding='utf-16')
    
    # 날짜 컬럼 변환
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # SA/DA 컬럼 내 '-'를 '미분류(기타)'로 처리
    df['SA/DA'] = df['SA/DA'].replace('-', '미분류(기타)')
    
    # 추가 지표 계산 (Derived Metrics)
    df['CTR'] = (df['클릭수'] / df['노출수'] * 100).fillna(0).replace([float('inf'), float('-inf')], 0)
    df['CPC'] = (df['광고비용'] / df['클릭수']).fillna(0).replace([float('inf'), float('-inf')], 0)
    df['CPA'] = (df['광고비용'] / df['전환수']).fillna(0).replace([float('inf'), float('-inf')], 0)
    df['ROAS'] = (df['전환값'] / df['광고비용'] * 100).fillna(0).replace([float('inf'), float('-inf')], 0)
    
    return df

# 2-1. AI 상세 분석용 Gemini API 연동 함수 (에러 가드레일 및 순차적 모델 폴백 복구 루프 포함)
def get_gemini_analysis(api_key, data_md, section_name):
    if not api_key:
        st.warning("먼저 좌측 사이드바에 Gemini API Key를 입력해주세요.")
        return None
    
    with st.spinner("AI가 데이터를 분석 중입니다..."):
        try:
            genai.configure(api_key=api_key, transport='rest')
            
            # API 키에 종속된 가용 생성 모델 목록을 실시간으로 가져옵니다
            try:
                available_models = [
                    m.name for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods 
                    and 'gemma' not in m.name
                ]
            except Exception:
                available_models = []
            
            preferred_models = [
                "models/gemini-2.5-flash-lite",
                "models/gemini-2.5-flash",
                "models/gemini-1.5-flash",
                "models/gemini-1.5-flash-latest",
                "models/gemini-1.5-pro",
                "models/gemini-pro",
                "models/gemini-1.0-pro"
            ]
            
            # 시도할 후보 모델 목록 빌드
            candidate_models = []
            for pm in preferred_models:
                if pm in available_models:
                    candidate_models.append(pm)
            for am in available_models:
                if am not in candidate_models:
                    candidate_models.append(am)
            
            # 가용 모델 조회가 실패했거나 비어있는 경우, 하드코딩 후보군을 뒤에 추가
            fallback_hardcoded = [
                "models/gemini-1.5-flash-latest",
                "models/gemini-pro",
                "models/gemini-1.5-flash",
                "models/gemini-1.0-pro"
            ]
            for fh in fallback_hardcoded:
                if fh not in candidate_models:
                    candidate_models.append(fh)
                    
            prompt = f"""
너는 10년 경력의 시니어 디지털 광고 AE야. 아래 제공된 원본 데이터를 바탕으로 광고비 누수 구간이나 효율 극대화 방안을 날카롭게 분석해줘. 대행사 보고 서식에 맞춰 한글로 핵심 요약 3줄과 액션 플랜 2가지를 명확히 제안해라. 분석 속도를 극대화하기 위해 인사말, 불필요한 수식어, 또는 설명조 서술을 완전히 배제하고, 즉시 각 항목당 1줄 이내의 극도로 짧고 명확한 문장으로만 개조식 제안을 완성해줘.

[분석 대상 섹션]
{section_name}

[데이터 원본 (Markdown)]
{data_md}
"""
            generation_config = {
                "max_output_tokens": 3000,
                "temperature": 0.3
            }
            
            # 가용 후보 모델을 순차적으로 찔러보며 성공하는 모델을 바로 반환
            last_err = None
            for model_name in candidate_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(
                        prompt,
                        generation_config=generation_config,
                        request_options={"timeout": 90.0}
                    )
                    return response.text
                except Exception as err:
                    last_err = err
                    continue
            
            # 전부 실패한 경우 에러를 상위 try-except로 전파
            raise last_err if last_err else Exception("No models available.")
            
        except Exception as e:
            st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
            st.warning("⚠️ API Key의 쿼터(Quota) 한도가 소진되었거나, 사용자의 API Key 환경에서 사용할 수 있는 유효 모델이 없습니다. 구글 AI 스튜디오 설정을 확인해 주세요.")
            return None

# 2-2. AI 챗봇 전용 Gemini API 연동 함수 (에러 가드레일 및 순차적 모델 폴백 복구 루프 포함)
def get_gemini_chat_response(api_key, chat_history, current_question, context_data):
    if not api_key:
        return "⚠️ 사이드바에 Gemini API Key를 먼저 입력해주세요."
        
    try:
        genai.configure(api_key=api_key, transport='rest')
        
        try:
            available_models = [
                m.name for m in genai.list_models()
                if 'generateContent' in m.supported_generation_methods
                and 'gemma' not in m.name
            ]
        except Exception:
            available_models = []
            
        preferred_models = [
            "models/gemini-2.5-flash-lite",
            "models/gemini-2.5-flash",
            "models/gemini-1.5-flash",
            "models/gemini-1.5-flash-latest",
            "models/gemini-1.5-pro",
            "models/gemini-pro",
            "models/gemini-1.0-pro"
        ]
        
        # 시도할 후보 모델 목록 빌드
        candidate_models = []
        for pm in preferred_models:
            if pm in available_models:
                candidate_models.append(pm)
        for am in available_models:
            if am not in candidate_models:
                candidate_models.append(am)
        
        fallback_hardcoded = [
            "models/gemini-1.5-flash-latest",
            "models/gemini-pro",
            "models/gemini-1.5-flash",
            "models/gemini-1.0-pro"
        ]
        for fh in fallback_hardcoded:
            if fh not in candidate_models:
                candidate_models.append(fh)
                
        history_str = ""
        for role, text in chat_history[-6:]:
            role_label = "광고주/AE" if role == "user" else "AI 비서"
            history_str += f"{role_label}: {text}\n"
            
        system_prompt = f"""
너는 10년 경력의 탑티어 디지털 광고 데이터 사이언티스트이자 시니어 AE인 'AI 비서'야.
광고주나 AE가 데이터에 관해 질문했을 때, 아래 제공된 '현재 필터링된 실시간 데이터 요약 정보'를 기반으로 정확하고 날카로운 비즈니스 인사이트를 요약해서 한글로 전문적인 답변을 해줘.
답변은 장황하지 않고 3-4문장 내외로 명확하고 설득력 있게 대답해라.

[현재 필터링된 실시간 데이터 요약 정보]
{context_data}

[이전 대화 내역]
{history_str}

[새로운 질문]
광고주/AE: {current_question}
"""
        generation_config = {
            "max_output_tokens": 3000,
            "temperature": 0.3
        }
        
        # 가용 후보 모델을 순차적으로 찔러보며 성공하는 모델을 바로 반환
        last_err = None
        for model_name in candidate_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    system_prompt,
                    generation_config=generation_config,
                    request_options={"timeout": 90.0}
                )
                return response.text
            except Exception as err:
                last_err = err
                continue
                
        # 전부 실패한 경우 최종 에러 문자열을 반환
        return f"❌ 챗봇 답변 생성 실패: {last_err}. API Key 또는 쿼터 설정을 다시 확인해 주세요."
                
    except Exception as e:
        return f"❌ AI 비서 연결 오류: {e}"

# 데이터 로드 실행
try:
    raw_df = load_data()
except Exception as e:
    st.error(f"❌ 데이터 로드 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 사이드바 - 필터링 컨트롤 구성
st.sidebar.markdown("# 📊 필터 패널 (Filters)")
st.sidebar.markdown("---")

# 날짜 범위 설정
min_date = raw_df['날짜'].min().date()
max_date = raw_df['날짜'].max().date()

st.sidebar.subheader("📅 분석 기간 설정 (Date Range)")
date_range = st.sidebar.date_input(
    "조회 기간",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="시작일과 종료일을 지정하세요."
)

# 매체 선택
st.sidebar.subheader("📺 매체 (Media)")
all_media = sorted(raw_df['매체'].unique())
selected_media = st.sidebar.multiselect(
    "분석할 매체를 선택하세요",
    options=all_media,
    default=all_media
)

# 광고 유형 선택
st.sidebar.subheader("🏷️ 광고 유형 (Type)")
all_types = sorted(raw_df['SA/DA'].unique())
selected_types = st.sidebar.multiselect(
    "광고 유형을 선택하세요",
    options=all_types,
    default=all_types
)

# 1. secrets 에서 가져오기 시도
api_key = st.secrets.get("GEMINI_API_KEY", "")

# 2. secrets에 없거나 비어있는 경우, 사이드바에서 입력받기
st.sidebar.markdown("---")
st.sidebar.subheader("🔑 AI Config")
if api_key:
    st.sidebar.success("🔑 API Key가 st.secrets를 통해 로드되었습니다.")
    override_key = st.sidebar.text_input("Gemini API Key 변경 (st.secrets 재정의)", type="password", help="secrets에 설정된 API Key 대신 다른 키를 사용하려면 입력하세요.")
    if override_key:
        api_key = override_key
else:
    api_key = st.sidebar.text_input("Gemini API Key 입력", type="password", help="Gemini API Key를 입력하거나 .streamlit/secrets.toml 파일에 GEMINI_API_KEY를 등록해 주세요.")
    st.sidebar.caption("💡 API Key는 서버에 저장되지 않고 로컬 브라우저 세션에만 안전하게 유지됩니다.")


# 날짜 범위 입력값 검증 (조회 기간이 온전히 설정되었는지 확인)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    st.warning("⚠️ 날짜 범위의 시작일과 종료일을 모두 선택해 주세요.")
    st.stop()

# 4. 데이터 필터링 실행
filtered_df = raw_df[
    (raw_df['날짜'].dt.date >= start_date) &
    (raw_df['날짜'].dt.date <= end_date) &
    (raw_df['매체'].isin(selected_media)) &
    (raw_df['SA/DA'].isin(selected_types))
]

# 데이터가 비어 있는 경우 가드레일
if filtered_df.empty:
    st.info("ℹ️ 선택한 필터 조건에 부합하는 데이터가 없습니다. 필터를 조정해 주세요.")
    st.stop()

# 5. 메인 타이틀 및 실시간 브리핑 영역
# 필터 변경 감지 및 세션 상태 초기화 (오케스트레이션)
current_filter_key = f"{start_date}_{end_date}_{sorted(selected_media)}_{sorted(selected_types)}"

if 'show_kpi_analysis' not in st.session_state:
    st.session_state['show_kpi_analysis'] = False
if 'show_kpi_ai_analysis' not in st.session_state:
    st.session_state['show_kpi_ai_analysis'] = False
if 'show_trend_analysis' not in st.session_state:
    st.session_state['show_trend_analysis'] = False
if 'show_trend_ai_analysis' not in st.session_state:
    st.session_state['show_trend_ai_analysis'] = False
if 'show_channel_analysis' not in st.session_state:
    st.session_state['show_channel_analysis'] = False
if 'show_channel_ai_analysis' not in st.session_state:
    st.session_state['show_channel_ai_analysis'] = False
if 'last_filter_key' not in st.session_state:
    st.session_state['last_filter_key'] = current_filter_key

# 필터가 변경되면 이전의 분석 코멘트 박스를 모두 리셋(False)
if st.session_state['last_filter_key'] != current_filter_key:
    st.session_state['show_kpi_analysis'] = False
    st.session_state['show_kpi_ai_analysis'] = False
    st.session_state['show_trend_analysis'] = False
    st.session_state['show_trend_ai_analysis'] = False
    st.session_state['show_channel_analysis'] = False
    st.session_state['show_channel_ai_analysis'] = False
    st.session_state['last_filter_key'] = current_filter_key

st.markdown('<div class="main-title">Real-time Marketing Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">10년차 시니어 AE의 인사이트가 담긴 실시간 매체 통합 분석 플랫폼</div>', unsafe_allow_html=True)

# 화면 3분할 레이아웃 적용 (좌측 대시보드 70% : 우측 AI 비서 챗봇 30%)
left_col, right_col = st.columns([0.7, 0.3])

# 좌측 시각화 대시보드 호출 이식
with left_col:
    import dashboard_left
    dashboard_left.render_dashboard(
        filtered_df=filtered_df,
        start_date=start_date,
        end_date=end_date,
        selected_media=selected_media,
        selected_types=selected_types,
        api_key=api_key,
        get_gemini_analysis=get_gemini_analysis
    )

# 우측 AI 챗봇 에이전트 영역 구현
with right_col:
    st.markdown('<h3 style="color: #F8FAFC; margin-bottom: 20px; font-weight: 700;">🤖 AE 전용 데이터 AI 비서</h3>', unsafe_allow_html=True)
    
    # 챗봇 세션 상태 초기화
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = [
            {"role": "assistant", "content": "안녕하세요! 10년 경력의 탑티어 디지털 광고 데이터 사이언티스트 'AI 비서'입니다. 현재 필터링된 실시간 광고 데이터에 대해 어떤 인사이트나 분석이 필요하신가요?"}
        ]
        
    # 채팅 스크롤 박스 및 디자인 요소 주입 (CSS)
    st.markdown("""
    <style>
        .chat-bubble-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 520px;
            overflow-y: auto;
            background-color: #1E293B;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid #334155;
            margin-bottom: 15px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 채팅 메시지들을 화면에 순차 렌더링
    for msg in st.session_state['chat_messages']:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    # 사용자로부터 질문을 입력받음
    if user_query := st.chat_input("AI 비서에게 질문을 남겨보세요... (예: 가장 효율적인 매체와 그 이유는?)"):
        # 사용자 질문 추가
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state['chat_messages'].append({"role": "user", "content": user_query})
        
        # 실시간 통계 요약 데이터 구축 (Gemini 컨텍스트 바인딩)
        # 1) 현재 필터링된 화면 데이터 집계
        chat_total_spend = filtered_df['광고비용'].sum()
        chat_total_conv_value = filtered_df['전환값'].sum()
        chat_overall_roas = (chat_total_conv_value / chat_total_spend * 100) if chat_total_spend > 0 else 0.0
        chat_total_conversions = filtered_df['전환수'].sum()
        chat_overall_cpa = (chat_total_spend / chat_total_conversions) if chat_total_conversions > 0 else 0.0

        # 필터링 매체별 집계 마크다운 표 생성
        chat_media_metrics = filtered_df.groupby('매체').agg({
            '광고비용': 'sum',
            '전환값': 'sum',
            '전환수': 'sum'
        }).reset_index()
        chat_media_metrics['ROAS(%)'] = (chat_media_metrics['전환값'] / chat_media_metrics['광고비용'] * 100).fillna(0).round(1)
        chat_media_metrics['CPA'] = (chat_media_metrics['광고비용'] / chat_media_metrics['전환수']).fillna(0).astype(int)
        chat_media_md = chat_media_metrics[['매체', '광고비용', '전환수', 'ROAS(%)', 'CPA']].to_markdown(index=False)

        # 필터링 유형별 집계 마크다운 표 생성
        chat_sada_metrics = filtered_df.groupby('SA/DA').agg({
            '광고비용': 'sum',
            '전환값': 'sum',
            '전환수': 'sum'
        }).reset_index()
        chat_sada_metrics['ROAS(%)'] = (chat_sada_metrics['전환값'] / chat_sada_metrics['광고비용'] * 100).fillna(0).round(1)
        chat_sada_metrics['CPA'] = (chat_sada_metrics['광고비용'] / chat_sada_metrics['전환수']).fillna(0).astype(int)
        chat_sada_md = chat_sada_metrics[['SA/DA', '광고비용', '전환수', 'ROAS(%)', 'CPA']].to_markdown(index=False)

        # 2) 전체 원본 데이터 (raw_df) 누적 통계 실시간 집계
        raw_total_spend = raw_df['광고비용'].sum()
        raw_total_conv_value = raw_df['전환값'].sum()
        raw_overall_roas = (raw_total_conv_value / raw_total_spend * 100) if raw_total_spend > 0 else 0.0
        raw_total_conversions = raw_df['전환수'].sum()
        raw_overall_cpa = (raw_total_spend / raw_total_conversions) if raw_total_conversions > 0 else 0.0

        # 원본 데이터 매체별 집계 마크다운 표 생성
        raw_media_metrics = raw_df.groupby('매체').agg({
            '광고비용': 'sum',
            '전환값': 'sum'
        }).reset_index()
        raw_media_metrics['ROAS(%)'] = (raw_media_metrics['전환값'] / raw_media_metrics['광고비용'] * 100).fillna(0).round(1)
        raw_media_md = raw_media_metrics[['media_spend' if False else '매체', '광고비용', 'ROAS(%)']].to_markdown(index=False)

        # 원본 데이터 내 역사상 최고 ROAS 기록 날짜 검색
        highest_roas_row = raw_df.loc[raw_df['ROAS'].idxmax()] if not raw_df.empty else None
        highest_roas_date = highest_roas_row['날짜'].strftime('%Y-%m-%d') if highest_roas_row is not None else "N/A"
        highest_roas_val = highest_roas_row['ROAS'] if highest_roas_row is not None else 0.0

        chat_context = f"""
### 1. 현재 필터링된 화면 데이터 요약 (설정 기간: {start_date} ~ {end_date})
- 로드된 총 로그 행 수: {len(filtered_df)}행
- 전체 집행 광고비: ₩{chat_total_spend:,.0f}원
- 전체 달성 전환가치: ₩{chat_total_conv_value:,.0f}원
- 종합 광고 효율 ROAS: {chat_overall_roas:.2f}%
- 평균 신규 획득 단가 CPA: ₩{chat_overall_cpa:,.0f}원

[필터링된 매체별 성과 상세표]
{chat_media_md}

[필터링된 광고유형별(SA/DA) 성과 상세표]
{chat_sada_md}

### 2. 전체 원본 데이터 개요 요약 (전체 역사적 누계)
- 원본 데이터 총 로그 수: {len(raw_df)}행
- 누적 총 집행 광고비: ₩{raw_total_spend:,.0f}원
- 누적 총 달성 전환가치: ₩{raw_total_conv_value:,.0f}원
- 원본 데이터 종합 ROAS: {raw_overall_roas:.2f}%
- 전체 기간 평균 CPA: ₩{raw_overall_cpa:,.0f}원
- 역사상 단일 일자 최고 ROAS 기록일: {highest_roas_date} ({highest_roas_val:.1f}%)

[전체 원본 데이터 매체별 누적 성과표]
{raw_media_md}
"""

        # AI의 대답 생성 프로세스 시작
        with st.spinner("AI 비서가 데이터를 상세 검토 중입니다..."):
            ai_reply = get_gemini_chat_response(
                api_key=api_key,
                chat_history=[(m["role"], m["content"]) for m in st.session_state['chat_messages']],
                current_question=user_query,
                context_data=chat_context
            )
            
        with st.chat_message("assistant"):
            st.write(ai_reply)
        st.session_state['chat_messages'].append({"role": "assistant", "content": ai_reply})
        st.rerun()
