import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import plotly.graph_objects as go

# ==========================================
# 1. 다국어 사전 (Translation Dictionary)
# ==========================================
TRANSLATIONS = {
    'ko': {
        'title': "🔋 Eco-Cycle AI 대시보드",
        'subtitle': "폐배터리 블랙매스 하이브리드 정제 공정 시뮬레이터",
        'sidebar_title': "🎛️ 공정 제어 (Process Control)",
        'tab1': "📊 공정 시뮬레이션 (Forward)",
        'tab2': "🎯 목표 역설계 (Reverse)",
        'step1_label': "1단계: 불순물 제거 (Impurity Removal)",
        'step1_help': "불순물(Al, Cu)을 침전시키기 위한 산성 구간입니다. pH가 너무 높으면 코발트까지 손실될 수 있습니다.",
        'step1_caption': "💡 목표: 알루미늄/구리 제거 (권장 pH 4.0~5.0)",
        'step2_label': "2단계: 코발트 회수 (Cobalt Extraction)",
        'step2_help': "여과된 용액에서 코발트를 수산화물로 회수하는 염기성 구간입니다. pH가 낮으면 회수율이 떨어집니다.",
        'step2_caption': "💡 목표: 수산화코발트 회수 (권장 pH 9.0~10.0)",
        'step3_label': "3단계: 리튬 회수 (Lithium Recovery)",
        'step3_help': "온도가 높을수록 탄산리튬의 용해도가 낮아져 결정화가 잘 됩니다.",
        'step3_caption': "💡 목표: 탄산리튬 결정화 (권장 온도 80°C+)",
        'result_profit': "예상 순수익",
        'result_yield': "종합 회수율",
        'result_purity': "불순물 제거율",
        'graph_profit': "📈 실시간 수익 분석 (10시간 공정)",
        'graph_eff': "⚡ 공정 효율 추적",
        'summary_header': "📋 현재 설정 요약",
        'summary_rec': "예상 회수량",
        'summary_cost': "에너지 & 약품비",
        'summary_grade': "순도 등급",
        'rev_target_title': "🎯 목표 설정",
        'rev_purity': "목표 순도 (%)",
        'rev_yield': "최소 회수율 (%)",
        'rev_lock_title': "🔒 제약 조건 (변수 고정)",
        'rev_btn': "최적 레시피 찾기 🚀",
        'rev_success': "✅ 목표 달성 가능한 레시피를 찾았습니다!",
        'rev_fail': "⚠️ 해당 목표를 만족하는 조건을 찾지 못했습니다.",
        'rev_chart_title': "🆚 비교 분석 (현재 vs AI 추천)",
        'flow_title': "🔗 공정 흐름도 (Process Flow)",
        'flow_s1': "불순물 제거",
        'flow_s2': "코발트 추출",
        'flow_s3': "리튬 회수",
        'guide_title': "📘 시뮬레이터 사용 가이드",
        'guide_desc': """
        **1. 공정 시뮬레이션 (Forward):** 왼쪽 사이드바에서 pH와 온도를 조절하여 실시간 수익성을 예측하세요.
        **2. 목표 역설계 (Reverse):** 원하는 순도와 회수율을 입력하면 AI가 최적의 조건을 찾아줍니다.
        **3. 순도 페널티:** 순도가 낮을수록 등급(Battery/Technical/Crude/Scrap)에 따라 판매 가격이 차등 적용됩니다.
        """
    },
    'en': {
        'title': "🔋 Eco-Cycle AI Dashboard",
        'subtitle': "Advanced Battery Recycling Process Simulator",
        'sidebar_title': "🎛️ Process Parameters",
        'tab1': "📊 Forward Simulation",
        'tab2': "🎯 Target Reverse-Engineering",
        'step1_label': "Step 1: Impurity Removal",
        'step1_help': "Acidic range to precipitate impurities (Al, Cu). Higher pH may cause Cobalt loss.",
        'step1_caption': "💡 Target: Remove Al/Cu (Rec. pH 4.0~5.0)",
        'step2_label': "Step 2: Cobalt Extraction",
        'step2_help': "Basic range to recover Cobalt hydroxide. Low pH reduces recovery rate.",
        'step2_caption': "💡 Target: Recover Co(OH)2 (Rec. pH 9.0~10.0)",
        'step3_label': "Step 3: Lithium Recovery",
        'step3_help': "Higher temperature reduces Li2CO3 solubility, enhancing crystallization.",
        'step3_caption': "💡 Target: Li2CO3 Crystallization (Rec. Temp 80°C+)",
        'result_profit': "Est. Net Profit",
        'result_yield': "Avg. Recovery",
        'result_purity': "Purity Grade",
        'graph_profit': "📈 Real-time Profit Analysis (10h)",
        'graph_eff': "⚡ Process Efficiency Tracking",
        'summary_header': "📋 Current Configuration Summary",
        'summary_rec': "Exp. Recovery",
        'summary_cost': "Energy & Chem Cost",
        'summary_grade': "Purity Grade",
        'rev_target_title': "🎯 Target Definition",
        'rev_purity': "Target Purity (%)",
        'rev_yield': "Min. Recovery (%)",
        'rev_lock_title': "🔒 Constraint Settings",
        'rev_btn': "Calculate Optimal Recipe 🚀",
        'rev_success': "✅ Optimal Recipe Found!",
        'rev_fail': "⚠️ No conditions found meeting the targets.",
        'rev_chart_title': "🆚 Comparative Analysis (Current vs AI)",
        'flow_title': "🔗 Process Flow Visualization",
        'flow_s1': "Impurity Removal",
        'flow_s2': "Cobalt Extraction",
        'flow_s3': "Lithium Recovery",
        'guide_title': "📘 User Guide",
        'guide_desc': """
        **1. Forward Simulation:** Adjust pH & Temp in the sidebar to predict real-time profitability.
        **2. Reverse Engineering:** Set your target purity & yield, and let AI find the best recipe.
        **3. Purity Penalty:** Sales price is adjusted based on purity grade (Battery/Technical/Crude/Scrap).
        """
    }
}

