import streamlit as st
import pandas as pd
import json
import os
import hashlib
from datetime import datetime, date
import plotly.graph_objects as go

# ─── הגדרות ───────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="פנקס 💰 מעקב הוצאות",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CATEGORIES = {
    "expense": [
        {"id": "food",          "label": "🍔 אוכל"},
        {"id": "rent",          "label": "🏠 שכירות"},
        {"id": "transport",     "label": "🚗 תחבורה"},
        {"id": "health",        "label": "❤️ בריאות"},
        {"id": "shopping",      "label": "🛍️ קניות"},
        {"id": "entertainment", "label": "🎬 בידור"},
        {"id": "utilities",     "label": "💡 חשבונות"},
        {"id": "other_ex",      "label": "➖ אחר"},
    ],
    "income": [
        {"id": "salary",        "label": "💼 משכורת"},
        {"id": "freelance",     "label": "🖥️ פרילנס"},
        {"id": "investment",    "label": "📈 השקעות"},
        {"id": "gift",          "label": "🎁 מתנה"},
        {"id": "other_in",      "label": "➕ אחר"},
    ],
}
ALL_CATS = {c["id"]: c["label"] for cats in CATEGORIES.values() for c in cats}
MONTH_NAMES = {1:"ינואר",2:"פברואר",3:"מרץ",4:"אפריל",5:"מאי",6:"יוני",
               7:"יולי",8:"אוגוסט",9:"ספטמבר",10:"אוקטובר",11:"נובמבר",12:"דצמבר"}
PIE_COLORS = ["#4361ee","#f72585","#4cc9f0","#f8961e","#43aa8b","#fee440","#7209b7","#90be6d"]

# ─── עזרים ───────────────────────────────────────────────────────────────────
def hash_pass(p): return hashlib.sha256(p.encode()).hexdigest()
def fmt_ils(n): return f"₪{abs(n):,.2f}"
def get_month_label(ym):
    y, m = ym.split("-")
    return f"{MONTH_NAMES[int(m)]} {y}"
def user_file(username, kind):
    os.makedirs("data", exist_ok=True)
    return f"data/{username}_{kind}.json"
