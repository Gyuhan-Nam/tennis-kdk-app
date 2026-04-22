import streamlit as st
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="KDK 테니스 월례회", layout="wide")

st.markdown("""
    <style>
    .stButton>button { width: 100%; height: 3.5em; font-size: 1.5rem !important; font-weight: bold; }
    .score-display { font-size: 4rem; font-weight: bold; text-align: center; color: #ff4b4b; background-color: #f0f2f6; border-radius: 10px; padding: 10px; margin: 10px 0; border: 2px solid #d1d5db; }
    .team-name { font-size: 1.3rem; font-weight: bold; text-align: center; min-height: 60px; display: flex; align-items: center; justify-content: center; background-color: #3b82f6; color: white; border-radius: 8px; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🎾 KDK 테니스 월례회 통합 시스템")

# ----------------------------------------------------------------
# 2. 대진표 파싱 로직 (공통 함수)
# ----------------------------------------------------------------
def get_kdk_matches(num):
    schedules = {
        5: ["12:34","13:25","14:35","15:24","23:45"],
        6: ["12:34","15:46","23:56","14:25","24:36","16:35"],
        7: ["12:34","56:17","35:24","14:67","23:57","16:25","46:37"],
        8: ["12:34","56:78","13:57","24:68","15:26","37:48","16:38","25:47"],
        9: ["12:34","56:78","19:57","23:68","49:38","15:26","36:45","17:89","24:79"],
        10: ["12:34","56:78","23:6A","19:58","3A:45","27:89","4A:68","13:79","46:59","17:2A"],
        11: ["12:34","56:78","1B:9A","23:68","4A:57","26:9B","13:5B","49:8A","17:28","5A:6B","39:47"],
        12: ["12:34","56:78","9A:BC","13:57","24:68","9B:15","AC:23","48:7B","6A:19","2C:5B","36:8A","9C:47"]
    }
    raw = schedules.get(num, [])
    mapping = {"1":1,"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"A":10,"B":11,"C":12}
    parsed = []
    for m in raw:
        t1s, t2s = m.split(":")
        parsed.append(([mapping[c] for c in t1s], [mapping[c] for c in t2s]))
    return parsed

# ----------------------------------------------------------------
# 3. 조별 UI 렌더링 함수 (금/은/동 공통 사용)
# ----------------------------------------------------------------
def run_group_logic(group_key, group_name):
    # 인원수 설정
    n_key = f"n_{group_key}"
    if n_key not in st.session_state: st.session_state[n_key] = 6
    
    col_set1, col_set2 = st.columns([1, 4])
    with col_set1:
        n = st.number_input(f"{group_name} 인원", 5, 12, value=st.session_state[n_key], key=f"input_{n_key}")
        if n != st.session_state[n_key]:
            st.session_state[n_key] = n
            # 해당 조의 모든 데이터 초기화
            for k in list(st.session_state.keys()):
                if k.startswith(f"sc_{group_key}") or k.startswith(f"name_{group_key}"):
                    del st.session_state[k]
            st.rerun()

    # 선수 이름 입력
    with st.expander(f"👤 {group_name} 선수 명단 편집"):
        p_names = []
        cols = st.columns(4)
        for i in range(n):
            with cols[i % 4]:
                name = st.text_input(f"{i+1}번", value=f"P{i+1}", key=f"name_{group_key}_{i}")
                p_names.append(name)

    # 대진표 가져오기
    matches = get_kdk_matches(n)
    
    # 경기 선택
    g_idx_key = f"g_idx_{group_key}"
    if g_idx_key not in st.session_state: st.session_state[g_idx_key] = 0
    
    labels = []
    for i, (t1, t2) in enumerate(matches):
        s_k = f"sc_{group_key}_{i}"
        is_done = f"✅" if s_k in st.session_state and sum(st.session_state[s_k]) > 0 else "⚪"
        t1_ns = ",".join([str(x) for x in t1])
        t2_ns = ",".join([str(x) for x in t2])
        labels.append(f"{is_done} {i+1}경기 ({t1_ns} vs {t2_ns})")

    selected_idx = st.selectbox(f"{group_name} 경기 선택", range(len(matches)), 
                                index=st.session_state[g_idx_key], 
                                format_func=lambda x: labels[x], key=f"select_{group_key}")
    st.session_state[g_idx_key] = selected_idx

    # 경기 대진 표시
    t1_ids, t2_ids = matches[selected_idx]
    team1_display = " & ".join([p_names[idx-1] for idx in t1_ids])
    team2_display = " & ".join([p_names[idx-1] for idx in t2_ids])
    
    st.info(f"**현재 경기:** {team1_display}  **VS**  {team2_display}")

    # 점수 입력 UI
    score_key = f"sc_{group_key}_{selected_idx}"
    if score_key not in st.session_state: st.session_state[score_key] = [0, 0]

    c1, c2, c3 = st.columns([2, 1, 2])
    with c1:
        st.markdown(f"<div class='team-name'>{team1_display}</div>", unsafe_allow_html=True)
        if st.button("➕", key=f"p1_{group_key}_{selected_idx}"):
            st.session_state[score_key][0] = min(6, st.session_state[score_key][0] + 1); st.rerun()
        if st.button("➖", key=f"m1_{group_key}_{selected_idx}"):
            st.session_state[score_key][0] = max(0, st.session_state[score_key][0] - 1); st.rerun()
    with c2:
        st.markdown(f"<div class='score-display'>{st.session_state[score_key][0]}:{st.session_state[score_key][1]}</div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='team-name'>{team2_display}</div>", unsafe_allow_html=True)
        if st.button("➕ ", key=f"p2_{group_key}_{selected_idx}"):
            st.session_state[score_key][1] = min(6, st.session_state[score_key][1] + 1); st.rerun()
        if st.button("➖ ", key=f"m2_{group_key}_{selected_idx}"):
            st.session_state[score_key][1] = max(0, st.session_state[score_key][1] - 1); st.rerun()

    # 순위표 계산
    st.divider()
    st.subheader(f"🏆 {group_name} 순위표")
    stats = {i: {"승":0,"패":0,"득":0,"실":0,"결과":["-"]*len(matches)} for i in range(1, n+1)}
    for i, (t1, t2) in enumerate(matches):
        sk = f"sc_{group_key}_{i}"
        if sk in st.session_state:
            v1, v2 = st.session_state[sk]
            if v1 == 0 and v2 == 0: continue
            for p in t1:
                stats[p]["득"] += v1; stats[p]["실"] += v2; stats[p]["결과"][i] = f"{v1}:{v2}"
                if v1 > v2: stats[p]["승"] += 1
                elif v1 < v2: stats[p]["패"] += 1
            for p in t2:
                stats[p]["득"] += v2; stats[p]["실"] += v1; stats[p]["결과"][i] = f"{v2}:{v1}"
                if v2 > v1: stats[p]["승"] += 1
                elif v2 < v1: stats[p]["패"] += 1

    rows = []
    for i in range(1, n+1):
        s = stats[i]
        rows.append({"이름": p_names[i-1], **{f"{j+1}R": s["결과"][j] for j in range(len(matches))},
                    "승": s["승"], "패": s["패"], "득점": s["득"], "실점": s["실"], "득실차": s["득"] - s["실"]})
    df = pd.DataFrame(rows).sort_values(by=["승", "득실차", "득점"], ascending=False).reset_index(drop=True)
    df.insert(0, "순위", df.index + 1)
    st.dataframe(df, use_container_width=True, hide_index=True)

# ----------------------------------------------------------------
# 4. 메인 화면 - 탭 구성
# ----------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["🥇 금조", "🥈 은조", "🥉 동조"])

with tab1:
    run_group_logic("gold", "금조")

with tab2:
    run_group_logic("silver", "은조")

with tab3:
    run_group_logic("bronze", "동조")

# 초기화 버튼
st.sidebar.divider()
if st.sidebar.button("♻️ 전체 데이터 초기화"):
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.rerun()