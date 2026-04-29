import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
from datetime import datetime, date

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SmartSpend Finance Dashboard",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Currency config ───────────────────────────────────────────────────────────
CURRENCY_RATES = {"ZAR": 1, "USD": 0.053, "EUR": 0.049, "GBP": 0.042}
CURRENCY_SYMBOLS = {"ZAR": "R", "USD": "$", "EUR": "€", "GBP": "£"}
CATEGORIES = [
    "Salary", "Freelance", "Rent", "Food", "Transport",
    "Entertainment", "Health", "Shopping", "Utilities", "Insurance",
    "Savings", "Other",
]

# ── Sample data ───────────────────────────────────────────────────────────────
SAMPLE_DATA = [
    ("2026-01-05", "Salary",        "Monthly Salary",       25000, "Income"),
    ("2026-01-07", "Rent",          "Apartment",             8000, "Expense"),
    ("2026-01-08", "Food",          "Groceries",             1500, "Expense"),
    ("2026-01-10", "Transport",     "Uber",                   300, "Expense"),
    ("2026-01-12", "Entertainment", "Netflix + Spotify",      500, "Expense"),
    ("2026-01-14", "Food",          "Restaurant Lunch",       450, "Expense"),
    ("2026-01-18", "Health",        "Gym Membership",         800, "Expense"),
    ("2026-01-20", "Shopping",      "Clothing",              2200, "Expense"),
    ("2026-01-22", "Utilities",     "Electricity Bill",       650, "Expense"),
    ("2026-01-25", "Insurance",     "Car Insurance",         1100, "Expense"),
    ("2026-01-28", "Food",          "Groceries",             1200, "Expense"),
    ("2026-01-30", "Freelance",     "Design Project",        8000, "Income"),
    ("2026-02-05", "Salary",        "Monthly Salary",       25000, "Income"),
    ("2026-02-07", "Rent",          "Apartment",             8000, "Expense"),
    ("2026-02-09", "Food",          "Groceries",             1800, "Expense"),
    ("2026-02-11", "Transport",     "Uber",                   420, "Expense"),
    ("2026-02-13", "Entertainment", "Cinema",                 360, "Expense"),
    ("2026-02-15", "Health",        "Pharmacy",               250, "Expense"),
    ("2026-02-17", "Shopping",      "Electronics",           3500, "Expense"),
    ("2026-02-19", "Utilities",     "Water Bill",             300, "Expense"),
    ("2026-02-21", "Food",          "Restaurant",             650, "Expense"),
    ("2026-02-24", "Transport",     "Petrol",                 580, "Expense"),
    ("2026-02-26", "Insurance",     "Medical Insurance",      900, "Expense"),
    ("2026-02-28", "Freelance",     "Website Audit",         5000, "Income"),
    ("2026-03-05", "Salary",        "Monthly Salary",       25000, "Income"),
    ("2026-03-07", "Rent",          "Apartment",             8000, "Expense"),
    ("2026-03-08", "Food",          "Groceries",             2100, "Expense"),
    ("2026-03-10", "Transport",     "Uber",                   200, "Expense"),
    ("2026-03-12", "Entertainment", "Concerts",              1200, "Expense"),
    ("2026-03-14", "Health",        "Doctor Visit",           500, "Expense"),
    ("2026-03-17", "Shopping",      "Home Goods",            1800, "Expense"),
    ("2026-03-19", "Utilities",     "Internet",               450, "Expense"),
    ("2026-03-21", "Food",          "Restaurants",            980, "Expense"),
    ("2026-03-24", "Transport",     "Petrol",                 620, "Expense"),
    ("2026-03-27", "Savings",       "Emergency Fund",        3000, "Expense"),
    ("2026-03-28", "Freelance",     "App Development",      12000, "Income"),
    ("2026-04-05", "Salary",        "Monthly Salary",       25000, "Income"),
    ("2026-04-07", "Rent",          "Apartment",             8500, "Expense"),
    ("2026-04-09", "Food",          "Groceries",             1950, "Expense"),
    ("2026-04-11", "Transport",     "Uber",                   310, "Expense"),
    ("2026-04-13", "Entertainment", "Streaming",              600, "Expense"),
    ("2026-04-15", "Health",        "Gym Membership",         800, "Expense"),
    ("2026-04-17", "Shopping",      "Clothing",              1100, "Expense"),
    ("2026-04-20", "Utilities",     "Electricity",            720, "Expense"),
    ("2026-04-22", "Food",          "Restaurants",            870, "Expense"),
    ("2026-04-25", "Insurance",     "Car Insurance",         1100, "Expense"),
    ("2026-04-27", "Transport",     "Petrol",                 540, "Expense"),
    ("2026-04-29", "Freelance",     "Consulting",            6500, "Income"),
]


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    if "df" not in st.session_state:
        st.session_state.df = pd.DataFrame(
            SAMPLE_DATA, columns=["Date", "Category", "Description", "Amount", "Type"]
        )
        st.session_state.df["Date"] = pd.to_datetime(st.session_state.df["Date"])
        st.session_state.df["Amount"] = st.session_state.df["Amount"].astype(float)


