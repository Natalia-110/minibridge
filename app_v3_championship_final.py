# ---------------------------------------------------------
# 專案名稱：迷你橋牌大會計分系統 - V3 決賽旗艦版 (Final)
# 核心功能：
# 1. Open/Closed Room 實體檔案分流。
# 2. 智慧預填：自動偵測另一室是否完賽，一鍵沿用點力。
# 3. 跨系統防呆：手動輸入時比對兩室點力，不符則紅燈阻擋。
# 4. 極限值防護：後端阻擋非法磴數 (>13 或 <0)，確保計分合理。
# ---------------------------------------------------------

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
            st.session_state.room_choice = "Open"
            st.rerun()
    with c2:
        if st.button("🔵 進入 開閉室 (Closed Room)", use_container_width=True):
            st.session_state.room_choice = "Closed"
            st.rerun()
    
    st.warning("⚠️ 注意：根據賽制，兩室成績嚴格隔離，請務必確認您的位置。")
    st.stop() 

# --- 2. 空間隔離與路徑設定 ---
ROOM = st.session_state.room_choice
DB_FILE = f"db_{ROOM.lower()}.csv"

OTHER_ROOM = "Closed" if ROOM == "Open" else "Open"
OTHER_DB_FILE = f"db_{OTHER_ROOM.lower()}.csv"

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
if st.sidebar.button("⬅️ 返回分流入口 (切換賽室)"):
    del st.session_state.room_choice
    st.session_state.history = []
    st.rerun()

st.sidebar.divider()
if st.sidebar.button("🗑️ 清空本室所有紀錄", type="primary"):
    st.session_state.history = []
    if os.path.exists(DB_FILE): os.remove(DB_FILE)
    st.session_state.contract_locked = False
    st.rerun()

# --- 5. 點力輸入與合約邏輯 ---
st.header("1. 牌號與點力 (HCP)")
lock = st.session_state.contract_locked

col_b, col_empty = st.columns([1, 3])
board_no = col_b.number_input("🔢 牌號 (Board No.)", 1, 32, 1, key="board_no", disabled=lock)

# --- [智慧預填功能：偵測另一室點力] ---
other_played = False
other_hcp = {}
if not lock and os.path.exists(OTHER_DB_FILE):
    try:
        df_other = pd.read_csv(OTHER_DB_FILE)
        board_match = df_other[df_other['牌號'] == board_no]
        if not board_match.empty:
            other_data = board_match.iloc[0]
            if 'N_HCP' in other_data:
                other_played = True
                other_hcp = {
                    'n': int(other_data['N_HCP']), 'e': int(other_data['E_HCP']),
                    's': int(other_data['S_HCP']), 'w': int(other_data['W_HCP'])
                }
    except: pass

if other_played and not lock:
    st.success(f"✨ 系統偵測到【{OTHER_ROOM} 室】已完成第 {board_no} 牌的點力紀錄！")
    if st.button("📥 一鍵沿用另一室點力 (免手動輸入)"):
        st.session_state.n = other_hcp['n']
        st.session_state.e = other_hcp['e']
        st.session_state.s = other_hcp['s']
        st.session_state.w = other_hcp['w']
        st.rerun()

# 點力輸入區
c1, c2, c3, c4 = st.columns(4)
n = c1.number_input("🔴 北 HCP", 0, 40, key="n", disabled=lock)
e = c2.number_input("🟢 東 HCP", 0, 40, key="e", disabled=lock)
s = c3.number_input("🔴 南 HCP", 0, 40, key="s", disabled=lock)
w = c4.number_input("🟢 西 HCP", 0, 40, key="w", disabled=lock)

