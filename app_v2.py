import streamlit as st
import pandas as pd
import os

# 基本設定
st.set_page_config(page_title="迷你橋牌大會計分系統", layout="wide")
st.title("🏆 迷你橋牌官方數位計分終端")

# --- 1. 資料持久化與狀態初始化 ---
DB_FILE = "bridge_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE).to_dict('records')
        except:
            return []
    return []

def save_data(data):
    pd.DataFrame(data).to_csv(DB_FILE, index=False, encoding="utf-8-sig")

# 初始化 Session State
if 'history' not in st.session_state:
    st.session_state.history = load_data()
if 'contract_locked' not in st.session_state:
    st.session_state.contract_locked = False

# --- 側邊欄管理 ---
st.sidebar.header("⚙️ 賽事管理")
if st.sidebar.button("🆕 開始下一局 (重設輸入)"):
    st.session_state.contract_locked = False
    st.rerun()

if st.sidebar.button("🗑️ 清空大會所有紀錄"):
    st.session_state.history = []
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
    st.session_state.contract_locked = False
    st.rerun()

# --- 第一階段：點數判定 ---
st.header("第一階段：高牌點數與莊家")
is_locked = st.session_state.contract_locked

col1, col2, col3, col4 = st.columns(4)
with col1: n_hcp = st.number_input("🔴 北風", 0, 40, 0, key="n", disabled=is_locked)
with col2: e_hcp = st.number_input("🟢 東風", 0, 40, 0, key="e", disabled=is_locked)
with col3: s_hcp = st.number_input("🔴 南風", 0, 40, 0, key="s", disabled=is_locked)
with col4: w_hcp = st.number_input("🟢 西風", 0, 40, 0, key="w", disabled=is_locked)

total_hcp = n_hcp + e_hcp + s_hcp + w_hcp

if total_hcp == 40:
    ns_total, ew_total = n_hcp + s_hcp, e_hcp + w_hcp
    if ns_total > 20:
        attacker, at_color = "南北軍", "red"
    elif ew_total > 20:
        attacker, at_color = "東西軍", "green"
    else:
        attacker = st.radio("平手！指定主打方：", ["南北軍", "東西軍"], horizontal=True, disabled=is_locked)
        at_color = "red" if attacker == "南北軍" else "green"

    st.divider()

    # --- 第二階段：合約確認框 ---
    st.header("第二階段：設定合約")
    c_col1, c_col2 = st.columns(2)
    # 優化選項顯示
    with c_col1: suit = st.selectbox("選擇王牌花色", ["無王 (NT)", "高花 (♠️/♥️)", "低花 (♦️/♣️)"], disabled=is_locked)
    with c_col2: ctype = st.radio("合約等級", ["部分合約", "成局合約"], horizontal=True, disabled=is_locked)
    
    # 計算線位與目標磴數
    ts = 1 if "無王" in suit else (2 if "高花" in suit else 3)
    level = (3 if ts==1 else (4 if ts==2 else 5)) if "成局" in ctype else 1
    target_tricks = level + 6
    
    # --- [關鍵修改] 更直覺的摘要顯示 ---
    suit_name = suit.split(" ")[0] # 只取 "無王", "高花", "低花"
    st.warning(f"🔔 **當前合約摘要**：由 :{at_color}[{attacker}] 主打 **{suit_name}**，目標需吃足 **{target_tricks}** 磴 ({ctype})")
    
    if not is_locked:
        if st.button("✅ 確認合約 (確認後開始打牌)", use_container_width=True):
            st.session_state.contract_locked = True
            st.rerun()
    else:
        st.success("🔒 合約已鎖定，比賽進行中...")
        tricks = st.number_input(f"莊家實際吃到幾磴？", 0, 13, target_tricks)

        if st.button("💾 計算得分並紀錄", use_container_width=True):
            base = (40 + (level-1)*30) if ts==1 else (level*30 if ts==2 else level*20)
            if tricks >= target_tricks:
                over = tricks - target_tricks
                bonus = 300 if "成局" in ctype else 50
                score = base + over * (30 if ts <= 2 else 20) + bonus
                res = f"完成 ({tricks} 磴)"
            else:
                under = target_tricks - tricks
                score = -(under * 50)
                res = f"倒約 (僅 {tricks} 磴)"
            
            # 存入紀錄時也存入直覺的描述
            st.session_state.history.append({
                "莊家": attacker, 
                "合約": f"{suit_name} ({target_tricks} 磴)", # 存入如 "高花 (7 磴)"
                "結果": res,
                "得分": score, 
                "莊家顏色": at_color 
            })
            save_data(st.session_state.history)
            st.session_state.contract_locked = False 
            st.toast("成績已存入硬碟！")
            st.rerun()

# --- 4. 歷史紀錄 ---
st.divider()
st.header("📊 歷史比賽紀錄")
if st.session_state.history:
    ns_score = sum(r['得分'] for r in st.session_state.history if r['莊家'] == "南北軍")
    ew_score = sum(r['得分'] for r in st.session_state.history if r['莊家'] == "東西軍")
    m1, m2 = st.columns(2)
    m1.metric("🔴 南北軍 總分", f"{ns_score}", delta=ns_score-ew_score)
    m2.metric("🟢 東西軍 總分", f"{ew_score}", delta=ew_score-ns_score)

    csv_bytes = pd.DataFrame(st.session_state.history).to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button("📥 導出大會報表 (CSV)", data=csv_bytes, file_name="bridge_report.csv", mime="text/csv")

    for i, record in enumerate(st.session_state.history):
        cols = st.columns([1, 2, 3, 2, 2, 1])
        cols[0].write(f"#{i+1}")
        cols[1].markdown(f":{record['莊家顏色']}[**{record['莊家']}**]")
        cols[2].write(record['合約']) # 現在會顯示 "高花 (7 磴)"
        cols[3].write(record['結果'])
        s = record['得分']
        if s > 0: cols[4].markdown(f":{record['莊家顏色']}[**{s} 分**]")
        else: cols[4].write(f"({abs(s)}) 分")
        if cols[5].button("🗑️", key=f"del_{i}"):
            st.session_state.history.pop(i)
            save_data(st.session_state.history)
            st.rerun()
else:
    st.info("待機中...")