init_state()


# ── Helpers ───────────────────────────────────────────────────────────────────
def fmt(amount: float, currency: str = "ZAR", compact: bool = False) -> str:
    converted = amount * CURRENCY_RATES[currency]
    sym = CURRENCY_SYMBOLS[currency]
    if compact and abs(converted) >= 1_000:
        return f"{sym}{converted/1000:.1f}K"
    return f"{sym}{converted:,.2f}"


def get_filtered(df: pd.DataFrame, month: str | None) -> pd.DataFrame:
    if month and month != "All":
        return df[df["Date"].dt.strftime("%Y-%m") == month]
    return df


def compute_summary(df: pd.DataFrame):
    income = df[df["Type"] == "Income"]["Amount"].sum()
    expenses = df[df["Type"] == "Expense"]["Amount"].sum()
    savings = income - expenses
    rate = (savings / income * 100) if income > 0 else 0
    count = len(df)
    cat_totals = df[df["Type"] == "Expense"].groupby("Category")["Amount"].sum()
    top_cat = cat_totals.idxmax() if not cat_totals.empty else "N/A"
    expense_days = df[df["Type"] == "Expense"]["Date"].nunique()
    avg_daily = expenses / expense_days if expense_days > 0 else 0
    return income, expenses, savings, rate, count, top_cat, avg_daily


PLOTLY_COLORS = ["#0079F2", "#795EFF", "#009118", "#A60808", "#ec4899", "#f59e0b", "#14b8a6", "#f97316"]


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💼 SmartSpend")
    st.markdown("*Finance Dashboard*")
    st.divider()

    page = st.radio(
        "Navigate",
        ["Overview", "Transactions", "Spending Analysis", "Savings Insights", "Settings"],
        label_visibility="collapsed",
    )

    st.divider()

    currency = st.selectbox("Currency", list(CURRENCY_RATES.keys()), index=0)

    df = st.session_state.df
    months = ["All"] + sorted(df["Date"].dt.strftime("%Y-%m").unique().tolist(), reverse=True)
    month_filter = st.selectbox("Month Filter", months, index=1 if len(months) > 1 else 0)

    st.divider()
    st.caption("SmartSpend v1.0 · Python Edition")


