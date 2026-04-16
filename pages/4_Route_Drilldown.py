import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, add_sidebar_filters, build_route_df

st.set_page_config(page_title="Route Drill-Down", page_icon="🔍", layout="wide")

df = load_data()
df = add_sidebar_filters(df)
route_df = build_route_df(df)

if len(df) == 0:
    st.warning("No data. Adjust filters.")
    st.stop()

st.markdown("## Route Drill-Down")

# ── Route Selector ────────────────────────────────────────────
st.markdown("**SELECT ROUTE**")
all_routes = sorted(df['Route'].unique().tolist())
selected_route = st.selectbox("Route", all_routes, label_visibility="collapsed")

route_data = df[df['Route'] == selected_route].copy()

if len(route_data) == 0:
    st.warning("No data for this route with current filters.")
    st.stop()

# Score
route_score_row = route_df[route_df['Route'] == selected_route]
efficiency = route_score_row['Avg_Efficiency'].values[0] if len(route_score_row) > 0 else 0

st.markdown("---")

# ── KPIs ──────────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)

def kpi(col, label, value, color="#4fc3f7"):
    col.markdown(f"""
    <div>
        <div style='font-size:0.65rem;color:rgba(255,255,255,0.45);
                    text-transform:uppercase;letter-spacing:1px;'>{label}</div>
        <div style='font-size:1.5rem;font-weight:700;color:{color};'>{value}</div>
    </div>""", unsafe_allow_html=True)

kpi(c1, "Total Shipments", f"{len(route_data):,}")
kpi(c2, "Avg Lead Time",   f"{route_data['Lead_Time'].mean():.0f} days")
kpi(c3, "Min Lead Time",   f"{route_data['Lead_Time'].min():.0f} days")
kpi(c4, "Max Lead Time",   f"{route_data['Lead_Time'].max():.0f} days")
kpi(c5, "Delay Rate",      f"{route_data['Is_Delayed'].mean()*100:.1f}%", "#e74c3c")

st.info(
    f"Showing **{len(route_data):,}** shipments for route "
    f"**{selected_route}** | Avg efficiency score: **{efficiency:.3f}**"
)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["State Insights", "Order Timeline", "KPI Trends"])

with tab1:
    st.markdown("#### State-Level Performance Insights")

    state_perf = route_data.groupby('State/Province').agg(
        Shipments  = ('Lead_Time','count'),
        Avg_Lead   = ('Lead_Time','mean'),
        Min_Lead   = ('Lead_Time','min'),
        Max_Lead   = ('Lead_Time','max'),
        Delay_Rate = ('Is_Delayed','mean'),
        Total_Sales= ('Sales','sum')
    ).reset_index()
    state_perf['Avg_Lead']   = state_perf['Avg_Lead'].round(1)
    state_perf['Delay_Rate'] = (state_perf['Delay_Rate'] * 100).round(1)
    state_perf = state_perf.sort_values('Avg_Lead', ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        st.caption("Avg Lead Time — All States")
        fig1 = px.bar(state_perf.head(15),
                      x='Avg_Lead', y='State/Province',
                      orientation='h',
                      color='Avg_Lead',
                      color_continuous_scale=[
                          [0.0,'#2ecc71'],
                          [0.3,'#4fc3f7'],
                          [0.6,'#f39c12'],
                          [0.8,'#e67e22'],
                          [1.0,'#e74c3c']
                      ],
                      text='Avg_Lead',
                      labels={
                          'Avg_Lead'      :'Avg Lead Time (Days)',
                          'State/Province':'State'
                      })
        fig1.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
        fig1.update_yaxes(autorange='reversed')
        fig1.update_layout(
            height=480, coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, title='Avg Lead Time (days)'),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.caption("State Volume vs Lead Time (colour = delay %)")
        fig2 = px.scatter(
            state_perf,
            x='Shipments', y='Avg_Lead',
            color='Delay_Rate', size='Total_Sales',
            hover_name='State/Province',
            color_continuous_scale='RdYlGn_r',
            labels={
                'Shipments' :'Shipments',
                'Avg_Lead'  :'Avg Lead Time (Days)',
                'Delay_Rate':'Delay %'
            },
            color_continuous_midpoint=50
        )
        fig2.update_layout(
            height=480,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, title='Shipments'),
            yaxis=dict(showgrid=False, title='Avg Lead Time (Days)'),
            coloraxis_colorbar=dict(
            title=dict(
                text='Delay %',
                font=dict(color='white')
            ),
            tickfont=dict(color='white')
        )
            )
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    display_state = state_perf.rename(columns={
        'State/Province':'State','Avg_Lead':'Avg Lead Time (days)',
        'Min_Lead':'Min Lead','Max_Lead':'Max Lead',
        'Delay_Rate':'Delay Rate (%)','Total_Sales':'Total Sales ($)'
    })
    st.dataframe(display_state.reset_index(drop=True),
                 use_container_width=True, height=300)

