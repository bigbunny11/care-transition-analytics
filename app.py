import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Care Transition Analytics", layout="wide")

# ── LOAD DATA ──
@st.cache_data
def load_data():
    df = pd.read_csv("KPI Sheet - HHS_Unaccompanied_Alien_Children_Program.csv")
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        'Date': 'Date',
        'Children apprehended and placed in CBP custody*': 'Apprehended',
        'Children in CBP custody': 'CBP_Custody',
        'Children transferred out of CBP custody': 'Transferred',
        'Children in HHS Care': 'HHS_Care',
        'Children discharged from HHS Care': 'Discharged',
        'Transfer Efficiency Ratio': 'Transfer_Efficiency',
        'Discharge Effectiveness Index': 'Discharge_Effectiveness',
        'Pipeline Throughput Rate': 'Pipeline_Throughput',
        'Backlog Accumulation Rate': 'Backlog',
        'Outcome Stability Score': 'Stability_Score',
        'Combined Efficiency Score': 'Combined_Score',
        'Months': 'Month'
    })
    # Clean numeric columns (remove commas)
    for col in ['CBP_Custody', 'HHS_Care']:
        df[col] = df[col].astype(str).str.replace(',', '').str.strip()
        df[col] = pd.to_numeric(df[col], errors='coerce')
    # Convert date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df.sort_values('Date')
    return df

df = load_data()

# ── HEADER ──
st.title("🏥 Care Transition Efficiency & Placement Outcome Analytics")
st.markdown("**UAC Program — CBP → HHS → Sponsor Pipeline Dashboard**")
st.divider()

# ── DATE FILTER ──
st.sidebar.header("🔍 Filters")
start_date = st.sidebar.date_input("Start Date", df['Date'].min())
end_date = st.sidebar.date_input("End Date", df['Date'].max())

df_f = df[(df['Date'] >= pd.to_datetime(start_date)) &
          (df['Date'] <= pd.to_datetime(end_date))]

# ── THRESHOLD ALERT ──
avg_backlog = df_f['Backlog'].mean()
if avg_backlog > 0:
    st.sidebar.error(f"🚨 Backlog Alert! Avg: {avg_backlog:.1f}")
else:
    st.sidebar.success(f"✅ System Flowing. Avg Backlog: {avg_backlog:.1f}")

# ── METRIC TOGGLE ──
st.sidebar.markdown("---")
show_ratios = st.sidebar.toggle("Show Ratio Metrics", value=True)
show_raw = st.sidebar.toggle("Show Raw Numbers", value=True)

# ── KPI CARDS ──
st.subheader("📊 Key Performance Indicators")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg Transfer Efficiency", f"{df_f['Transfer_Efficiency'].mean():.2%}")
k2.metric("Avg Discharge Effectiveness", f"{df_f['Discharge_Effectiveness'].mean():.2%}")
k3.metric("Avg Pipeline Throughput", f"{df_f['Pipeline_Throughput'].mean():.2f}")
k4.metric("Total Backlog", f"{df_f['Backlog'].sum():,.0f}")
k5.metric("Avg Stability Score", f"{df_f['Stability_Score'].mean():.4f}")
st.divider()

# ── MODULE 1: CARE PIPELINE FLOW ──
st.subheader("🔄 Module 1 — Care Pipeline Flow Visualization")
if show_raw:
    fig1 = px.line(df_f, x='Date',
                   y=['CBP_Custody', 'HHS_Care'],
                   labels={'value': 'Number of Children', 'variable': 'Stage'},
                   title='Children in CBP Custody vs HHS Care Over Time',
                   color_discrete_map={'CBP_Custody': '#EF553B', 'HHS_Care': '#636EFA'})
    st.plotly_chart(fig1, width="stretch")

col1, col2 = st.columns(2)
with col1:
    fig_in = px.bar(df_f, x='Date', y='Apprehended',
                    title='Daily Apprehensions (New Intakes)',
                    color_discrete_sequence=['#FFA15A'])
    st.plotly_chart(fig_in, width="stretch")
