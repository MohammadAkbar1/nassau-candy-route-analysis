import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, add_sidebar_filters, build_route_df

st.set_page_config(page_title="Route Efficiency", page_icon="📊", layout="wide")

df = load_data()
df = add_sidebar_filters(df)

if len(df) == 0:
    st.warning("No data. Adjust filters.")
    st.stop()

route_df = build_route_df(df)

# ── Header ────────────────────────────────────────────────────
st.markdown("## Route Efficiency Analysis")

c1, c2, c3, c4 = st.columns(4)

def kpi(col, label, value, color="#4fc3f7"):
    col.markdown(f"""
    <div>
        <div style='font-size:0.68rem;color:rgba(255,255,255,0.45);
                    text-transform:uppercase;letter-spacing:1px;'>{label}</div>
        <div style='font-size:1.5rem;font-weight:700;color:{color};'>{value}</div>
    </div>""", unsafe_allow_html=True)

kpi(c1, "Total Routes",       str(len(route_df)))
kpi(c2, "Fastest Route Avg",  f"{route_df['Avg_Lead_Time'].min():.0f} days")
kpi(c3, "Slowest Route Avg",  f"{route_df['Avg_Lead_Time'].max():.0f} days")
kpi(c4, "Overall Avg",        f"{route_df['Avg_Lead_Time'].mean():.0f} days")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["Leaderboard", "Fastest Routes", "Slowest Routes"])

with tab1:
    st.markdown("#### Route Performance Leaderboard")
    st.caption("All routes sorted by average lead time")

    display = route_df[[
        'Route','Avg_Lead_Time','Total_Shipments',
        'Total_Sales','Delay_Rate','Avg_Efficiency'
    ]].copy()
    display.index = range(1, len(display)+1)
    display.columns = [
        'Route','Avg Lead Time (days)','Volume',
        'Total Sales ($)','Delay Rate (%)','Avg Efficiency'
    ]
    st.dataframe(display, use_container_width=True, height=480)

with tab2:
    st.markdown("#### Top 15 Fastest Routes")
    st.caption("Routes with the lowest average lead times")

    fastest = route_df.nsmallest(15, 'Avg_Lead_Time')
    fig1 = px.bar(fastest,
                  x='Avg_Lead_Time', y='Route',
                  orientation='h',
                  color='Avg_Lead_Time',
                  color_continuous_scale=[
                      [0,'#2ecc71'],[0.5,'#4fc3f7'],[1,'#e74c3c']
                  ],
                  text='Avg_Lead_Time',
                  labels={'Avg_Lead_Time':'Avg Lead Time (Days)','Route':'Route'})
    fig1.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
    fig1.update_yaxes(autorange='reversed')
    fig1.update_layout(
        height=520, coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab3:
    st.markdown("#### Top 15 Slowest Routes")
    st.caption("Routes with the highest average lead times — need immediate attention")

    slowest = route_df.nlargest(15, 'Avg_Lead_Time')
    fig2 = px.bar(slowest,
                  x='Avg_Lead_Time', y='Route',
                  orientation='h',
                  color='Avg_Lead_Time',
                  color_continuous_scale=[
                      [0,'#f39c12'],[0.5,'#e67e22'],[1,'#e74c3c']
                  ],
                  text='Avg_Lead_Time',
                  labels={'Avg_Lead_Time':'Avg Lead Time (Days)','Route':'Route'})
    fig2.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
    fig2.update_yaxes(autorange='reversed')
    fig2.update_layout(
        height=520, coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── Volume vs Lead Time Scatter ───────────────────────────────
st.markdown("---")
st.markdown("#### Volume vs. Lead Time Scatter")
st.caption("Identify high-risk, high-volume routes")

fig3 = px.scatter(
    route_df,
    x='Total_Shipments', y='Avg_Lead_Time',
    color='Avg_Lead_Time',
    size='Total_Sales',
    hover_name='Route',
    hover_data={
        'Total_Shipments' : True,
        'Avg_Lead_Time'   : True,
        'Delay_Rate'      : True,
        'Avg_Efficiency'  : True
    },
    color_continuous_scale='RdYlGn_r',
    labels={
        'Total_Shipments' : 'Shipment Volume',
        'Avg_Lead_Time'   : 'Avg Lead Time (Days)'
    }
)

avg_vol  = route_df['Total_Shipments'].mean()
avg_lead = route_df['Avg_Lead_Time'].mean()
fig3.add_vline(x=avg_vol,  line_dash='dash', line_color='rgba(255,255,255,0.3)')
fig3.add_hline(y=avg_lead, line_dash='dash', line_color='rgba(255,255,255,0.3)',
               annotation_text=f"Avg: {avg_lead:.0f}d",
               annotation_font_color='rgba(255,255,255,0.6)')

fig3.update_layout(
    height=480,
    plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=False)
)
st.plotly_chart(fig3, use_container_width=True)