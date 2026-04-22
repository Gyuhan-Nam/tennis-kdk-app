import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="KDK 테니스 월례회", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. CSS 스타일 (모바일 최적화 및 버튼 디자인)
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; font-size: 1.5rem !important; font-weight: bold; border-radius: 12px; }
    /* 플러스 버튼 (파란색) */
    div[data-testid="stVerticalBlock"] > div:nth-child(2) button { background-color: #3b82f6; color: white; border: none; }
    /* 마이너스 버튼 (회색) */
    div[data-testid="stVerticalBlock"] > div:nth-child(3) button { background-color: #64748b; color: white; border: none; opacity: 0.8; }
    
    .player-box {
        font-size: 1.2rem; font-weight: bold; text-align: center; background-color: #1e293b; color: white;
        border-radius: 10px; padding: 15px 5px; min-height: 90px; display: flex; flex-direction: column;
        justify-content: center; line-height: 1.4; margin-bottom: 10px;
    }
    .score-display {
        font-size: 4rem; font-weight: 900; color: #ff4b4b; text-align: center; line-height: 1.1; margin: 10px 0;
    }
    .vs-text { font-size: 1rem; color: #64748b; text-align: center; font-weight: bold; margin-bottom: -15px; }
    .rank-table { font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# 4. KDK 대진표 파싱 로직
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
    parsed = []
    for m in raw:
        t1s, t2s = m.split(":")
        parsed.append(([mapping[c] for c in t1s], [mapping[c] for c in t2s]))
    return parsed

# 5. DB 관련 함수
def load_db():
    return conn.read(ttl=0)

def save_db(month, group, match_id, s1, s2):
    df = load_db()
    # 기존 기록 찾기
    mask = (df['date'] == month) & (df['group'] == group) & (df['match_id'] == match_id)
    if not df[mask].empty:
        df.loc[mask, ['score1', 'score2', 'last_updated']] = [s1, s2, str(datetime.now())]
    else:
        new_data = pd.DataFrame([{"date": month, "group": group, "match_id": match_id, "score1": s1, "score2": s2, "last_updated": str(datetime.now())}])
        df = pd.concat([df, new_data], ignore_index=True)
    conn.update(data=df)
    st.cache_data.clear()

# ----------------------------------------------------------------
# 메인 화면 구성
# ----------------------------------------------------------------
st.title("🎾 KDK 테니스 통합 시스템")

# 사이드바 설정
with st.sidebar:
    st.header("📅 대회 정보")
    
    # 1. 현재 날짜 정보 가져오기
    now = datetime.now()
    curr_year = now.year
    curr_month = now.month

    # 2. 연도 선택 (2024년부터 내년까지 선택 가능)
    year_list = list(range(2024, curr_year + 2))
    selected_year = st.selectbox("연도 선택", year_list, index=year_list.index(curr_year))

    # 3. 월 선택
    month_list = [f"{i:02d}" for i in range(1, 13)]
    selected_month = st.selectbox("월 선택", month_list, index=curr_month - 1)

    # 4. DB 조회를 위한 날짜 키값 생성 (예: "2024-05")
    target_month = f"{selected_year}-{selected_month}"
    
    st.info(f"선택된 대회: {target_month}")
    
    if st.button("🔄 데이터 강제 새로고침"):
        st.rerun()

all_data = load_db()
tabs = st.tabs(["🥇 금조", "🥈 은조", "🥉 동조"])

for i, group_name in enumerate(["금조", "은조", "동조"]):
    group_key = ["gold", "silver", "bronze"][i]
    with tabs[i]:
        # 1. 설정 및 이름 입력
        col_n1, col_n2 = st.columns([1, 3])
        with col_n1:
            n = st.number_input(f"인원({group_name})", 5, 10, 6, key=f"n_{group_key}")
        with col_n2:
            with st.expander("👤 선수 명단 편집"):
                p_names = [st.text_input(f"{j+1}번", f"선수{j+1}", key=f"nm_{group_key}_{j}") for j in range(n)]

        # 2. 대진표 및 경기 선택
        matches = get_kdk_matches(n)
        m_labels = []
        for idx, (t1, t2) in enumerate(matches):
            m_db = all_data[(all_data['date']==target_month) & (all_data['group']==group_key) & (all_data['match_id']==idx)]
            status = "✅" if not m_db.empty and (m_db.iloc[0]['score1'] > 0 or m_db.iloc[0]['score2'] > 0) else "⚪"
            m_labels.append(f"{status} {idx+1}경기 ({t1} vs {t2})")
        
        selected_m_idx = st.selectbox(f"경기 선택", range(len(matches)), format_func=lambda x: m_labels[x], key=f"sel_{group_key}")

        # 3. 점수 입력 UI (요청하신 수직형 모바일 최적화)
        curr_m = all_data[(all_data['date']==target_month) & (all_data['group']==group_key) & (all_data['match_id']==selected_m_idx)]
        s1 = int(curr_m.iloc[0]['score1']) if not curr_m.empty else 0
        s2 = int(curr_m.iloc[0]['score2']) if not curr_m.empty else 0
        
        t1_ids, t2_ids = matches[selected_m_idx]
        
        st.write("") # 간격
        c1, c_mid, c2 = st.columns([2, 1.5, 2])
        
        with c1:
            st.markdown(f"<div class='player-box'>{p_names[t1_ids[0]-1]}<br>{p_names[t1_ids[1]-1]}</div>", unsafe_allow_html=True)
            if st.button("➕", key=f"p1_up_{group_key}"):
                save_db(target_month, group_key, selected_m_idx, s1+1, s2); st.rerun()
            if st.button("➖", key=f"p1_down_{group_key}"):
                save_db(target_month, group_key, selected_m_idx, max(0, s1-1), s2); st.rerun()

        with c_mid:
            st.markdown(f"<div class='vs-text'>VS</div><div class='score-display'>{s1}:{s2}</div>", unsafe_allow_html=True)
            if st.button("🔄", key=f"reset_{group_key}"):
                save_db(target_month, group_key, selected_m_idx, 0, 0); st.rerun()

        with c2:
            st.markdown(f"<div class='player-box'>{p_names[t2_ids[0]-1]}<br>{p_names[t2_ids[1]-1]}</div>", unsafe_allow_html=True)
            if st.button("➕ ", key=f"p2_up_{group_key}"):
                save_db(target_month, group_key, selected_m_idx, s1, s2+1); st.rerun()
            if st.button("➖ ", key=f"p2_down_{group_key}"):
                save_db(target_month, group_key, selected_m_idx, s1, max(0, s2-1)); st.rerun()

        # 4. 순위표 계산 및 표시
        st.divider()
        st.subheader(f"🏆 {group_name} 실시간 순위")
        
        stats = {i: {"승":0,"패":0,"득":0,"실":0} for i in range(1, n+1)}
        group_db = all_data[(all_data['date']==target_month) & (all_data['group']==group_key)]
        
        for _, row in group_db.iterrows():
            m_idx = int(row['match_id'])
            if m_idx >= len(matches): continue
            res1, res2 = int(row['score1']), int(row['score2'])
            if res1 == 0 and res2 == 0: continue
            
            t1, t2 = matches[m_idx]
            for p in t1:
                stats[p]["득"] += res1; stats[p]["실"] += res2
                if res1 > res2: stats[p]["승"] += 1
                elif res1 < res2: stats[p]["패"] += 1
            for p in t2:
                stats[p]["득"] += res2; stats[p]["실"] += res1
                if res2 > res1: stats[p]["승"] += 1
                elif res2 < res1: stats[p]["패"] += 1

        rows = []
        for i in range(1, n+1):
            s = stats[i]
            rows.append({"이름": p_names[i-1], "승": s["승"], "패": s["패"], "득실차": s["득"]-s["실"], "득점": s["득"]})
        
        df_rank = pd.DataFrame(rows).sort_values(by=["승", "득실차", "득점"], ascending=False).reset_index(drop=True)
        df_rank.insert(0, "순위", df_rank.index + 1)
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
