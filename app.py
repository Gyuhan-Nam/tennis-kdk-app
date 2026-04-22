import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="KDK 테니스 점수판", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. [스케치 완벽 반영] 모바일 가로 고정 및 UI 디자인 CSS
st.markdown("""
    <style>
    /* 상단 기본 여백 제거 */
    .block-container { padding: 1rem 0.5rem !important; }
    
    /* 모바일에서도 3열 가로 정렬 강제 */
    [data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 5px !important;
    }
    [data-testid="column"] {
        min-width: 0px !important;
        flex: 1 !important;
        padding: 0px !important;
    }

    /* 성명 표시 영역 (수직 배치) */
    .name-area {
        text-align: center;
        font-size: 1.1rem !important;
        font-weight: 800;
        line-height: 1.3;
        color: #1e293b;
        margin-bottom: 8px;
        min-height: 50px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* 중앙 점수 표시 */
    .score-display {
        font-size: 3.5rem !important;
        font-weight: 900;
        color: #ff4b4b;
        text-align: center;
        line-height: 1.0 !important;
        margin-bottom: 5px;
    }
    .vs-text { font-size: 0.7rem; color: #64748b; text-align: center; margin-bottom: -5px; }

    /* 버튼 스타일 (가로 배치용) */
    .stButton > button {
        width: 100% !important;
        height: 2.5rem !important;
        font-size: 1.2rem !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 0px !important;
    }
    
    /* 버튼 색상 구분 */
    .plus-btn button { background-color: #3b82f6 !important; color: white !important; border: none; }
    .minus-btn button { background-color: #f1f5f9 !important; color: #475569 !important; border: 1px solid #cbd5e1 !important; }
    .reset-btn button { width: 50px !important; height: 35px !important; font-size: 1rem !important; margin: 0 auto; }

    /* 저장 버튼 디자인 */
    .btn-save button {
        background-color: #10b981 !important;
        color: white !important;
        height: 3.5rem !important;
        font-size: 1.2rem !important;
        margin-top: 15px !important;
        border: none;
    }

    /* 순위표 가로 스크롤 및 폰트 조절 */
    div[data-testid="stDataFrame"] { overflow-x: auto !important; }
    div[data-testid="stDataFrame"] td, div[data-testid="stDataFrame"] th { font-size: 0.85rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. KDK 대진표 로직 (10인 지원)
def get_kdk_matches(num):
    schedules = {
        5: ["12:34","13:25","14:35","15:24","23:45"],
        6: ["12:34","15:46","23:56","14:25","24:36","16:35"],
        7: ["12:34","56:17","35:24","14:67","23:57","16:25","46:37"],
        8: ["12:34","56:78","13:57","24:68","15:26","37:48","16:38","25:47"],
        9: ["12:34","56:78","19:57","23:68","49:38","15:26","36:45","17:89","24:79"],
        10: ["12:34","56:78","23:6A","19:58","3A:45","27:89","4A:68","13:79","46:59","17:2A"]
    }
    mapping = {"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"A":10}
    raw = schedules.get(num, [])
    return [([mapping[c] for c in m.split(":")[0]], [mapping[c] for c in m.split(":")[1]]) for m in raw]

# 5. DB 관리 함수 (KeyError 방지 및 API 할당량 관리)
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
# 메인 로직 시작
# ----------------------------------------------------------------
st.title("🎾 KDK 테니스 통합관리")

# 사이드바: 날짜 및 설정
with st.sidebar:
    now = datetime.now()
    year = st.selectbox("연도", range(2024, now.year + 2))
    month = st.selectbox("월", [f"{i:02d}" for i in range(1, 13)], index=now.month-1)
    target_month = f"{year}-{month}"
    if st.button("🔄 전체 데이터 새로고침"):
        st.cache_data.clear(); st.rerun()

all_data = load_db_cached()
tabs = st.tabs(["🥇 금", "🥈 은", "🥉 동"])

for i, group_name in enumerate(["금조", "은조", "동조"]):
    group_key = ["gold", "silver", "bronze"][i]
    with tabs[i]:
        # 인원 설정 및 명단 편집
        c1, c2 = st.columns([1, 2])
        with c1: n = st.number_input(f"인원", 5, 10, 6, key=f"n_{group_key}")
        with c2:
            with st.expander("👤 명단 편집"):
                p_names = [st.text_input(f"{j+1}번", f"선수{j+1}", key=f"nm_{group_key}_{j}") for j in range(n)]

        matches = get_kdk_matches(n)
        selected_m_idx = st.selectbox(f"경기 선택", range(len(matches)), 
                                      format_func=lambda x: f"{x+1}R: {matches[x][0]} vs {matches[x][1]}", 
                                      key=f"sel_{group_key}")

        # 로컬 점수 로드 (세션 상태 이용)
        ss1, ss2 = f"local_s1_{group_key}_{selected_m_idx}", f"local_s2_{group_key}_{selected_m_idx}"
        if ss1 not in st.session_state:
            curr_m = all_data[(all_data['date']==target_month) & (all_data['group']==group_key) & (all_data['match_id']==selected_m_idx)]
            st.session_state[ss1] = int(curr_m.iloc[0]['score1']) if not curr_m.empty else 0
            st.session_state[ss2] = int(curr_m.iloc[0]['score2']) if not curr_m.empty else 0

        # ----------------------------------------------------------------
        # [스케치 기반 점수판 레이아웃 구현]
        # ----------------------------------------------------------------
        t1_ids, t2_ids = matches[selected_m_idx]
        m_col1, m_col_mid, m_col2 = st.columns([1, 0.8, 1])

        with m_col1:
            # 팀 1 성명 수직 배치
            st.markdown(f"<div class='name-area'>{p_names[t1_ids[0]-1]}<br>{p_names[t1_ids[1]-1]}</div>", unsafe_allow_html=True)
            # 하단 버튼 가로 배치 (서브 컬럼)
            b1, b2 = st.columns(2)
            with b1:
                st.markdown("<div class='plus-btn'>", unsafe_allow_html=True)
                if st.button("＋", key=f"p1u_{group_key}"):
                    st.session_state[ss1] = min(6, st.session_state[ss1] + 1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with b2:
                st.markdown("<div class='minus-btn'>", unsafe_allow_html=True)
                if st.button("－", key=f"p1d_{group_key}"):
                    st.session_state[ss1] = max(0, st.session_state[ss1] - 1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        with m_col_mid:
            st.markdown(f"<div class='vs-text'>VS</div><div class='score-display'>{st.session_state[ss1]}:{st.session_state[ss2]}</div>", unsafe_allow_html=True)
            st.markdown("<div class='reset-btn'>", unsafe_allow_html=True)
            if st.button("🔄", key=f"reset_{group_key}"):
                st.session_state[ss1] = 0; st.session_state[ss2] = 0; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with m_col2:
            # 팀 2 성명 수직 배치
            st.markdown(f"<div class='name-area'>{p_names[t2_ids[0]-1]}<br>{p_names[t2_ids[1]-1]}</div>", unsafe_allow_html=True)
            # 하단 버튼 가로 배치 (서브 컬럼)
            b3, b4 = st.columns(2)
            with b3:
                st.markdown("<div class='plus-btn'>", unsafe_allow_html=True)
                if st.button("＋ ", key=f"p2u_{group_key}"):
                    st.session_state[ss2] = min(6, st.session_state[ss2] + 1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with b4:
                st.markdown("<div class='minus-btn'>", unsafe_allow_html=True)
                if st.button("－ ", key=f"p2d_{group_key}"):
                    st.session_state[ss2] = max(0, st.session_state[ss2] - 1); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        # 결과 저장 버튼
        st.markdown("<div class='btn-save'>", unsafe_allow_html=True)
        if st.button(f"💾 {selected_m_idx+1}경기 결과 서버 저장", key=f"save_{group_key}"):
            with st.spinner("서버에 기록 중..."):
                df = load_db_fresh()
                mask = (df['date'] == target_month) & (df['group'] == group_key) & (df['match_id'] == selected_m_idx)
                s1_val, s2_val = st.session_state[ss1], st.session_state[ss2]
                if not df[mask].empty:
                    df.loc[mask, ['score1', 'score2', 'last_updated']] = [s1_val, s2_val, str(datetime.now())]
                else:
                    new_row = pd.DataFrame([{"date": target_month, "group": group_key, "match_id": selected_m_idx, "score1": s1_val, "score2": s2_val, "last_updated": str(datetime.now())}])
                    df = pd.concat([df, new_row], ignore_index=True)
                save_db(df)
                st.success("저장되었습니다!"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # ----------------------------------------------------------------
        # 순위표 계산 및 표시
        # ----------------------------------------------------------------
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
            row_data.update({"승": s["승"], "득실차": s["득"]-s["실"], "득점": s["득"]})
            rows.append(row_data)
        
        df_rank = pd.DataFrame(rows).sort_values(by=["승", "득실차", "득점"], ascending=False).reset_index(drop=True)
        df_rank.insert(0, "순위", df_rank.index + 1)
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
