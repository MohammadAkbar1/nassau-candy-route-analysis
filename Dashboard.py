import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils import load_data, add_sidebar_filters, build_route_df

st.set_page_config(
    page_title="Nassau Logistics Dashboard",
    page_icon="📊", layout="wide",
    initial_sidebar_state="expanded"
)

df = load_data()
df = add_sidebar_filters(df)

if len(df) == 0:
    st.warning("No data matches your filters.")
    st.stop()

# ── Header ────────────────────────────────────────────────────
st.markdown("## Nassau Candy | Route Efficiency & Lead Time Analysis")
st.markdown("## Overview Dashboard")

# ── Top KPIs ──────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

def metric_card(col, label, value, color="#4fc3f7"):
    col.markdown(f"""
    <div style='padding:4px 0;'>
        <div style='font-size:0.7rem;color:rgba(255,255,255,0.5);
                    text-transform:uppercase;letter-spacing:1px;'>{label}</div>
        <div style='font-size:1.6rem;font-weight:700;color:{color};'>{value}</div>
    </div>
    """, unsafe_allow_html=True)

delay_rate   = df['Is_Delayed'].mean() * 100
route_df     = build_route_df(df)

metric_card(c1, "Total Shipments",  f"{len(df):,}")
metric_card(c2, "Avg Lead Time",    f"{df['Lead_Time'].mean():.0f} days")
metric_card(c3, "Active Routes",    f"{len(route_df)}")
metric_card(c4, "Delay Rate",       f"{delay_rate:.1f}%")
metric_card(c5, "Total Sales",      f"${df['Sales'].sum():,.0f}")

st.markdown("---")

# ── Row 1: Shipments by Ship Mode + Shipments by Division ─────
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Shipments by Ship Mode")
    st.caption("Volume distribution across shipping methods")
    mode_counts = df.groupby('Ship Mode').size().reset_index(name='Shipments')
    fig1 = px.bar(mode_counts.sort_values('Shipments', ascending=False),
                  x='Ship Mode', y='Shipments',
                  color='Ship Mode',
                  color_discrete_sequence=['#4fc3f7','#f39c12','#2ecc71','#e74c3c'],
                  text='Shipments')
    fig1.update_traces(textposition='outside')
    fig1.update_layout(
        showlegend=False, height=320,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False, title='')
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("##### Shipments by Division")
    st.caption("Candy product category breakdown")
    div_counts = df.groupby('Division').size().reset_index(name='Shipments')
    fig2 = px.pie(div_counts, values='Shipments', names='Division',
                  hole=0.55,
                  color_discrete_sequence=['#4fc3f7','#2ecc71','#f39c12'])
    fig2.update_traces(textposition='inside', textinfo='percent+label')
    fig2.update_layout(
        height=320,
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(orientation='v', x=1, y=0.5)
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Monthly Volume + Shipments by Region ───────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("##### Monthly Shipment Volume and Avg Lead Time")
    st.caption("Trend over the order date period")
    df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
    monthly = df.groupby('Month').agg(
        Shipments     = ('Lead_Time','count'),
        Avg_Lead_Time = ('Lead_Time','mean')
    ).reset_index().sort_values('Month')

    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Bar(x=monthly['Month'], y=monthly['Shipments'],
                          name='Shipments', marker_color='#4fc3f7', opacity=0.8),
                   secondary_y=False)
    fig3.add_trace(go.Scatter(x=monthly['Month'], y=monthly['Avg_Lead_Time'].round(0),
                              name='Avg Lead Time', mode='lines+markers',
                              line=dict(color='#f39c12', width=2.5),
                              marker=dict(size=5)),
                   secondary_y=True)
    fig3.update_layout(
        height=320, showlegend=True,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='h', x=0, y=1.1),
        xaxis=dict(showgrid=False, tickangle=45),
        yaxis=dict(showgrid=False, title='Shipments'),
        yaxis2=dict(showgrid=False, title='Avg Lead Time (Days)')
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("##### Shipments by Region")
    region_counts = df.groupby('Region').size().reset_index(name='Shipments')
    fig4 = px.bar(region_counts.sort_values('Shipments', ascending=True),
                  x='Shipments', y='Region', orientation='h',
                  color_discrete_sequence=['#4fc3f7'],
                  text='Shipments')
    fig4.update_traces(textposition='outside')
    fig4.update_layout(
        height=320,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title='Shipments'),
        yaxis=dict(showgrid=False, title='')
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Delayed vs On-Time by Ship Mode ────────────────────
st.markdown("##### Delayed vs On-Time Shipments by Ship Mode")

mode_delay = df.groupby('Ship Mode').agg(
    Total   = ('Is_Delayed','count'),
    Delayed = ('Is_Delayed','sum')
).reset_index()
mode_delay['On_Time'] = mode_delay['Total'] - mode_delay['Delayed']

fig5 = go.Figure()
fig5.add_trace(go.Bar(
    name='On-Time', x=mode_delay['Ship Mode'],
    y=mode_delay['On_Time'], marker_color='#2ecc71',
    text=mode_delay['On_Time'], textposition='outside'
))
fig5.add_trace(go.Bar(
    name='Delayed', x=mode_delay['Ship Mode'],
    y=mode_delay['Delayed'], marker_color='#e74c3c',
    text=mode_delay['Delayed'], textposition='outside'
))
fig5.update_layout(
    barmode='group', height=320,
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    legend=dict(orientation='h', x=0.8, y=1.1),
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False, title='Shipments')
)
st.plotly_chart(fig5, use_container_width=True)