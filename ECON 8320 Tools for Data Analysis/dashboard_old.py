import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURATION ---
DATA_FILE = 'processed_data.csv'

# --- 1. LOAD DATA ---
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

# --- 2. PAGE SETTINGS ---
st.set_page_config(page_title="US Economic Dashboard", layout="wide")
st.title("US Macro Economic Dashboard")

if df is None:
    st.error(f"Data file '{DATA_FILE}' not found. Please run the data pipeline first.")
    st.stop()

# --- 3. SIDEBAR: MONTH-YEAR SELECTION ---
st.sidebar.header("⚙️ Dashboard Settings")

# Create a list of all available months
available_months = df['Month_Label'].tolist() 

# Helper to find default indices
try:
    default_start_index = available_months.index("Jan 2020")
except ValueError:
    default_start_index = len(available_months) - 13 

# --- CHANGED: Stacked Dropdowns (Vertical) ---
st.sidebar.markdown("**Select Time Range**")

start_month_str = st.sidebar.selectbox(
    "Start Month", 
    available_months, 
    index=default_start_index
)

end_month_str = st.sidebar.selectbox(
    "End Month", 
    available_months, 
    index=len(available_months) - 1 
)

# Convert the string selections back to actual Date objects
start_date = df[df['Month_Label'] == start_month_str]['Date'].values[0]
end_date = df[df['Month_Label'] == end_month_str]['Date'].values[0]

# Logic Check
if start_date >= end_date:
    st.error("Start Date must be before End Date.")
    st.stop()

# Filter Data
mask = (df['Date'] >= start_date) & (df['Date'] <= end_date)
df_filtered = df.loc[mask].copy()

if df_filtered.empty:
    st.warning("No data found for this range.")
    st.stop()

# --- 4. TOP METRICS (KPIs) ---
start_row = df_filtered.iloc[0]
end_row = df_filtered.iloc[-1]

# --- CHANGED: Correct Delta Calculation ---
# 1. Unemployment: Point Difference
unemp_delta = end_row['Unemployment Rate'] - start_row['Unemployment Rate']

# 2. Inflation: Percent Growth & Index Point Change
cpi_growth = ((end_row['CPI'] - start_row['CPI']) / start_row['CPI']) * 100
cpi_delta_val = end_row['CPI'] - start_row['CPI']

# 3. Nominal Wages: Percent Growth & Dollar Amount Change
wage_growth = ((end_row['Weekly Earnings'] - start_row['Weekly Earnings']) / start_row['Weekly Earnings']) * 100
wage_delta_val = end_row['Weekly Earnings'] - start_row['Weekly Earnings']

# 4. Real Wages: Percent Growth & Dollar Amount Change
real_wage_growth = ((end_row['Real Weekly Earnings'] - start_row['Real Weekly Earnings']) / start_row['Real Weekly Earnings']) * 100
real_wage_delta_val = end_row['Real Weekly Earnings'] - start_row['Real Weekly Earnings']

st.markdown(f"### 📊 Changes from {start_month_str} to {end_month_str}")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric(
    "Unemployment Rate", 
    f"{end_row['Unemployment Rate']}%", 
    f"{unemp_delta:+.1f} pts", 
    delta_color="inverse"
)
kpi2.metric(
    "Total Inflation", 
    f"{cpi_growth:.1f}%", 
    f"{cpi_delta_val:+.1f} Index Pts", 
    delta_color="inverse"
)
kpi3.metric(
    "Nominal Wage Growth", 
    f"{wage_growth:.1f}%", 
    f"{wage_delta_val:+.2f} /wk",
    delta_color="normal"
)
kpi4.metric(
    "Real Purchasing Power", 
    f"{real_wage_growth:.1f}%", 
    f"{real_wage_delta_val:+.2f} (Adj)", 
    delta_color="normal"
)

st.divider()

