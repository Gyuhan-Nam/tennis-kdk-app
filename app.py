import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="KDK", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. [아이폰 짤림 방지] 극한의 가로 고정 CSS
st.markdown("""
    <style>
    /* 전체 여백 제거 */
    .block-container { padding: 0.5rem 0.2rem !important; }
    
    /* [핵심] 5개 컬럼을 강제로 한 줄에 고정 (모바일에서도 절대 안 깨짐) */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: space-between !important;
        width: 100% !important;
        gap: 2px !important;
    }
    
    /* 각 컬럼 너비 강제 할당 (%) */
    [data-testid="column"] {
        min-width: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
    }
    /* 선수명 컬럼 (28%) / 점수 입력 (20%) / 콜론 (4%) */
    [data-testid="stHorizontalBlock"] > div:nth-child(1),
    [data-testid="stHorizontalBlock"] > div:nth-child(5) { flex: 2.8 !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(2),
    [data-testid="stHorizontalBlock"] > div:nth-child(4) { flex: 2.0 !important; }
    [data-testid="stHorizontalBlock"] > div:nth-child(3) { flex: 0.4 !important; }

    /* 선수 이름 스타일 (배경색 추가로 가독성 확보) */
    .name-text {
        text-align: center;
        font-size: 0.75rem !important;
        font-weight: 700;
        line-height: 1.2;
        color: white;
        background-color: #1e293b;
        padding: 5px 2px;
        border-radius: 4px;
        word-break: break-all;
    }

    /* 입력창(Selectbox) 아이폰 최적화 */
    div[data-testid="stSelectbox"] > div {
        min-height: 30px !important;
    }
    div[data-testid="stSelectbox"] div[role="button"] {
        padding: 0px 2px !important;
        font-size: 0.9rem !important;
        height: 30px !important;
        text-align: center;
    }

    /* 콜론 스타일 */
    .vs-colon {
        font-size: 1.2rem;
        font-weight: bold;
        color: #ff4b4b;
        text-align: center;
    }

    /* 저장 버튼 (하단 전체 너비) */
    .stButton > button {
        width: 100% !important;
        background-color: #10b981 !important;
        color: white !important;
        height: 3rem !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        margin-top: 15px !important;
        border-radius: 8px !important;
    }

    /* 순위표 데이터 크기 축소 */
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th {
        font-size: 0.75rem !important;
        padding: 2px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. 데이터 로드 및 저장 함수
REQUIRED_COLUMNS = ["date", "group", "match_id", "score1", "score2", "last_updated"]

@st.cache_data(ttl=60)
def load_db_cached():
    try:
        df = conn.read(ttl="60s")
        if df is None or df.empty or 'date' not in df.columns: return pd.DataFrame(columns=REQUIRED_COLUMNS)
        return df
    except: return pd.DataFrame(columns=REQUIRED_COLUMNS)

def save_db(df):
    conn.update(data=df)
    st.cache_data.clear()

# 5. KDK 대진표 로직
def get_kdk_matches(num):
    schedules = {5: ["12:34","13:25","14:35","15:24","23:45"], 6: ["12:34","15:46","23:56","14:25","24:36","16:35"], 7: ["12:34","56:17","35:24","14:67","23:57","16:25","46:37"], 8: ["12:34","56:78","13:57","24:68","15:26","37:48","16:38","25:47"], 9: ["12:34","56:78","19:57","23:68","49:38","15:26","36:45","17:89","24:79"], 10: ["12:34","56:78","23:6A","19:58","3A:45","27:89","4A:68","13:79","46:59","17:2A"]}
    mapping = {"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"A":10}
    return [([mapping[c] for c in m.split(":")[0]], [mapping[c] for c in m.split(":")[1]]) for m in schedules.get(num, [])]

# ----------------------------------------------------------------
# 메인 로직
# ----------------------------------------------------------------
st.title("🎾 KDK")

with st.sidebar:
    now = datetime.now()
    year = st.selectbox("연도", range(2024, now.year + 2))
    month = st.selectbox("월", [f"{i:02d}" for i in range(1, 13)], index=now.month-1)
    target_month = f"{year}-{month}"
    if st.button("🔄 새로고침"): st.cache_data.clear(); st.rerun()

all_data = load_db_cached()
tabs = st.tabs(["🥇 금", "🥈 은", "🥉 동"])

for i, group_key in enumerate(["gold", "silver", "bronze"]):
    with tabs[i]:
        # 인원 설정
        c_set1, c_set2 = st.columns([1, 2.5])
        with c_set1: n = st.number_input(f"인원", 5, 10, 6, key=f"n_{group_key}")
        with c_set2:
            with st.expander("👤 명단편집"):
                p_names = [st.text_input(f"{j+1}", f"P{j+1}", key=f"nm_{group_key}_{j}") for j in range(n)]

        matches = get_kdk_matches(n)
        selected_m_idx = st.selectbox(f"경기", range(len(matches)), 
                                      format_func=lambda x: f"{x+1}R: {matches[x][0]} vs {matches[x][1]}", 
                                      key=f"sel_{group_key}")

        # DB 점수 로드
        curr_m = all_data[(all_data['date']==target_month) & (all_data['group']==group_key) & (all_data['match_id']==selected_m_idx)]
        db_s1 = int(curr_m.iloc[0]['score1']) if not curr_m.empty else 0
        db_s2 = int(curr_m.iloc[0]['score2']) if not curr_m.empty else 0

        # --- [핵심] 5개 컬럼으로 쪼개서 가로 배치 고정 ---
        t1, t2 = matches[selected_m_idx]
        col1, col2, col_v, col3, col4 = st.columns([2.8, 2, 0.4, 2, 2.8])

        with col1:
            st.markdown(f"<div class='name-text'>{p_names[t1[0]-1]}<br>{p_names[t1[1]-1]}</div>", unsafe_allow_html=True)
        with col2:
            s1_val = st.selectbox("S1", range(7), index=db_s1, key=f"s1_{group_key}_{selected_m_idx}", label_visibility="collapsed")
        with col_v:
            st.markdown("<div class='vs-colon'>:</div>", unsafe_allow_html=True)
        with col3:
            s2_val = st.selectbox("S2", range(7), index=db_s2, key=f"s2_{group_key}_{selected_m_idx}", label_visibility="collapsed")
        with col4:
            st.markdown(f"<div class='name-text'>{p_names[t2[0]-1]}<br>{p_names[t2[1]-1]}</div>", unsafe_allow_html=True)

        # 저장 버튼
        if st.button(f"💾 {selected_m_idx+1}R 결과 저장", key=f"btn_{group_key}"):
            with st.spinner("저장 중..."):
                df = conn.read(ttl=0)
                mask = (df['date'] == target_month) & (df['group'] == group_key) & (df['match_id'] == selected_m_idx)
                if not df[mask].empty:
                    df.loc[mask, ['score1', 'score2', 'last_updated']] = [s1_val, s2_val, str(datetime.now())]
                else:
                    new_row = pd.DataFrame([{"date": target_month, "group": group_key, "match_id": selected_m_idx, "score1": s1_val, "score2": s2_val, "last_updated": str(datetime.now())}])
                    df = pd.concat([df, new_row], ignore_index=True)
                save_db(df)
                st.success("저장 완료!"); st.rerun()

        # 순위표 (기존 로직 유지)
        st.divider()
        stats = {i: {"승":0, "득실":0, "결과": ["-"] * len(matches)} for i in range(1, n+1)}
        group_db = all_data[(all_data['date']==target_month) & (all_data['group']==group_key)]
        for _, row in group_db.iterrows():
            m_idx = int(row['match_id'])
            if m_idx >= len(matches): continue
            r1, r2 = int(row['score1']), int(row['score2'])
            if r1 == 0 and r2 == 0: continue
            tm1, tm2 = matches[m_idx]
            for p in tm1:
                stats[p]["득실"] += (r1 - r2); stats[p]["결과"][m_idx] = f"{r1}:{r2}"
                if r1 > r2: stats[p]["승"] += 1
            for p in tm2:
                stats[p]["득실"] += (r2 - r1); stats[p]["결과"][m_idx] = f"{r2}:{r1}"
                if r2 > r1: stats[p]["승"] += 1
        rows = []
        for i in range(1, n+1):
            rd = {"이름": p_names[i-1]}
            for j in range(len(matches)): rd[f"{j+1}R"] = stats[i]["결과"][j]
            rd.update({"승": stats[i]["승"], "득실": stats[i]["득실"]})
            rows.append(rd)
        df_rank = pd.DataFrame(rows).sort_values(by=["승", "득실"], ascending=False).reset_index(drop=True)
        df_rank.insert(0, "위", df_rank.index + 1)
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