df = st.session_state.df
filtered = get_filtered(df, month_filter if month_filter != "All" else None)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Overview":
    st.title("Overview")
    st.caption("Your financial snapshot at a glance")

    income, expenses, savings, rate, count, top_cat, avg_daily = compute_summary(filtered)

    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Income",    fmt(income, currency),   delta=None)
    c2.metric("Total Expenses",  fmt(expenses, currency), delta=None)
    c3.metric("Savings",         fmt(savings, currency),  delta=f"{rate:.1f}% rate")
    c4.metric("Savings Rate",    f"{rate:.1f}%",          delta="Target: 20%")

    c5, c6, c7 = st.columns(3)
    c5.metric("Transactions",        count)
    c6.metric("Top Expense Category", top_cat)
    c7.metric("Avg Daily Expense",   fmt(avg_daily, currency))

    st.divider()

    # Monthly bar chart
    monthly = (
        df.assign(Month=df["Date"].dt.strftime("%Y-%m"))
        .groupby(["Month", "Type"])["Amount"]
        .sum()
        .reset_index()
        .pivot(index="Month", columns="Type", values="Amount")
        .fillna(0)
        .reset_index()
        .sort_values("Month")
    )

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Monthly Income vs Expenses")
        fig = go.Figure()
        if "Income" in monthly.columns:
            fig.add_bar(x=monthly["Month"], y=monthly["Income"],  name="Income",   marker_color=PLOTLY_COLORS[0])
        if "Expense" in monthly.columns:
            fig.add_bar(x=monthly["Month"], y=monthly["Expense"], name="Expenses", marker_color=PLOTLY_COLORS[3])
        fig.update_layout(barmode="group", plot_bgcolor="rgba(0,0,0,0)",
                          paper_bgcolor="rgba(0,0,0,0)", height=300,
                          margin=dict(t=10, b=10, l=10, r=10),
                          legend=dict(orientation="h", y=-0.2))
        fig.update_yaxes(tickprefix=CURRENCY_SYMBOLS[currency])
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Spending by Category")
        cat_df = filtered[filtered["Type"] == "Expense"].groupby("Category")["Amount"].sum().reset_index()
        if not cat_df.empty:
            fig2 = px.pie(cat_df, values="Amount", names="Category",
                          hole=0.45, color_discrete_sequence=PLOTLY_COLORS)
            fig2.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10),
                               paper_bgcolor="rgba(0,0,0,0)")
            fig2.update_traces(textinfo="percent+label")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No expense data for selected period.")

    # Savings trend
    st.subheader("Savings Trend Over Time")
    monthly2 = (
        df.assign(Month=df["Date"].dt.strftime("%Y-%m"))
        .groupby(["Month", "Type"])["Amount"].sum().reset_index()
        .pivot(index="Month", columns="Type", values="Amount").fillna(0).reset_index()
        .sort_values("Month")
    )
    monthly2.columns.name = None
    if "Income" in monthly2.columns and "Expense" in monthly2.columns:
        monthly2["Savings"] = monthly2["Income"] - monthly2["Expense"]
        monthly2["Cumulative"] = monthly2["Savings"].cumsum()

        fig3 = go.Figure()
        fig3.add_scatter(x=monthly2["Month"], y=monthly2["Savings"],
                         mode="lines+markers", name="Monthly Savings",
                         line=dict(color=PLOTLY_COLORS[0], width=2),
                         fill="tozeroy", fillcolor="rgba(0,121,242,0.12)")
        fig3.add_scatter(x=monthly2["Month"], y=monthly2["Cumulative"],
                         mode="lines+markers", name="Cumulative",
                         line=dict(color=PLOTLY_COLORS[1], width=2, dash="dash"))
        fig3.update_layout(height=260, plot_bgcolor="rgba(0,0,0,0)",
                           paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=10, b=10, l=10, r=10),
                           legend=dict(orientation="h", y=-0.25))
        fig3.update_yaxes(tickprefix=CURRENCY_SYMBOLS[currency])
        st.plotly_chart(fig3, use_container_width=True)

    # CSV export
    csv = filtered.to_csv(index=False).encode()
    st.download_button("Download filtered data as CSV", csv, "smartspend_overview.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Transactions":
    st.title("Transactions")
    st.caption("All your income and expense entries")

    # Search & filters
    col1, col2, col3 = st.columns([3, 1, 1])
    search = col1.text_input("Search", placeholder="Description or category...", label_visibility="collapsed")
    type_filter = col2.selectbox("Type", ["All", "Income", "Expense"], label_visibility="collapsed")
    cat_filter = col3.selectbox("Category", ["All"] + CATEGORIES, label_visibility="collapsed")

    view = filtered.copy()
    if search:
        mask = (view["Description"].str.contains(search, case=False, na=False) |
                view["Category"].str.contains(search, case=False, na=False))
        view = view[mask]
    if type_filter != "All":
        view = view[view["Type"] == type_filter]
    if cat_filter != "All":
        view = view[view["Category"] == cat_filter]

    view_display = view.copy()
    view_display["Amount"] = view_display.apply(
        lambda r: f"+{fmt(r['Amount'], currency)}" if r["Type"] == "Income" else f"-{fmt(r['Amount'], currency)}", axis=1
    )
    view_display["Date"] = view_display["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(
        view_display[["Date", "Category", "Description", "Amount", "Type"]].reset_index(drop=True),
        use_container_width=True, height=400,
    )
    st.caption(f"{len(view)} records shown")

    st.divider()
    col_a, col_b = st.columns(2)

    # Add transaction form
    with col_a:
        st.subheader("Add Transaction")
        with st.form("add_tx", clear_on_submit=True):
            f_date = st.date_input("Date", value=date.today())
            f_type = st.selectbox("Type", ["Expense", "Income"])
            f_cat = st.selectbox("Category", CATEGORIES)
            f_desc = st.text_input("Description")
            f_amt = st.number_input("Amount (ZAR)", min_value=0.01, step=0.01, format="%.2f")
            if st.form_submit_button("Add Transaction", use_container_width=True):
                new_row = pd.DataFrame([{
                    "Date": pd.to_datetime(f_date),
                    "Category": f_cat,
                    "Description": f_desc,
                    "Amount": float(f_amt),
                    "Type": f_type,
                }])
                st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
                st.success(f"Added: {f_desc} — {fmt(f_amt, currency)}")
                st.rerun()

    # CSV upload
    with col_b:
        st.subheader("Upload CSV")
        st.caption("Format: Date, Category, Description, Amount, Type")
        uploaded = st.file_uploader("Choose CSV file", type=["csv"], label_visibility="collapsed")
        if uploaded:
            try:
                upload_df = pd.read_csv(uploaded)
                upload_df.columns = [c.strip() for c in upload_df.columns]
                upload_df["Date"] = pd.to_datetime(upload_df["Date"])
                upload_df["Amount"] = upload_df["Amount"].abs().astype(float)
                st.session_state.df = pd.concat([st.session_state.df, upload_df], ignore_index=True)
                st.success(f"Imported {len(upload_df)} transactions.")
                st.rerun()
            except Exception as e:
                st.error(f"Error reading CSV: {e}")

        st.markdown("**Expected format:**")
        sample = pd.DataFrame([
            {"Date": "2026-04-05", "Category": "Salary", "Description": "Monthly Salary", "Amount": 25000, "Type": "Income"},
            {"Date": "2026-04-07", "Category": "Rent",   "Description": "Apartment",      "Amount":  8000, "Type": "Expense"},
        ])
        st.dataframe(sample, use_container_width=True, hide_index=True)

    st.divider()
    csv = view.copy()
    csv["Date"] = csv["Date"].dt.strftime("%Y-%m-%d")
    st.download_button("Download transactions as CSV", csv.to_csv(index=False).encode(), "transactions.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SPENDING ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Spending Analysis":
    st.title("Spending Analysis")
    st.caption("Where your money goes")

    expenses_df = filtered[filtered["Type"] == "Expense"].copy()
    cat_totals = expenses_df.groupby("Category")["Amount"].sum().reset_index().sort_values("Amount", ascending=False)

    if cat_totals.empty:
        st.warning("No expense data for selected period.")
        st.stop()

    cat_totals["Percentage"] = (cat_totals["Amount"] / cat_totals["Amount"].sum() * 100).round(2)
    cat_totals["AmountFmt"] = cat_totals["Amount"].apply(lambda x: fmt(x, currency))

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Spending by Category")
        fig = px.pie(cat_totals, values="Amount", names="Category",
                     hole=0.4, color_discrete_sequence=PLOTLY_COLORS)
        fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                          margin=dict(t=10, b=10, l=10, r=10))
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Top Expense Categories")
        fig2 = px.bar(cat_totals.head(8), x="Amount", y="Category",
                      orientation="h", color="Category",
                      color_discrete_sequence=PLOTLY_COLORS,
                      text="AmountFmt")
        fig2.update_layout(height=320, showlegend=False,
                           paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=10, b=10, l=10, r=10),
                           yaxis=dict(autorange="reversed"))
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    # Daily cashflow heatmap
    st.subheader("Daily Cashflow Heatmap")
    daily = filtered.copy()
    daily["DateStr"] = daily["Date"].dt.strftime("%Y-%m-%d")
    daily_income = daily[daily["Type"] == "Income"].groupby("DateStr")["Amount"].sum().rename("Income")
    daily_expense = daily[daily["Type"] == "Expense"].groupby("DateStr")["Amount"].sum().rename("Expense")
    daily_cf = pd.concat([daily_income, daily_expense], axis=1).fillna(0)
    daily_cf["Net"] = daily_cf["Income"] - daily_cf["Expense"]
    daily_cf = daily_cf.reset_index()
    daily_cf["Date"] = pd.to_datetime(daily_cf["DateStr"])
    daily_cf["Day"] = daily_cf["Date"].dt.day
    daily_cf["WeekNum"] = daily_cf["Date"].dt.isocalendar().week.astype(int)
    daily_cf["DayOfWeek"] = daily_cf["Date"].dt.dayofweek
    daily_cf["DayName"] = daily_cf["Date"].dt.strftime("%a")
    daily_cf["Label"] = daily_cf["DateStr"] + "<br>Net: " + daily_cf["Net"].apply(lambda x: fmt(x, currency))

    if not daily_cf.empty:
        pivot = daily_cf.pivot_table(index="DayOfWeek", columns="WeekNum", values="Net", aggfunc="sum")
        hover = daily_cf.pivot_table(index="DayOfWeek", columns="WeekNum", values="Label", aggfunc="first")
        day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

        fig3 = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=[f"Wk{w}" for w in pivot.columns],
            y=[day_labels[i] for i in pivot.index],
            text=hover.values,
            hoverinfo="text",
            colorscale=[[0, "#A60808"], [0.5, "#1e293b"], [1, "#009118"]],
            zmid=0,
            showscale=True,
        ))
        fig3.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=10, b=10, l=40, r=10))
        st.plotly_chart(fig3, use_container_width=True)

    # Category details table
    st.subheader("Category Details")
    display_cat = cat_totals.copy()
    display_cat["Amount"] = display_cat["Amount"].apply(lambda x: fmt(x, currency))
    display_cat["Percentage"] = display_cat["Percentage"].apply(lambda x: f"{x:.1f}%")
    display_cat.columns = ["Category", "Amount", "% of Total"]
    st.dataframe(display_cat, use_container_width=True, hide_index=True)

    csv = cat_totals.to_csv(index=False).encode()
    st.download_button("Download category breakdown as CSV", csv, "category_breakdown.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SAVINGS INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Savings Insights":
    st.title("Savings Insights")
    st.caption("Track your wealth-building journey")

    income, expenses, savings, rate, _, _, _ = compute_summary(filtered)

    c1, c2, c3 = st.columns(3)
    c1.metric("Savings This Period", fmt(savings, currency), delta=f"{rate:.1f}% rate")
    c2.metric("Savings Rate",        f"{rate:.1f}%", delta="Target: 20%")

    # Monthly savings trend
    monthly = (
        df.assign(Month=df["Date"].dt.strftime("%Y-%m"))
        .groupby(["Month", "Type"])["Amount"].sum().reset_index()
        .pivot(index="Month", columns="Type", values="Amount").fillna(0)
        .reset_index().sort_values("Month")
    )
    monthly.columns.name = None

    if "Income" not in monthly.columns:
        monthly["Income"] = 0
    if "Expense" not in monthly.columns:
        monthly["Expense"] = 0

    monthly["Savings"] = monthly["Income"] - monthly["Expense"]
    monthly["Cumulative"] = monthly["Savings"].cumsum()
    monthly["SavingsRate"] = (monthly["Savings"] / monthly["Income"].replace(0, np.nan) * 100).fillna(0).round(2)

    c3.metric("Cumulative Savings", fmt(monthly["Cumulative"].iloc[-1], currency) if not monthly.empty else "—")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Monthly Savings")
        fig = go.Figure()
        fig.add_scatter(x=monthly["Month"], y=monthly["Savings"],
                        mode="lines+markers", name="Savings",
                        line=dict(color=PLOTLY_COLORS[0], width=2.5),
                        fill="tozeroy", fillcolor="rgba(0,121,242,0.12)")
        fig.add_hline(y=0, line_dash="dash", line_color="#6b7280")
        fig.update_layout(height=280, plot_bgcolor="rgba(0,0,0,0)",
                          paper_bgcolor="rgba(0,0,0,0)",
                          margin=dict(t=10, b=10, l=10, r=10))
        fig.update_yaxes(tickprefix=CURRENCY_SYMBOLS[currency])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Cumulative Savings Growth")
        fig2 = go.Figure()
        fig2.add_scatter(x=monthly["Month"], y=monthly["Cumulative"],
                         mode="lines+markers", name="Cumulative",
                         line=dict(color=PLOTLY_COLORS[1], width=2.5))
        fig2.add_scatter(x=monthly["Month"], y=monthly["SavingsRate"],
                         mode="lines", name="Rate %",
                         line=dict(color=PLOTLY_COLORS[2], width=1.5, dash="dot"),
                         yaxis="y2")
        fig2.update_layout(height=280, plot_bgcolor="rgba(0,0,0,0)",
                           paper_bgcolor="rgba(0,0,0,0)",
                           margin=dict(t=10, b=10, l=10, r=10),
                           yaxis2=dict(overlaying="y", side="right", showgrid=False))
        fig2.update_yaxes(tickprefix=CURRENCY_SYMBOLS[currency])
        st.plotly_chart(fig2, use_container_width=True)

    # AI-style spending insights
    st.subheader("Spending Insights")

    all_months = sorted(df["Date"].dt.strftime("%Y-%m").unique())
    if len(all_months) >= 2 and month_filter != "All":
        curr_m = month_filter
        curr_idx = all_months.index(curr_m) if curr_m in all_months else -1
        if curr_idx > 0:
            prev_m = all_months[curr_idx - 1]
            curr_cats = df[
                (df["Date"].dt.strftime("%Y-%m") == curr_m) & (df["Type"] == "Expense")
            ].groupby("Category")["Amount"].sum()
            prev_cats = df[
                (df["Date"].dt.strftime("%Y-%m") == prev_m) & (df["Type"] == "Expense")
            ].groupby("Category")["Amount"].sum()

            changes = []
            for cat in curr_cats.index:
                curr_val = curr_cats.get(cat, 0)
                prev_val = prev_cats.get(cat, 0)
                if prev_val > 0:
                    pct = (curr_val - prev_val) / prev_val * 100
                    changes.append((cat, pct, curr_val, prev_val))
                elif curr_val > 0:
                    changes.append((cat, 100.0, curr_val, 0))

            increases = sorted([c for c in changes if c[1] > 0], key=lambda x: -x[1])

            if increases:
                st.markdown("**Notable changes vs last month:**")
                for cat, pct, curr, prev in increases[:3]:
                    direction = "increased" if pct > 0 else "decreased"
                    st.info(f"**{cat}** spending {direction} **{abs(pct):.1f}%** — {fmt(prev, currency)} → {fmt(curr, currency)}")
            else:
                st.success("No significant spending increases vs last month.")
        else:
            st.info("Select a month with a previous month to compare.")
    else:
        st.info("Select a specific month to see month-over-month insights.")

    st.divider()
    st.markdown("**Recommendations**")
    st.success("Review subscription services monthly to eliminate unused ones.")
    st.success("Consider setting a budget cap for your top spending category.")
    st.success("Aim to maintain a savings rate above 20% for financial health.")

    csv = monthly.to_csv(index=False).encode()
    st.download_button("Download savings trend as CSV", csv, "savings_trend.csv", "text/csv")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Settings":
    st.title("Settings")
    st.caption("Customize and manage your data")

    st.subheader("Currency")
    st.info(f"Currently displaying in **{currency}**. Change via the sidebar selector.")

    st.divider()
    st.subheader("CSV Format Reference")
    st.caption("Use this format when uploading transaction files")
    st.code(
        "Date,Category,Description,Amount,Type\n"
        "2026-04-05,Salary,Monthly Salary,25000,Income\n"
        "2026-04-07,Rent,Apartment,8000,Expense\n"
        "2026-04-10,Food,Groceries,1500,Expense",
        language="csv",
    )
    st.caption("Amount should be a positive number. Type must be 'Income' or 'Expense'.")

    st.divider()
    st.subheader("Reset Data")
    if st.button("Reset to sample data", type="secondary"):
        del st.session_state["df"]
        init_state()
        st.success("Data reset to sample transactions.")
        st.rerun()

    st.divider()
    st.subheader("Export All Data")
    full_export = st.session_state.df.copy()
    full_export["Date"] = full_export["Date"].dt.strftime("%Y-%m-%d")
    st.download_button(
        "Download all transactions as CSV",
        full_export.to_csv(index=False).encode(),
        "smartspend_all_transactions.csv",
        "text/csv",
        use_container_width=True,
    )
