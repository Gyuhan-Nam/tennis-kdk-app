import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="KDK 테니스", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. [스케치 반영] 핵심 CSS
st.markdown("""
    <style>
    .block-container { padding: 1rem 0.5rem !important; }
    
    /* 메인 3컬럼 가로 고정 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 5px !important;
    }

    /* 선수 성명 영역 (수직 쌓기) */
    .name-area {
        text-align: center;
        font-size: 1.1rem !important;
        font-weight: bold;
        line-height: 1.2;
        color: #1e293b;
        margin-bottom: 5px;
    }

    /* 점수 표시 */
    .score-display {
        font-size: 3rem !important;
        font-weight: 800;
        color: #ff4b4b;
        text-align: center;
        line-height: 1 !important;
    }

    /* 플러스/마이너스 버튼 가로 나열을 위한 서브 컬럼 설정 */
    .btn-row {
        display: flex !important;
        flex-direction: row !important;
        gap: 2px !important;
        justify-content: center !important;
    }

    /* 버튼 스타일 최적화 (작고 둥글게) */
    .stButton > button {
        width: 100% !important;
        height: 2.2rem !important;
        padding: 0px !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        border-radius: 6px !important;
    }
    
    /* 플러스 버튼: 파란색 / 마이너스 버튼: 회색 */
    .plus-btn button { background-color: #3b82f6 !important; color: white !important; }
    .minus-btn button { background-color: #f1f5f9 !important; color: #475569 !important; border: 1px solid #cbd5e1 !important; }

    /* 저장 버튼 */
    .btn-save button {
        background-color: #10b981 !important;
        color: white !important;
        height: 3rem !important;
        margin-top: 20px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 기본 로직 (대진표/DB는 이전과 동일) ---
def get_kdk_matches(num):
    schedules = {5: ["12:34","13:25","14:35","15:24","23:45"], 6: ["12:34","15:46","23:56","14:25","24:36","16:35"], 7: ["12:34","56:17","35:24","14:67","23:57","16:25","46:37"], 8: ["12:34","56:78","13:57","24:68","15:26","37:48","16:38","25:47"], 9: ["12:34","56:78","19:57","23:68","49:38","15:26","36:45","17:89","24:79"], 10: ["12:34","56:78","23:6A","19:58","3A:45","27:89","4A:68","13:79","46:59","17:2A"]}
    mapping = {"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"A":10}
    return [([mapping[c] for c in m.split(":")[0]], [mapping[c] for c in m.split(":")[1]]) for m in schedules.get(num, [])]

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

# --- 메인 UI ---
st.title("🎾 KDK 점수판")

with st.sidebar:
    now = datetime.now()
    target_month = f"{st.selectbox('연도', range(2024, now.year+2))}-{st.selectbox('월', [f'{i:02d}' for i in range(1, 13)], index=now.month-1)}"
    if st.button("🔄 동기화"): st.cache_data.clear(); st.rerun()

all_data = load_db_cached()
group_key = st.radio("조 선택", ["gold", "silver", "bronze"], horizontal=True, label_visibility="collapsed")

# 인원 및 이름 설정
c_set1, c_set2 = st.columns([1, 2])
with c_set1: n = st.number_input(f"인원", 5, 10, 6, key=f"n_{group_key}")
with c_set2:
    with st.expander("👤 이름편집"):
        p_names = [st.text_input(f"{j+1}", f"P{j+1}", key=f"nm_{group_key}_{j}") for j in range(n)]

matches = get_kdk_matches(n)
selected_m_idx = st.selectbox(f"경기 선택", range(len(matches)), format_func=lambda x: f"{x+1}R: {matches[x][0]} vs {matches[x][1]}", key=f"sel_{group_key}")

# 세션 점수 로드
ss1, ss2 = f"s1_{group_key}_{selected_m_idx}", f"s2_{group_key}_{selected_m_idx}"
if ss1 not in st.session_state:
    curr_m = all_data[(all_data['date']==target_month) & (all_data['group']==group_key) & (all_data['match_id']==selected_m_idx)]
    st.session_state[ss1] = int(curr_m.iloc[0]['score1']) if not curr_m.empty else 0
    st.session_state[ss2] = int(curr_m.iloc[0]['score2']) if not curr_m.empty else 0

# ----------------------------------------------------------------
# [스케치 구현 핵심 구문]
# ----------------------------------------------------------------
t1, t2 = matches[selected_m_idx]
m_col1, m_col_mid, m_col2 = st.columns([1, 1, 1])

with m_col1:
    # 성명 수직 배치
    st.markdown(f"<div class='name-area'>{p_names[t1[0]-1]}<br>{p_names[t1[1]-1]}</div>", unsafe_allow_html=True)
    # 버튼 가로 배치 (서브 컬럼)
    b1, b2 = st.columns(2)
    with b1:
        st.markdown("<div class='plus-btn'>", unsafe_allow_html=True)
        if st.button("＋", key="p1u"): st.session_state[ss1] = min(6, st.session_state[ss1]+1); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with b2:
        st.markdown("<div class='minus-btn'>", unsafe_allow_html=True)
        if st.button("－", key="p1d"): st.session_state[ss1] = max(0, st.session_state[ss1]-1); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with m_col_mid:
    st.markdown(f"<div class='score-display'>{st.session_state[ss1]}:{st.session_state[ss2]}</div>", unsafe_allow_html=True)
    if st.button("🔄", key="reset"): st.session_state[ss1]=0; st.session_state[ss2]=0; st.rerun()

with m_col2:
    # 성명 수직 배치
    st.markdown(f"<div class='name-area'>{p_names[t2[0]-1]}<br>{p_names[t2[1]-1]}</div>", unsafe_allow_html=True)
    # 버튼 가로 배치 (서브 컬럼)
    b3, b4 = st.columns(2)
    with b3:
        st.markdown("<div class='plus-btn'>", unsafe_allow_html=True)
        if st.button("＋ ", key="p2u"): st.session_state[ss2] = min(6, st.session_state[ss2]+1); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with b4:
        st.markdown("<div class='minus-btn'>", unsafe_allow_html=True)
        if st.button("－ ", key="p2d"): st.session_state[ss2] = max(0, st.session_state[ss2]-1); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 저장 버튼
st.markdown("<div class='btn-save'>", unsafe_allow_html=True)
if st.button("💾 경기 결과 저장", key="sv"):
    df = conn.read(ttl=0)
    mask = (df['date']==target_month) & (df['group']==group_key) & (df['match_id']==selected_m_idx)
    if not df[mask].empty: df.loc[mask, ['score1','score2','last_updated']] = [st.session_state[ss1], st.session_state[ss2], str(datetime.now())]
    else: df = pd.concat([df, pd.DataFrame([{"date":target_month, "group":group_key, "match_id":selected_m_idx, "score1":st.session_state[ss1], "score2":st.session_state[ss2], "last_updated":str(datetime.now())}])], ignore_index=True)
    save_db(df); st.success("저장되었습니다!"); st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

        # 순위표
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
