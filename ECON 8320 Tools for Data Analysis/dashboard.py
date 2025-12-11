import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURATION ---
DATA_FILE = 'processed_data.csv'

# --- 1. SETUP & STATE ---
st.set_page_config(page_title="US Economic Dashboard", layout="wide")

# Initialize Session State for Page Navigation
if 'page_view' not in st.session_state:
    st.session_state.page_view = "Wage vs Inflation" # Default Start Page

# --- 2. LOAD DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_csv(DATA_FILE)
        df['Date'] = pd.to_datetime(df['Date'])
        # Create a formatted string column for the dropdowns (e.g., "Jan 2020")
        df['Month_Label'] = df['Date'].dt.strftime('%b %Y') 
        return df
    except FileNotFoundError:
        return None

df = load_data()

# --- 3. CUSTOM CSS (Just for Button Width) ---
# Keeping only this small styling to make sidebar buttons look like full-width tabs
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        text-align: left;
        border-radius: 8px;
        height: 3em;
    }
</style>
""", unsafe_allow_html=True)

if df is None:
    st.error(f"Data file '{DATA_FILE}' not found. Please run the data pipeline first.")
    st.stop()

st.title("US Macro Economic Dashboard")

# --- 4. SIDEBAR: NAVIGATION & SETTINGS ---
st.sidebar.header("Navigation")

# Callback function to change the page
def set_page(page_name):
    st.session_state.page_view = page_name

# Navigation Buttons
st.sidebar.button("Wage vs Inflation", on_click=set_page, args=("Wage vs Inflation",))
st.sidebar.button("Work Hours & Pay", on_click=set_page, args=("Work Hours & Pay",))
st.sidebar.button("Employment Market", on_click=set_page, args=("Employment Market",))

st.sidebar.markdown("---")
st.sidebar.header("Time Settings")

# Date Selection Logic
available_months = df['Month_Label'].tolist() 
try:
    default_start = available_months.index("Jan 2020")
except ValueError:
    default_start = len(available_months) - 13

start_str = st.sidebar.selectbox("Start Month", available_months, index=default_start)
end_str = st.sidebar.selectbox("End Month", available_months, index=len(available_months)-1)

start_date = df[df['Month_Label'] == start_str]['Date'].values[0]
end_date = df[df['Month_Label'] == end_str]['Date'].values[0]

if start_date >= end_date:
    st.error("Start Date must be before End Date.")
    st.stop()

# Filter Data
mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
df_filtered = df.loc[mask].copy()


# --- 5. TOP SECTION: INDICATORS ---
start_row, end_row = df_filtered.iloc[0], df_filtered.iloc[-1]

# Calculations
unemp_delta = end_row['Unemployment Rate'] - start_row['Unemployment Rate']
cpi_growth = ((end_row['CPI'] - start_row['CPI']) / start_row['CPI']) * 100
cpi_delta = end_row['CPI'] - start_row['CPI']
wage_growth = ((end_row['Weekly Earnings'] - start_row['Weekly Earnings']) / start_row['Weekly Earnings']) * 100
wage_delta = end_row['Weekly Earnings'] - start_row['Weekly Earnings']
real_growth = ((end_row['Real Weekly Earnings'] - start_row['Real Weekly Earnings']) / start_row['Real Weekly Earnings']) * 100
real_delta = end_row['Real Weekly Earnings'] - start_row['Real Weekly Earnings']

st.markdown(f"### ⏱️ Period: {start_str} — {end_str}")
k1, k2, k3, k4 = st.columns(4)

k1.metric("Unemployment", f"{end_row['Unemployment Rate']}%", f"{unemp_delta:+.1f} pts", delta_color="inverse")
k2.metric("Total Inflation", f"{cpi_growth:.1f}%", f"{cpi_delta:+.1f} Index Pts", delta_color="inverse")
k3.metric("Nominal Wages", f"{wage_growth:.1f}%", f"{wage_delta:+.2f} /wk", delta_color="normal")
k4.metric("Real Wages", f"{real_growth:.1f}%", f"{real_delta:+.2f} (Adj)", delta_color="normal")

st.divider()

# --- 6. BOTTOM SECTION: VISUALS ---

# PAGE 1: WAGE VS INFLATION
if st.session_state.page_view == "Wage vs Inflation":
    st.subheader("The Race: Wages vs. Inflation")
    st.markdown("Comparing cumulative growth from your start date (Base = 0%).")
    
    # Rebase Logic
    base_cpi = start_row['CPI']
    base_wage = start_row['Weekly Earnings']
    df_filtered['CPI_Growth'] = ((df_filtered['CPI'] - base_cpi) / base_cpi) * 100
    df_filtered['Wage_Growth'] = ((df_filtered['Weekly Earnings'] - base_wage) / base_wage) * 100

    selection = st.pills("Metrics:", ["Inflation (CPI)", "Wage Growth"], 
                         default=["Inflation (CPI)", "Wage Growth"], selection_mode="multi")

    fig = go.Figure()
    if "Inflation (CPI)" in selection:
        fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['CPI_Growth'], 
                                 name='Inflation', line=dict(color='#ff4b4b', width=3)))
    if "Wage Growth" in selection:
        fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Wage_Growth'], 
                                 name='Wage Growth', line=dict(color='#2bd666', width=3)))
        
    if len(selection) == 2:
        fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Wage_Growth'], 
                                 fill='tonexty', fillcolor='rgba(43, 214, 102, 0.1)', 
                                 mode='none', showlegend=False, hoverinfo='skip'))

    fig.update_layout(yaxis_title="Cumulative Growth (%)", hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)

# PAGE 2: WORK HOURS & PAY
elif st.session_state.page_view == "Work Hours & Pay":
    st.subheader("Labor Inputs: Hours & Pay")
    st.markdown("Comparing Hourly Rates (Left Axis) vs Weekly Hours (Right Axis).")
    
    selection = st.pills("Metrics:", ["Hourly Earnings ($)", "Weekly Hours"], 
                         default=["Hourly Earnings ($)", "Weekly Hours"], selection_mode="multi")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "Hourly Earnings ($)" in selection:
        fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Hourly Earnings'], 
                                 name="Hourly Rate ($)", line=dict(color='#3498db', width=3)), secondary_y=False)
        
    if "Weekly Hours" in selection:
        fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Hours Worked'], 
                                 name="Weekly Hours", line=dict(color='#9b59b6', width=3, dash='dot')), secondary_y=True)

    fig.update_yaxes(title_text="Hourly Rate ($)", secondary_y=False, showgrid=True)
    fig.update_yaxes(title_text="Hours Worked", secondary_y=True, showgrid=False)
    fig.update_layout(hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)

# PAGE 3: EMPLOYMENT MARKET
elif st.session_state.page_view == "Employment Market":
    st.subheader("Employment Status")
    st.markdown("Total Employment (Left Axis) vs Unemployment Rate (Right Axis).")
    
    selection = st.pills("Metrics:", ["Total Jobs", "Unemployment Rate"], 
                         default=["Total Jobs", "Unemployment Rate"], selection_mode="multi")

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "Total Jobs" in selection:
        fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Employment Level'], 
                                 name="Total Jobs (000s)", fill='tozeroy', 
                                 line=dict(color='#34495e')), secondary_y=False)

    if "Unemployment Rate" in selection:
        fig.add_trace(go.Scatter(x=df_filtered['Date'], y=df_filtered['Unemployment Rate'], 
                                 name="Unemployment Rate (%)", 
                                 line=dict(color='#e74c3c', width=3)), secondary_y=True)

    fig.update_yaxes(title_text="Total Jobs", secondary_y=False, showgrid=True)
    fig.update_yaxes(title_text="Unemployment Rate (%)", secondary_y=True, showgrid=False)
    fig.update_layout(hovermode="x unified", height=500)
    st.plotly_chart(fig, use_container_width=True)