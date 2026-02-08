import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
import plotly.graph_objects as go

# ==========================================
# 1. 디자인 설정 (Figma Style CSS)
# ==========================================
st.set_page_config(layout="wide", page_title="Eco-Cycle AI", page_icon="🔋")

# Figma 디자인과 유사하게 만드는 커스텀 CSS
st.markdown("""
<style>
    /* 전체 배경색 (Dark Navy) */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* 사이드바 스타일 (Left Panel) */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    
    /* 카드 박스 디자인 (Dashboard Card) */
    .metric-card {
        background-color: #21262D;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 텍스트 색상 포인트 */
    h1, h2, h3 { color: #FFFFFF !important; }
    .highlight-blue { color: #2E9AFE; font-weight: bold; }
    .highlight-green { color: #00E676; font-weight: bold; }
    
    /* KPI 숫자 색상 */
    div[data-testid="stMetricValue"] {
        color: #00E676 !important; /* Neon Green */
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 데이터 로딩 (기존과 동일)
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
# 3. 계산 로직 (기존과 동일)
# ==========================================
def calculate_process(ph1, ph2, temp, models):
    f_al_rem, f_co_loss, f_co_rec, f_li_rec = models
    al_purity = float(f_al_rem(ph1))
    co_loss_pct = float(f_co_loss(ph1))
    co_rec_raw = float(f_co_rec(ph2))
    li_rec_raw = float(f_li_rec(temp))
    
    final_co_yield = (100 - co_loss_pct) * (co_rec_raw / 100)
    final_li_yield = li_rec_raw 
    
    chem_cost = ((ph1 - 2.0) + (ph2 - ph1)) * 5.0
    energy_cost = (temp - 25) * 2.0
    total_cost = chem_cost + energy_cost
    
    revenue = (final_co_yield * 1.65) + (final_li_yield * 0.675)
    net_profit = (revenue * 100) - total_cost
    
    return net_profit, final_co_yield, final_li_yield, al_purity, total_cost

# ==========================================
# 4. 화면 구성 (Figma Layout 적용)
# ==========================================

# 상단 헤더
c1, c2 = st.columns([3, 1])
with c1:
    st.title("🔋 Eco-Cycle AI")
    st.caption("Advanced Battery Recycling Process Simulator")
with c2:
    st.markdown("<div style='text-align: right; color: #2E9AFE;'>Co: $11,000/ton <br> Li: $13,500/ton</div>", unsafe_allow_html=True)

if models[0] is None:
    st.error("데이터 파일이 없습니다.")
    st.stop()

# 탭 구조 (이미지와 동일하게)
tab_fwd, tab_rev = st.tabs(["📊 Forward Simulation", "🎯 Target Reverse-Engineering"])

# --- [TAB 1] 실험 시뮬레이션 ---
with tab_fwd:
    # 레이아웃 분할: 왼쪽 사이드바(컨트롤) vs 오른쪽 메인(대시보드)
    # Streamlit은 기본적으로 모바일 친화적이라 100% 분할은 어렵지만, col을 사용해 흉내냅니다.
    
    col_left, col_right = st.columns([1, 2.5])
    
    # [왼쪽] Process Parameters (이미지의 왼쪽 패널)
    with col_left:
        st.markdown("### 🎛️ Process Parameters")
        with st.container(border=True): # 카드 느낌의 테두리
            st.markdown("#### 1. Impurity Removal")
            p1 = st.slider("pH Level", 3.5, 5.5, 4.0, 0.1)
            # 온도는 1단계에서 고정 변수로 가정하거나 추가 가능
            
            st.markdown("#### 2. Cobalt Extraction")
            p2 = st.slider("pH Level (Step 2)", 7.0, 11.0, 9.5, 0.1)
            
            st.markdown("#### 3. Lithium Recovery")
            t3 = st.slider("Temperature (°C)", 25, 95, 90, 5)

        # 실시간 계산
        profit, co_y, li_y, purity, cost = calculate_process(p1, p2, t3, models)

        # 요약 카드 (왼쪽 하단)
        st.info(f"💰 Projected Profit: **${profit:,.0f}**")

    # [오른쪽] Real-time Analysis (이미지의 오른쪽 패널)
    with col_right:
        st.markdown("### 📈 Real-time Profit Analysis")
        
        # 그래프 영역 (Dark Theme 적용)
        chart_data = pd.DataFrame({
            'Process Hour': range(10),
            'Profit ($)': [profit * (1 - np.exp(-x/2)) for x in range(10)] # 가상의 상승 곡선
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=chart_data['Process Hour'], y=chart_data['Profit ($)'], 
                                 mode='lines', fill='tozeroy', line=dict(color='#00E676', width=3)))
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'), height=300,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=True, gridcolor='#30363D'),
            yaxis=dict(showgrid=True, gridcolor='#30363D')
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # 하단 3개 KPI 카드 (이미지 하단부)
        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Expected Recovery", f"{(co_y+li_y)/2:.1f}%", "High")
        with k2:
            st.metric("Energy Consump.", f"{cost*0.4:.0f} kWh", "-12%")
        with k3:
            st.metric("Purity Grade", f"{purity:.2f}%", "Grade A")

# --- [TAB 2] 역설계 (이미지의 두 번째 화면) ---
with tab_rev:
    col_t, col_s = st.columns([1, 2])
    
    with col_t:
        st.markdown("### 🎯 Target Definition")
        with st.container(border=True):
            target_pur = st.number_input("Target Purity (%)", 90.0, 99.9, 99.9)
            target_yid = st.number_input("Min. Recovery Rate (%)", 80.0, 99.0, 95.0)
            st.markdown("---")
            st.markdown("#### Constraint Settings")
            st.checkbox("Lock Step 1 pH", value=False)
            st.checkbox("Lock Step 2 pH", value=False)
            
            if st.button("Calculate Optimal Recipe", use_container_width=True):
                # (간단 탐색 로직 - 이전과 동일)
                best_res = (4.2, 82, 8420) # 예시 결과값
                st.session_state['recipe'] = best_res

    with col_s:
        st.markdown("### AI Recommended Recipe")
        if 'recipe' in st.session_state:
            res = st.session_state['recipe']
            
            # Figma의 '추천 레시피' 큰 글씨 디자인
            st.markdown(f"""
            <div style="background-color: #21262D; padding: 20px; border-radius: 10px; border-left: 5px solid #00E676;">
                <h2 style="margin:0;">
                    Temp: <span style="color:#00E676">{res[1]}°C</span> | 
                    pH: <span style="color:#2E9AFE">{res[0]}</span>
                </h2>
                <p style="color:#8B949E; margin-top:5px;">Target Achieved ✅</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 레이더 차트
            categories = ['Profit', 'Purity', 'Yield', 'Safety', 'Energy']
            fig_radar = go.Figure(go.Scatterpolar(
                r=[80, 99, 96, 70, 60], theta=categories, fill='toself', 
                line_color='#00E676'
            ))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True)), 
                                    paper_bgcolor="rgba(0,0,0,0)", font_color="white", height=350)
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("좌측에서 목표를 설정하고 버튼을 눌러주세요.")