def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
def get_months(txs):
    months = set(t["date"][:7] for t in txs)
    now = datetime.now()
    months.add(f"{now.year}-{now.month:02d}")
    return sorted(months, reverse=True)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Assistant', sans-serif !important;
    direction: rtl;
    background: #f0f4ff;
    color: #1a1a2e;
}
.main { background: #f0f4ff; }
.block-container { padding: 1.5rem 2rem 4rem; max-width: 980px; }

.card { border-radius: 18px; padding: 20px 22px; text-align: center; margin-bottom: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
.card-balance { background: linear-gradient(135deg, #4361ee, #7209b7); color: white; }
.card-income  { background: linear-gradient(135deg, #43aa8b, #4cc9f0); color: white; }
.card-expense { background: linear-gradient(135deg, #f72585, #f8961e); color: white; }
.card-label { font-size: 12px; opacity: 0.85; margin-bottom: 6px; }
.card-value { font-size: 28px; font-weight: 800; }

.tx-row { background: white; border-radius: 14px; padding: 14px 18px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.tx-cat  { font-size: 12px; color: #888; margin-top: 2px; }
.tx-note { font-size: 15px; font-weight: 700; color: #1a1a2e; }
.tx-plus  { color: #43aa8b; font-weight: 800; font-size: 17px; }
.tx-minus { color: #f72585; font-weight: 800; font-size: 17px; }

.stButton > button { background: linear-gradient(135deg, #4361ee, #7209b7) !important; color: white !important; border: none !important; border-radius: 12px !important; font-family: 'Assistant', sans-serif !important; font-size: 15px !important; font-weight: 700 !important; padding: 10px 24px !important; box-shadow: 0 4px 15px rgba(67,97,238,0.3) !important; }
.stButton > button:hover { transform: translateY(-2px) !important; }

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input { background: white !important; border: 2px solid #e8ecff !important; border-radius: 12px !important; color: #1a1a2e !important; font-family: 'Assistant', sans-serif !important; font-size: 15px !important; }

.stSelectbox > div > div { background: white !important; border: 2px solid #e8ecff !important; border-radius: 12px !important; color: #1a1a2e !important; }

.stTabs [data-baseweb="tab-list"] { background: white; border-radius: 14px; gap: 4px; padding: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.06); }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #888 !important; border-radius: 10px !important; font-family: 'Assistant', sans-serif !important; font-size: 14px !important; font-weight: 600 !important; padding: 8px 18px !important; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg, #4361ee, #7209b7) !important; color: white !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 16px !important; }

.stRadio > div { flex-direction: row !important; gap: 12px; }
.stRadio > div > label { background: white; border: 2px solid #e8ecff; border-radius: 12px; padding: 10px 22px; color: #888 !important; font-weight: 600 !important; cursor: pointer; }

.stSelectbox label, .stNumberInput label, .stTextInput label, .stDateInput label, .stRadio label { color: #555 !important; font-size: 13px !important; font-weight: 600 !important; }

#MainMenu, footer, header { visibility: hidden; }

.section-title { font-size: 13px; color: #888; font-weight: 700; letter-spacing: 0.06em; margin: 20px 0 12px; text-transform: uppercase; }
.budget-bar-bg { background: #e8ecff; border-radius: 6px; height: 10px; width: 100%; margin: 6px 0 4px; }
.budget-bar-fill { height: 10px; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# מסך כניסה
# ══════════════════════════════════════════════════════════════════════════════
USERS_FILE = "data/users.json"
os.makedirs("data", exist_ok=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username  = ""

if not st.session_state.logged_in:
    st.markdown("""
    <div style='text-align:center;margin-top:30px'>
        <div style='font-size:56px'>💰</div>
        <h1 style='font-size:36px;font-weight:800;background:linear-gradient(135deg,#4361ee,#f72585);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:8px 0'>פנקס</h1>
        <p style='color:#888;font-size:16px'>מעקב הוצאות והכנסות אישי</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab_login, tab_register = st.tabs(["🔑 כניסה", "✨ הרשמה"])

        with tab_login:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            login_user = st.text_input("שם משתמש", key="login_user", placeholder="הכנס שם משתמש")
            login_pass = st.text_input("סיסמה", type="password", key="login_pass", placeholder="הכנס סיסמה")
            if st.button("כניסה 🚀", use_container_width=True, key="btn_login"):
                users = load_json(USERS_FILE, {})
                if login_user in users and users[login_user] == hash_pass(login_pass):
                    st.session_state.logged_in = True
                    st.session_state.username  = login_user
                    st.rerun()
                else:
                    st.error("שם משתמש או סיסמה שגויים")

        with tab_register:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            reg_user  = st.text_input("שם משתמש", key="reg_user",  placeholder="בחר שם משתמש")
            reg_pass  = st.text_input("סיסמה",     type="password", key="reg_pass",  placeholder="בחר סיסמה")
            reg_pass2 = st.text_input("אימות סיסמה", type="password", key="reg_pass2", placeholder="הכנס שוב את הסיסמה")
            if st.button("הרשמה ✨", use_container_width=True, key="btn_reg"):
                if not reg_user or not reg_pass:
                    st.error("נא למלא את כל השדות")
                elif reg_pass != reg_pass2:
                    st.error("הסיסמאות לא תואמות")
                else:
                    users = load_json(USERS_FILE, {})
                    if reg_user in users:
                        st.error("שם המשתמש כבר קיים")
                    else:
                        users[reg_user] = hash_pass(reg_pass)
                        save_json(USERS_FILE, users)
                        st.success("✅ נרשמת בהצלחה! עכשיו היכנס")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# האפליקציה הראשית
# ══════════════════════════════════════════════════════════════════════════════
username = st.session_state.username
TX_FILE  = user_file(username, "transactions")
BUD_FILE = user_file(username, "budgets")

if "transactions" not in st.session_state or st.session_state.get("_user") != username:
    st.session_state.transactions = load_json(TX_FILE, [])
    st.session_state.budgets      = load_json(BUD_FILE, {})
    st.session_state._user        = username

def save_all():
    save_json(TX_FILE,  st.session_state.transactions)
    save_json(BUD_FILE, st.session_state.budgets)

# כותרת
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(f"""
    <div style='display:flex;align-items:center;gap:12px;margin-bottom:4px'>
        <span style='font-size:36px'>💰</span>
        <div>
            <h1 style='font-size:28px;font-weight:800;margin:0;background:linear-gradient(135deg,#4361ee,#f72585);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>פנקס</h1>
            <p style='color:#888;font-size:13px;margin:0'>שלום, <b style="color:#4361ee">{username}</b> 👋</p>
        </div>
    </div>""", unsafe_allow_html=True)
with col_h2:
    if st.button("יציאה 👋"):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        for k in ["transactions","budgets","_user"]:
            st.session_state.pop(k, None)
        st.rerun()

# בחירת חודש
months       = get_months(st.session_state.transactions)
month_labels = [get_month_label(m) for m in months]
sel_idx      = st.selectbox("📅 חודש", range(len(months)), format_func=lambda i: month_labels[i])
sel_month    = months[sel_idx]
month_txs    = [t for t in st.session_state.transactions if t["date"][:7] == sel_month]

# כרטיסי סיכום
total_income  = sum(t["amount"] for t in month_txs if t["type"] == "income")
total_expense = sum(t["amount"] for t in month_txs if t["type"] == "expense")
balance       = total_income - total_expense

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="card card-balance"><div class="card-label">💳 יתרה</div><div class="card-value">{fmt_ils(balance)}</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="card card-income"><div class="card-label">📈 הכנסות</div><div class="card-value">{fmt_ils(total_income)}</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="card card-expense"><div class="card-label">📉 הוצאות</div><div class="card-value">{fmt_ils(total_expense)}</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
tab1, tab2, tab3, tab4 = st.tabs(["📊 סקירה", "📋 היסטוריה", "🎯 יעדים", "➕ הוסף עסקה"])

# ── סקירה ────────────────────────────────────────────────────────────────────
with tab1:
    exp_txs = [t for t in month_txs if t["type"] == "expense"]
    if exp_txs:
        cat_sums = {}
        for t in exp_txs:
            cat_sums[t["category"]] = cat_sums.get(t["category"], 0) + t["amount"]
        labels = [ALL_CATS.get(k, k) for k in cat_sums]
        values = list(cat_sums.values())
        col_pie, col_bar = st.columns([1, 1])
        with col_pie:
            fig = go.Figure(data=[go.Pie(
                labels=labels, values=values, hole=0.52,
                marker=dict(colors=PIE_COLORS[:len(labels)], line=dict(color="white", width=3)),
                textfont=dict(family="Assistant", size=12),
                hovertemplate="<b>%{label}</b><br>₪%{value:,.2f}<br>%{percent}<extra></extra>",
            )])
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Assistant", color="#1a1a2e"),
                showlegend=False, margin=dict(t=10,b=10,l=0,r=0), height=260,
                annotations=[dict(text=f"<b>{fmt_ils(total_expense)}</b>", x=0.5, y=0.5,
                    font=dict(size=14, color="#1a1a2e", family="Assistant"), showarrow=False)]
            )
            st.plotly_chart(fig, use_container_width=True)
        with col_bar:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            for i, (cat_id, val) in enumerate(sorted(cat_sums.items(), key=lambda x: x[1], reverse=True)):
                max_v = max(cat_sums.values())
                pct   = int((val / max_v) * 100)
                color = PIE_COLORS[i % len(PIE_COLORS)]
                label = ALL_CATS.get(cat_id, cat_id)
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;margin-bottom:3px">
                    <span style="font-size:13px;font-weight:600">{label}</span>
                    <span style="font-size:13px;font-weight:700;color:{color}">{fmt_ils(val)}</span>
                </div>
                <div class="budget-bar-bg"><div class="budget-bar-fill" style="width:{pct}%;background:{color}"></div></div>
                """, unsafe_allow_html=True)
    else:
        st.markdown("<br><div style='text-align:center;color:#aaa;padding:40px;font-size:16px'>😊 אין הוצאות בחודש זה</div>", unsafe_allow_html=True)

    if month_txs:
        st.markdown("<div class='section-title'>עסקאות אחרונות</div>", unsafe_allow_html=True)
        for t in month_txs[:5]:
            cat_label = ALL_CATS.get(t["category"], t["category"])
            note = t.get("note") or cat_label
            sign = "+" if t["type"] == "income" else "−"
            cls  = "tx-plus" if t["type"] == "income" else "tx-minus"
            st.markdown(f'<div class="tx-row"><div><div class="tx-note">{note}</div><div class="tx-cat">{cat_label} · {t["date"]}</div></div><div class="{cls}">{sign}{fmt_ils(t["amount"])}</div></div>', unsafe_allow_html=True)

# ── היסטוריה ─────────────────────────────────────────────────────────────────
with tab2:
    if not month_txs:
        st.markdown("<br><div style='text-align:center;color:#aaa;padding:40px'>אין עסקאות בחודש זה</div>", unsafe_allow_html=True)
    else:
        all_opts = ["הכל"] + [c["label"] for cats in CATEGORIES.values() for c in cats]
        all_ids  = ["all"]  + [c["id"]    for cats in CATEGORIES.values() for c in cats]
        fi       = st.selectbox("סנן לפי קטגוריה", range(len(all_opts)), format_func=lambda i: all_opts[i])
        filtered = month_txs if all_ids[fi] == "all" else [t for t in month_txs if t["category"] == all_ids[fi]]
        st.markdown(f"<div class='section-title'>{len(filtered)} עסקאות — {get_month_label(sel_month)}</div>", unsafe_allow_html=True)
        for t in filtered:
            cat_label = ALL_CATS.get(t["category"], t["category"])
            note = t.get("note") or cat_label
            sign = "+" if t["type"] == "income" else "−"
            cls  = "tx-plus" if t["type"] == "income" else "tx-minus"
            col_tx, col_del = st.columns([10, 1])
            with col_tx:
                st.markdown(f'<div class="tx-row"><div><div class="tx-note">{note}</div><div class="tx-cat">{cat_label} · {t["date"]}</div></div><div class="{cls}">{sign}{fmt_ils(t["amount"])}</div></div>', unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_{t['id']}"):
                    st.session_state.transactions = [x for x in st.session_state.transactions if x["id"] != t["id"]]
                    save_all()
                    st.rerun()
        if filtered:
            df = pd.DataFrame([{"תאריך": t["date"], "סוג": "הכנסה" if t["type"] == "income" else "הוצאה",
                "קטגוריה": ALL_CATS.get(t["category"], ""), "הערה": t.get("note", ""), "סכום": t["amount"]} for t in filtered])
            st.download_button("⬇️ ייצא ל-CSV", df.to_csv(index=False, encoding="utf-8-sig"),
                               file_name=f"פנקס_{get_month_label(sel_month)}.csv", mime="text/csv")

# ── יעדים ────────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='section-title'>יעדי תקציב חודשיים</div>", unsafe_allow_html=True)
    for cat in CATEGORIES["expense"]:
        cat_id, cat_label = cat["id"], cat["label"]
        spent  = sum(t["amount"] for t in month_txs if t["type"] == "expense" and t["category"] == cat_id)
        budget = st.session_state.budgets.get(cat_id, 0)
        over   = budget > 0 and spent > budget
        pct    = int(min((spent / budget) * 100, 100)) if budget > 0 else 0
        bar_color = "#f72585" if over else "#43aa8b"
        border    = "#fde8f0" if over else "#e8ecff"
        st.markdown(f"""
        <div style="background:white;border:2px solid {border};border-radius:16px;padding:16px 20px;margin-bottom:10px;box-shadow:0 2px 10px rgba(0,0,0,0.05)">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:{'8px' if budget else '0'}">
                <span style="font-size:16px;font-weight:700">{cat_label}</span>
                <span style="font-size:13px;color:{'#f72585' if over else '#888'};font-weight:600">
                    {fmt_ils(spent)} מתוך {fmt_ils(budget) if budget else 'לא הוגדר'} {'⚠️' if over else ''}
                </span>
            </div>
            {"" if not budget else f'<div class="budget-bar-bg"><div class="budget-bar-fill" style="width:{pct}%;background:{bar_color}"></div></div>'}
        </div>""", unsafe_allow_html=True)
        col_inp, col_btn = st.columns([3, 1])
        with col_inp:
            new_bud = st.number_input("יעד", min_value=0.0, step=100.0,
                                       value=float(budget) if budget else 0.0,
                                       key=f"bud_{cat_id}", label_visibility="collapsed")
        with col_btn:
            if st.button("💾 שמור", key=f"savebud_{cat_id}"):
                st.session_state.budgets[cat_id] = new_bud
                save_all()
                st.success("✅ נשמר!")
                st.rerun()

# ── הוסף עסקה ────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    tx_type = st.radio("סוג עסקה", ["expense", "income"],
                        format_func=lambda x: "💸 הוצאה" if x == "expense" else "💰 הכנסה",
                        horizontal=True)
    col_a, col_b = st.columns(2)
    with col_a:
        amount  = st.number_input("סכום (₪)", min_value=0.01, step=10.0, format="%.2f")
    with col_b:
        tx_date = st.date_input("תאריך", value=date.today())
    cats     = CATEGORIES[tx_type]
    cat_ids  = [c["id"]    for c in cats]
    cat_lbls = [c["label"] for c in cats]
    cat_sel  = st.selectbox("קטגוריה", range(len(cats)), format_func=lambda i: cat_lbls[i])
    category = cat_ids[cat_sel]
    note     = st.text_input("הערה (אופציונלי)", placeholder="למשל: סופרמרקט, שכירות חודשית…")

    grad = "linear-gradient(135deg,#f72585,#f8961e)" if tx_type == "expense" else "linear-gradient(135deg,#43aa8b,#4cc9f0)"
    st.markdown(f"<style>div[data-testid='stButton'] > button[kind='primary'] {{ background: {grad} !important; }}</style>", unsafe_allow_html=True)

    btn_label = "➕ הוסף הוצאה" if tx_type == "expense" else "💰 הוסף הכנסה"
    if st.button(btn_label, type="primary", use_container_width=True):
        if amount > 0:
            new_tx = {"id": int(datetime.now().timestamp() * 1000), "type": tx_type,
                      "amount": amount, "category": category, "note": note, "date": tx_date.isoformat()}
            st.session_state.transactions.insert(0, new_tx)
            save_all()
            st.success(f"✅ נוסף! {cat_lbls[cat_sel]} — {fmt_ils(amount)}")
            st.balloons()
        else:
            st.error("אנא הכנס סכום גדול מ-0")
