# ---------------------------------------------------------
# 專案名稱：迷你橋牌大會計分系統 - 專業分流版 (Pro Version)
# 開發重點：實作 Open/Closed Room 獨立存取空間，確保賽事資訊安全隔離
# ---------------------------------------------------------

import streamlit as st
import pandas as pd
import os

# --- 1. 賽室分流入口 (Entry Gate) ---
# 利用 Session State 判定使用者目前所在的「邏輯空間」
if 'room_choice' not in st.session_state:
    st.set_page_config(page_title="大會計分分流入口", layout="centered")
    st.title("🏆 迷你橋牌大會計分系統")
    st.subheader("請選擇您的賽室位置：")
    st.write("---")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔴 進入 公開室 (Open Room)", use_container_width=True):
            st.session_state.room_choice = "Open"
            st.rerun()
    with c2:
        if st.button("🔵 進入 開閉室 (Closed Room)", use_container_width=True):
            st.session_state.room_choice = "Closed"
            st.rerun()
    
    st.warning("⚠️ 注意：根據賽制，兩室成績嚴格隔離，請務必確認您的位置。")
    st.stop() # 阻擋程式往下執行，直到使用者選擇房間

# --- 2. 空間隔離設定 (Space Isolation) ---
ROOM = st.session_state.room_choice

# 動態生成檔名，達成數據物理隔離
# Open Room 存入 db_open.csv, Closed Room 存入 db_closed.csv
DB_FILE = f"db_{ROOM.lower()}.csv"

st.set_page_config(page_title=f"{ROOM} Room - 專用終端", layout="wide")
st.title(f"📍 當前賽室：{'🔴 公開室 (Open Room)' if ROOM == 'Open' else '🔵 開閉室 (Closed Room)'}")

# --- 3. 資料存取函式 ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            return pd.read_csv(DB_FILE).to_dict('records')
        except:
            return []
    return []

def save_data(data):
    pd.DataFrame(data).to_csv(DB_FILE, index=False, encoding="utf-8-sig")

if 'history' not in st.session_state:
    st.session_state.history = load_data()
if 'contract_locked' not in st.session_state:
    st.session_state.contract_locked = False

# --- 4. 側邊欄控制 ---
st.sidebar.header(f"⚙️ {ROOM} 室管理")
if st.sidebar.button("⬅️ 返回分流入口"):
    # 安全清除 Session，防止資料交叉污染
    del st.session_state.room_choice
    st.session_state.history = []
    st.rerun()

st.sidebar.divider()
if st.sidebar.button("🗑️ 清空本室所有紀錄", type="primary"):
    st.session_state.history = []
    if os.path.exists(DB_FILE): 
        os.remove(DB_FILE)
    st.session_state.contract_locked = False
    st.rerun()

# --- 5. 計分與合約邏輯 ---
st.header("1. 設定合約")
lock = st.session_state.contract_locked

col1, col2 = st.columns(2)
board_no = col1.number_input("🔢 牌號 (Board No.)", 1, 32, 1, disabled=lock)
attacker = col2.radio("⚔️ 莊家方", ["NS", "EW"], horizontal=True, disabled=lock)
at_color = "red" if attacker == "NS" else "green"

suit = st.selectbox("王牌花色", ["無王 (NT)", "高花 (M: ♠️/♥️)", "低花 (m: ♦️/♣️)"], disabled=lock)
ctype = st.radio("合約等級", ["部分合約", "成局合約"], horizontal=True, disabled=lock)

# 迷你橋牌計算邏輯
ts = 1 if "無王" in suit else (2 if "高花" in suit else 3)
level = (3 if ts==1 else (4 if ts==2 else 5)) if "成局" in ctype else 1
target = level + 6

if not lock:
    if st.button("✅ 鎖定合約，開始打牌", use_container_width=True):
        st.session_state.contract_locked = True
        st.rerun()
else:
    st.warning(f"🔒 合約鎖定中：由 {attacker} 主打 {suit.split(' ')[0]} (目標需吃足 {target} 磴)")
    st.divider()
    st.header("2. 輸入結果")
    tricks = st.number_input("莊家實際吃到幾磴？", 0, 13, target)
    
    if st.button("💾 結算並儲存本局成績", use_container_width=True):
        # 計算得分
        base = (40 + (level-1)*30) if ts==1 else (level*30 if ts==2 else level*20)
        if tricks >= target:
            final_score = base + (tricks-target)*(30 if ts<=2 else 20) + (300 if "成局" in ctype else 50)
            res_desc = f"過關 ({tricks} 磴)"
        else:
            final_score = -(target-tricks)*50
            res_desc = f"倒約 (僅 {tricks} 磴)"
            
        st.session_state.history.append({
            "牌號": board_no, 
            "莊家": attacker, 
            "合約": f"{level}{suit[0]}", 
            "結果": res_desc, 
            "得分": final_score, 
            "顏色": at_color
        })
        save_data(st.session_state.history)
        st.session_state.contract_locked = False
        st.rerun()

# --- 6. 顯示紀錄表 ---
st.divider()
st.subheader(f"📊 {ROOM} Room 歷史紀錄表")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    st.dataframe(df.drop(columns=['顏色']), use_container_width=True) # 隱藏顏色欄位，讓表格更乾淨
    
    # 導出功能
    csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label=f"📥 下載 {ROOM} 室正式 CSV 報表", 
        data=csv, 
        file_name=f"bridge_{ROOM.lower()}_records.csv",
        mime="text/csv"
    )
else:
    st.info("目前尚無比賽紀錄，請於上方輸入牌號與合約開始。")