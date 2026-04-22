import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="KDK 테니스 월례회", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. CSS 스타일 (모바일 최적화)
st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; font-size: 1.5rem !important; font-weight: bold; border-radius: 12px; }
    /* 플러스/마이너스 버튼 스타일 */
    .btn-plus button { background-color: #3b82f6 !important; color: white !important; }
    .btn-minus button { background-color: #64748b !important; color: white !important; opacity: 0.8; }
    /* 저장 버튼 스타일 */
    .btn-save button { background-color: #10b981 !important; color: white !important; height: 4em !important; margin-top: 10px; }
    
    .player-box {
        font-size: 1.2rem; font-weight: bold; text-align: center; background-color: #1e293b; color: white;
        border-radius: 10px; padding: 15px 5px; min-height: 90px; display: flex; flex-direction: column;
        justify-content: center; line-height: 1.4; margin-bottom: 10px;
    }
    .score-display {
        font-size: 4rem; font-weight: 900; color: #ff4b4b; text-align: center; line-height: 1.1; margin: 10px 0;
    }
    .vs-text { font-size: 1rem; color: #64748b; text-align: center; font-weight: bold; margin-bottom: -15px; }
    </style>
    """, unsafe_allow_html=True)

# 4. KDK 대진표 로직 (10인까지 지원)
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

# 5. DB 관련 함수
def load_db():
    return conn.read(ttl=0)

def save_db(df):
    conn.update(data=df)
    st.cache_data.clear()

# ----------------------------------------------------------------
# 메인 로직
# ----------------------------------------------------------------
st.title("🎾 KDK 테니스 통합 시스템")

# 사이드바: 날짜 설정
with st.sidebar:
    st.header("📅 대회 설정")
    now = datetime.now()
    year = st.selectbox("연도", range(2024, now.year + 2), index=0)
    month = st.selectbox("월", [f"{i:02d}" for i in range(1, 13)], index=now.month-1)
    target_month = f"{year}-{month}"
    if st.button("🔄 전체 데이터 불러오기"):
        st.rerun()

all_data = load_db()
tabs = st.tabs(["🥇 금조", "🥈 은조", "🥉 동조"])

for i, group_name in enumerate(["금조", "은조", "동조"]):
    group_key = ["gold", "silver", "bronze"][i]
    with tabs[i]:
        # 인원 및 이름 설정
        c_n1, c_n2 = st.columns([1, 3])
        with c_n1:
            n = st.number_input(f"인원({group_name})", 5, 10, 6, key=f"n_{group_key}")
        with c_n2:
            with st.expander("👤 명단 편집"):
                p_names = [st.text_input(f"{j+1}번", f"P{j+1}", key=f"nm_{group_key}_{j}") for j in range(n)]

        matches = get_kdk_matches(n)
        
        # 경기 선택 및 로컬 점수 관리
        selected_m_idx = st.selectbox(f"경기 선택", range(len(matches)), 
                                      format_func=lambda x: f"{x+1}경기 ({matches[x][0]} vs {matches[x][1]})", 
                                      key=f"sel_{group_key}")

        # [중요] 선택된 경기의 점수를 세션 스테이트에 로컬로 저장
        ss_key_s1 = f"local_s1_{group_key}_{selected_m_idx}"
        ss_key_s2 = f"local_s2_{group_key}_{selected_m_idx}"

        # DB에서 데이터 가져와서 초기값 설정 (세션에 없을 때만)
        if ss_key_s1 not in st.session_state:
            curr_m = all_data[(all_data['date']==target_month) & (all_data['group']==group_key) & (all_data['match_id']==selected_m_idx)]
            st.session_state[ss_key_s1] = int(curr_m.iloc[0]['score1']) if not curr_m.empty else 0
            st.session_state[ss_key_s2] = int(curr_m.iloc[0]['score2']) if not curr_m.empty else 0

        # UI 배치
        t1, t2 = matches[selected_m_idx]
        col1, col_mid, col2 = st.columns([2, 1.5, 2])
        
        with col1:
            st.markdown(f"<div class='player-box'>{p_names[t1[0]-1]}<br>{p_names[t1[1]-1]}</div>", unsafe_allow_html=True)
            st.markdown("<div class='btn-plus'>", unsafe_allow_html=True)
            if st.button("➕", key=f"p1_u_{group_key}"):
                st.session_state[ss_key_s1] += 1
                st.rerun()
            st.markdown("</div><div class='btn-minus'>", unsafe_allow_html=True)
            if st.button("➖", key=f"p1_d_{group_key}"):
                st.session_state[ss_key_s1] = max(0, st.session_state[ss_key_s1] - 1)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with col_mid:
            st.markdown(f"<div class='vs-text'>VS</div><div class='score-display'>{st.session_state[ss_key_s1]}:{st.session_state[ss_key_s2]}</div>", unsafe_allow_html=True)
            if st.button("🔄 리셋", key=f"rs_{group_key}"):
                st.session_state[ss_key_s1] = 0
                st.session_state[ss_key_s2] = 0
                st.rerun()

        with col2:
            st.markdown(f"<div class='player-box'>{p_names[t2[0]-1]}<br>{p_names[t2[1]-1]}</div>", unsafe_allow_html=True)
            st.markdown("<div class='btn-plus'>", unsafe_allow_html=True)
            if st.button("➕ ", key=f"p2_u_{group_key}"):
                st.session_state[ss_key_s2] += 1
                st.rerun()
            st.markdown("</div><div class='btn-minus'>", unsafe_allow_html=True)
            if st.button("➖ ", key=f"p2_d_{group_key}"):
                st.session_state[ss_key_s2] = max(0, st.session_state[ss_key_s2] - 1)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        # 구글 시트에 저장 버튼 (이 버튼을 누를 때만 서버에 전송)
        st.markdown("<div class='btn-save'>", unsafe_allow_html=True)
        if st.button(f"💾 {selected_m_idx+1}경기 결과 서버에 저장", key=f"save_{group_key}"):
            with st.spinner("서버에 기록 중..."):
                # 최신 전체 데이터 다시 읽기
                df = load_db()
                mask = (df['date'] == target_month) & (df['group'] == group_key) & (df['match_id'] == selected_m_idx)
                s1, s2 = st.session_state[ss_key_s1], st.session_state[ss_key_s2]
                
                if not df[mask].empty:
                    df.loc[mask, ['score1', 'score2', 'last_updated']] = [s1, s2, str(datetime.now())]
                else:
                    new_row = pd.DataFrame([{"date": target_month, "group": group_key, "match_id": selected_m_idx, "score1": s1, "score2": s2, "last_updated": str(datetime.now())}])
                    df = pd.concat([df, new_row], ignore_index=True)
                
                save_db(df)
                st.success("저장 완료!")
        st.markdown("</div>", unsafe_allow_html=True)

        # 순위표 계산 (all_data 기반)
        st.divider()
        st.subheader(f"🏆 {group_name} 실시간 순위")
        # ... (순위표 계산 로직은 동일)
        stats = {i: {"승":0,"패":0,"득":0,"실":0} for i in range(1, n+1)}
        group_db = all_data[(all_data['date']==target_month) & (all_data['group']==group_key)]
        
        for _, row in group_db.iterrows():
            m_idx = int(row['match_id'])
            if m_idx >= len(matches): continue
            r1, r2 = int(row['score1']), int(row['score2'])
            if r1 == 0 and r2 == 0: continue
            
            tm1, tm2 = matches[m_idx]
            for p in tm1:
                stats[p]["득"] += r1; stats[p]["실"] += r2
                if r1 > r2: stats[p]["승"] += 1
                elif r1 < r2: stats[p]["패"] += 1
            for p in tm2:
                stats[p]["득"] += r2; stats[p]["실"] += r1
                if r2 > r1: stats[p]["승"] += 1
                elif r2 < r1: stats[p]["패"] += 1

        rows = []
        for i in range(1, n+1):
            s = stats[i]
            rows.append({"이름": p_names[i-1], "승": s["승"], "패": s["패"], "득실차": s["득"]-s["실"], "득점": s["득"]})
        
        df_rank = pd.DataFrame(rows).sort_values(by=["승", "득실차", "득점"], ascending=False).reset_index(drop=True)
        df_rank.insert(0, "순위", df_rank.index + 1)
        st.dataframe(df_rank, use_container_width=True, hide_index=True)