with tab2:
    st.markdown("#### Order Timeline")

    route_data['Month'] = route_data['Order Date'].dt.to_period('M').astype(str)
    monthly = route_data.groupby('Month').agg(
        Shipments  = ('Lead_Time','count'),
        Avg_Lead   = ('Lead_Time','mean'),
        Delay_Rate = ('Is_Delayed','mean'),
        Total_Sales= ('Sales','sum')
    ).reset_index()
    monthly['Avg_Lead']   = monthly['Avg_Lead'].round(1)
    monthly['Delay_Rate'] = (monthly['Delay_Rate'] * 100).round(1)
    monthly = monthly.sort_values('Month')

    # Monthly volume + lead time
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=monthly['Month'], y=monthly['Shipments'],
        name='Shipments', marker_color='#4fc3f7', opacity=0.8,
        yaxis='y1'
    ))
    fig3.add_trace(go.Scatter(
        x=monthly['Month'], y=monthly['Avg_Lead'],
        name='Avg Lead Time', mode='lines+markers',
        line=dict(color='#f39c12', width=2.5),
        marker=dict(size=6), yaxis='y2'
    ))
    fig3.update_layout(
        title=f'Monthly Volume & Lead Time — {selected_route}',
        height=360,
        yaxis=dict(showgrid=False, title='Shipments'),
        yaxis2=dict(overlaying='y', side='right',
                    showgrid=False, title='Avg Lead Time (Days)'),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickangle=45),
        legend=dict(orientation='h', x=0, y=1.1)
    )
    st.plotly_chart(fig3, use_container_width=True)

    # Order records
    st.markdown("---")
    st.markdown("**Individual Order Records**")
    st.caption(f"All {len(route_data):,} orders for {selected_route}")

    order_cols = ['Order ID','Order Date','Ship Date','Ship Mode',
                  'State/Province','Lead_Time','Is_Delayed','Sales','Gross Profit']
    display_orders = route_data[order_cols].copy()
    display_orders['Is_Delayed'] = display_orders['Is_Delayed'].map(
        {True:'⚠️ Delayed', False:'✅ On-Time'}
    )
    display_orders = display_orders.rename(columns={
        'State/Province':'State', 'Lead_Time':'Lead Time (days)',
        'Is_Delayed':'Status', 'Sales':'Sales ($)', 'Gross Profit':'Profit ($)'
    })
    st.dataframe(display_orders.reset_index(drop=True),
                 use_container_width=True, height=380)

with tab3:
    st.markdown("#### KPI Trends")

    col3, col4 = st.columns(2)

    with col3:
        fig4 = px.line(monthly, x='Month', y='Delay_Rate',
                       title='Monthly Delay Rate (%)',
                       markers=True,
                       labels={'Delay_Rate':'Delay Rate (%)','Month':'Month'},
                       color_discrete_sequence=['#e74c3c'])
        fig4.update_traces(line_width=2.5, marker_size=7)
        fig4.update_layout(
            height=320,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, tickangle=45),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        mode_rt = route_data.groupby('Ship Mode').agg(
            Shipments = ('Lead_Time','count'),
            Avg_Lead  = ('Lead_Time','mean'),
            Delay     = ('Is_Delayed','mean')
        ).reset_index()
        mode_rt['Avg_Lead'] = mode_rt['Avg_Lead'].round(1)
        mode_rt['Delay']    = (mode_rt['Delay'] * 100).round(1)

        mode_colors = {
            'First Class':'#4fc3f7','Same Day':'#f39c12',
            'Second Class':'#e74c3c','Standard Class':'#2ecc71'
        }
        fig5 = px.bar(mode_rt.sort_values('Avg_Lead'),
                      x='Ship Mode', y='Avg_Lead',
                      color='Ship Mode',
                      color_discrete_map=mode_colors,
                      text='Avg_Lead',
                      title='Avg Lead Time by Ship Mode — This Route',
                      labels={'Avg_Lead':'Avg Lead Time (Days)'})
        fig5.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
        fig5.update_layout(
            showlegend=False, height=320,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig5, use_container_width=True)

    fig6 = px.bar(monthly, x='Month', y='Total_Sales',
                  title='Monthly Revenue — This Route ($)',
                  color_discrete_sequence=['#2ecc71'],
                  labels={'Total_Sales':'Revenue ($)','Month':'Month'})
    fig6.update_layout(
        height=300,
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, tickangle=45),
        yaxis=dict(showgrid=False)
    )
    st.plotly_chart(fig6, use_container_width=True)