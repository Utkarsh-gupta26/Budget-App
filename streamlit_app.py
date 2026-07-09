import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Set page configuration
st.set_page_config(
    page_title="Union Budget Visualizer (2013-2026)",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Style Customizations
st.markdown("""
<style>
    .metric-card {
        background-color: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .trend-positive {
        color: #00e676;
        font-size: 13px;
        font-weight: bold;
    }
    .trend-negative {
        color: #ff1744;
        font-size: 13px;
        font-weight: bold;
    }
    .trend-neutral {
        color: #958eb6;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# Load data helper
@st.cache_data
def load_data():
    with open("budget_data.json", "r") as f:
        data = json.load(f)
    return data

try:
    data = load_data()
    years = data["years"]
    ministries_data = data["ministries"]
    
    # Restructure into a flat pandas DataFrame for easy queries
    flat_rows = []
    for m in ministries_data:
        for year in years:
            val = m["history"].get(year, 0)
            flat_rows.append({
                "Ministry": m["name"],
                "Key": m["key"],
                "Year": year,
                "Outlay (₹ Cr)": val
            })
    df = pd.DataFrame(flat_rows)
    
    # Sidebar
    st.sidebar.title("📊 FinScope")
    st.sidebar.caption("Union Budget Analysis (2013-2026)")
    st.sidebar.markdown("---")
    
    # Navigation tabs
    tab_choice = st.sidebar.radio(
        "Navigation Menu",
        ["Overview", "Ministry Analyzer", "Yearly Breakdown", "Share Comparison", "Data Table"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("Data source: Official Union Budget of India publications")

    # Dynamic computations
    latest_year = years[-1]
    prev_year = years[-2]
    
    def get_year_total(yr):
        return df[df["Year"] == yr]["Outlay (₹ Cr)"].sum()

    latest_total = get_year_total(latest_year)
    prev_total = get_year_total(prev_year)
    yoy_outlay_diff = latest_total - prev_total
    yoy_outlay_pct = (yoy_outlay_diff / prev_total * 100) if prev_total > 0 else 0

    # 13-Year Avg Outlay
    total_outlays_by_year = [get_year_total(y) for y in years]
    avg_outlay = sum(total_outlays_by_year) / len(years)

    # Top spending ministry in latest year
    latest_df = df[df["Year"] == latest_year]
    top_row = latest_df.loc[latest_df["Outlay (₹ Cr)"].idxmax()]
    top_ministry_name = top_row["Ministry"].split(" & ")[0].split(" / ")[0]
    top_ministry_val = top_row["Outlay (₹ Cr)"]
    top_ministry_pct = (top_ministry_val / latest_total * 100) if latest_total > 0 else 0

    # ================= OVERVIEW TAB =================
    if tab_choice == "Overview":
        st.title("Overview Dashboard")
        st.write("Key fiscal statistics and spending trends of the last decade.")
        
        # Metrics Grid
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">Latest Total Outlay</span>
                <h2 style="margin: 5px 0;">₹{latest_total:,.2f} Cr</h2>
                <span class="{"trend-positive" if yoy_outlay_pct >= 0 else "trend-negative"}">
                    {"▲" if yoy_outlay_pct >= 0 else "▼"} {yoy_outlay_pct:+.2% } (YoY)
                </span>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">13-Year Avg Outlay</span>
                <h2 style="margin: 5px 0;">₹{avg_outlay:,.2f} Cr</h2>
                <span class="trend-neutral">Combined 10 Ministries</span>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">Highest Funded Sector</span>
                <h2 style="margin: 5px 0; font-size: 20px;">{top_ministry_name}</h2>
                <span class="trend-neutral">
                    {top_ministry_pct:.1f}% share (₹{top_ministry_val:,.0f} Cr)
                </span>
            </div>
            """, unsafe_allow_html=True)
            
        with col4:
            st.markdown("""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">Overall CAGR</span>
                <h2 style="margin: 5px 0;">10.51%</h2>
                <span class="trend-neutral">Growth Rate (2013-2026)</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Overview charts
        chart_col1, chart_col2 = st.columns([3, 2])
        
        with chart_col1:
            st.subheader("Total Outlay Trend (10 Ministries Aggregated)")
            yearly_totals_df = pd.DataFrame({
                "Year": years,
                "Outlay (₹ Cr)": total_outlays_by_year
            })
            fig = px.area(
                yearly_totals_df, x="Year", y="Outlay (₹ Cr)",
                color_discrete_sequence=["#8f7efc"],
                template="plotly_dark"
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis_title="Outlay (₹ Crores)",
                xaxis_gridcolor="rgba(255,255,255,0.05)",
                yaxis_gridcolor="rgba(255,255,255,0.05)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with chart_col2:
            st.subheader(f"Budget Share ({latest_year})")
            latest_shares_df = latest_df.copy()
            latest_shares_df["Label"] = latest_shares_df["Ministry"].apply(lambda x: x.split(" & ")[0].split(" / ")[0])
            fig = px.pie(
                latest_shares_df, values="Outlay (₹ Cr)", names="Label",
                hole=0.6, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)

    # ================= MINISTRY ANALYZER TAB =================
    elif tab_choice == "Ministry Analyzer":
        st.title("Ministry Outlay Analyzer")
        
        m_list = [m["name"] for m in ministries_data]
        selected_m_name = st.selectbox("Select Ministry", m_list)
        
        m_key = [m["key"] for m in ministries_data if m["name"] == selected_m_name][0]
        m_df = df[df["Ministry"] == selected_m_name].sort_values("Year")
        
        # Stats computation
        m_avg = m_df["Outlay (₹ Cr)"].mean()
        peak_row = m_df.loc[m_df["Outlay (₹ Cr)"].idxmax()]
        peak_year = peak_row["Year"]
        peak_val = peak_row["Outlay (₹ Cr)"]
        
        v2013 = m_df[m_df["Year"] == "2013-14"]["Outlay (₹ Cr)"].values[0]
        v2025 = m_df[m_df["Year"] == "2025-26"]["Outlay (₹ Cr)"].values[0]
        growth = ((v2025 - v2013) / v2013 * 100) if v2013 > 0 else 0
        
        # Compute avg share
        shares = []
        for year in years:
            yr_tot = get_year_total(year)
            m_val = m_df[m_df["Year"] == year]["Outlay (₹ Cr)"].values[0]
            shares.append((m_val / yr_tot * 100) if yr_tot > 0 else 0)
        avg_share = sum(shares) / len(shares)
        
        # Analyzer stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">Average Outlay</span>
                <h2 style="margin: 5px 0;">₹{m_avg:,.2f} Cr</h2>
                <span class="trend-neutral">Annual average allocation</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">Peak Outlay Year</span>
                <h2 style="margin: 5px 0;">₹{peak_val:,.0f} Cr</h2>
                <span class="trend-neutral">Achieved in {peak_year}</span>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">Growth Since 2013</span>
                <h2 style="margin: 5px 0;">{growth:+.1f}%</h2>
                <span class="trend-neutral">Cumulative expansion</span>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <span style="color: #958eb6; font-size: 12px; text-transform: uppercase;">Avg Share of Budget</span>
                <h2 style="margin: 5px 0;">{avg_share:.2f}%</h2>
                <span class="trend-neutral">Relative budget footprint</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Double charts
        chart_col1, chart_col2 = st.columns([3, 2])
        
        with chart_col1:
            st.subheader(f"{selected_m_name} Budget & Growth Trend")
            
            # Calculate YoY growth
            m_df["YoY Growth (%)"] = m_df["Outlay (₹ Cr)"].pct_change() * 100
            m_df["YoY Growth (%)"] = m_df["YoY Growth (%)"].fillna(0)
            
            # Dual Axis Chart using Graph Objects
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Bar(
                    x=m_df["Year"], y=m_df["Outlay (₹ Cr)"],
                    name="Outlay (₹ Cr)",
                    marker_color="rgba(0, 210, 211, 0.6)",
                    marker_line_color="rgb(0, 210, 211)",
                    marker_line_width=1.5
                ),
                secondary_y=False
            )
            fig.add_trace(
                go.Scatter(
                    x=m_df["Year"], y=m_df["YoY Growth (%)"],
                    name="YoY Growth (%)",
                    line=dict(color="#ff7675", width=2.5),
                    mode="lines+markers"
                ),
                secondary_y=True
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis_gridcolor="rgba(255,255,255,0.05)",
                yaxis_gridcolor="rgba(255,255,255,0.05)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig.update_yaxes(title_text="Outlay (₹ Crores)", secondary_y=False)
            fig.update_yaxes(title_text="Growth (%)", secondary_y=True)
            
            st.plotly_chart(fig, use_container_width=True)
            
        with chart_col2:
            st.subheader("Average Budget Share Profile")
            others_avg = df[df["Ministry"] != selected_m_name].groupby("Ministry")["Outlay (₹ Cr)"].mean().sum()
            
            fig = px.pie(
                names=[selected_m_name.split(" & ")[0].split(" / ")[0], "Others Combined"],
                values=[m_avg, others_avg],
                template="plotly_dark",
                color_discrete_sequence=["#8f7efc", "rgba(255,255,255,0.05)"]
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)

    # ================= YEARLY BREAKDOWN TAB =================
    elif tab_choice == "Yearly Breakdown":
        st.title("Yearly Allocation Breakdown")
        
        selected_year = st.selectbox("Select Fiscal Year", years, index=len(years)-1)
        st.write(f"Detailed spending distribution for the budget year **{selected_year}**.")
        
        y_total = get_year_total(selected_year)
        
        # Calculate YoY expansion
        year_idx = years.index(selected_year)
        yoy_growth_str = "N/A"
        if year_idx > 0:
            py_total = get_year_total(years[year_idx - 1])
            growth = (y_total - py_total) / py_total * 100
            yoy_growth_str = f"{growth:+.2f}%"

        chart_col1, info_col = st.columns([3, 2])
        
        with chart_col1:
            st.subheader("Outlay Share Distribution")
            y_df = df[df["Year"] == selected_year].copy()
            y_df["Label"] = y_df["Ministry"].apply(lambda x: x.split(" & ")[0].split(" / ")[0])
            fig = px.pie(
                y_df, values="Outlay (₹ Cr)", names="Label",
                hole=0.5, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with info_col:
            st.subheader("Yearly Budget Insights")
            st.markdown(f"""
            <div style="margin-bottom: 20px;">
                <span style="color: #958eb6; font-size: 13px;">Total Consolidated Outlay</span>
                <h2 style="font-size: 32px; font-weight: 800; margin: 0;">₹{y_total:,.2f} Cr</h2>
            </div>
            <div style="margin-bottom: 30px;">
                <span style="color: #958eb6; font-size: 13px;">YoY Budget Expansion</span>
                <h3 style="color: #8f7efc; font-size: 24px; font-weight: 700; margin: 0;">{yoy_growth_str}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("**Top 3 Budget Allocations:**")
            sorted_y_df = y_df.sort_values("Outlay (₹ Cr)", ascending=False)
            for idx, r in enumerate(sorted_y_df.head(3).itertuples()):
                pct = (r._4 / y_total * 100) if y_total > 0 else 0
                st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; margin-bottom: 10px;">
                    <span style="font-weight: bold; color: #8f7efc; width: 25px;">#{idx+1}</span>
                    <span style="flex-grow: 1; font-size: 13px;">{r.Label}</span>
                    <span style="font-weight: bold; font-size: 13px;">₹{r._4:,.0f} Cr <span style="color: #958eb6; font-weight: normal; font-size: 11px;">({pct:.1f}%)</span></span>
                </div>
                """, unsafe_allow_html=True)

    # ================= COMPARISON TAB =================
    elif tab_choice == "Share Comparison":
        st.title("Year-on-Year Share Comparison")
        st.write("Compare budget distributions and sector growth between any two selected years side-by-side.")
        
        col1, divider_col, col2 = st.columns([5, 1, 5])
        with col1:
            year_a = st.selectbox("Base Year (A)", years, index=0)
        with divider_col:
            st.write("<div style='text-align: center; font-size: 24px; margin-top: 25px;'>↔️</div>", unsafe_allow_html=True)
        with col2:
            year_b = st.selectbox("Target Year (B)", years, index=len(years)-1)
            
        total_a = get_year_total(year_a)
        total_b = get_year_total(year_b)
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader(f"Distribution in {year_a}")
            df_a = df[df["Year"] == year_a].copy()
            df_a["Label"] = df_a["Ministry"].apply(lambda x: x.split(" & ")[0].split(" / ")[0])
            fig_a = px.pie(
                df_a, values="Outlay (₹ Cr)", names="Label",
                hole=0.55, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_a.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_a, use_container_width=True)
            
        with chart_col2:
            st.subheader(f"Distribution in {year_b}")
            df_b = df[df["Year"] == year_b].copy()
            df_b["Label"] = df_b["Ministry"].apply(lambda x: x.split(" & ")[0].split(" / ")[0])
            fig_b = px.pie(
                df_b, values="Outlay (₹ Cr)", names="Label",
                hole=0.55, template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_b.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.subheader("Shift & Absolute Growth Table")
        
        # Calculate comparison dataframe
        comp_rows = []
        for m in ministries_data:
            val_a = df[(df["Ministry"] == m["name"]) & (df["Year"] == year_a)]["Outlay (₹ Cr)"].values[0]
            val_b = df[(df["Ministry"] == m["name"]) & (df["Year"] == year_b)]["Outlay (₹ Cr)"].values[0]
            share_a = (val_a / total_a * 100) if total_a > 0 else 0
            share_b = (val_b / total_b * 100) if total_b > 0 else 0
            
            abs_diff = val_b - val_a
            pct_growth = (abs_diff / val_a * 100) if val_a > 0 else 0
            share_shift = share_b - share_a
            
            comp_rows.append({
                "Ministry": m["name"],
                f"Outlay {year_a} (₹ Cr)": val_a,
                f"Outlay {year_b} (₹ Cr)": val_b,
                "Growth (₹ Cr)": abs_diff,
                "Growth (%)": pct_growth,
                "Share Shift (%)": share_shift
            })
            
        comp_df = pd.DataFrame(comp_rows)
        
        # Format styling for display
        styled_df = comp_df.style.format({
            f"Outlay {year_a} (₹ Cr)": "{:,.2f}",
            f"Outlay {year_b} (₹ Cr)": "{:,.2f}",
            "Growth (₹ Cr)": "{:+,.2f}",
            "Growth (%)": "{:+.2f}%",
            "Share Shift (%)": "{:+.2f}%"
        })
        
        st.write(styled_df)

    # ================= DATA TABLE TAB =================
    elif tab_choice == "Data Table":
        st.title("Historical Budget Data Ledger")
        st.write("Examine, filter, and download the entire visualizer dataset.")
        
        # Add quick filters
        search_query = st.text_input("Search Ministry or Year", "")
        
        # Flattened dataset
        tbl_df = df.copy()
        tbl_df["Share of Annual Budget (%)"] = tbl_df.apply(
            lambda r: (r["Outlay (₹ Cr)"] / get_year_total(r["Year"]) * 100), axis=1
        )
        
        # Filter table
        if search_query:
            tbl_df = tbl_df[
                tbl_df["Ministry"].str.contains(search_query, case=False) |
                tbl_df["Year"].str.contains(search_query, case=False)
            ]
            
        # Reorder and format columns
        tbl_display = tbl_df[["Ministry", "Year", "Outlay (₹ Cr)", "Share of Annual Budget (%)"]].sort_values(["Year", "Outlay (₹ Cr)"], ascending=[False, False])
        
        st.dataframe(
            tbl_display.style.format({
                "Outlay (₹ Cr)": "{:,.2f}",
                "Share of Annual Budget (%)": "{:.2f}%"
            }),
            use_container_width=True
        )
        
        # CSV download
        csv = tbl_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Full Dataset CSV",
            data=csv,
            file_name="union_budget_ledger_2013_2026.csv",
            mime="text/csv"
        )
except Exception as e:
    st.error(f"Error initializing Streamlit Dashboard: {e}")