# ==========================================
# 2. 디자인 및 페이지 설정
# ==========================================
st.set_page_config(layout="wide", page_title="Eco-Cycle AI", page_icon="🔋")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #C9D1D9; font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    div.metric-card { background-color: #21262D; border: 1px solid #30363D; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .highlight-green { color: #00E676; font-weight: bold; }
    .highlight-blue { color: #2E9AFE; font-weight: bold; }
    .big-font { font-size: 24px; font-weight: bold; color: white; }
    div[data-testid="stMetricValue"] { color: #00E676 !important; }
    .process-box { background-color: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 15px; text-align: center; color: white; }
    .arrow { font-size: 20px; color: #8B949E; padding-top: 25px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 데이터 로딩 & 계산 엔진 (로직 업그레이드)
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

def calculate_process(ph1, ph2, temp, models):
    f_al_rem, f_co_loss, f_co_rec, f_li_rec = models
    
    # 1. 공정 효율 예측
    al_purity = float(f_al_rem(ph1))        # 불순물 제거율 (순도 지표)
    co_loss_pct = float(f_co_loss(ph1))     # 코발트 손실률
    co_rec_raw = float(f_co_rec(ph2))       # 코발트 회수율
    li_rec_raw = float(f_li_rec(temp))      # 리튬 회수율
    
    # 2. 최종 수율 계산
    final_co_yield = (100 - co_loss_pct) * (co_rec_raw / 100)
    final_li_yield = li_rec_raw 
    
    # 3. 운영 비용 (OPEX)
    chem_cost = ((abs(ph1 - 7.0)) + (abs(ph2 - 7.0))) * 8.0 
    energy_cost = (temp - 25) * 3.5
    total_cost = chem_cost + energy_cost
    
    # [핵심 수정] 4. 등급별 차등 가격 정책 (Tiered Pricing Model)
    # 현실 반영: 순도가 60~70%여도 '중간재(Intermediate)'로서 가치는 인정받음.
    
    if al_purity >= 99.0:
        quality_factor = 1.0    # [Battery Grade] 제값 받음
    elif al_purity >= 85.0:
        quality_factor = 0.85   # [Technical Grade] 15% 감가 (정제비)
    elif al_purity >= 60.0:
        quality_factor = 0.50   # [Crude Intermediate] 50% 감가 (재처리 필요)
    else:
        quality_factor = 0.20   # [Scrap/Waste] 80% 감가 (폐기물 수준)
        
    # 매출 계산 (품질 계수 적용)
    # Co: $11,000, Li: $13,500
    revenue = (final_co_yield * 1.65 * quality_factor) + (final_li_yield * 0.675 * quality_factor)
    
    # 순이익
    net_profit = (revenue * 100) - total_cost
    
    return net_profit, final_co_yield, final_li_yield, al_purity, total_cost

def generate_time_series(profit, efficiency, hours=10):
    time_index = np.arange(hours)
    profit_trend = profit * (1 - (time_index * 0.015)) 
    eff_trend = efficiency * (1 - (time_index * 0.005))
    return time_index, profit_trend, eff_trend

# ==========================================
# 4. UI 구성
# ==========================================
lang_choice = st.sidebar.radio("🌐 Language / 언어", ["한국어", "English"])
lang = 'ko' if lang_choice == "한국어" else 'en'
t = TRANSLATIONS[lang]

st.title(t['title'])
st.caption(t['subtitle'])

with st.expander(t['guide_title']):
    st.markdown(t['guide_desc'])

if models[0] is None:
    st.error("🚨 Data files not found (CSV).")
    st.stop()

tab_fwd, tab_rev = st.tabs([t['tab1'], t['tab2']])

# [TAB 1] Forward Simulation
with tab_fwd:
    col_sidebar, col_main = st.columns([1, 2.5])
    
    with col_sidebar:
        st.markdown(f"### {t['sidebar_title']}")
        st.markdown("---")
        
        st.markdown(f"#### {t['step1_label']}")
        p1 = st.slider("pH Level (Step 1)", 3.5, 5.5, 4.0, 0.1, key="fwd_p1", help=t['step1_help'])
        st.caption(t['step1_caption'])
        
        st.markdown(f"#### {t['step2_label']}")
        p2 = st.slider("pH Level (Step 2)", 7.0, 11.0, 9.5, 0.1, key="fwd_p2", help=t['step2_help'])
        st.caption(t['step2_caption'])
        
        st.markdown(f"#### {t['step3_label']}")
        t3 = st.slider("Temperature (°C)", 25, 95, 90, 5, key="fwd_t3", help=t['step3_help'])
        st.caption(t['step3_caption'])
        
        profit, co_y, li_y, purity, cost = calculate_process(p1, p2, t3, models)
        avg_eff = (co_y + li_y) / 2
        
        st.markdown("---")
        
        # 순도에 따른 경고 메시지 표시
        if purity < 60.0:
            st.error("⚠️ Low Purity: Product downgraded to Scrap (20% value).")
        elif purity < 85.0:
            st.warning("⚠️ Medium Purity: Crude Intermediate (50% value).")
        
        st.info(f"💰 {t['result_profit']}: **${profit:,.0f}**")

    with col_main:
        hours, profit_data, eff_data = generate_time_series(profit, avg_eff)
        
        st.markdown(f"##### {t['graph_profit']}")
        fig_profit = go.Figure()
        fig_profit.add_trace(go.Scatter(x=hours, y=profit_data, fill='tozeroy', mode='lines', line=dict(color='#00E676', width=3)))
        fig_profit.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#C9D1D9'), height=250, margin=dict(l=20,r=20,t=10,b=20))
        st.plotly_chart(fig_profit, use_container_width=True)
        
        st.markdown(f"##### {t['graph_eff']}")
        fig_eff = go.Figure()
        fig_eff.add_trace(go.Scatter(x=hours, y=eff_data, mode='lines+markers', line=dict(color='#2E9AFE', width=2)))
        fig_eff.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#C9D1D9'), height=200, margin=dict(l=20,r=20,t=10,b=20), yaxis=dict(range=[0, 105]))
        st.plotly_chart(fig_eff, use_container_width=True)
        
        st.markdown(f"##### {t['summary_header']}")
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"""<div class="metric-card"><span style="color:#8B949E">{t['summary_rec']}</span><br><span class="big-font highlight-blue">{avg_eff:.1f}%</span></div>""", unsafe_allow_html=True)
        with c2: st.markdown(f"""<div class="metric-card"><span style="color:#8B949E">{t['summary_cost']}</span><br><span class="big-font" style="color:#FF5252">${cost:,.0f}</span></div>""", unsafe_allow_html=True)
        
        # 순도 색상 동적 변경
        purity_color = "#00E676" if purity >= 90 else "#FF5252"
        with c3: st.markdown(f"""<div class="metric-card"><span style="color:#8B949E">{t['summary_grade']}</span><br><span class="big-font" style="color:{purity_color}">{purity:.2f}%</span></div>""", unsafe_allow_html=True)

# [TAB 2] Reverse Engineering
with tab_rev:
    col_rev_sidebar, col_rev_main = st.columns([1, 2.5])
    
    with col_rev_sidebar:
        st.markdown(f"### {t['rev_target_title']}")
        target_purity = st.number_input(t['rev_purity'], 90.0, 99.9, 99.0)
        min_recovery = st.number_input(t['rev_yield'], 80.0, 99.0, 95.0)
        
        st.markdown("---")
        st.markdown(f"#### {t['rev_lock_title']}")
        
        lock_p1 = st.checkbox("Lock Step 1 pH", value=False)
        fixed_p1 = st.slider("Fixed pH 1", 3.5, 5.5, 4.0, 0.1, disabled=not lock_p1)
        
        lock_p2 = st.checkbox("Lock Step 2 pH", value=False)
        fixed_p2 = st.slider("Fixed pH 2", 7.0, 11.0, 9.5, 0.1, disabled=not lock_p2)
        
        lock_t3 = st.checkbox("Lock Step 3 Temp", value=False)
        fixed_t3 = st.slider("Fixed Temp", 25, 95, 80, 5, disabled=not lock_t3)
        
        btn_optimize = st.button(t['rev_btn'], type="primary", use_container_width=True)

    with col_rev_main:
        if btn_optimize:
            best_score = -9999
            best_res = None
            
            # [AI 탐색 정밀도 향상]
            space_p1 = [fixed_p1] if lock_p1 else np.linspace(3.5, 5.5, 10)
            space_p2 = [fixed_p2] if lock_p2 else np.linspace(7.0, 11.0, 10)
            space_t3 = [fixed_t3] if lock_t3 else [25, 40, 60, 80, 90, 95]
            
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
                st.markdown(f"""<div style="background-color: #161B22; border: 1px solid #00E676; border-radius: 10px; padding: 20px;"><h2 style="color:#00E676;">{t['rev_success']}</h2><hr style="border-color: #30363D;"><div style="display: flex; justify-content: space-around;"><div><p style="color:#8B949E; margin:0;">Impurity pH</p><h3 style="color:white;">{best_res[0]:.2f}</h3></div><div><p style="color:#8B949E; margin:0;">Cobalt pH</p><h3 style="color:white;">{best_res[1]:.2f}</h3></div><div><p style="color:#8B949E; margin:0;">Lithium Temp</p><h3 style="color:white;">{best_res[2]}°C</h3></div><div><p style="color:#8B949E; margin:0;">Profit</p><h3 style="color:#2E9AFE;">${best_res[3]:,.0f}</h3></div></div></div>""", unsafe_allow_html=True)
                
                # Comparative Analysis
                st.markdown(f"### {t['rev_chart_title']}")
                categories = ['Profit', 'Purity', 'Recovery', 'Energy Save', 'Safety']
                
                curr_profit, curr_co, curr_li, curr_pur, curr_cost = calculate_process(p1, p2, t3, models)
                curr_avg_rec = (curr_co + curr_li) / 2
                
                def normalize(val, max_val): return max(0, min(val/max_val*100, 100))
                
                current_scores = [normalize(curr_profit, 20000), curr_pur, curr_avg_rec, normalize(1000-curr_cost, 1000), 80]
                ai_scores = [normalize(best_res[3], 20000), best_res[5], best_res[4], normalize(1000-(best_res[3]/200), 1000), 95]
                
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=current_scores, theta=categories, fill='toself', name='Current Plan (Tab 1)', line_color='#FF5252'))
                fig_radar.add_trace(go.Scatterpolar(r=ai_scores, theta=categories, fill='toself', name='AI Optimal Plan', line_color='#00E676'))
                
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#C9D1D9'), height=350)
                st.plotly_chart(fig_radar, use_container_width=True)

            else:
                st.error(t['rev_fail'])
        else:
            st.info(f"👈 {t['rev_btn']}")

    st.markdown(f"### {t['flow_title']}")
    c1, a1, c2, a2, c3 = st.columns([2, 0.5, 2, 0.5, 2])
    with c1: st.markdown(f"""<div class="process-box"><h4 style="color:#2E9AFE">Step 1</h4><b>{t['flow_s1']}</b></div>""", unsafe_allow_html=True)
    with a1: st.markdown('<div class="arrow">→</div>', unsafe_allow_html=True)
    with c2: st.markdown(f"""<div class="process-box"><h4 style="color:#2E9AFE">Step 2</h4><b>{t['flow_s2']}</b></div>""", unsafe_allow_html=True)
    with a2: st.markdown('<div class="arrow">→</div>', unsafe_allow_html=True)
    with c3: st.markdown(f"""<div class="process-box"><h4 style="color:#2E9AFE">Step 3</h4><b>{t['flow_s3']}</b></div>""", unsafe_allow_html=True)

st.markdown("---")
st.caption("© 2026 Eco-Cycle AI")