# --- 5. CHART 1: THE RACE ---
st.subheader("Wages Growth vs. Inflation")
st.markdown(f"Comparing cumulative growth starting from 0% in **{start_month_str}**.")

base_cpi = start_row['CPI']
base_wage = start_row['Weekly Earnings']
df_filtered['Cumulative Inflation'] = ((df_filtered['CPI'] - base_cpi) / base_cpi) * 100
df_filtered['Cumulative Wages'] = ((df_filtered['Weekly Earnings'] - base_wage) / base_wage) * 100

race_metrics = st.multiselect(
    "Select Metrics:", ["Inflation (CPI)", "Wage Growth"],
    default=["Inflation (CPI)", "Wage Growth"], key="race"
)

fig_race = go.Figure()

if "Inflation (CPI)" in race_metrics:
    fig_race.add_trace(go.Scatter(
        x=df_filtered['Date'], y=df_filtered['Cumulative Inflation'],
        mode='lines', name='Inflation (CPI)', line=dict(color='#ff4b4b', width=3)
    ))

if "Wage Growth" in race_metrics:
    fig_race.add_trace(go.Scatter(
        x=df_filtered['Date'], y=df_filtered['Cumulative Wages'],
        mode='lines', name='Wage Growth', line=dict(color='#2bd666', width=3)
    ))

if len(race_metrics) == 2:
    fig_race.add_trace(go.Scatter(
        x=df_filtered['Date'], y=df_filtered['Cumulative Wages'],
        fill='tonexty', fillcolor='rgba(43, 214, 102, 0.1)',
        mode='none', showlegend=False, hoverinfo='skip'
    ))

fig_race.update_layout(yaxis_title="Cumulative Growth (%)", hovermode="x unified")
st.plotly_chart(fig_race, use_container_width=True)

# --- 6. CHART 2: LABOR COMPONENTS ---
st.subheader("Labor Components")
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("**Hourly Earnings ($)**")
    if st.checkbox("Show Hourly Earnings", value=True):
        fig_h = go.Figure()
        fig_h.add_trace(go.Scatter(
            x=df_filtered['Date'], y=df_filtered['Hourly Earnings'],
            line=dict(color='#3498db', width=2)
        ))
        fig_h.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig_h, use_container_width=True)

with col_right:
    st.markdown("**Weekly Hours Worked**")
    if st.checkbox("Show Hours Worked", value=True):
        fig_w = go.Figure()
        fig_w.add_trace(go.Scatter(
            x=df_filtered['Date'], y=df_filtered['Hours Worked'],
            line=dict(color='#9b59b6', width=2)
        ))
        fig_w.update_layout(height=300, margin=dict(l=10,r=10,t=10,b=10))
        st.plotly_chart(fig_w, use_container_width=True)

# --- 7. CHART 3: EMPLOYMENT STATUS ---
st.subheader("Employment Status")
labor_metrics = st.multiselect(
    "Select Metrics:", ["Unemployment Rate", "Total Employment"],
    default=["Unemployment Rate", "Total Employment"], key="labor"
)

fig_labor = make_subplots(specs=[[{"secondary_y": True}]])

if "Total Employment" in labor_metrics:
    fig_labor.add_trace(
        go.Scatter(x=df_filtered['Date'], y=df_filtered['Employment Level']/1000, name="Total Jobs",
                   line=dict(color='#34495e', width=3)), secondary_y=False
    )

if "Unemployment Rate" in labor_metrics:
    fig_labor.add_trace(
        go.Scatter(x=df_filtered['Date'], y=df_filtered['Unemployment Rate'], name="Unemployment %",
                   line=dict(color='#e74c3c', width=3, dash='dot')), secondary_y=True
    )

fig_labor.update_yaxes(title_text="Jobs (MM)", secondary_y=False, showgrid=False)
fig_labor.update_yaxes(title_text="Unemployment (%)", secondary_y=True, showgrid=False)
st.plotly_chart(fig_labor, use_container_width=True)