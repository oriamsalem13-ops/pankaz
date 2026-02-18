import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# ─── הגדרות ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="פנקס 📒 מעקב הוצאות",
    page_icon="📒",
    layout="wide",
    initial_sidebar_state="collapsed"
)

DATA_FILE = "transactions.json"
BUDGETS_FILE = "budgets.json"

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

MONTH_NAMES = {
    1:"ינואר", 2:"פברואר", 3:"מרץ", 4:"אפריל",
    5:"מאי", 6:"יוני", 7:"יולי", 8:"אוגוסט",
    9:"ספטמבר", 10:"אוקטובר", 11:"נובמבר", 12:"דצמבר"
}

PIE_COLORS = ["#f87171","#fb923c","#fbbf24","#a3e635",
              "#34d399","#38bdf8","#818cf8","#e879f9"]

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Assistant', sans-serif !important;
    direction: rtl;
    background-color: #0d0d0d;
    color: #f5f0e8;
}

.main { background-color: #0d0d0d; }
.block-container { padding: 1.5rem 2rem 4rem; max-width: 960px; }

h1, h2, h3 { font-family: 'Assistant', sans-serif !important; color: #f5f0e8; }

/* כרטיסי סיכום */
.card {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 14px;
    padding: 18px 22px;
    text-align: center;
    margin-bottom: 8px;
}
.card-label { font-size: 12px; color: #555; margin-bottom: 6px; letter-spacing: 0.05em; }
.card-value { font-size: 26px; font-weight: 700; }
.green  { color: #4ade80; }
.red    { color: #f87171; }
.white  { color: #f5f0e8; }

/* שורת עסקה */
.tx-row {
    background: #111;
    border: 1px solid #1e1e1e;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.tx-cat  { font-size: 13px; color: #888; }
.tx-note { font-size: 15px; font-weight: 600; }
.tx-plus  { color: #4ade80; font-weight: 700; font-size: 16px; }
.tx-minus { color: #f87171; font-weight: 700; font-size: 16px; }

/* כפתורים */
.stButton > button {
    background: #1e1e1e !important;
    color: #f5f0e8 !important;
    border: 1px solid #333 !important;
    border-radius: 8px !important;
    font-family: 'Assistant', sans-serif !important;
    font-size: 14px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #2a2a2a !important;
    border-color: #555 !important;
}

/* אינפוטים */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stDateInput > div > div > input,
.stSelectbox > div > div {
    background: #111 !important;
    border: 1px solid #2a2a2a !important;
    border-radius: 8px !important;
    color: #f5f0e8 !important;
    font-family: 'Assistant', sans-serif !important;
    direction: rtl;
}

/* טאבים */
.stTabs [data-baseweb="tab-list"] {
    background: #111;
    border-radius: 10px;
    gap: 4px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #888 !important;
    border-radius: 8px !important;
    font-family: 'Assistant', sans-serif !important;
    font-size: 14px !important;
    padding: 8px 18px !important;
}
.stTabs [aria-selected="true"] {
    background: #f5f0e8 !important;
        color: #0d0d0d !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* סלקטבוקס */
.stSelectbox label, .stNumberInput label, .stTextInput label,
.stDateInput label, .stRadio label { color: #888 !important; font-size: 13px !important; }

/* רדיו */
.stRadio > div { flex-direction: row !important; gap: 10px; }
.stRadio > div > label {
    background: #111;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 8px 20px;
    color: #888 !important;
    cursor: pointer;
}

/* הסתר watermark */
#MainMenu, footer, header { visibility: hidden; }

/* מחיצות */
hr { border-color: #1e1e1e !important; }

.section-title {
    font-size: 11px;
    color: #555;
    letter-spacing: 0.08em;
    margin: 18px 0 10px;
    text-transform: uppercase;
}

.budget-bar-bg {
    background: #1e1e1e;
    border-radius: 4px;
    height: 8px;
    width: 100%;
    margin: 6px 0 4px;
}
.budget-bar-fill {
    height: 8px;
    border-radius: 4px;
    transition: width 0.5s ease;
}
</style>
""", unsafe_allow_html=True)


# ─── טעינה ושמירה ────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_budgets():
    if os.path.exists(BUDGETS_FILE):
        with open(BUDGETS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_budgets(budgets):
    with open(BUDGETS_FILE, "w", encoding="utf-8") as f:
        json.dump(budgets, f, ensure_ascii=False, indent=2)

if "transactions" not in st.session_state:
    st.session_state.transactions = load_data()
if "budgets" not in st.session_state:
    st.session_state.budgets = load_budgets()


# ─── עזרים ───────────────────────────────────────────────────────────────────
def fmt_ils(n):
    return f"₪{abs(n):,.2f}"

def get_month_label(ym: str):
    y, m = ym.split("-")
    return f"{MONTH_NAMES[int(m)]} {y}"

def get_months():
    months = set()
    for t in st.session_state.transactions:
        months.add(t["date"][:7])
    now = datetime.now()
    months.add(f"{now.year}-{now.month:02d}")
    return sorted(months, reverse=True)

def transactions_for_month(ym):
    return [t for t in st.session_state.transactions if t["date"][:7] == ym]


# ─── כותרת ───────────────────────────────────────────────────────────────────
col_title, col_add = st.columns([4, 1])
with col_title:
    st.markdown("# 📒 פנקס")
    st.markdown("<p style='color:#555;font-size:13px;margin-top:-12px'>מעקב הוצאות והכנסות</p>", unsafe_allow_html=True)

# ─── בחירת חודש ──────────────────────────────────────────────────────────────
months = get_months()
month_labels = [get_month_label(m) for m in months]
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
sel_idx = st.selectbox("📅 חודש", options=range(len(months)), format_func=lambda i: month_labels[i], key="month_sel")
selected_month = months[sel_idx]
month_txs = transactions_for_month(selected_month)

# ─── סיכום ───────────────────────────────────────────────────────────────────
total_income  = sum(t["amount"] for t in month_txs if t["type"] == "income")
total_expense = sum(t["amount"] for t in month_txs if t["type"] == "expense")
balance = total_income - total_expense

c1, c2, c3 = st.columns(3)
with c1:
    color = "green" if balance >= 0 else "red"
    st.markdown(f"""<div class="card">
        <div class="card-label">יתרה</div>
        <div class="card-value {color}">{fmt_ils(balance)}</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="card">
        <div class="card-label">הכנסות</div>
        <div class="card-value green">{fmt_ils(total_income)}</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="card">
        <div class="card-label">הוצאות</div>
        <div class="card-value red">{fmt_ils(total_expense)}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ─── טאבים ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📊 סקירה", "📋 היסטוריה", "🎯 יעדים", "➕ הוסף עסקה"])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — סקירה
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    expense_txs = [t for t in month_txs if t["type"] == "expense"]

    if expense_txs:
        # גרף עוגה
        cat_sums = {}
        for t in expense_txs:
            cat_sums[t["category"]] = cat_sums.get(t["category"], 0) + t["amount"]

        labels = [ALL_CATS.get(k, k) for k in cat_sums]
        values = list(cat_sums.values())

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker=dict(colors=PIE_COLORS[:len(labels)], line=dict(color="#0d0d0d", width=2)),
            textfont=dict(family="Assistant", size=13, color="#f5f0e8"),
            hovertemplate="<b>%{label}</b><br>₪%{value:,.2f}<br>%{percent}<extra></extra>",
        )])
        fig.update_layout(
            paper_bgcolor="#0d0d0d",
            plot_bgcolor="#0d0d0d",
            font=dict(family="Assistant", color="#f5f0e8"),
            showlegend=True,
            legend=dict(
                font=dict(family="Assistant", color="#f5f0e8", size=13),
                bgcolor="#111",
                bordercolor="#1e1e1e",
                borderwidth=1,
            ),
            margin=dict(t=20, b=20, l=0, r=0),
            height=320,
            annotations=[dict(
                text=f"<b>{fmt_ils(total_expense)}</b>",
                x=0.5, y=0.5, font=dict(size=16, color="#f5f0e8", family="Assistant"),
                showarrow=False
            )]
        )
        st.plotly_chart(fig, use_container_width=True)

        # סרגלי קטגוריות
        st.markdown("<div class='section-title'>פילוח לפי קטגוריה</div>", unsafe_allow_html=True)
        sorted_cats = sorted(cat_sums.items(), key=lambda x: x[1], reverse=True)
        max_val = sorted_cats[0][1] if sorted_cats else 1
        for cat_id, val in sorted_cats:
            pct = int((val / max_val) * 100)
            label = ALL_CATS.get(cat_id, cat_id)
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;margin-bottom:4px">
                <span style="font-size:14px">{label}</span>
                <span style="color:#f87171;font-size:14px;font-weight:600">{fmt_ils(val)}</span>
            </div>
            <div class="budget-bar-bg">
                <div class="budget-bar-fill" style="width:{pct}%;background:#f87171"></div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<br><div style='text-align:center;color:#333;padding:40px'>אין הוצאות בחודש זה</div>", unsafe_allow_html=True)

    # עסקאות אחרונות
    if month_txs:
        st.markdown("<div class='section-title'>עסקאות אחרונות</div>", unsafe_allow_html=True)
        for t in month_txs[:6]:
            cat_label = ALL_CATS.get(t["category"], t["category"])
            note = t.get("note") or cat_label
            sign = "+" if t["type"] == "income" else "−"
            color_cls = "tx-plus" if t["type"] == "income" else "tx-minus"
            st.markdown(f"""
            <div class="tx-row">
                <div>
                    <div class="tx-note">{note}</div>
                    <div class="tx-cat">{cat_label} · {t['date']}</div>
                </div>
                <div class="{color_cls}">{sign}{fmt_ils(t['amount'])}</div>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — היסטוריה
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    if not month_txs:
        st.markdown("<br><div style='text-align:center;color:#333;padding:40px'>אין עסקאות בחודש זה</div>", unsafe_allow_html=True)
    else:
        # פילטר קטגוריה
        all_cats_options = ["הכל"] + [c["label"] for cats in CATEGORIES.values() for c in cats]
        all_cats_ids     = ["all"]  + [c["id"]    for cats in CATEGORIES.values() for c in cats]
        filter_sel = st.selectbox("סנן לפי קטגוריה", options=range(len(all_cats_options)),
                                   format_func=lambda i: all_cats_options[i], key="hist_filter")
        filter_id = all_cats_ids[filter_sel]

        filtered = month_txs if filter_id == "all" else [t for t in month_txs if t["category"] == filter_id]
        st.markdown(f"<div class='section-title'>{len(filtered)} עסקאות — {get_month_label(selected_month)}</div>", unsafe_allow_html=True)

        for i, t in enumerate(filtered):
            cat_label = ALL_CATS.get(t["category"], t["category"])
            note = t.get("note") or cat_label
            sign = "+" if t["type"] == "income" else "−"
            color_cls = "tx-plus" if t["type"] == "income" else "tx-minus"

            col_tx, col_del = st.columns([9, 1])
            with col_tx:
                st.markdown(f"""
                <div class="tx-row">
                    <div>
                        <div class="tx-note">{note}</div>
                        <div class="tx-cat">{cat_label} · {t['date']}</div>
                    </div>
                    <div class="{color_cls}">{sign}{fmt_ils(t['amount'])}</div>
                </div>""", unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_{t['id']}"):
                    st.session_state.transactions = [x for x in st.session_state.transactions if x["id"] != t["id"]]
                    save_data(st.session_state.transactions)
                    st.rerun()

        # ייצוא CSV
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        if filtered:
            df = pd.DataFrame([{
                "תאריך": t["date"],
                "סוג": "הכנסה" if t["type"] == "income" else "הוצאה",
                "קטגוריה": ALL_CATS.get(t["category"], t["category"]),
                "הערה": t.get("note", ""),
                "סכום": t["amount"],
            } for t in filtered])
            csv = df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="⬇️ ייצא ל-CSV",
                data=csv,
                file_name=f"פנקס_{get_month_label(selected_month)}.csv",
                mime="text/csv"
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — יעדים
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-title'>יעדי תקציב חודשיים לכל קטגוריה</div>", unsafe_allow_html=True)

    for cat in CATEGORIES["expense"]:
        cat_id    = cat["id"]
        cat_label = cat["label"]
        spent = sum(t["amount"] for t in month_txs if t["type"] == "expense" and t["category"] == cat_id)
        budget = st.session_state.budgets.get(cat_id, 0)
        over   = budget > 0 and spent > budget

        border = "#7f1d1d" if over else "#1e1e1e"
        st.markdown(f"""
        <div style="background:#111;border:1px solid {border};border-radius:12px;padding:16px 18px;margin-bottom:10px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
                <span style="font-size:16px;font-weight:600">{cat_label}</span>
                <span style="font-size:13px;color:{'#f87171' if over else '#888'}">
                    {fmt_ils(spent)} מתוך {fmt_ils(budget) if budget else 'לא הוגדר'}
                    {'⚠️ חרגת!' if over else ''}
                </span>
            </div>
            {"" if not budget else f'''
            <div class="budget-bar-bg">
                <div class="budget-bar-fill" style="width:{min(int(spent/budget*100),100)}%;background:{'#f87171' if over else '#4ade80'}"></div>
            </div>
            '''}
        </div>
        """, unsafe_allow_html=True)

        col_inp, col_btn = st.columns([3, 1])
        with col_inp:
            new_budget = st.number_input(
                f"יעד ל{cat_label}", min_value=0.0, step=100.0,
                value=float(budget) if budget else 0.0,
                key=f"budget_{cat_id}", label_visibility="collapsed"
            )
        with col_btn:
            if st.button("💾 שמור", key=f"save_{cat_id}"):
                st.session_state.budgets[cat_id] = new_budget
                save_budgets(st.session_state.budgets)
                st.success("✓ נשמר!")
                st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — הוסף עסקה
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    tx_type = st.radio("סוג עסקה", options=["expense", "income"],
                        format_func=lambda x: "💸 הוצאה" if x == "expense" else "💰 הכנסה",
                        horizontal=True, key="tx_type")

    col_a, col_b = st.columns(2)
    with col_a:
        amount = st.number_input("סכום (₪)", min_value=0.01, step=10.0, format="%.2f", key="tx_amount")
    with col_b:
        tx_date = st.date_input("תאריך", value=date.today(), key="tx_date")

    cats = CATEGORIES[tx_type]
    cat_ids    = [c["id"]    for c in cats]
    cat_labels = [c["label"] for c in cats]
    cat_sel = st.selectbox("קטגוריה", options=range(len(cats)),
                            format_func=lambda i: cat_labels[i], key="tx_cat")
    category = cat_ids[cat_sel]

    note = st.text_input("הערה (אופציונלי)", placeholder="למשל: סופרמרקט, שכירות חודשית…", key="tx_note")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    btn_label = "➕ הוסף הוצאה" if tx_type == "expense" else "💰 הוסף הכנסה"
    btn_color = "#f87171" if tx_type == "expense" else "#4ade80"

    st.markdown(f"""
    <style>
    div[data-testid="stButton"] > button[kind="primary"] {{
        background: {btn_color} !important;
        color: #0d0d0d !important;
        font-size: 16px !important;
        font-weight: 700 !important;
        padding: 12px 0 !important;
        width: 100% !important;
        border: none !important;
        border-radius: 10px !important;
    }}
    </style>""", unsafe_allow_html=True)

    if st.button(btn_label, type="primary", use_container_width=True):
        if amount > 0:
            new_tx = {
                "id":       int(datetime.now().timestamp() * 1000),
                "type":     tx_type,
                "amount":   amount,
                "category": category,
                "note":     note,
                "date":     tx_date.isoformat(),
            }
            st.session_state.transactions.insert(0, new_tx)
            save_data(st.session_state.transactions)
            st.success(f"✓ העסקה נוספה! {cat_labels[cat_sel]} — {fmt_ils(amount)}")
            st.balloons()
        else:
            st.error("אנא הכנס סכום גדול מ-0")
