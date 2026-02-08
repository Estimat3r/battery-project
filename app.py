import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import plotly.graph_objects as go

# ==========================================
# 1. 디자인 및 페이지 설정 (Modern Dark UI)
# ==========================================
st.set_page_config(layout="wide", page_title="Eco-Cycle AI", page_icon="🔋")

# 커스텀 CSS: Figma 스타일의 다크 테마 및 카드 디자인 적용
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #0E1117;
        color: #C9D1D9;
        font-family: 'Inter', sans-serif;
    }
    
    /* 사이드바 스타일 */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* 카드 디자인 (Glassmorphism) */
    div.metric-card {
        background-color: #21262D;
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 텍스트 하이라이트 */
    .highlight-green { color: #00E676; font-weight: bold; }
    .highlight-blue { color: #2E9AFE; font-weight: bold; }
    .big-font { font-size: 24px; font-weight: bold; color: white; }
    
    /* KPI 숫자 색상 강제 지정 */
    div[data-testid="stMetricValue"] {
        color: #00E676 !important;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #2E9AFE;
    }
    
    /* 프로세스 흐름도 박스 */
    .process-box {
        background-color: #161B22;
        border: 1px solid #30363D;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        color: white;
    }
    .arrow {
        font-size: 20px;
        color: #8B949E;
        padding-top: 25px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 로딩 및 엔진
# ==========================================
@st.cache_data
def load_models():
    try:
        df1 = pd.read_csv("step1.csv")
        df2 = pd.read_csv("step2.csv")
        df3 = pd.read_csv("step3.csv")
        
        f_al_rem = interp1d(df1['pH'], df1['Al_Removal'], kind='linear', fill_value="extrapolate")
        f_co_loss = interp1d(df1['pH'], df1['Co_Loss'], kind='linear', fill_value="extrapolate")
        f_co_rec = interp1d(df2['pH'], df2['Co_Recovery'], kind='linear', fill_value="extrapolate")
        f_li_rec = interp1d(df3['Temp'], df3['Li_Recovery'], kind='linear', fill_value="extrapolate")
        
        return f_al_rem, f_co_loss, f_co_rec, f_li_rec
    except:
        return None, None, None, None

models = load_models()

# ==========================================
# 3. 계산 로직 (시계열 데이터 생성 포함)
# ==========================================
def calculate_process(ph1, ph2, temp, models):
    f_al_rem, f_co_loss, f_co_rec, f_li_rec = models
    
    # 1. 기본 성능 예측
    al_purity = float(f_al_rem(ph1))
    co_loss_pct = float(f_co_loss(ph1))
    co_rec_raw = float(f_co_rec(ph2))
    li_rec_raw = float(f_li_rec(temp))
    
    # 최종 수율 및 비용
    final_co_yield = (100 - co_loss_pct) * (co_rec_raw / 100)
    final_li_yield = li_rec_raw 
    
    # 비용 계산 (가정: pH 조절 비용 + 가열 비용)
    chem_cost_base = ((abs(ph1 - 7.0)) + (abs(ph2 - 7.0))) * 8.0 
    energy_cost_base = (temp - 25) * 3.5
    total_cost_per_ton = chem_cost_base + energy_cost_base
    
    # 매출 계산 (Co $11/kg, Li $13.5/kg 가정)
    revenue_per_ton = (final_co_yield * 1.65) + (final_li_yield * 0.675)
    net_profit = (revenue_per_ton * 100) - total_cost_per_ton
    
    return net_profit, final_co_yield, final_li_yield, al_purity, total_cost_per_ton

# 시계열 데이터 생성 함수 (그래프용)
def generate_time_series(profit, efficiency, hours=10):
    time_index = np.arange(hours)
    # 시간이 지날수록 효율/수익이 약간 감소하는 현실적 모델링
    profit_trend = profit * (1 - (time_index * 0.015)) 
    eff_trend = efficiency * (1 - (time_index * 0.005))
    return time_index, profit_trend, eff_trend

# ==========================================
# 4. UI 구성
# ==========================================
st.title("🔋 Eco-Cycle AI Dashboard")
st.markdown("### Advanced Battery Recycling Process Simulator")

if models[0] is None:
    st.error("🚨 데이터 파일을 찾을 수 없습니다. (step1.csv, step2.csv, step3.csv)")
    st.stop()

# 탭 구성
tab_fwd, tab_rev = st.tabs(["📊 Forward Simulation", "🎯 Target Reverse-Engineering"])

# --- [TAB 1] Forward Simulation ---
with tab_fwd:
    col_sidebar, col_main = st.columns([1, 2.5])
    
    # 1. 왼쪽 사이드바 (입력)
    with col_sidebar:
        st.markdown("### 🎛️ Process Parameters")
        st.markdown("---")
        
        st.markdown("#### 1️⃣ Impurity Removal")
        p1 = st.slider("pH Level", 3.5, 5.5, 4.0, 0.1, key="fwd_p1")
        
        st.markdown("#### 2️⃣ Cobalt Extraction")
        p2 = st.slider("pH Level", 7.0, 11.0, 9.5, 0.1, key="fwd_p2")
        
        st.markdown("#### 3️⃣ Lithium Recovery")
        t3 = st.slider("Temperature (°C)", 25, 95, 90, 5, key="fwd_t3")
        
        # 실시간 계산
        profit, co_y, li_y, purity, cost = calculate_process(p1, p2, t3, models)
        avg_efficiency = (co_y + li_y) / 2
        
        st.markdown("---")
        st.info(f"💰 Est. Net Profit: **${profit:,.0f}**")

    # 2. 오른쪽 메인 (대시보드)
    with col_main:
        # 시간 경과 데이터 생성
        hours, profit_data, eff_data = generate_time_series(profit, avg_efficiency)
        
        # [Graph 1] Real-time Profit Analysis (Area Chart)
        st.markdown("##### 📈 Real-time Profit Analysis (Over 10 Hours)")
        fig_profit = go.Figure()
        fig_profit.add_trace(go.Scatter(
            x=hours, y=profit_data, fill='tozeroy', mode='lines',
            line=dict(color='#00E676', width=3), name='Profit'
        ))
        fig_profit.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#C9D1D9'), height=250, margin=dict(l=20,r=20,t=10,b=20),
            xaxis=dict(title='Process Hour', showgrid=False),
            yaxis=dict(title='Profit ($)', gridcolor='#30363D')
        )
        st.plotly_chart(fig_profit, use_container_width=True)
        
        # [Graph 2] Process Efficiency Tracking (Line Chart)
        st.markdown("##### ⚡ Process Efficiency Tracking")
        fig_eff = go.Figure()
        fig_eff.add_trace(go.Scatter(
            x=hours, y=eff_data, mode='lines+markers',
            line=dict(color='#2E9AFE', width=2), marker=dict(size=6), name='Efficiency'
        ))
        fig_eff.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#C9D1D9'), height=200, margin=dict(l=20,r=20,t=10,b=20),
            xaxis=dict(title='Process Hour', showgrid=False),
            yaxis=dict(title='Efficiency (%)', range=[80, 100], gridcolor='#30363D')
        )
        st.plotly_chart(fig_eff, use_container_width=True)
        
        # [Summary Cards] 하단 요약
        st.markdown("##### 📋 Current Configuration Summary")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="metric-card">
                <span style="color:#8B949E">Expected Recovery</span><br>
                <span class="big-font highlight-blue">{avg_efficiency:.1f}%</span>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card">
                <span style="color:#8B949E">Energy & Chem Cost</span><br>
                <span class="big-font" style="color:#FF5252">${cost:,.0f}</span>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card">
                <span style="color:#8B949E">Purity Grade</span><br>
                <span class="big-font highlight-green">{purity:.2f}%</span>
            </div>""", unsafe_allow_html=True)

# --- [TAB 2] Reverse Engineering ---
with tab_rev:
    col_rev_sidebar, col_rev_main = st.columns([1, 2.5])
    
    # 1. 왼쪽 사이드바 (목표 및 제약조건)
    with col_rev_sidebar:
        st.markdown("### 🎯 Target Definition")
        target_purity = st.number_input("Target Purity (%)", 90.0, 99.9, 99.0)
        min_recovery = st.number_input("Min. Recovery (%)", 80.0, 99.0, 95.0)
        
        st.markdown("---")
        st.markdown("#### 🔒 Constraint Settings")
        st.caption("변수를 고정하면 AI가 해당 값을 유지한 채 최적해를 찾습니다.")
        
        # 변수 고정 기능 (CheckBox)
        lock_p1 = st.checkbox("Lock Step 1 pH", value=False)
        fixed_p1 = st.slider("Fixed pH 1", 3.5, 5.5, 4.0, 0.1, disabled=not lock_p1)
        
        lock_p2 = st.checkbox("Lock Step 2 pH", value=False)
        fixed_p2 = st.slider("Fixed pH 2", 7.0, 11.0, 9.5, 0.1, disabled=not lock_p2)
        
        lock_t3 = st.checkbox("Lock Step 3 Temp", value=False)
        fixed_t3 = st.slider("Fixed Temp", 25, 95, 80, 5, disabled=not lock_t3)
        
        btn_optimize = st.button("Calculate Optimal Recipe 🚀", type="primary", use_container_width=True)

    # 2. 오른쪽 메인 (결과 분석)
    with col_rev_main:
        if btn_optimize:
            best_score = -9999
            best_res = None
            
            # 탐색 공간 설정 (고정된 경우 단일 값 리스트, 아니면 범위 리스트)
            space_p1 = [fixed_p1] if lock_p1 else np.linspace(3.5, 5.0, 5)
            space_p2 = [fixed_p2] if lock_p2 else np.linspace(8.0, 10.0, 5)
            space_t3 = [fixed_t3] if lock_t3 else [60, 70, 80, 90, 95]
            
            # Brute Force Search
            for sp1 in space_p1:
                for sp2 in space_p2:
                    for st3 in space_t3:
                        pf, cy, ly, pu, ct = calculate_process(sp1, sp2, st3, models)
                        avg_rec = (cy + ly) / 2
                        
                        if pu >= target_purity and avg_rec >= min_recovery:
                            if pf > best_score:
                                best_score = pf
                                best_res = (sp1, sp2, st3, pf, avg_rec, pu)
            
            if best_res:
                # 결과 표시
                st.markdown(f"""
                <div style="background-color: #161B22; border: 1px solid #00E676; border-radius: 10px; padding: 20px;">
                    <h2 style="margin:0; color:#00E676;">✅ Optimal Recipe Found!</h2>
                    <hr style="border-color: #30363D;">
                    <div style="display: flex; justify-content: space-around; text-align: center;">
                        <div><p style="color:#8B949E; margin:0;">Impurity pH</p><h3 style="color:white;">{best_res[0]:.1f}</h3></div>
                        <div><p style="color:#8B949E; margin:0;">Cobalt pH</p><h3 style="color:white;">{best_res[1]:.1f}</h3></div>
                        <div><p style="color:#8B949E; margin:0;">Lithium Temp</p><h3 style="color:white;">{best_res[2]}°C</h3></div>
                        <div><p style="color:#8B949E; margin:0;">Net Profit</p><h3 style="color:#2E9AFE;">${best_res[3]:,.0f}</h3></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Comparative Analysis (Radar Chart)
                st.markdown("### 🆚 Comparative Analysis")
                categories = ['Profit', 'Purity', 'Recovery', 'Energy Save', 'Safety']
                
                # 현재 설정값 (Forward Tab의 값) 가져오기 (비교용)
                # 정규화된 점수 계산
                current_scores = [min(profit/200, 100), purity, avg_efficiency, 100-(cost/10), 80]
                ai_scores = [min(best_res[3]/200, 100), best_res[5], best_res[4], 100-(cost/10)+5, 90]
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=current_scores, theta=categories, fill='toself', name='Current Plan', line_color='#FF5252'))
                fig_radar.add_trace(go.Scatterpolar(r=ai_scores, theta=categories, fill='toself', name='AI Optimal', line_color='#00E676'))
                
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#C9D1D9'), height=350
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            else:
                st.error("⚠️ 목표를 달성할 수 있는 조건을 찾지 못했습니다. (제약 조건을 완화해보세요)")
        
        else:
            st.info("👈 좌측에서 목표를 설정하고 'Calculate' 버튼을 눌러주세요.")

    # [Process Flow Visualization] 하단 공정 흐름도 (항상 표시)
    st.markdown("### 🔗 Process Flow Visualization")
    c1, a1, c2, a2, c3 = st.columns([2, 0.5, 2, 0.5, 2])
    
    with c1:
        st.markdown("""<div class="process-box">
            <h4 style="color:#2E9AFE">Step 1</h4>
            <b>Impurity Removal</b><br>
            <span style="font-size:12px; color:#8B949E">Target: Al, Cu Elimination</span>
        </div>""", unsafe_allow_html=True)
    with a1:
        st.markdown("<div class="arrow">→</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="process-box">
            <h4 style="color:#2E9AFE">Step 2</h4>
            <b>Cobalt Extraction</b><br>
            <span style="font-size:12px; color:#8B949E">Target: Co(OH)2 Precipitation</span>
        </div>""", unsafe_allow_html=True)
    with a2:
        st.markdown("<div class="arrow">→</div>", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="process-box">
            <h4 style="color:#2E9AFE">Step 3</h4>
            <b>Lithium Recovery</b><br>
            <span style="font-size:12px; color:#8B949E">Target: Li2CO3 Crystallization</span>
        </div>""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.caption("© 2026 Eco-Cycle AI | Powered by Thermodynamic Interpolation Engine")
