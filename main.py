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

# 프리미엄 다크 테마 커스텀 CSS 주입 (Visual Guide)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap');
    
    /* 폰트 및 기본 스크롤바 디자인 */
    html, body, [class*="css"], .stMarkdown {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    /* Streamlit 전체 페이지 마진/배경 제어 */
    .stApp {
        background-color: #0B0C10 !important;
        color: #F8FAFC !important;
    }
    
    /* 메인 페이지 마진 축소 */
    div.block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    
    /* 헤더 숨김 */
    header[data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }
    
    /* 사이드바 다크 스타일 정의 */
    section[data-testid="stSidebar"] {
        background-color: #0E1117 !important;
        border-right: 1px solid rgba(138, 43, 226, 0.15) !important;
        color: #F8FAFC !important;
    }
    section[data-testid="stSidebar"] .stMarkdown h1, 
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #8A2BE2 !important;
    }
    
    /* 1단: 고밀도 커스텀 KPI 카드 CSS */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 15px;
        margin-bottom: 25px;
    }
    
    .custom-card {
        background-color: #161A23 !important;
        border: 1px solid rgba(138, 43, 226, 0.2) !important;
        border-radius: 10px;
        padding: 18px;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .custom-card:hover {
        transform: translateY(-3px);
        border-color: rgba(0, 210, 255, 0.5) !important;
        box-shadow: 0 8px 24px rgba(138, 43, 226, 0.25);
    }
    
    .highlight-card {
        border: 1px solid rgba(0, 210, 255, 0.3) !important;
        background: linear-gradient(145deg, #161A23 0%, #1c153b 100%) !important;
    }
    .highlight-card:hover {
        border-color: rgba(0, 210, 255, 0.8) !important;
    }
    
    .card-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
    }
    
    .card-icon {
        font-size: 1.1rem;
    }
    
    .card-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .card-value {
        font-size: 1.35rem;
        font-weight: 800;
        color: #FFFFFF;
        margin-bottom: 4px;
        display: flex;
        align-items: baseline;
        gap: 6px;
    }
    
    .card-value-sub {
        font-size: 0.82rem;
        font-weight: 500;
        color: #94A3B8;
    }
    
    .card-delta {
        font-size: 0.75rem;
        font-weight: 700;
        margin-top: 5px;
    }
    
    .delta-up {
        color: #10B981;
    }
    
    .delta-down {
        color: #EF4444;
    }
    
    .delta-neutral {
        color: #94A3B8;
    }
    
    /* 섹션 공통 스타일 */
    .section-card {
        background-color: #161A23;
        border: 1px solid rgba(138, 43, 226, 0.2);
        border-radius: 10px;
        padding: 22px;
        margin-bottom: 25px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    .section-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 15px;
        border-bottom: 1px solid rgba(138, 43, 226, 0.1);
        padding-bottom: 8px;
    }
    
    /* 메인 타이틀 장식 */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(to right, #00D2FF, #8A2BE2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 5px;
    }
    .sub-title {
        font-size: 1rem;
        color: #94A3B8;
        margin-bottom: 25px;
    }
    
    /* 3단: 우측 AI 챗봇 컨테이너 및 둥근 에두리 적용 */
    .chat-container-card {
        background-color: #161A23 !important;
        border: 1px solid rgba(138, 43, 226, 0.25) !important;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    
    /* 커스텀 버튼 (Neon Violet Accent) */
    div.stButton > button {
        background: linear-gradient(135deg, #8A2BE2 0%, #4B0082 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(138, 43, 226, 0.4) !important;
        border-radius: 8px !important;
        padding: 6px 16px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 10px rgba(138, 43, 226, 0.2) !important;
        width: 100%;
    }
    
    div.stButton > button:hover {
        background: linear-gradient(135deg, #00D2FF 0%, #8A2BE2 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 15px rgba(0, 210, 255, 0.35) !important;
        border-color: #00D2FF !important;
    }
    
    /* stAlert 커스터마이징 */
    div[data-testid="stAlert"] {
        background-color: #0E1117 !important;
        border: 1px solid rgba(138, 43, 226, 0.3) !important;
        color: #E2E8F0 !important;
        border-radius: 8px;
    }
    
    /* 스크롤바 디자인 */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0B0C10;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(138, 43, 226, 0.3);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(138, 43, 226, 0.6);
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

# 2-1. AI 상세 분석용 Gemini API 연동 함수
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
            
            raise last_err if last_err else Exception("No models available.")
            
        except Exception as e:
            st.error(f"❌ AI 분석 중 에러가 발생했습니다: {e}")
            st.warning("⚠️ API Key의 쿼터(Quota) 한도가 소진되었거나, 사용자의 API Key 환경에서 사용할 수 있는 유효 모델이 없습니다. 구글 AI 스튜디오 설정을 확인해 주세요.")
            return None

# 2-2. AI 챗봇 전용 Gemini API 연동 함수
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
                
        return f"❌ 챗봇 답변 생성 실패: {last_err}. API Key 또는 쿼터 설정을 다시 확인해 주세요."
                
    except Exception as e:
        return f"❌ AI 비서 연결 오류: {e}"

# 2-3. 이등분 기간 성과비교(Delta %) 계산 함수
def calculate_deltas(df):
    unique_dates = sorted(df['날짜'].unique())
    n_dates = len(unique_dates)
    
    if n_dates < 2:
        return {
            'spend_change': 0.0,
            'clicks_change': 0.0,
            'conversions_change': 0.0,
            'roas_change': 0.0,
            'ctr_change': 0.0,
            'cpa_change': 0.0,
            'prior_exists': False
        }
    
    # 14일 이상인 경우 최근 7일 vs 이전 7일, 미만인 경우 절반씩 분할
    if n_dates >= 14:
        max_date = unique_dates[-1]
        recent_start = max_date - pd.Timedelta(days=6)
        prior_start = max_date - pd.Timedelta(days=13)
        prior_end = max_date - pd.Timedelta(days=7)
        
        recent_df = df[(df['날짜'] >= recent_start) & (df['날짜'] <= max_date)]
        prior_df = df[(df['날짜'] >= prior_start) & (df['날짜'] <= prior_end)]
    else:
        half = n_dates // 2
        recent_df = df[df['날짜'].isin(unique_dates[half:])]
        prior_df = df[df['날짜'].isin(unique_dates[:half])]
        
    if prior_df.empty or recent_df.empty:
        return {
            'spend_change': 0.0,
            'clicks_change': 0.0,
            'conversions_change': 0.0,
            'roas_change': 0.0,
            'ctr_change': 0.0,
            'cpa_change': 0.0,
            'prior_exists': False
        }
        
    # Recent 집계
    r_spend = recent_df['광고비용'].sum()
    r_clicks = recent_df['클릭수'].sum()
    r_conversions = recent_df['전환수'].sum()
    r_conv_val = recent_df['전환값'].sum()
    r_impressions = recent_df['노출수'].sum()
    
    r_ctr = (r_clicks / r_impressions * 100) if r_impressions > 0 else 0.0
    r_cpa = (r_spend / r_conversions) if r_conversions > 0 else 0.0
    r_roas = (r_conv_val / r_spend * 100) if r_spend > 0 else 0.0
    
    # Prior 집계
    p_spend = prior_df['광고비용'].sum()
    p_clicks = prior_df['클릭수'].sum()
    p_conversions = prior_df['전환수'].sum()
    p_conv_val = prior_df['전환값'].sum()
    p_impressions = prior_df['노출수'].sum()
    
    p_ctr = (p_clicks / p_impressions * 100) if p_impressions > 0 else 0.0
    p_cpa = (p_spend / p_conversions) if p_conversions > 0 else 0.0
    p_roas = (p_conv_val / p_spend * 100) if p_spend > 0 else 0.0
    
    # % 변화 계산
    spend_change = ((r_spend - p_spend) / p_spend * 100) if p_spend > 0 else 0.0
    clicks_change = ((r_clicks - p_clicks) / p_clicks * 100) if p_clicks > 0 else 0.0
    conversions_change = ((r_conversions - p_conversions) / p_conversions * 100) if p_conversions > 0 else 0.0
    roas_change = r_roas - p_roas
    ctr_change = r_ctr - p_ctr
    cpa_change = ((r_cpa - p_cpa) / p_cpa * 100) if p_cpa > 0 else 0.0
    
    return {
        'spend_change': spend_change,
        'clicks_change': clicks_change,
        'conversions_change': conversions_change,
        'roas_change': roas_change,
        'ctr_change': ctr_change,
        'cpa_change': cpa_change,
        'prior_exists': True
    }

# 데이터 로드 실행
try:
    raw_df = load_data()
except Exception as e:
    st.error(f"❌ 데이터 로드 중 오류가 발생했습니다: {e}")
    st.stop()

# 3. 사이드바 - 필터링 컨트롤 구성
st.sidebar.markdown('<h1 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 0px; line-height: 1.2;">📊 에이전틱<br>대시보드</h1><div style="font-size: 0.85rem; color: #94A3B8; margin-top: 5px; margin-bottom: 15px;">Agentic Dashboard</div>', unsafe_allow_html=True)
st.sidebar.markdown("---")

# 날짜 범위 설정
min_date = raw_df['날짜'].min().date()
max_date = raw_df['날짜'].max().date()

st.sidebar.subheader("📅 분석 기간 설정  \n(Date Range)")
date_range = st.sidebar.date_input(
    "조회 기간",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="시작일과 종료일을 지정하세요."
)

# 매체 선택
st.sidebar.subheader("📺 매체  \n(Media)")
all_media = sorted(raw_df['매체'].unique())
selected_media = st.sidebar.multiselect(
    "분석할 매체를 선택하세요",
    options=all_media,
    default=all_media
)

# 광고 유형 선택
st.sidebar.subheader("🏷️ 광고 유형  \n(Type)")
all_types = sorted(raw_df['SA/DA'].unique())
selected_types = st.sidebar.multiselect(
    "광고 유형을 선택하세요",
    options=all_types,
    default=all_types
)

# Secrets 및 API Key 로드
api_key = st.secrets.get("GEMINI_API_KEY", "")

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


# 날짜 범위 입력값 검증
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

# 5. 메인 타이틀 및 세션 상태 관리
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

# 메인 헤더 타이틀
st.markdown('<div class="main-title">Real-time Marketing Performance Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">프리미엄 다크 테마와 10년차 시니어 AE의 분석 로직이 결합된 에이전틱 대시보드</div>', unsafe_allow_html=True)

# 70% (대시보드) vs 30% (AI 챗봇) 화면 분할 레이아웃
left_col, right_col = st.columns([0.75, 0.25], gap="large")

# 좌측 시각화 대시보드 구현
with left_col:
    # 6. 핵심 KPI 계산 및 요약 카드
    total_spend = filtered_df['광고비용'].sum()
    total_impressions = filtered_df['노출수'].sum()
    total_clicks = filtered_df['클릭수'].sum()
    total_conversions = filtered_df['전환수'].sum()
    total_conv_value = filtered_df['전환값'].sum()
    
    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
    overall_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0
    overall_cpa = (total_spend / total_conversions) if total_conversions > 0 else 0.0
    overall_roas = (total_conv_value / total_spend * 100) if total_spend > 0 else 0.0
    
    # Delta % 계산
    deltas = calculate_deltas(filtered_df)
    
    def get_delta_label(val, is_diff=False):
        if not deltas['prior_exists']:
            return '<span class="delta-neutral">- (전기 대비)</span>'
        suffix = "%p" if is_diff else "%"
        if val > 0:
            return f'<span class="delta-up">▲ {val:.1f}{suffix} (전기 대비)</span>'
        elif val < 0:
            return f'<span class="delta-down">▼ {abs(val):.1f}{suffix} (전기 대비)</span>'
        else:
            return '<span class="delta-neutral">- (전기 대비)</span>'

    spend_delta_html = get_delta_label(deltas['spend_change'])
    clicks_delta_html = get_delta_label(deltas['clicks_change'])
    conversions_delta_html = get_delta_label(deltas['conversions_change'])
    roas_delta_html = get_delta_label(deltas['roas_change'], is_diff=True)
    
    # 4분할 그리드 KPI 마크업 렌더링
    kpi_html = f"""
    <div class="metrics-grid">
        <div class="custom-card">
            <div class="card-header">
                <span class="card-icon">💸</span>
                <span class="card-title">총 광고비용 (Spend)</span>
            </div>
            <div class="card-value">₩{total_spend:,.0f}</div>
            <div class="card-delta">{spend_delta_html}</div>
        </div>
        <div class="custom-card">
            <div class="card-header">
                <span class="card-icon">🖱️</span>
                <span class="card-title">유입 성과 (Clicks & CTR)</span>
            </div>
            <div class="card-value">{total_clicks:,.0f} <span class="card-value-sub">({overall_ctr:.2f}%)</span></div>
            <div class="card-delta">{clicks_delta_html}</div>
        </div>
        <div class="custom-card">
            <div class="card-header">
                <span class="card-icon">🎯</span>
                <span class="card-title">전환 효율 (Conversions & CPA)</span>
            </div>
            <div class="card-value">{total_conversions:,.0f} <span class="card-value-sub">(₩{overall_cpa:,.0f})</span></div>
            <div class="card-delta">{conversions_delta_html}</div>
        </div>
        <div class="custom-card highlight-card">
            <div class="card-header">
                <span class="card-icon">📈</span>
                <span class="card-title">총 매출 효율 (ROAS & Revenue)</span>
            </div>
            <div class="card-value">{overall_roas:.1f}% <span class="card-value-sub">(₩{total_conv_value:,.0f})</span></div>
            <div class="card-delta">{roas_delta_html}</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)
    
    # KPI 요약 성과 분석 버튼 영역
    kpi_btn1, kpi_btn2, _ = st.columns([3, 3, 4])
    with kpi_btn1:
        if st.button("📊 성과 요약 진단", key="kpi_analysis_btn"):
            st.session_state['show_kpi_analysis'] = not st.session_state['show_kpi_analysis']
    with kpi_btn2:
        if st.button("🤖 AI 상세분석", key="kpi_ai_btn"):
            st.session_state['show_kpi_ai_analysis'] = not st.session_state['show_kpi_ai_analysis']
            
    if st.session_state['show_kpi_analysis']:
        target_roas = 3000.0
        roas_achievement = (overall_roas / target_roas) * 100
        st.info(f"""
        💡 **[AE 진단] 핵심 성과 요약 결과**
        - 필터링된 기간의 평균 ROAS는 **{overall_roas:.1f}%**이며, 대행사 목표치({target_roas:,.0f}%) 대비 **{roas_achievement:.1f}%**를 기록하고 있습니다.
        - 누적 광고비 **₩{total_spend:,.0f}** 소진을 통해 최종 전환 가치 **₩{total_conv_value:,.0f}**를 달성했습니다.
        """)
        
    if st.session_state['show_kpi_ai_analysis']:
        if not api_key:
            st.warning("먼저 좌측 사이드바에 Gemini API Key를 입력해주세요.")
        else:
            kpi_data = {
                "핵심지표": ["총 광고비용", "총 노출수", "총 클릭수", "평균 CTR", "평균 CPC", "총 전환수", "총 전환가치", "종합 ROAS", "평균 CPA"],
                "값": [f"₩{total_spend:,.0f}", f"{total_impressions:,.0f}", f"{total_clicks:,.0f}", f"{overall_ctr:.2f}%", f"₩{overall_cpc:,.0f}", f"{total_conversions:,.0f}", f"₩{total_conv_value:,.0f}", f"{overall_roas:.2f}%", f"₩{overall_cpa:,.0f}"]
            }
            kpi_df_md = pd.DataFrame(kpi_data).to_markdown(index=False)
            ai_res = get_gemini_analysis(api_key, kpi_df_md, "전체 핵심 KPI 성과 요약")
            if ai_res:
                st.info(f"✨ **[AI 분석 리포트] 핵심 KPI 요약 분석**\n\n{ai_res}")
                
    st.write("") # 간격 조절

    # 7. 성과 트렌드 분석 영역 (Trend Charts)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📈 실시간 성과 트렌드 분석<br><span style="font-size:0.75rem; color:#94A3B8; font-weight:normal;">(Performance Trend Analysis)</span></div>', unsafe_allow_html=True)
    
    # 일별 집계
    daily_df = filtered_df.groupby('날짜').agg({
        '광고비용': 'sum',
        '노출수': 'sum',
        '클릭수': 'sum',
        '전환수': 'sum',
        '전환값': 'sum'
    }).reset_index()
    
    daily_df['CTR'] = (daily_df['클릭수'] / daily_df['노출수'] * 100).fillna(0)
    daily_df['CPC'] = (daily_df['광고비용'] / daily_df['클릭수']).fillna(0)
    daily_df['CPA'] = (daily_df['광고비용'] / daily_df['전환수']).fillna(0)
    daily_df['ROAS'] = (daily_df['전환값'] / daily_df['광고비용'] * 100).fillna(0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div style="font-size:0.85rem; font-weight:600; color:#CBD5E1; margin-bottom:10px;">🔹 일별 광고비용 vs 전환수 추이  \n(Spend vs Conversions)</div>', unsafe_allow_html=True)
        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        
        fig_trend.add_trace(
            qs.Bar(
                x=daily_df['날짜'], 
                y=daily_df['광고비용'], 
                name="광고비용 (Spend)",
                marker_color='#00D2FF',
                opacity=0.85
            ),
            secondary_y=False
        )
        
        fig_trend.add_trace(
            qs.Scatter(
                x=daily_df['날짜'], 
                y=daily_df['전환수'], 
                name="전환수 (Conversions)",
                mode='lines+markers',
                line=dict(color='#8A2BE2', width=3),
                marker=dict(size=6)
            ),
            secondary_y=True
        )
        
        fig_trend.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False, tickfont=dict(color="#94A3B8")),
            yaxis=dict(title="광고비용 (₩)", showgrid=True, gridcolor='rgba(138, 43, 226, 0.1)', tickfont=dict(color="#94A3B8")),
            yaxis2=dict(title="전환수 (건)", showgrid=False, tickfont=dict(color="#94A3B8")),
            font=dict(color="#CBD5E1")
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col2:
        st.markdown('<div style="font-size:0.85rem; font-weight:600; color:#CBD5E1; margin-bottom:10px;">🔹 일별 ROAS 트렌드 추이  \n(Daily ROAS Trend)</div>', unsafe_allow_html=True)
        fig_roas = qs.Figure()
        
        fig_roas.add_trace(
            qs.Scatter(
                x=daily_df['날짜'], 
                y=daily_df['ROAS'], 
                name="일별 ROAS (%)",
                mode='lines+markers',
                line=dict(color='#10B981', width=3),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.08)'
            )
        )
        
        overall_roas_val = (total_conv_value / total_spend * 100) if total_spend > 0 else 0
        fig_roas.add_trace(
            qs.Scatter(
                x=daily_df['날짜'],
                y=[overall_roas_val] * len(daily_df),
                name=f"평균 ROAS ({overall_roas_val:.1f}%)",
                mode='lines',
                line=dict(color='#EF4444', width=1.5, dash='dash')
            )
        )
        
        fig_roas.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False, tickfont=dict(color="#94A3B8")),
            yaxis=dict(title="ROAS (%)", showgrid=True, gridcolor='rgba(138, 43, 226, 0.1)', tickfont=dict(color="#94A3B8")),
            font=dict(color="#CBD5E1")
        )
        st.plotly_chart(fig_roas, use_container_width=True)
        
    # 트렌드 진단 및 AI 분석 버튼
    trend_btn1, trend_btn2, _ = st.columns([3, 3, 4])
    with trend_btn1:
        if st.button("🔍 추세 및 효율 진단", key="trend_analysis_btn"):
            st.session_state['show_trend_analysis'] = not st.session_state['show_trend_analysis']
    with trend_btn2:
        if st.button("🤖 AI 상세분석", key="trend_ai_btn"):
            st.session_state['show_trend_ai_analysis'] = not st.session_state['show_trend_ai_analysis']
            
    if st.session_state['show_trend_analysis']:
        unique_dates = sorted(filtered_df['날짜'].unique())
        n_dates = len(unique_dates)
        
        if n_dates < 2:
            st.info("💡 **[AE 진단] 추세 분석 결과**\n\n조회 기간이 너무 짧아(1일 이하) 추세 분석을 실행할 수 없습니다. 더 넓은 기간을 선택해 주세요.")
        else:
            if n_dates >= 14:
                max_date_in_data = unique_dates[-1]
                recent_7_start = max_date_in_data - pd.Timedelta(days=6)
                prior_7_start = max_date_in_data - pd.Timedelta(days=13)
                prior_7_end = max_date_in_data - pd.Timedelta(days=7)
                
                recent_df = filtered_df[(filtered_df['날짜'] >= recent_7_start) & (filtered_df['날짜'] <= max_date_in_data)]
                prior_df = filtered_df[(filtered_df['날짜'] >= prior_7_start) & (filtered_df['날짜'] <= prior_7_end)]
                compare_period_desc = "최근 7일 대비 이전 7일"
            else:
                half = n_dates // 2
                recent_df = filtered_df[filtered_df['날짜'].isin(unique_dates[half:])]
                prior_df = filtered_df[filtered_df['날짜'].isin(unique_dates[:half])]
                compare_period_desc = f"후반부 {len(unique_dates[half:])}일 대비 전반부 {half}일"
                
            recent_spend = recent_df['광고비용'].sum()
            recent_conv = recent_df['전환수'].sum()
            recent_cpa = (recent_spend / recent_conv) if recent_conv > 0 else 0
            
            prior_spend = prior_df['광고비용'].sum()
            prior_conv = prior_df['전환수'].sum()
            prior_cpa = (prior_spend / prior_conv) if prior_conv > 0 else 0
            
            spend_diff_pct = ((recent_spend - prior_spend) / prior_spend * 100) if prior_spend > 0 else 0.0
            cpa_diff = recent_cpa - prior_cpa
            
            spend_trend = "증가" if spend_diff_pct > 0 else "감소"
            cpa_trend = "상승" if cpa_diff > 0 else "하락"
            
            advice = ""
            if spend_diff_pct > 0 and cpa_diff > 0:
                advice = "⚠️ 광고비 집행은 늘었으나 CPA(전환단가)가 상승하고 있어, 매체 효율의 상세 정밀 진단과 타겟 최적화가 긴급히 요구됩니다."
            elif spend_diff_pct > 0 and cpa_diff <= 0:
                advice = "✨ 광고비 예산을 증액했음에도 CPA가 하락/유지되어 이상적인 확장 국면입니다. 현 매체 예산 구성을 유지 또는 추가 확장을 추천합니다."
            elif spend_diff_pct <= 0 and cpa_diff > 0:
                advice = "⚠️ 광고 예산을 축소했으나 전환 효율성(CPA)이 저하되고 있습니다. 모객 퀄리티 저하 가능성이 있으니 크리에이티브 피로도를 확인하십시오."
            else:
                advice = "✅ 광고비가 절감되는 동시에 CPA도 하락하여 매우 효율적인 타겟 최적화가 이뤄지고 있는 긍정적인 상황입니다."
                
            st.info(f"""
            💡 **[AE 진단] 트렌드 추세 및 효율 진단 ({compare_period_desc})**
            - {compare_period_desc} 비교 결과, 광고비 집행은 **{spend_diff_pct:+.1f}%** {spend_trend}하였으며, CPA는 **{cpa_diff:+,.0f}원** {cpa_trend}했습니다.
            - {advice}
            """)
            
    if st.session_state['show_trend_ai_analysis']:
        if not api_key:
            st.warning("먼저 좌측 사이드바에 Gemini API Key를 입력해주세요.")
        else:
            trend_md = daily_df[['날짜', '광고비용', '전환수', 'ROAS']].to_markdown(index=False)
            ai_res = get_gemini_analysis(api_key, trend_md, "일별 광고비용 및 ROAS 성과 추이")
            if ai_res:
                st.info(f"✨ **[AI 분석 리포트] 트렌드 성과 분석**\n\n{ai_res}")
                
    st.markdown('</div>', unsafe_allow_html=True)

    # 8. 매체 및 유형별 비중 분석 (Composition Analysis)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📊 비중 및 성과 비교 분석<br><span style="font-size:0.75rem; color:#94A3B8; font-weight:normal;">(Composition & Comparison)</span></div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown('<div style="font-size:0.85rem; font-weight:600; color:#CBD5E1; margin-bottom:10px;">🔹 매체별 광고비 집행 비중  \n(Share of Voice by Media)</div>', unsafe_allow_html=True)
        media_spend = filtered_df.groupby('매체')['광고비용'].sum().reset_index()
        
        fig_media = px.pie(
            media_spend, 
            values='광고비용', 
            names='매체',
            hole=0.45,
            color_discrete_sequence=['#8A2BE2', '#00D2FF', '#10B981', '#F59E0B', '#F43F5E']
        )
        
        fig_media.update_traces(
            textposition='inside', 
            textinfo='percent+label',
            hovertemplate="<b>%{label}</b><br>광고비용: ₩%{value:,.0f}<br>비율: %{percent}<extra></extra>"
        )
        
        fig_media.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(size=10, color="#94A3B8")),
            font=dict(color="#CBD5E1")
        )
        st.plotly_chart(fig_media, use_container_width=True)
        
    with col4:
        st.markdown('<div style="font-size:0.85rem; font-weight:600; color:#CBD5E1; margin-bottom:10px;">🔹 SA vs DA 성과 비교 분석  \n(SA vs DA Performance)</div>', unsafe_allow_html=True)
        metric_choice = st.selectbox(
            "비교할 지표를 선택해 주세요",
            options=["광고비용", "전환값", "ROAS", "전환수", "클릭수"],
            index=2,
            key="sada_metric_selector"
        )
        
        sada_group = filtered_df.groupby('SA/DA').agg({
            '광고비용': 'sum',
            '전환수': 'sum',
            '전환값': 'sum',
            '클릭수': 'sum'
        }).reset_index()
        
        sada_group['ROAS'] = (sada_group['전환값'] / sada_group['광고비용'] * 100).fillna(0)
        
        label_map = {
            "광고비용": "광고비용 (₩)",
            "전환값": "전환가치 (₩)",
            "ROAS": "ROAS (%)",
            "전환수": "전환수 (건)",
            "클릭수": "클릭수 (회)"
        }
        
        fig_sada = px.bar(
            sada_group,
            x='SA/DA',
            y=metric_choice,
            text=metric_choice,
            color='SA/DA',
            color_discrete_map={
                "SA": "#8A2BE2",
                "DA": "#00D2FF",
                "미분류(기타)": "#94A3B8"
            }
        )
        
        if metric_choice in ["광고비용", "전환값"]:
            fig_sada.update_traces(texttemplate='₩%{text:,.0f}', textposition='outside')
        elif metric_choice == "ROAS":
            fig_sada.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        else:
            fig_sada.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            
        fig_sada.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(title="광고 유형", showgrid=False, tickfont=dict(color="#94A3B8")),
            yaxis=dict(title=label_map[metric_choice], showgrid=True, gridcolor='rgba(138, 43, 226, 0.1)', tickfont=dict(color="#94A3B8")),
            showlegend=False,
            font=dict(color="#CBD5E1")
        )
        st.plotly_chart(fig_sada, use_container_width=True)
        
    # 채널 믹스 및 AI 분석 버튼
    channel_btn1, channel_btn2, _ = st.columns([3, 3, 4])
    with channel_btn1:
        if st.button("📊 채널 믹스 인사이트", key="channel_analysis_btn"):
            st.session_state['show_channel_analysis'] = not st.session_state['show_channel_analysis']
    with channel_btn2:
        if st.button("🤖 AI 상세분석", key="channel_ai_btn"):
            st.session_state['show_channel_ai_analysis'] = not st.session_state['show_channel_ai_analysis']
            
    if st.session_state['show_channel_analysis']:
        media_metrics = filtered_df.groupby('매체').agg({
            '광고비용': 'sum',
            '전환값': 'sum'
        }).reset_index()
        
        media_metrics['ROAS'] = (media_metrics['전환값'] / media_metrics['광고비용'] * 100).fillna(0)
        
        total_med_spend = media_metrics['광고비용'].sum()
        if total_med_spend > 0:
            media_metrics['비중'] = (media_metrics['광고비용'] / total_med_spend * 100)
            max_spend_row = media_metrics.loc[media_metrics['광고비용'].idxmax()]
            max_spend_media = max_spend_row['매체']
            max_spend_share = max_spend_row['비중']
        else:
            max_spend_media = "N/A"
            max_spend_share = 0.0
            
        if not media_metrics.empty:
            max_roas_row = media_metrics.loc[media_metrics['ROAS'].idxmax()]
            max_roas_media = max_roas_row['매체']
            max_roas_val = max_roas_row['ROAS']
        else:
            max_roas_media = "N/A"
            max_roas_val = 0.0
            
        st.info(f"""
        💡 **[AE 진단] 채널 믹스 분석 결과**
        - 현재 **{max_spend_media}** 매체의 광고비 집행 비중이 **{max_spend_share:.1f}%**로 최대 소진 중이지만, 실질 효율(ROAS)은 **{max_roas_media}** 매체(**{max_roas_val:.1f}%**)가 최고 효율을 내고 있습니다.
        - 높은 효율성을 기록 중인 **{max_roas_media}** 매체로 예산을 리밸런싱하여 캠페인 전반의 통합 믹스 효율 극대화를 제안합니다.
        """)
        
    if st.session_state['show_channel_ai_analysis']:
        if not api_key:
            st.warning("먼저 좌측 사이드바에 Gemini API Key를 입력해주세요.")
        else:
            mix_md = "### 매체별 성과\n" + media_spend.to_markdown(index=False) + "\n\n### 광고유형별 성과\n" + sada_group.to_markdown(index=False)
            ai_res = get_gemini_analysis(api_key, mix_md, "매체 및 광고유형(SA/DA)별 비중/효율 리밸런싱")
            if ai_res:
                st.info(f"✨ **[AI 분석 리포트] 채널 믹스 및 효율 분석**\n\n{ai_res}")
                
    st.markdown('</div>', unsafe_allow_html=True)

    # 9. 상세 데이터 테이블 (Detailed View)
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">📋 성과 상세 데이터<br><span style="font-size:0.75rem; color:#94A3B8; font-weight:normal;">(Detailed Performance Log)</span></div>', unsafe_allow_html=True)
    
    table_display_df = filtered_df.copy()
    
    table_display_df['날짜'] = table_display_df['날짜'].dt.strftime('%Y-%m-%d')
    table_display_df['ROAS(%)'] = table_display_df['ROAS'].round(2)
    table_display_df['CTR(%)'] = table_display_df['CTR'].round(4)
    table_display_df['CPA'] = table_display_df['CPA'].astype(int)
    table_display_df['CPC'] = table_display_df['CPC'].astype(int)
    
    table_display_df = table_display_df[[
        '날짜', '매체', 'SA/DA', '노출수', '클릭수', '광고비용', 'CTR(%)', 'CPC', '전환수', '전환값', 'ROAS(%)', 'CPA'
    ]]
    
    csv_data = table_display_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 필터링된 데이터 다운로드 (CSV)",
        data=csv_data,
        file_name=f"marketing_performance_{start_date}_to_{end_date}.csv",
        mime="text/csv"
    )
    
    st.dataframe(
        table_display_df,
        use_container_width=True,
        hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# 우측 AI 챗봇 에이전트 영역 구현
with right_col:
    st.markdown('<div class="chat-container-card">', unsafe_allow_html=True)
    st.markdown('<h3 style="color: #F8FAFC; margin-bottom: 20px; font-weight: 700; display: flex; align-items: center; gap: 8px;">🤖 <span style="font-size: 1.15rem;">AE 전용 데이터 AI 비서</span></h3>', unsafe_allow_html=True)
    
    # 챗봇 세션 상태 초기화
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = [
            {"role": "assistant", "content": "안녕하세요! 10년 경력의 탑티어 디지털 광고 데이터 사이언티스트 'AI 비서'입니다. 현재 필터링된 실시간 광고 데이터에 대해 어떤 인사이트나 분석이 필요하신가요?"}
        ]
        
    # Streamlit 네이티브 스크롤 고정형 컨테이너 적용 (대시보드와 독립)
    with st.container(height=420):
        for msg in st.session_state['chat_messages']:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
    # 사용자로부터 질문을 입력받음
    if user_query := st.chat_input("AI 비서에게 질문을 남겨보세요... (예: 가장 효율적인 매체와 그 이유는?)", key="chatbot_chat_input"):
        with st.chat_message("user"):
            st.write(user_query)
        st.session_state['chat_messages'].append({"role": "user", "content": user_query})
        
        # 실시간 통계 요약 데이터 구축
        chat_total_spend = filtered_df['광고비용'].sum()
        chat_total_conv_value = filtered_df['전환값'].sum()
        chat_overall_roas = (chat_total_conv_value / chat_total_spend * 100) if chat_total_spend > 0 else 0.0
        chat_total_conversions = filtered_df['전환수'].sum()
        chat_overall_cpa = (chat_total_spend / chat_total_conversions) if chat_total_conversions > 0 else 0.0

        chat_media_metrics = filtered_df.groupby('매체').agg({
            '광고비용': 'sum',
            '전환값': 'sum',
            '전환수': 'sum'
        }).reset_index()
        chat_media_metrics['ROAS(%)'] = (chat_media_metrics['전환값'] / chat_media_metrics['광고비용'] * 100).fillna(0).round(1)
        chat_media_metrics['CPA'] = (chat_media_metrics['광고비용'] / chat_media_metrics['전환수']).fillna(0).astype(int)
        chat_media_md = chat_media_metrics[['매체', '광고비용', '전환수', 'ROAS(%)', 'CPA']].to_markdown(index=False)

        chat_sada_metrics = filtered_df.groupby('SA/DA').agg({
            '광고비용': 'sum',
            '전환값': 'sum',
            '전환수': 'sum'
        }).reset_index()
        chat_sada_metrics['ROAS(%)'] = (chat_sada_metrics['전환값'] / chat_sada_metrics['광고비용'] * 100).fillna(0).round(1)
        chat_sada_metrics['CPA'] = (chat_sada_metrics['광고비용'] / chat_sada_metrics['전환수']).fillna(0).astype(int)
        chat_sada_md = chat_sada_metrics[['SA/DA', '광고비용', '전환수', 'ROAS(%)', 'CPA']].to_markdown(index=False)

        raw_total_spend = raw_df['광고비용'].sum()
        raw_total_conv_value = raw_df['전환값'].sum()
        raw_overall_roas = (raw_total_conv_value / raw_total_spend * 100) if raw_total_spend > 0 else 0.0
        raw_total_conversions = raw_df['전환수'].sum()
        raw_overall_cpa = (raw_total_spend / raw_total_conversions) if raw_total_conversions > 0 else 0.0

        raw_media_metrics = raw_df.groupby('매체').agg({
            '광고비용': 'sum',
            '전환값': 'sum'
        }).reset_index()
        raw_media_metrics['ROAS(%)'] = (raw_media_metrics['전환값'] / raw_media_metrics['광고비용'] * 100).fillna(0).round(1)
        raw_media_md = raw_media_metrics[['매체', '광고비용', 'ROAS(%)']].to_markdown(index=False)

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

    st.markdown('</div>', unsafe_allow_html=True)
