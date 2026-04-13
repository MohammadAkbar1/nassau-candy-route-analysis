import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, add_sidebar_filters

st.set_page_config(page_title="Ship Mode Comparison", page_icon="🚚", layout="wide")

df = load_data()
df = add_sidebar_filters(df)

if len(df) == 0:
    st.warning("No data. Adjust filters.")
    st.stop()

mode_df = df.groupby('Ship Mode').agg(
    Total_Shipments = ('Lead_Time','count'),
    Avg_Lead_Time   = ('Lead_Time','mean'),
    Min_Lead_Time   = ('Lead_Time','min'),
    Max_Lead_Time   = ('Lead_Time','max'),
    Std_Dev         = ('Lead_Time','std'),
    Avg_Sales       = ('Sales','mean'),
    Total_Sales     = ('Sales','sum'),
    Total_Profit    = ('Gross Profit','sum'),
    Avg_Margin      = ('Profit_Margin','mean'),
    Delay_Rate      = ('Is_Delayed','mean')
).reset_index().round(2)
mode_df['Delay_Rate']    = (mode_df['Delay_Rate'] * 100).round(1)
mode_df['Avg_Lead_Time'] = mode_df['Avg_Lead_Time'].round(1)

# ── Header KPIs per mode ──────────────────────────────────────
st.markdown("### Ship Mode Performance")

cols = st.columns(4)
mode_colors = {
    'First Class'   : '#4fc3f7',
    'Same Day'      : '#f39c12',
    'Second Class'  : '#e74c3c',
    'Standard Class': '#2ecc71'
}
for i, (_, row) in enumerate(mode_df.sort_values('Avg_Lead_Time').iterrows()):
    color = mode_colors.get(row['Ship Mode'], '#4fc3f7')
    cols[i].markdown(f"""
    <div style='padding:4px 0;'>
        <div style='font-size:0.65rem;color:rgba(255,255,255,0.45);
                    text-transform:uppercase;letter-spacing:1px;'>
            {row['Ship Mode']}</div>
        <div style='font-size:1.4rem;font-weight:700;color:{color};'>
            {row['Avg_Lead_Time']:.0f}d avg</div>
        <div style='font-size:0.72rem;color:rgba(255,255,255,0.4);'>
            {row['Total_Shipments']:,} shipments</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Row 1: Avg Lead Time bar + Pie ────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Average Lead Time by Ship Mode")
    st.caption("Avg Lead Time Comparison")

    colors = [mode_colors.get(m,'#4fc3f7') for m in
              mode_df.sort_values('Avg_Lead_Time')['Ship Mode']]
    mode_sorted = mode_df.sort_values('Avg_Lead_Time')

    fig1 = go.Figure()
    for _, row in mode_sorted.iterrows():
        color = mode_colors.get(row['Ship Mode'], '#4fc3f7')
        fig1.add_trace(go.Bar(
            x=[row['Ship Mode']], y=[row['Avg_Lead_Time']],
            name=row['Ship Mode'], marker_color=color,
            text=[f"{row['Avg_Lead_Time']:.0f}d"],
            textposition='outside'
        ))
    fig1.update_layout(
        showlegend=False, height=300,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(showgrid=False, title='Avg Lead Time (Days)')
    )
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.markdown("##### Shipment Volume by Ship Mode")
    st.caption("Volume Distribution")

    fig2 = px.pie(mode_df,
                  values='Total_Shipments', names='Ship Mode',
                  hole=0.55,
                  color='Ship Mode',
                  color_discrete_map=mode_colors)
    fig2.update_traces(textposition='outside', textinfo='percent')
    fig2.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation='v', x=1, y=0.5)
    )
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ── Row 2: Box plot + Delay Rate ──────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.markdown("##### Lead Time Distribution by Ship Mode")
    st.caption("Lead Time Box Plot")

    fig3 = go.Figure()
    mode_order = ['Standard Class','First Class','Second Class','Same Day']
    for mode in mode_order:
        color = mode_colors.get(mode, '#4fc3f7')
        mode_data = df[df['Ship Mode'] == mode]['Lead_Time']
        fig3.add_trace(go.Box(
    y=mode_data, 
    name=mode,
    marker_color=color, 
    line_color=color,
    fillcolor=color,   
    opacity=0.2        
))
        
    fig3.update_layout(
        showlegend=False, height=320,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(showgrid=False, title='Lead Time (Days)')
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.markdown("##### Delay Rate by Ship Mode")
    st.caption("% Delayed Shipments")

    fig4 = go.Figure()
    mode_delay_s = mode_df.sort_values('Delay_Rate', ascending=False)
    for _, row in mode_delay_s.iterrows():
        color = mode_colors.get(row['Ship Mode'], '#4fc3f7')
        fig4.add_trace(go.Bar(
            x=[row['Ship Mode']], y=[row['Delay_Rate']],
            name=row['Ship Mode'], marker_color=color,
            text=[f"{row['Delay_Rate']:.1f}%"],
            textposition='outside'
        ))
    fig4.update_layout(
        showlegend=False, height=320,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, title=''),
        yaxis=dict(showgrid=False, title='Delay Rate (%)')
    )
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ── Summary Table ─────────────────────────────────────────────
st.markdown("##### Ship Mode Performance Summary Table")

display_mode = mode_df[[
    'Ship Mode','Avg_Lead_Time','Total_Shipments','Avg_Sales','Total_Sales',
    'Avg_Margin','Delay_Rate'
]].copy()
display_mode.index = range(1, len(display_mode)+1)
display_mode.columns = [
    'Ship Mode','Avg Lead Time','Total Shipments','Avg Sales',
    'Total Sales','Avg Profit Margin','Delay Rate'
]
st.dataframe(display_mode, use_container_width=True)

st.markdown("---")

# ── Lead Time Trend Over Time ─────────────────────────────────
st.markdown("##### Ship Mode Lead Time Trend Over Time")

df['Month'] = df['Order Date'].dt.to_period('M').astype(str)
monthly_mode = df.groupby(['Month','Ship Mode'])['Lead_Time'].mean().reset_index()
monthly_mode['Lead_Time'] = monthly_mode['Lead_Time'].round(1)
monthly_mode = monthly_mode.sort_values('Month')

fig5 = px.line(monthly_mode, x='Month', y='Lead_Time',
               color='Ship Mode',
               color_discrete_map=mode_colors,
               markers=True,
               labels={
                   'Lead_Time':'Avg Lead Time (Days)',
                   'Month':'Month'
               })
fig5.update_traces(marker_size=4, line_width=1.8)
fig5.update_layout(
    height=360,
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False, tickangle=45),
    yaxis=dict(showgrid=False, title='Avg Lead Time (Days)'),
    legend=dict(orientation='h', x=0.8, y=1.12)
)
st.plotly_chart(fig5, use_container_width=True)