# 判斷總點力是否為 40
if (n+e+s+w) == 40:
    st.divider()
    st.header("2. 設定合約")
    
    ns_hcp, ew_hcp = n+s, e+w
    if ns_hcp > 20: attacker = "NS"
    elif ew_hcp > 20: attacker = "EW"
    else: attacker = st.radio("⚔️ 點力平手，請手動選擇莊家", ["NS", "EW"], horizontal=True, disabled=lock)
        
    at_color = "red" if attacker == "NS" else "green"
    
    col_s1, col_s2 = st.columns(2)
    suit = col_s1.selectbox("王牌花色", ["無王 (NT)", "高花 (M: ♠️/♥️)", "低花 (m: ♦️/♣️)"], disabled=lock)
    ctype = col_s2.radio("合約等級", ["部分合約", "成局合約"], horizontal=True, disabled=lock)

    ts = 1 if "無王" in suit else (2 if "高花" in suit else 3)
    level = (3 if ts==1 else (4 if ts==2 else 5)) if "成局" in ctype else 1
    target = level + 6

    if not lock:
        st.info(f"🔔 **合約確認**：由 :{at_color}[**{attacker}**] 主打 **{level}{suit[0]}** ({ctype})，目標需吃足 **{target}** 磴")
        
        # --- [跨室防呆檢核] ---
        if st.button("✅ 鎖定合約，開始打牌", use_container_width=True):
            conflict = False
            if os.path.exists(OTHER_DB_FILE):
                try:
                    df_other = pd.read_csv(OTHER_DB_FILE)
                    board_match = df_other[df_other['牌號'] == board_no]
                    if not board_match.empty:
                        other_data = board_match.iloc[0]
                        if 'N_HCP' in other_data: 
                            if (n != other_data['N_HCP'] or e != other_data['E_HCP'] or 
                                s != other_data['S_HCP'] or w != other_data['W_HCP']):
                                conflict = True
                except: pass
            
            if conflict:
                st.error(f"🚨 嚴重衝突警告：您輸入的四家點力與【{OTHER_ROOM} 室】紀錄不一致！請呼叫裁判核對實體牌萍。")
            else:
                st.session_state.contract_locked = True
                st.rerun()
                
    else:
        st.warning(f"🔒 鎖定中：:{at_color}[**{attacker}**] 主打 **{level}{suit[0]}** (目標 {target} 磴)")
        st.divider()
        st.header("3. 輸入結果")
        
        # 即使前端有 0~13 的限制，後端依舊要防護
        tricks = st.number_input("莊家實際吃到幾磴？", 0, 13, target)
        
        if st.button("💾 結算並儲存成績", use_container_width=True):
            # --- [極限值防護：後端阻擋] ---
            if tricks > 13:
                st.error("🚨 輸入錯誤：一副牌最多只有 13 磴喔！請重新確認成績。")
            else:
                base = (40 + (level-1)*30) if ts==1 else (level*30 if ts==2 else level*20)
                if tricks >= target:
                    final_score = base + (tricks-target)*(30 if ts<=2 else 20) + (300 if "成局" in ctype else 50)
                    res_desc = f"過關 ({tricks})"
                else:
                    final_score = -(target-tricks)*50
                    res_desc = f"倒約 ({tricks})"
                    
                st.session_state.history.append({
                    "牌號": board_no, "莊家": attacker, "合約": f"{level}{suit[0]}", 
                    "結果": res_desc, "得分": final_score, "顏色": at_color,
                    "N_HCP": n, "E_HCP": e, "S_HCP": s, "W_HCP": w
                })
                save_data(st.session_state.history)
                st.session_state.contract_locked = False
                st.rerun()
else:
    if not lock:
        st.info("💡 請於上方輸入四家點力，總和須為 40 點才會解鎖合約設定。")

# --- 6. 顯示紀錄表 ---
st.divider()
st.subheader(f"📊 {ROOM} Room 歷史紀錄表")
if st.session_state.history:
    df = pd.DataFrame(st.session_state.history)
    cols_to_drop = ['顏色', 'N_HCP', 'E_HCP', 'S_HCP', 'W_HCP']
    st.dataframe(df.drop(columns=cols_to_drop, errors='ignore'), use_container_width=True)
    
    csv = df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label=f"📥 下載 {ROOM} 室 CSV 報表", 
        data=csv, file_name=f"bridge_{ROOM.lower()}_records.csv", mime="text/csv"
    )