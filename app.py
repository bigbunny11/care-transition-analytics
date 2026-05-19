import streamlit as st
import pandas as pd
import plotly.express as px 

st.set_page_config(page_title="Care Transition Analytics", layout="wide")

# load the data 
@st.cache_data
def load_data():
    df = pd.read_csv("KPI Sheet  - HHS_Unaccompanied_Alien_Children_Program.csv")
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        'Date': 'Date',
        'Children apprehended and placed in CBP custody*': 'Apprehended',
        'Children in CBP custody': 'CBP_custody',
        'Children transferred out of CBP custody': 'Transferred',
        'Children in HHS Care': 'HHS_Care',
        'Children discharged from HHS Care': 'Discharged',
        'Transfer Efficiency Ratio': 'Transfer_Efficiency',
        'Discharge Effectiveness Index': 'Discharge_Effectiveness',
        'Pipeline Throughput Rate': 'Pipeline_Throughput',
        'Backlog Accumulation Rate': 'Backlog',
        'Outcome Stability Score': 'Stability_Score',
        'Combined Efficiency Score': 'Combined_Score',
        'Months':'Month'
    })

    # Clean numeric columns (remove commas and convert to numeric)
    numeric_cols = ['CBP_custody','HHS_Care','Apprehended','Transferred','Discharged',
                    'Transfer_Efficiency','Discharge_Effectiveness','Pipeline_Throughput',
                    'Backlog','Stability_Score','Combined_Score']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(',','').str.strip()
            df[col] = pd.to_numeric(df[col],errors='coerce')

    # Convert date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df.sort_values('Date')
    return df

df = load_data()

# HEADER

# st.title("🏥 Care Transition Efficiency & Placement Outcome Analytics")
st.markdown("** UAC Program - CBP ➡️ HHS ➡️ Sponsor Pipeline Dashboard**")
st.divider()

# Date Filter 
st.sidebar.header("🔎 Filters")
start_date = st.sidebar.date_input("Start Date", df['Date'].min())
end_date = st.sidebar.date_input("End Date", df['Date'].max())

df_f = df[(df['Date'] >= pd.to_datetime(start_date)) &
          (df['Date'] <= pd.to_datetime(end_date))]

# Threshold Alert

avg_backlog = df_f['Backlog'].mean()
if avg_backlog > 0:
    st.sidebar.error(f"🚨 Backlog Alert! Avg: {avg_backlog:.1f}")
else:
    st.sidebar.success(f"✅ System Flowing. Avg Backlog: {avg_backlog:.1f}")

# Metric Toggle 

st.sidebar.markdown("---")
show_ratios = st.sidebar.toggle("Show Ratio Metrics", value=True)
show_raw = st.sidebar.toggle("Show Raw Data Metrics", value=True)

#KPI Cards

st.subheader("📊 Key Performance Indicators")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Avg Transfer Efficiency", f"{df_f['Transfer_Efficiency'].mean():.2%}")
k2.metric("Avg Discharge Effectiveness", f"{df_f['Discharge_Effectiveness'].mean():.2%}")
k3.metric("Avg Pipeline Throughput", f"{df_f['Pipeline_Throughput'].mean():.2f}")
k4.metric("Total Backlog", f"{df_f['Backlog'].sum():,.0f}")
k5.metric("Avg Stability Score", f"{df_f['Stability_Score'].mean():.4f}")
st.divider()

# Module 1: Care Pipeline Flow 

