import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="FinScope - Budget Analytics Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Glassmorphic Theme matching style.css
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');
    
    /* Global Background and Typography */
    .stApp {
        background: radial-gradient(circle at 80% 20%, #1e133a, #0b071a, #04030a) !important;
        color: #f5f4fc !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Headers Styling */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(8, 6, 17, 0.7) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }
    
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    
    /* Premium Glassmorphic Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        margin-bottom: 20px;
    }
    
    /* Custom Stats Metric Container */
    .stat-container {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.4);
        margin-bottom: 16px;
        backdrop-filter: blur(10px);
        border-left: 4px solid #8f7efc; /* Default purple neon indicator */
    }
    
    .stat-container.blue { border-left-color: #00a8ff; }
    .stat-container.purple { border-left-color: #8f7efc; }
    .stat-container.green { border-left-color: #00d2d3; }
    .stat-container.yellow { border-left-color: #ff9f43; }
    
    .stat-title {
        font-size: 12px;
        color: #958eb6;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    
    .stat-value {
        font-size: 26px;
        font-weight: 700;
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
    }
    
    .stat-delta {
        font-size: 12px;
        margin-top: 6px;
        font-weight: 500;
    }
    
    .stat-delta.positive { color: #00d2d3; }
    .stat-delta.neutral { color: #958eb6; }
    
    /* Styled Lists */
    ol.top-list {
        color: #f5f4fc;
        padding-left: 20px;
    }
    ol.top-list li {
        margin-bottom: 8px;
        font-size: 14px;
    }
    
    /* Custom spacing and selectors */
    .stSelectbox label {
        color: #958eb6 !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
</style>
""", unsafe_allow_html=True)

# Colors matching style.css theme
CHART_COLORS = ['#8f7efc', '#00a8ff', '#00d2d3', '#ff9f43', '#ff7675', '#fd79a8', '#fdcb6e', '#00cec9', '#a55eea', '#26de81']

# Custom Plotly helper
def customize_plotly_chart(fig):
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif", color="#958eb6", size=11),
        title=dict(font=dict(family="Outfit, sans-serif", size=16, color="#ffffff")),
        margin=dict(l=40, r=40, t=50, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.04)',
            linecolor='rgba(255,255,255,0.08)',
            tickfont=dict(color="#958eb6")
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.04)',
            linecolor='rgba(255,255,255,0.08)',
            tickfont=dict(color="#958eb6")
        ),
        legend=dict(
            font=dict(color="#958eb6"),
            bgcolor='rgba(0,0,0,0)'
        )
    )
    return fig

# Load JSON budget data
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, 'budget_data.json')
    
    if not os.path.exists(json_path):
        st.error(f"Required budget data file not found at: {json_path}")
        st.stop()
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    years = data['years']
    ministries_list = data['ministries']
    
    flat_records = []
    for m in ministries_list:
        key = m['key']
        name = m['name']
        for yr, val in m['history'].items():
            flat_records.append({
                'MinistryKey': key,
                'MinistryName': name,
                'Year': yr,
                'Outlay (₹ Cr)': val
            })
            
    df = pd.DataFrame(flat_records)
    
    # Calculate yearly aggregates
    df_totals = df.groupby('Year')['Outlay (₹ Cr)'].sum().reset_index()
    df_totals.rename(columns={'Outlay (₹ Cr)': 'TotalOutlay'}, inplace=True)
    
    # Combine back to get share percentage
    df = df.merge(df_totals, on='Year')
    df['Share (%)'] = (df['Outlay (₹ Cr)'] / df['TotalOutlay'] * 100).round(2)
    
    return df, years, ministries_list, df_totals

# Load core datasets
df, years, ministries_list, df_totals = load_data()

# Layout Side Header / branding
st.sidebar.markdown("""
<div style='display: flex; align-items: center; gap: 12px; margin-bottom: 24px;'>
    <div style='background: linear-gradient(135deg, #8f7efc, #5f27cd); width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(143, 126, 252, 0.4);'>
        <span style='color: white; font-weight: 800; font-size: 18px;'>F</span>
    </div>
    <div style='line-height: 1.1;'>
        <h3 style='margin: 0; font-size: 20px; font-weight: 700;'>FinScope</h3>
        <span style='color: #958eb6; font-size: 11px;'>Budget Analytics (2013-26)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Navigation Menu
st.sidebar.subheader("Navigation")
menu_selection = st.sidebar.radio(
    label="Go to:",
    options=[
        "Overview Dashboard",
        "Ministry Analyzer",
        "Yearly Breakdown",
        "Share Comparison",
        "Data Table"
    ],
    index=0,
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='color: #958eb6; font-size: 11px; display: flex; align-items: center; gap: 6px;'>
    <span>ℹ️ Data source: Union Budget of India official reports</span>
</div>
""", unsafe_allow_html=True)

# Helper to format currency
def format_cr(val):
    return f"₹{val:,.2f} Cr" if val % 1 != 0 else f"₹{val:,.0f} Cr"

# ==========================================
# 📊 OVERVIEW VIEW
# ==========================================
if menu_selection == "Overview Dashboard":
    st.markdown("## Overview Dashboard")
    st.markdown("<p style='color:#958eb6; margin-top:-15px; margin-bottom: 25px;'>Key fiscal statistics and trends of the last decade</p>", unsafe_allow_html=True)
    
    # Calculate global overview stats
    latest_year = years[-1]
    prev_year = years[-2]
    
    # Outlays
    latest_outlay = df_totals[df_totals['Year'] == latest_year]['TotalOutlay'].values[0]
    prev_outlay = df_totals[df_totals['Year'] == prev_year]['TotalOutlay'].values[0]
    outlay_yoy_growth = ((latest_outlay - prev_outlay) / prev_outlay * 100).round(2)
    
    # Average outlay
    avg_outlay = df_totals['TotalOutlay'].mean().round(2)
    
    # Top ministry in latest year
    df_latest = df[df['Year'] == latest_year]
    top_row = df_latest.loc[df_latest['Outlay (₹ Cr)'].idxmax()]
    top_name = top_row['MinistryName']
    top_share = top_row['Share (%)']
    
    # CAGR calculation
    first_year = years[0]
    first_outlay = df_totals[df_totals['Year'] == first_year]['TotalOutlay'].values[0]
    n_years = len(years)
    cagr = (((latest_outlay / first_outlay) ** (1 / (n_years - 1))) - 1) * 100
    
    # Metrics Cards Grid
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-container blue">
            <div class="stat-title">Latest Total Outlay ({latest_year})</div>
            <div class="stat-value">{format_cr(latest_outlay)}</div>
            <div class="stat-delta positive">📈 +{outlay_yoy_growth}% (YoY)</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-container purple">
            <div class="stat-title">13-Year Average Outlay</div>
            <div class="stat-value">{format_cr(avg_outlay)}</div>
            <div class="stat-delta neutral">Combined Major Sectors</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-container green">
            <div class="stat-title">Highest Funded Sector ({latest_year})</div>
            <div class="stat-value" style="font-size:18px; margin-top: 10px; margin-bottom: 2px;">{top_name}</div>
            <div class="stat-delta positive">⭐ {top_share}% share of outlay</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-container yellow">
            <div class="stat-title">Overall CAGR</div>
            <div class="stat-value">{cagr.round(2)}%</div>
            <div class="stat-delta neutral">Growth Rate (2013 - 2026)</div>
        </div>
        """, unsafe_allow_html=True)
        
    # Chart Row
    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig_line = px.line(
            df_totals, 
            x='Year', 
            y='TotalOutlay', 
            markers=True,
            title="Total Outlay Trend (10 Ministries Aggregated)",
            labels={'TotalOutlay': 'Outlay (₹ Crores)', 'Year': 'Fiscal Year'}
        )
        fig_line.update_traces(
            line_color='#8f7efc',
            line_width=3,
            marker=dict(size=8, color='#00d2d3', symbol='circle')
        )
        # Add area under line
        fig_line.update_traces(fill='tozeroy', fillcolor='rgba(143, 126, 252, 0.05)')
        st.plotly_chart(customize_plotly_chart(fig_line), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with right_col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig_pie = px.pie(
            df_latest, 
            values='Outlay (₹ Cr)', 
            names='MinistryName',
            title=f"Budget Share ({latest_year})",
            hole=0.4,
            color_discrete_sequence=CHART_COLORS
        )
        st.plotly_chart(customize_plotly_chart(fig_pie), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🏛️ MINISTRY ANALYZER VIEW
# ==========================================
elif menu_selection == "Ministry Analyzer":
    st.markdown("## Ministry Analyzer")
    st.markdown("<p style='color:#958eb6; margin-top:-15px; margin-bottom: 25px;'>Drill down into allocation history and growth parameters of individual ministries</p>", unsafe_allow_html=True)
    
    # Ministry Selector Dropdown
    selected_name = st.selectbox(
        "Select Ministry to Analyze",
        options=[m['name'] for m in ministries_list]
    )
    
    # Selected Ministry Data
    df_m = df[df['MinistryName'] == selected_name].sort_values('Year')
    first_val = df_m.iloc[0]['Outlay (₹ Cr)']
    latest_val = df_m.iloc[-1]['Outlay (₹ Cr)']
    
    # Calculation Metrics
    m_avg = df_m['Outlay (₹ Cr)'].mean().round(2)
    
    peak_row = df_m.loc[df_m['Outlay (₹ Cr)'].idxmax()]
    peak_val = peak_row['Outlay (₹ Cr)']
    peak_year = peak_row['Year']
    
    total_growth = ((latest_val - first_val) / first_val * 100).round(2)
    m_avg_share = df_m['Share (%)'].mean().round(2)
    
    # Stats cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-container blue">
            <div class="stat-title">Average Annual Outlay</div>
            <div class="stat-value">{format_cr(m_avg)}</div>
            <div class="stat-delta neutral">13-Year Period Mean</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-container purple">
            <div class="stat-title">Peak Outlay Year</div>
            <div class="stat-value">{peak_year}</div>
            <div class="stat-delta positive">⭐ Outlay of {format_cr(peak_val)}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-container green">
            <div class="stat-title">Growth Since 2013-14</div>
            <div class="stat-value">+{total_growth}%</div>
            <div class="stat-delta positive">📈 Cumulative expansion</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="stat-container yellow">
            <div class="stat-title">Avg Share of Outlay</div>
            <div class="stat-value">{m_avg_share}%</div>
            <div class="stat-delta neutral">Relative to 10 ministries</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig_m_trend = px.line(
            df_m,
            x='Year',
            y='Outlay (₹ Cr)',
            markers=True,
            title=f"Outlay Trend — {selected_name}",
            labels={'Outlay (₹ Cr)': 'Outlay (₹ Crores)', 'Year': 'Fiscal Year'}
        )
        fig_m_trend.update_traces(
            line_color='#00a8ff',
            line_width=3,
            marker=dict(size=8, color='#ff9f43')
        )
        fig_m_trend.update_traces(fill='tozeroy', fillcolor='rgba(0, 168, 255, 0.05)')
        st.plotly_chart(customize_plotly_chart(fig_m_trend), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with right_col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        # Average share donut
        other_share = (100 - m_avg_share).round(2)
        fig_m_share = go.Figure(data=[go.Pie(
            labels=[selected_name, 'Other Ministries combined'],
            values=[m_avg_share, other_share],
            hole=0.45,
            marker_colors=['#00d2d3', 'rgba(255,255,255,0.05)'],
            textinfo='label+percent',
            showlegend=False
        )])
        fig_m_share.update_layout(title="Average Budget Share Allocation")
        st.plotly_chart(customize_plotly_chart(fig_m_share), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 📅 YEARLY BREAKDOWN VIEW
# ==========================================
elif menu_selection == "Yearly Breakdown":
    st.markdown("## Yearly Breakdown")
    st.markdown("<p style='color:#958eb6; margin-top:-15px; margin-bottom: 25px;'>Review funding shares and insights for a specific budget year</p>", unsafe_allow_html=True)
    
    # Year selector
    selected_year = st.selectbox(
        "Select Fiscal Year",
        options=years
    )
    
    # Data for selected year
    df_y = df[df['Year'] == selected_year].sort_values('Outlay (₹ Cr)', ascending=False)
    
    # Totals and expansion
    y_total = df_totals[df_totals['Year'] == selected_year]['TotalOutlay'].values[0]
    
    idx = years.index(selected_year)
    if idx > 0:
        prev_yr = years[idx-1]
        prev_total = df_totals[df_totals['Year'] == prev_yr]['TotalOutlay'].values[0]
        yoy_growth = ((y_total - prev_total) / prev_total * 100).round(2)
        yoy_text = f"+{yoy_growth}% YoY Expansion"
    else:
        yoy_text = "Base year of dataset"
        
    # Get top 3 allocations
    top_3 = df_y.head(3)
    
    left_col, right_col = st.columns([3, 2])
    
    with left_col:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig_donut_y = px.pie(
            df_y,
            values='Outlay (₹ Cr)',
            names='MinistryName',
            title=f"Outlay Share Distribution ({selected_year})",
            hole=0.4,
            color_discrete_sequence=CHART_COLORS
        )
        st.plotly_chart(customize_plotly_chart(fig_donut_y), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with right_col:
        st.markdown("<div class='glass-card' style='height:100%;'>", unsafe_allow_html=True)
        st.markdown("<h4>Yearly Budget Insights</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#958eb6; font-size:12px; margin-top:-10px;'>Statistics for {selected_year}</p>", unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style='margin-bottom: 24px; margin-top:20px;'>
            <span style='font-size:11px; color:#958eb6; text-transform:uppercase; letter-spacing:1px;'>Total Consolidated Outlay</span>
            <h2 style='margin:0; font-size:36px; color:#00a8ff !important;'>{format_cr(y_total)}</h2>
        </div>
        
        <div style='margin-bottom: 28px;'>
            <span style='font-size:11px; color:#958eb6; text-transform:uppercase; letter-spacing:1px;'>YoY Budget Expansion</span>
            <h3 style='margin:0; font-size:24px; color:#00d2d3 !important;'>{yoy_text}</h3>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<h5 style='color:#ffffff; margin-bottom: 12px;'>Top 3 Budget Allocations</h5>", unsafe_allow_html=True)
        
        top_list_html = "<ol class='top-list'>"
        for rank, (_, row) in enumerate(top_3.iterrows(), start=1):
            top_list_html += f"""
            <li>
                <strong>{row['MinistryName']}</strong><br/>
                <span style='color:#958eb6;'>Allocation:</span> {format_cr(row['Outlay (₹ Cr)'])} 
                <span style='color:#8f7efc; margin-left: 6px;'>({row['Share (%)']}% share)</span>
            </li>
            """
        top_list_html += "</ol>"
        st.markdown(top_list_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 🔄 SHARE COMPARISON VIEW
# ==========================================
elif menu_selection == "Share Comparison":
    st.markdown("## Share Comparison")
    st.markdown("<p style='color:#958eb6; margin-top:-15px; margin-bottom: 25px;'>Analyze distribution changes, absolute budget growth, and share shift between two years</p>", unsafe_allow_html=True)
    
    # Comparison selectboxes side-by-side
    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        year_a = st.selectbox("Base Year (A)", options=years, index=0)
    with sel_col2:
        year_b = st.selectbox("Target Year (B)", options=years, index=len(years)-1)
        
    df_a = df[df['Year'] == year_a]
    df_b = df[df['Year'] == year_b]
    
    st.markdown("<br>", unsafe_allow_html=True)
    # Side-by-side pie charts
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig_a = px.pie(
            df_a, values='Outlay (₹ Cr)', names='MinistryName',
            title=f"Base Year ({year_a}) Distribution", hole=0.4,
            color_discrete_sequence=CHART_COLORS
        )
        st.plotly_chart(customize_plotly_chart(fig_a), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with chart_col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        fig_b = px.pie(
            df_b, values='Outlay (₹ Cr)', names='MinistryName',
            title=f"Target Year ({year_b}) Distribution", hole=0.4,
            color_discrete_sequence=CHART_COLORS
        )
        st.plotly_chart(customize_plotly_chart(fig_b), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Grid shift analysis table
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<h4>Ministry Share Shift & Absolute Growth Analysis</h4>", unsafe_allow_html=True)
    st.markdown("<span style='color:#958eb6; font-size:12px;'>Detailing redistribution metrics and percentage growth from Base Year to Target Year</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Calculate grid data
    compare_records = []
    for m in ministries_list:
        name = m['name']
        
        # Outlay A
        row_a = df_a[df_a['MinistryName'] == name]
        out_a = row_a['Outlay (₹ Cr)'].values[0] if len(row_a) > 0 else 0.0
        share_a = row_a['Share (%)'].values[0] if len(row_a) > 0 else 0.0
        
        # Outlay B
        row_b = df_b[df_b['MinistryName'] == name]
        out_b = row_b['Outlay (₹ Cr)'].values[0] if len(row_b) > 0 else 0.0
        share_b = row_b['Share (%)'].values[0] if len(row_b) > 0 else 0.0
        
        abs_growth = out_b - out_a
        rel_growth = (abs_growth / out_a * 100) if out_a > 0 else 0.0
        share_shift = share_b - share_a
        
        compare_records.append({
            'Ministry': name,
            f'Outlay in {year_a} (₹ Cr)': out_a,
            f'Outlay in {year_b} (₹ Cr)': out_b,
            'Absolute Growth (₹ Cr)': round(abs_growth, 2),
            'Growth (%)': f"{rel_growth:+.2f}%" if rel_growth != 0 else "0.00%",
            'Share Shift (%)': f"{share_shift:+.2f}%" if share_shift != 0 else "0.00%"
        })
        
    df_compare = pd.DataFrame(compare_records)
    st.dataframe(df_compare, hide_index=True, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# 📁 DATA TABLE VIEW
# ==========================================
elif menu_selection == "Data Table":
    st.markdown("## Data Table")
    st.markdown("<p style='color:#958eb6; margin-top:-15px; margin-bottom: 25px;'>Browse, search, and download the full historical budget metrics</p>", unsafe_allow_html=True)
    
    # Search input
    search_query = st.text_input("🔍 Search database by Ministry Name or Fiscal Year", value="")
    
    # Copy dataset for filtering
    df_view = df[['MinistryName', 'Year', 'Outlay (₹ Cr)', 'Share (%)']].copy()
    df_view.rename(columns={'MinistryName': 'Ministry'}, inplace=True)
    
    if search_query:
        # Case insensitive regex match on year and ministry
        df_view = df_view[
            df_view['Ministry'].str.contains(search_query, case=False, na=False) |
            df_view['Year'].str.contains(search_query, case=False, na=False)
        ]
        
    # Stats row counts
    count = len(df_view)
    st.markdown(f"<p style='color:#00d2d3; font-weight:600; font-size:13px; margin-top:-10px; margin-bottom:15px;'>Displaying {count} rows</p>", unsafe_allow_html=True)
    
    # Table card
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.dataframe(df_view, hide_index=True, use_container_width=True)
    
    # Download Button
    csv = df_view.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Export Filtered Data as CSV",
        data=csv,
        file_name="union_budget_filtered_data.csv",
        mime="text/csv"
    )
    st.markdown("</div>", unsafe_allow_html=True)
