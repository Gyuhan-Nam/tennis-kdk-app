import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="KDK 테니스", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. [초슬림 최적화] CSS 스타일
st.markdown("""
    <style>
    /* 전체 여백 극한으로 줄이기 */
    .block-container { padding: 0.5rem 0.5rem !important; }
    
    /* 컬럼 가로 배치 강제 및 간격 최소화 */
    [data-testid="column"] {
        flex: 1 1 0% !important;
        min-width: 0px !important;
        padding: 0px 2px !important;
    }
    [data-testid="stHorizontalBlock"] {
        gap: 2px !important;
        align-items: center !important;
    }

    /* 선수 이름 칸 - 높이와 여백 최소화 */
    .player-box {
        background-color: #1e293b;
        color: white;
        border-radius: 4px;
        padding: 2px 1px !important; /* 패딩 최소화 */
        text-align: center;
        font-size: 0.75rem !important; /* 글자 크기 살짝 축소 */
        line-height: 1.0 !important;
        min-height: 34px !important; /* 높이 대폭 축소 */
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 2px !important;
    }

    /* 점수 표시 - 높이 조절 */
    .score-display {
        font-size: 2rem !important;
        font-weight: 800;
        color: #ff4b4b;
        text-align: center;
        line-height: 1.0 !important;
        margin: 0px !important;
    }
    .vs-text { font-size: 0.55rem; color: #64748b; text-align: center; margin-bottom: -2px; }

    /* 버튼 높이 축소 */
    .stButton > button {
        width: 100% !important;
        height: 1.8rem !important; /* 버튼 높이 축소 */
        font-size: 0.9rem !important;
        padding: 0px !important;
        margin-top: 1px !important;
        border-radius: 4px !important;
    }
    
    /* 저장 버튼만 조금 더 크게 */
    .btn-save button {
        background-color: #10b981 !important;
        color: white !important;
        height: 2.5rem !important;
        font-size: 1rem !important;
        margin-top: 8px !important;
    }

    /* 순위표 글자 크기 조절 */
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
        font-size: 0.8rem !important;
    }
    
    /* 탭 간격 축소 */
    button[data-baseweb="tab"] {
        padding: 8px 12px !important;
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. KDK 대진표 로직 (기존 동일)
def get_kdk_matches(num):
    schedules = {5: ["12:34","13:25","14:35","15:24","23:45"], 6: ["12:34","15:46","23:56","14:25","24:36","16:35"], 7: ["12:34","56:17","35:24","14:67","23:57","16:25","46:37"], 8: ["12:34","56:78","13:57","24:68","15:26","37:48","16:38","25:47"], 9: ["12:34","56:78","19:57","23:68","49:38","15:26","36:45","17:89","24:79"], 10: ["12:34","56:78","23:6A","19:58","3A:45","27:89","4A:68","13:79","46:59","17:2A"]}
    mapping = {"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"A":10}
    return [([mapping[c] for c in m.split(":")[0]], [mapping[c] for c in m.split(":")[1]]) for m in schedules.get(num, [])]

# 5. DB 관련 함수 (기존 동일)
REQUIRED_COLUMNS = ["date", "group", "match_id", "score1", "score2", "last_updated"]
@st.cache_data(ttl=60)
def load_db_cached():
    try:
        df = conn.read(ttl="60s")
        if df is None or df.empty or 'date' not in df.columns: return pd.DataFrame(columns=REQUIRED_COLUMNS)
        return df
    except: return pd.DataFrame(columns=REQUIRED_COLUMNS)

def load_db_fresh():
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty or 'date' not in df.columns: return pd.DataFrame(columns=REQUIRED_COLUMNS)
        return df
    except: return pd.DataFrame(columns=REQUIRED_COLUMNS)

def save_db(df):
    conn.update(data=df)
    st.cache_data.clear()

# ----------------------------------------------------------------
# 메인 로직
# ----------------------------------------------------------------
st.title("🎾 KDK 테니스")

with st.sidebar:
    now = datetime.now()
    year = st.selectbox("연도", range(2024, now.year + 2))
    month = st.selectbox("월", [f"{i:02d}" for i in range(1, 13)], index=now.month-1)
    target_month = f"{year}-{month}"
    if st.button("🔄 동기화"):
        st.cache_data.clear()
        st.rerun()

all_data = load_db_cached()
tabs = st.tabs(["🥇 금", "🥈 은", "🥉 동"])

for i, group_name in enumerate(["금", "은", "동"]):
    group_key = ["gold", "silver", "bronze"][i]
    with tabs[i]:
        # 인원 설정 (매우 작게)
        c_n1, c_n2 = st.columns([1, 2.5])
        with c_n1: n = st.number_input(f"인원", 5, 10, 6, key=f"n_{group_key}")
        with c_n2:
            with st.expander("👤 이름편집"):
                p_names = [st.text_input(f"{j+1}", f"P{j+1}", key=f"nm_{group_key}_{j}") for j in range(n)]

        matches = get_kdk_matches(n)
        selected_m_idx = st.selectbox(f"경기 선택", range(len(matches)), 
                                      format_func=lambda x: f"{x+1}R: {matches[x][0]} vs {matches[x][1]}", 
                                      key=f"sel_{group_key}")

        ss_key_s1 = f"local_s1_{group_key}_{selected_m_idx}"
        ss_key_s2 = f"local_s2_{group_key}_{selected_m_idx}"

        if ss_key_s1 not in st.session_state:
            curr_m = all_data[(all_data['date']==target_month) & (all_data['group']==group_key) & (all_data['match_id']==selected_m_idx)]
            st.session_state[ss_key_s1] = int(curr_m.iloc[0]['score1']) if not curr_m.empty else 0
            st.session_state[ss_key_s2] = int(curr_m.iloc[0]['score2']) if not curr_m.empty else 0

        # --- 초슬림 점수 입력 UI ---
        t1, t2 = matches[selected_m_idx]
        col1, col_mid, col2 = st.columns([1, 0.8, 1])
        
        with col1:
            st.markdown(f"<div class='player-box'>{p_names[t1[0]-1]}<br>{p_names[t1[1]-1]}</div>", unsafe_allow_html=True)
            if st.button("➕", key=f"p1_u_{group_key}"):
                st.session_state[ss_key_s1] = min(6, st.session_state[ss_key_s1] + 1); st.rerun()
            if st.button("➖", key=f"p1_d_{group_key}"):
                st.session_state[ss_key_s1] = max(0, st.session_state[ss_key_s1] - 1); st.rerun()

        with col_mid:
            st.markdown(f"<div class='vs-text'>VS</div><div class='score-display'>{st.session_state[ss_key_s1]}:{st.session_state[ss_key_s2]}</div>", unsafe_allow_html=True)
            if st.button("🔄", key=f"rs_{group_key}"):
                st.session_state[ss_key_s1] = 0; st.session_state[ss_key_s2] = 0; st.rerun()

        with col2:
            st.markdown(f"<div class='player-box'>{p_names[t2[0]-1]}<br>{p_names[t2[1]-1]}</div>", unsafe_allow_html=True)
            if st.button("➕ ", key=f"p2_u_{group_key}"):
                st.session_state[ss_key_s2] = min(6, st.session_state[ss_key_s2] + 1); st.rerun()
            if st.button("➖ ", key=f"p2_d_{group_key}"):
                st.session_state[ss_key_s2] = max(0, st.session_state[ss_key_s2] - 1); st.rerun()

        st.markdown("<div class='btn-save'>", unsafe_allow_html=True)
        if st.button(f"💾 결과 저장", key=f"save_{group_key}"):
            with st.spinner("저장 중..."):
                df = load_db_fresh()
                mask = (df['date'] == target_month) & (df['group'] == group_key) & (df['match_id'] == selected_m_idx)
                if not df[mask].empty:
                    df.loc[mask, ['score1', 'score2', 'last_updated']] = [st.session_state[ss_key_s1], st.session_state[ss_key_s2], str(datetime.now())]
                else:
                    new_row = pd.DataFrame([{"date": target_month, "group": group_key, "match_id": selected_m_idx, "score1": st.session_state[ss_key_s1], "score2": st.session_state[ss_key_s2], "last_updated": str(datetime.now())}])
                    df = pd.concat([df, new_row], ignore_index=True)
                save_db(df)
                st.success("저장 완료!"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # --- 순위표 (가로 스크롤 가능) ---
        st.divider()
        stats = {i: {"승":0, "패":0, "득":0, "실":0, "결과": ["-"] * len(matches)} for i in range(1, n+1)}
        group_db = all_data[(all_data['date']==target_month) & (all_data['group']==group_key)]
        for _, row in group_db.iterrows():
            m_idx = int(row['match_id'])
            if m_idx >= len(matches): continue
            r1, r2 = int(row['score1']), int(row['score2'])
            if r1 == 0 and r2 == 0: continue
            tm1, tm2 = matches[m_idx]
            for p in tm1:
                stats[p]["득"] += r1; stats[p]["실"] += r2; stats[p]["결과"][m_idx] = f"{r1}:{r2}"
                if r1 > r2: stats[p]["승"] += 1
                elif r1 < r2: stats[p]["패"] += 1
            for p in tm2:
                stats[p]["득"] += r2; stats[p]["실"] += r1; stats[p]["결과"][m_idx] = f"{r2}:{r1}"
                if r2 > r1: stats[p]["승"] += 1
                elif r2 < r1: stats[p]["패"] += 1
        rows = []
        for i in range(1, n+1):
            s = stats[i]
            row_data = {"이름": p_names[i-1]}
            for idx in range(len(matches)): row_data[f"{idx+1}R"] = s["결과"][idx]
            row_data.update({"승": s["승"], "득실": s["득"]-s["실"]})
            rows.append(row_data)
        df_rank = pd.DataFrame(rows).sort_values(by=["승", "득실"], ascending=False).reset_index(drop=True)
        df_rank.insert(0, "순위", df_rank.index + 1)
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