st.subheader("🔄 Module 1 — Care Pipeline Flow Visualization")
if show_raw:
    fig1 = px.line(df_f, x='Date',
    y=['CBP_custody','HHS_Care'],
    labels={'value': 'Number of Children','variable':'Stage'},
    title="Children in Pipeline",
    color_discrete_map={'CBP_custody': '#EF553B', 'HHS_Care': '#636EFA'})
    st.plotly_chart(fig1, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    fig_in = px.bar(df_f, x='Date', y='Apprehended',
    title='Daily Apprehensions',
    color_discrete_sequence=['#19D3F3'])
    st.plotly_chart(fig_in, use_container_width=True)
with col2:
    fig_out = px.bar(df_f, x='Date', y='Discharged',
    title='Daily Discharges (Sponsor Placements)',
    color_discrete_sequence=['#00CC96'])
    st.plotly_chart(fig_out, use_container_width=True)
st.divider()

# Module 2: TRANSFER & DISCHARGE EFFICIENCY

st.subheader("⚡ Module 2 — Transfer & Discharge Efficiency")
if show_ratios:
    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.line(df_f,x='Date', y='Transfer_Efficiency',
        title='Transfer Efficiency Ratio (CBP ➡️ HHS)',
        color_discrete_sequence=['#00CC96'])
        fig2.add_hline(y=df_f['Transfer_Efficiency'].mean(),
        line_dash="dash", line_color="orange",
        annotation_text="Average")
        st.plotly_chart(fig2, use_container_width=True)
    with col2:
        fig3 = px.line(df_f, x='Date', y='Discharge_Effectiveness',
        title='Discharge Effectiveness Index (HHS ➡️ Sponsor)',
        color_discrete_sequence=['#AB63FA'])
        fig3.add_hline(y=df_f['Discharge_Effectiveness'].mean(),
        line_dash="dash", line_color="orange",
        annotation_text="Average")
        st.plotly_chart(fig3, use_container_width=True)
     
fig_pipe = px.line(df_f, x='Date', y='Pipeline_Throughput',
title='Pipeline Throughput Rate (Overall System Flow)',
color_discrete_sequence=['#FF6692'])
fig_pipe.add_hline(y=1, line_dash="dash", line_color="red",
annotation_text="Threshold =1.0")
st.plotly_chart(fig_pipe, use_container_width=True)
st.divider()

# Module 3: Backlog Detection 

st.subheader("🚨 Module 3 — Bottleneck Detection Charts")
fig4 = px.bar(df_f, x='Date', y='Backlog',
title='Daily Backlog Accumulation Rate (Negative = Good ✅, Positive = Clogged 🚨)',
color='Backlog', 
color_continuous_scale=['green','yellow','red'])
st.plotly_chart(fig4, use_container_width=True)

# Monthly Backlog Summary
df_f['Month_Label'] = df_f['Date'].dt.to_period('M').astype(str)
monthly = df_f.groupby('Month_Label')['Backlog'].sum().reset_index()
fig_monthly = px.bar(monthly, x='Month_Label', y='Backlog',
title='Monthly Total Backlog',
color='Backlog',
color_continuous_scale=['green', 'yellow', 'red'])
fig_monthly.update_xaxes(tickangle=45)
st.plotly_chart(fig_monthly, use_container_width=True)
st.divider()

# Module 4: Outcome Trend Analysis

st.subheader("📈 Module 4 — Outcome Trend Analysis")
fig5 = px.line(df_f, x='Date', y=['Apprehended', 'Discharged'],
title='Daily Apprehensions vs Discharges - Is System Keeping Up?',
color_discrete_map={'Apprehended': '#FFA15A', 'Discharged': '#19D3F3'})

st.plotly_chart(fig5, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    fig6 = px.line(df_f, x='Date', y='Stability_Score',
    title='Outcome Stability Score Over Time',
    color_discrete_sequence=['#B6E880'])
    st.plotly_chart(fig6, use_container_width=True)
with col2:
    fig7 = px.line(df_f, x='Date', y='Combined_Score',
    title='Combined Efficiency Score Over Time',
    color_discrete_sequence=['#FF97FF'])
    st.plotly_chart(fig7, use_container_width=True)

st.divider()
st.caption("📌 Data Source: HHS Unaccompanied Alien Children Program | Fellowship Project")