with col2:
    fig_out = px.bar(df_f, x='Date', y='Discharged',
                     title='Daily Discharges (Sponsor Placements)',
                     color_discrete_sequence=['#19D3F3'])
    st.plotly_chart(fig_out, width="stretch")
st.divider()

# ── MODULE 2: TRANSFER & DISCHARGE EFFICIENCY ──
st.subheader("⚡ Module 2 — Transfer & Discharge Efficiency Panels")
if show_ratios:
    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.line(df_f, x='Date', y='Transfer_Efficiency',
                       title='Transfer Efficiency Ratio (CBP → HHS)',
                       color_discrete_sequence=['#00CC96'])
        fig2.add_hline(y=df_f['Transfer_Efficiency'].mean(),
                       line_dash="dash", line_color="orange",
                       annotation_text="Average")
        st.plotly_chart(fig2, width="stretch")
    with col2:
        fig3 = px.line(df_f, x='Date', y='Discharge_Effectiveness',
                       title='Discharge Effectiveness Index (HHS → Sponsor)',
                       color_discrete_sequence=['#AB63FA'])
        fig3.add_hline(y=df_f['Discharge_Effectiveness'].mean(),
                       line_dash="dash", line_color="orange",
                       annotation_text="Average")
        st.plotly_chart(fig3, width="stretch")

    fig_pipe = px.line(df_f, x='Date', y='Pipeline_Throughput',
                       title='Pipeline Throughput Rate (Overall System Flow)',
                       color_discrete_sequence=['#FF6692'])
    fig_pipe.add_hline(y=1, line_dash="dash", line_color="red",
                       annotation_text="Threshold = 1.0")
    st.plotly_chart(fig_pipe, width="stretch")
st.divider()

# ── MODULE 3: BACKLOG DETECTION ──
st.subheader("🚨 Module 3 — Bottleneck Detection Charts")
fig4 = px.bar(df_f, x='Date', y='Backlog',
              title='Daily Backlog Accumulation Rate (Negative = Good ✅, Positive = Clogged 🔴)',
              color='Backlog',
              color_continuous_scale=['green', 'yellow', 'red'])
st.plotly_chart(fig4, width="stretch")

# Monthly backlog summary
df_f['Month_Label'] = df_f['Date'].dt.to_period('M').astype(str)
monthly = df_f.groupby('Month_Label')['Backlog'].sum().reset_index()
fig_monthly = px.bar(monthly, x='Month_Label', y='Backlog',
                     title='Monthly Total Backlog',
                     color='Backlog',
                     color_continuous_scale=['green', 'yellow', 'red'])
fig_monthly.update_xaxes(tickangle=45)
st.plotly_chart(fig_monthly, width="stretch")
st.divider()

# ── MODULE 4: OUTCOME TREND ANALYSIS ──
st.subheader("📈 Module 4 — Outcome Trend Analysis")
fig5 = px.line(df_f, x='Date', y=['Apprehended', 'Discharged'],
               title='Daily Apprehensions vs Discharges — Is System Keeping Up?',
               color_discrete_map={'Apprehended': '#FFA15A', 'Discharged': '#19D3F3'})
st.plotly_chart(fig5, width="stretch")

col1, col2 = st.columns(2)
with col1:
    fig6 = px.line(df_f, x='Date', y='Stability_Score',
                   title='Outcome Stability Score Over Time',
                   color_discrete_sequence=['#B6E880'])
    st.plotly_chart(fig6, width="stretch")
with col2:
    fig7 = px.line(df_f, x='Date', y='Combined_Score',
                   title='Combined Efficiency Score Over Time',
                   color_discrete_sequence=['#FF97FF'])
    st.plotly_chart(fig7, width="stretch")

st.divider()
st.caption("📌 Data Source: HHS Unaccompanied Alien Children Program | Fellowship Project")
