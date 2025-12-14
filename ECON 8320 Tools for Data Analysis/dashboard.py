import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import os
import time

#title
st.set_page_config(layout="wide")
st.title("U.S. Labor Statistics Dashboard")

if 'page_view' not in st.session_state:
    st.session_state.page_view = "Employment Statistics"

#load data
def load_data():
    df = pd.read_csv('data.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data()

file_timestamp = os.path.getmtime('data.csv')
refreshed_date = time.strftime('%B %d, %Y', time.localtime(file_timestamp))

#sidebar
st.sidebar.header("🧭 Navigation")

#switch between pages
def set_page(page_name):
    st.session_state.page_view = page_name

#add buttons
st.sidebar.button("💼 Employment Statistics", on_click = set_page, args = ("Employment Statistics",))
st.sidebar.button("📈 Wage Growth vs Inflation", on_click = set_page, args = ("Wage Growth vs Inflation",))
st.sidebar.button("💵 Work Hours & Pay", on_click = set_page, args = ("Work Hours & Pay",))

#time slider
st.sidebar.markdown("---")
st.sidebar.header("📅 Date Range")

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

start_date, end_date = st.sidebar.slider(
    "Select date range",
    min_value = min_date,
    max_value = max_date,
    value = (min_date, max_date), #default
    format="MMM YYYY" 
)
start_date = start_date.replace(day=1)

file_timestamp = os.path.getmtime('data.csv')
refreshed_date = time.strftime('%B %d, %Y', time.localtime(file_timestamp))

st.sidebar.markdown("---")
st.sidebar.caption(f"Dashboard last updated on {refreshed_date}")

#filtered data
df_plot = df.query(("Date >= @start_date and Date <= @end_date")).copy()

#base metrics index
start_row, end_row = df_plot.iloc[0], df_plot.iloc[-1]

#calculated columns
base_cpi = start_row["CPI"]
df_plot['Inflation'] = (df_plot["CPI"] - base_cpi) / base_cpi * 100

base_wage = start_row["Weekly Income"]
df_plot['Wage Growth'] = (df_plot["Weekly Income"] - base_wage) / base_wage * 100

df_plot['Adj Hourly Earnings'] = round(df_plot["Hourly Earnings"] / df_plot["CPI"] * base_cpi, 2)

#calculated indicators
emp_growth = end_row['Employment Level'] - start_row['Employment Level']
unemp_change = round(end_row['Unemployment Rate'] - start_row['Unemployment Rate'], 1)
wage_growth = round((end_row['Weekly Income'] - start_row['Weekly Income']) / start_row['Weekly Income'] * 100, 1)
cpi_change = round((end_row['CPI'] - start_row['CPI']) / start_row['CPI'] * 100, 1)
hr_growth = round((end_row["Hourly Earnings"] - start_row["Hourly Earnings"]) / start_row["Hourly Earnings"] * 100 , 1)
adjhr = round(end_row["Hourly Earnings"] / end_row["CPI"] * base_cpi, 2)
adjhr_growth = round((adjhr - start_row["Hourly Earnings"]) / start_row["Hourly Earnings"] * 100, 1)


fig = go.Figure()

if st.session_state.page_view == "Employment Statistics":
    st.markdown(f"## 💼 Employment Statistics ({start_date.strftime('%b %Y')} — {end_date.strftime('%b %Y')})")

    k1, k2 = st.columns(2)
    k1.metric("Employment", f"{round(end_row['Employment Level'] / 1000, 1):,}M", f"{emp_growth:,}k", delta_color = 'normal')
    k2.metric("Unemployment", f"{end_row['Unemployment Rate']} pts", f"{unemp_change} pts", delta_color = 'inverse')

    selection = st.pills("", ["Employment Level", "Unemployment Rate"], 
                         default=["Employment Level", "Unemployment Rate"], selection_mode="multi")
    

    if "Employment Level" in selection:
        fig.add_trace(go.Scatter(x = df_plot['Date'], y = df_plot['Employment Level'],
                                name = 'Employment Level', line = dict(color = "blue"), yaxis = "y",
                                hovertemplate='%{y:,.0f}k' ))

    if "Unemployment Rate" in selection:
        fig.add_trace(go.Scatter(x = df_plot['Date'], y = df_plot['Unemployment Rate'],
                                name = 'Unemployment Rate', line = dict(color = 'orange'), yaxis = "y2",
                                hovertemplate='%{y:.1f}%' ))

    fig.update_layout(
        yaxis = dict(title = "Employment Level (000s)"),
        yaxis2 = dict(
            title = "Unemployment Rate (%)",
            overlaying = "y",
            side = "right",
            showgrid=False
        ),
        legend=dict(
            orientation="h",  # Horizontal
            yanchor="bottom", 
            y=1.02,           # Slightly above the chart
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Raw Data"):
        st.dataframe(df_plot[['Date', 'Employment Level', 'Unemployment Rate']].style.format({"Employment Level": "{:,.0f}k", "Unemployment Rate": "{:.1f}%"}))


elif st.session_state.page_view == "Wage Growth vs Inflation":
    st.markdown(f"## 📈 Wage Growth vs Inflation ({start_date.strftime('%b %Y')} — {end_date.strftime('%b %Y')})")

    k1, k2 = st.columns(2)
    k1.metric("Est. Weekly Wage", f"${round(end_row['Weekly Income'],1):,}", f"{wage_growth:,}%", delta_color = 'normal')
    k2.metric("CPI", f"{end_row['CPI']}", f"{cpi_change}%", delta_color = 'inverse')

    selection = st.pills("", ["Wage Growth", "Inflation"], 
                         default=["Wage Growth", "Inflation"], selection_mode="multi")

    if "Wage Growth" in selection:
        fig.add_trace(go.Scatter(x = df_plot['Date'], y = df_plot['Wage Growth'],
                            name = 'Wage Growth', line = dict(color = "green"),
                                hovertemplate='%{y:.1f}%'))

    if "Inflation" in selection:
        fig.add_trace(go.Scatter(x = df_plot['Date'], y = df_plot['Inflation'],
                            name = 'Inflation', line = dict(color = 'red'),
                                hovertemplate='%{y:.1f}%'))

    fig.update_layout(
        yaxis = dict(title = "Cumulative Growth (%)"),
        legend=dict(
            orientation="h",  # Horizontal
            yanchor="bottom", 
            y=1.02,           # Slightly above the chart
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Raw Data"):
        st.dataframe(
            df_plot[['Weekly Income', 'Wage Growth', 'CPI', 'Inflation']].style.format({
                'Weekly Income': "${:,.1f}", 
                'Wage Growth': "{:.1f}%",
                'CPI': "{:.1f}", 
                'Inflation': "{:.1f}%"
            })
        )



elif st.session_state.page_view == "Work Hours & Pay":
    st.markdown(f"## 💵 Work Hours & Pay ({start_date.strftime('%b %Y')} — {end_date.strftime('%b %Y')})")

    k1, k2 = st.columns(2)
    k1.metric("Hourly Earnings", f"${round(end_row['Hourly Earnings'],1):,}", f"{hr_growth:,}%", delta_color = 'normal')
    k2.metric("Adj. Hourly Earnings", f"${round(adjhr,1):,}", f"{adjhr_growth}%", delta_color = 'normal')

    selection = st.pills("", ['Hourly Earnings', "Adj. Hourly Earnings", 'Hours Worked'], 
                         default=['Hourly Earnings',"Adj. Hourly Earnings", 'Hours Worked'], selection_mode="multi")
    if 'Hourly Earnings' in selection:
        fig.add_trace(go.Scatter(x = df_plot['Date'], y = df_plot['Hourly Earnings'],
                            name = 'Hourly Earnings', line = dict(color = "purple"), yaxis = "y",
                                hovertemplate='%{y:$,.1f}'))
    
    if 'Adj. Hourly Earnings' in selection:
        fig.add_trace(go.Scatter(x = df_plot['Date'], y = df_plot['Adj Hourly Earnings'],
                            name = 'Adj. Hourly Earnings', line = dict(color = "pink"), yaxis = "y",
                                hovertemplate='%{y:$,.1f}'))

    if 'Hours Worked' in selection:
        fig.add_trace(go.Scatter(x = df_plot['Date'], y = df_plot['Hours Worked'],
                            name = 'Hours Worked', line = dict(color = 'gold'), yaxis = "y2",
                                hovertemplate='%{y:.1f}'))

    fig.update_layout(
        yaxis = dict(title = "Wage ($)"),
        yaxis2 = dict(
            title = "Weekly Hours",
            overlaying = "y",
            side = "right",
            showgrid=False
        ),
        legend=dict(
            orientation="h",  # Horizontal
            yanchor="bottom", 
            y=1.02,           # Slightly above the chart
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View Raw Data"):
        st.dataframe(
            df_plot[['Hourly Earnings', 'Adj Hourly Earnings', 'Hours Worked']].style.format({
                'Hourly Earnings': "${:.1f}", 
                'Adj Hourly Earnings': "${:.1f}",
                'Hours Worked': "{:.1f}"
            })
        )