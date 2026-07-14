import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as qs
from plotly.subplots import make_subplots

def render_dashboard(filtered_df, start_date, end_date, selected_media, selected_types, api_key, get_gemini_analysis):
    # 6. 핵심 KPI 계산 및 요약 카드 (Summary Cards)
    # 가중 집계 방식을 활용하여 정확한 퍼포먼스 비율 계산 (단순 평균 대비 정밀성 확보)
    total_spend = filtered_df['광고비용'].sum()
    total_impressions = filtered_df['노출수'].sum()
    total_clicks = filtered_df['클릭수'].sum()
    total_conversions = filtered_df['전환수'].sum()
    total_conv_value = filtered_df['전환값'].sum()
    
    # 파생 비율 지표 안전 계산 (나눗셈 0 방지)
    overall_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0.0
    overall_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0.0
    overall_cpa = (total_spend / total_conversions) if total_conversions > 0 else 0.0
    overall_roas = (total_conv_value / total_spend * 100) if total_spend > 0 else 0.0
    
    # KPI 카드 마크업 생성
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-title">총 광고비용 (Spend)</div>
            <div class="kpi-value">₩{total_spend:,.0f}</div>
            <div class="kpi-sub">예산 소진 완료</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">총 노출수 (Impressions)</div>
            <div class="kpi-value">{total_impressions:,.0f}</div>
            <div class="kpi-sub">브랜드 노출 볼륨</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">총 클릭수 (Clicks)</div>
            <div class="kpi-value">{total_clicks:,.0f}</div>
            <div class="kpi-sub">웹사이트 유입 트래픽</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">평균 CTR</div>
            <div class="kpi-value">{overall_ctr:.2f}%</div>
            <div class="kpi-sub">노출 대비 클릭 효율</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">평균 CPC</div>
            <div class="kpi-value">₩{overall_cpc:,.0f}</div>
            <div class="kpi-sub font-gray">클릭당 평균 비용</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">총 전환수 (Conversions)</div>
            <div class="kpi-value">{total_conversions:,.0f}</div>
            <div class="kpi-sub">최종 목적 액션 달성</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">총 전환가치 (Conv. Value)</div>
            <div class="kpi-value">₩{total_conv_value:,.0f}</div>
            <div class="kpi-sub">전환 기여 총 매출</div>
        </div>
        <div class="kpi-card" style="border-color: #10B981;">
            <div class="kpi-title" style="color: #34D399;">종합 ROAS</div>
            <div class="kpi-value" style="color: #10B981;">{overall_roas:.1f}%</div>
            <div class="kpi-sub" style="color: #34D399;">투자 대비 투자수익률</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)
    
    # KPI 분석 버튼 및 로직
    kpi_btn_col, _ = st.columns([2, 8])
    with kpi_btn_col:
        if st.button("📈 전체 성과 요약 분석", key="kpi_analysis_btn"):
            st.session_state['show_kpi_analysis'] = not st.session_state['show_kpi_analysis']
            
    if st.session_state['show_kpi_analysis']:
        target_roas = 3000.0  # 목표 ROAS 3,000%
        roas_achievement = (overall_roas / target_roas) * 100
        
        st.info(f"""
        💡 **[AE 진단] 전체 성과 분석 결과**
        - 현재 필터링된 기간의 평균 ROAS는 **{overall_roas:.1f}%**이며, 목표치({target_roas:,.0f}%) 대비 **{roas_achievement:.1f}%** 달성 중입니다.
        - 총 광고비용 **₩{total_spend:,.0f}**을 소진하여 총 전환가치 **₩{total_conv_value:,.0f}**를 달성했습니다.
        """)
                
    # 7. 성과 트렌드 분석 영역 (Trend Charts)
    st.markdown("### 📈 실시간 성과 트렌드 분석  \n(Performance Trend Analysis)")
    
    # 시계열 차트를 위한 일별 데이터 집계
    daily_df = filtered_df.groupby('날짜').agg({
        '광고비용': 'sum',
        '노출수': 'sum',
        '클릭수': 'sum',
        '전환수': 'sum',
        '전환값': 'sum'
    }).reset_index()
    
    # 일별 파생 비율 계산
    daily_df['CTR'] = (daily_df['클릭수'] / daily_df['노출수'] * 100).fillna(0)
    daily_df['CPC'] = (daily_df['광고비용'] / daily_df['클릭수']).fillna(0)
    daily_df['CPA'] = (daily_df['광고비용'] / daily_df['전환수']).fillna(0)
    daily_df['ROAS'] = (daily_df['전환값'] / daily_df['광고비용'] * 100).fillna(0)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔹 일별 광고비용 vs 전환수 추이  \n(Spend vs Conversions)")
        # 이중 축 차트 구성 (바: 광고비용, 라인: 전환수)
        fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 광고비용 바 차트 (좌측 Y축)
        fig_trend.add_trace(
            qs.Bar(
                x=daily_df['날짜'], 
                y=daily_df['광고비용'], 
                name="광고비용 (Spend)",
                marker_color='#38BDF8',
                opacity=0.85
            ),
            secondary_y=False
        )
        
        # 전환수 라인 차트 (우측 Y축)
        fig_trend.add_trace(
            qs.Scatter(
                x=daily_df['날짜'], 
                y=daily_df['전환수'], 
                name="전환수 (Conversions)",
                mode='lines+markers',
                line=dict(color='#818CF8', width=3),
                marker=dict(size=6)
            ),
            secondary_y=True
        )
        
        fig_trend.update_layout(
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="광고비용 (₩)", showgrid=True, gridcolor='#334155'),
            yaxis2=dict(title="전환수 (건)", showgrid=False)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        
    with col2:
        st.markdown("#### 🔹 일별 ROAS 트렌드 추이  \n(Daily ROAS Trend)")
        
        fig_roas = qs.Figure()
        
        # ROAS 라인 차트
        fig_roas.add_trace(
            qs.Scatter(
                x=daily_df['날짜'], 
                y=daily_df['ROAS'], 
                name="일별 ROAS (%)",
                mode='lines+markers',
                line=dict(color='#10B981', width=3),
                marker=dict(size=6),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.1)'
            )
        )
        
        # 평균 ROAS 가이드라인선 추가
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
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False),
            yaxis=dict(title="ROAS (%)", showgrid=True, gridcolor='#334155')
        )
        st.plotly_chart(fig_roas, use_container_width=True)
        
    # 트렌드 분석 버튼 및 로직
    trend_btn_col, _ = st.columns([2, 8])
    with trend_btn_col:
        if st.button("🔍 추세 및 효율 진단", key="trend_analysis_btn"):
            st.session_state['show_trend_analysis'] = not st.session_state['show_trend_analysis']
            
    if st.session_state['show_trend_analysis']:
        unique_dates = sorted(filtered_df['날짜'].unique())
        n_dates = len(unique_dates)
        
        if n_dates < 2:
            st.info("💡 **[AE 진단] 추세 분석 결과**\n\n조회 기간이 너무 짧아(1일 이하) 추세 분석을 실행할 수 없습니다. 더 넓은 기간을 선택해 주세요.")
        else:
            # 14일 이상인 경우 최근 7일 vs 이전 7일, 미만인 경우 반으로 분할
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
                
    # 8. 매체 및 유형별 비중 분석 (Composition Analysis)
    st.markdown("---")
    st.markdown("### 📊 비중 및 성과 비교 분석  \n(Composition & Comparison)")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### 🔹 매체별 광고비 집행 비중  \n(Share of Voice by Media)")
        
        # 매체별 광고비 합계
        media_spend = filtered_df.groupby('매체')['광고비용'].sum().reset_index()
        
        fig_media = px.pie(
            media_spend, 
            values='광고비용', 
            names='매체',
            hole=0.45,
            color_discrete_sequence=['#4F46E5', '#10B981', '#F59E0B', '#06B6D4', '#F43F5E']
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
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False
        )
        st.plotly_chart(fig_media, use_container_width=True)
        
    with col4:
        st.markdown("#### 🔹 SA vs DA 성과 비교 분석  \n(SA vs DA Performance)")
        
        # SA/DA 비교 지표 선택 셀렉트박스
        metric_choice = st.selectbox(
            "비교할 지표를 선택해 주세요",
            options=["광고비용", "전환값", "ROAS", "전환수", "클릭수"],
            index=2, # 기본값: ROAS
            key="sada_metric_selector"
        )
        
        # SA/DA별 집계
        sada_group = filtered_df.groupby('SA/DA').agg({
            '광고비용': 'sum',
            '전환수': 'sum',
            '전환값': 'sum',
            '클릭수': 'sum'
        }).reset_index()
        
        sada_group['ROAS'] = (sada_group['전환값'] / sada_group['광고비용'] * 100).fillna(0)
        
        # 선택 지표에 따른 서식 및 레이블 매핑
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
                "SA": "#818CF8",
                "DA": "#F472B6",
                "미분류(기타)": "#94A3B8"
            }
        )
        
        # 막대 위 텍스트 서식 지정
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
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(title="광고 유형", showgrid=False),
            yaxis=dict(title=label_map[metric_choice], showgrid=True, gridcolor='#334155'),
            showlegend=False
        )
        st.plotly_chart(fig_sada, use_container_width=True)
        
    # 채널 분석 버튼 및 로직
    channel_btn_col, _ = st.columns([2, 8])
    with channel_btn_col:
        if st.button("📊 채널 믹스 인사이트", key="channel_analysis_btn"):
            st.session_state['show_channel_analysis'] = not st.session_state['show_channel_analysis']
            
    if st.session_state['show_channel_analysis']:
        # 매체별 광고비 및 ROAS 집계
        media_metrics = filtered_df.groupby('매체').agg({
            '광고비용': 'sum',
            '전환값': 'sum'
        }).reset_index()
        
        media_metrics['ROAS'] = (media_metrics['전환값'] / media_metrics['광고비용'] * 100).fillna(0)
        
        # 1. 광고비 비중이 가장 높은 매체 찾기
        total_med_spend = media_metrics['광고비용'].sum()
        if total_med_spend > 0:
            media_metrics['비중'] = (media_metrics['광고비용'] / total_med_spend * 100)
            max_spend_row = media_metrics.loc[media_metrics['광고비용'].idxmax()]
            max_spend_media = max_spend_row['매체']
            max_spend_share = max_spend_row['비중']
        else:
            max_spend_media = "N/A"
            max_spend_share = 0.0
            
        # 2. 효율(ROAS)이 가장 우수한 매체 찾기
        if not media_metrics.empty:
            max_roas_row = media_metrics.loc[media_metrics['ROAS'].idxmax()]
            max_roas_media = max_roas_row['매체']
            max_roas_val = max_roas_row['ROAS']
        else:
            max_roas_media = "N/A"
            max_roas_val = 0.0
            
        st.info(f"""
        💡 **[AE 진단] 채널 믹스 분석 결과**
        - 현재 **{max_spend_media}** 매체의 광고비 비중이 **{max_spend_share:.1f}%**로 가장 높지만, 효율(ROAS) 측면에서는 **{max_roas_media}** 매체(**{max_roas_val:.1f}%**)가 가장 우수합니다.
        - 효율이 우수한 **{max_roas_media}** 매체의 예산 집행 비율을 추가 조정하여 전체 캠페인의 믹스 효율(종합 ROAS)을 극대화하는 리밸런싱 전략을 제안합니다.
        """)
                
    # 9. 상세 데이터 테이블 (Detailed View)
    st.markdown("---")
    st.markdown("### 📋 성과 상세 데이터  \n(Detailed Performance Log)")
    
    # 다운로드 및 정렬용 정밀 필터링 테이블
    table_display_df = filtered_df.copy()
    
    # 보기 좋게 컬럼 순서 및 포맷 가시성 향상
    table_display_df['날짜'] = table_display_df['날짜'].dt.strftime('%Y-%m-%d')
    table_display_df['ROAS(%)'] = table_display_df['ROAS'].round(2)
    table_display_df['CTR(%)'] = table_display_df['CTR'].round(4)
    table_display_df['CPA'] = table_display_df['CPA'].astype(int)
    table_display_df['CPC'] = table_display_df['CPC'].astype(int)
    
    # 테이블 뷰용 컬럼 정렬 및 선택
    table_display_df = table_display_df[[
        '날짜', '매체', 'SA/DA', '노출수', '클릭수', '광고비용', 'CTR(%)', 'CPC', '전환수', '전환값', 'ROAS(%)', 'CPA'
    ]]
    
    # 다운로드 버튼 추가
    csv_data = table_display_df.to_csv(index=False, encoding='utf-8-sig') # 엑셀 한글 깨짐 방지 utf-8-sig
    st.download_button(
        label="📥 필터링된 데이터 다운로드 (CSV)",
        data=csv_data,
        file_name=f"marketing_performance_{start_date}_to_{end_date}.csv",
        mime="text/csv"
    )
    
    # 데이터프레임 표시
    st.dataframe(
        table_display_df,
        use_container_width=True,
        hide_index=True
    )
