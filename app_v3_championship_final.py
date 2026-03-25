import streamlit as st
import pandas as pd
import os

# --- 1. 賽室分流入口 ---
if 'room_choice' not in st.session_state:
    st.set_page_config(page_title="迷你橋牌大會分流入口", layout="centered")
    st.title("🏆 迷你橋牌大會計分系統")
    st.subheader("請選擇您的賽室位置：")
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔴 進入 公開室 (Open Room)", use_container_width=True):
            st.session_state.room_choice = "Open"; st.rerun()
    with c2:
        if st.button("🔵 進入 開閉室 (Closed Room)", use_container_width=True):
            st.session_state.room_choice = "Closed"; st.rerun()
    st.stop() 

# --- 2. 空間隔離與路徑設定 ---
ROOM = st.session_state.room_choice
DB_FILE = f"db_{ROOM.lower()}.csv"
OTHER_DB_FILE = f"db_{('closed' if ROOM == 'Open' else 'open')}.csv"

st.set_page_config(page_title=f"{ROOM} Room - 專用終端", layout="wide")
st.title(f"📍 當前賽室：{'🔴 公開室' if ROOM == 'Open' else '🔵 開閉室'}")

# --- 3. 資料存取函式 ---
def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE).to_dict('records')
        except: return []
    return []

def save_data(data):
    pd.DataFrame(data).to_csv(DB_FILE, index=False, encoding="utf-8-sig")

if 'history' not in st.session_state: st.session_state.history = load_data()
if 'contract_locked' not in st.session_state: st.session_state.contract_locked = False

# --- 4. 側邊欄控制 ---
st.sidebar.header(f"⚙️ {ROOM} 室管理")
if st.sidebar.button("⬅️ 返回入口"):
    del st.session_state.room_choice; st.rerun()
if st.sidebar.button("🗑️ 清空紀錄", type="primary"):
    st.session_state.history = []; st.session_state.contract_locked = False
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.rerun()

# --- 5. 點力輸入區 ---
st.header("1. 牌號與點力 (HCP)")
lock = st.session_state.contract_locked
board_no = st.number_input("🔢 牌號 (Board No.)", 1, 32, 1, disabled=lock)

# 智慧預填偵測
if not lock and os.path.exists(OTHER_DB_FILE):
    try:
        df_other = pd.read_csv(OTHER_DB_FILE)
        match = df_other[df_other['牌號'] == board_no]
        if not match.empty:
            st.success(f"✨ 偵測到另一室點力，可點擊下方按鈕自動帶入。")
            if st.button("📥 一鍵沿用另一室點力"):
                d = match.iloc[0]
                st.session_state.n, st.session_state.e = int(d['N_HCP']), int(d['E_HCP'])
                st.session_state.s, st.session_state.w = int(d['S_HCP']), int(d['W_HCP'])
                st.rerun()
    except: pass

c1, c2, c3, c4 = st.columns(4)
n = c1.number_input("🔴 北", 0, 40, key="n", disabled=lock)
e = c2.number_input("🟢 東", 0, 40, key="e", disabled=lock)
s = c3.number_input("🔴 南", 0, 40, key="s", disabled=lock)
w = c4.number_input("🟢 西", 0, 40, key="w", disabled=lock)

# --- 6. 合約與結果 (含物理防禦) ---
if (n+e+s+w) == 40:
    st.divider(); st.header("2. 設定合約")
    ns_hcp, ew_hcp = n+s, e+w
    if ns_hcp > 20: attacker = "NS"
    elif ew_hcp > 20: attacker = "EW"
    else: attacker = st.radio("⚔️ 莊家", ["NS", "EW"], horizontal=True, disabled=lock)
    at_color = "red" if attacker == "NS" else "green"
    col1, col2 = st.columns(2)
    suit = col1.selectbox("王牌花色", ["無王 (NT)", "高花 (M)", "低花 (m)"], disabled=lock)
    ctype = col2.radio("等級", ["部分合約", "成局合約"], horizontal=True, disabled=lock)
    ts = 1 if "無王" in suit else (2 if "高花" in suit else 3)
    level = (3 if ts==1 else (4 if ts==2 else 5)) if "成局" in ctype else 1
    target = level + 6

    if not lock:
        st.info(f"🔔 確認由 {attacker} 主打 {level}{suit[0]} (需吃足 {target} 磴)")
        if st.button("✅ 鎖定合約，開始打牌", use_container_width=True):
            st.session_state.contract_locked = True; st.rerun()
    else:
        st.warning(f"🔒 鎖定中：{attacker} 主打 {level}{suit[0]} (目標 {target} 磴)")
        st.divider(); st.header("3. 輸入結果")
        tricks = st.number_input("莊家實際吃到幾磴？", 0, 14, target) # 故意放寬到 14 讓測試能輸入錯誤

        # 🚀 【物理防禦：如果 >13，存檔按鈕消失，換成紅字錯誤】
        if tricks > 13:
            st.error("🚨 嚴重錯誤：一副牌最多只有 13 磴！請修正數字後才能儲存。")
            st.button("🚫 數據錯誤，無法儲存", disabled=True, use_container_width=True)
        else:
            if st.button("💾 結算並儲存成績", use_container_width=True):
                base = (40 + (level-1)*30) if ts==1 else (level*30 if ts==2 else level*20)
                if tricks >= target:
                    score = base + (tricks-target)*(30 if ts<=2 else 20) + (300 if "成局" in ctype else 50)
                    res = f"過關 ({tricks})"
                else:
                    score = -(target-tricks)*50; res = f"倒約 ({tricks})"
                st.session_state.history.append({
                    "牌號": board_no, "莊家": attacker, "合約": f"{level}{suit[0]}", 
                    "結果": res, "得分": score, "N_HCP": n, "E_HCP": e, "S_HCP": s, "W_HCP": w
                })
                save_data(st.session_state.history)
                st.session_state.contract_locked = False; st.rerun()
else:
    if not lock: st.info("💡 點力總和須為 40 點才會解鎖合約設定。")

# --- 7. 顯示紀錄表 ---
st.divider(); st.subheader(f"📊 {ROOM} 室歷史紀錄表")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df.drop(columns=['N_HCP','E_HCP','S_HCP','W_HCP'], errors='ignore'), use_container_width=True)