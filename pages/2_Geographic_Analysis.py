import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils import load_data, add_sidebar_filters

st.set_page_config(page_title="Geographic Analysis", page_icon="🌍", layout="wide")

df = load_data()
df = add_sidebar_filters(df)

if len(df) == 0:
    st.warning("No data. Adjust filters.")
    st.stop()

us_states = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
    'Colorado':'CO','Connecticut':'CT','Delaware':'DE','Florida':'FL','Georgia':'GA',
    'Hawaii':'HI','Idaho':'ID','Illinois':'IL','Indiana':'IN','Iowa':'IA','Kansas':'KS',
    'Kentucky':'KY','Louisiana':'LA','Maine':'ME','Maryland':'MD','Massachusetts':'MA',
    'Michigan':'MI','Minnesota':'MN','Mississippi':'MS','Missouri':'MO','Montana':'MT',
    'Nebraska':'NE','Nevada':'NV','New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM',
    'New York':'NY','North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK',
    'Oregon':'OR','Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC',
    'South Dakota':'SD','Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT',
    'Virginia':'VA','Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'
}

def normalize(s):
    if s.max() == s.min():
        return s * 0
    return (s - s.min()) / (s.max() - s.min())

# State summary
state_df = df.groupby('State/Province').agg(
    Shipments     = ('Lead_Time','count'),
    Avg_Lead_Time = ('Lead_Time','mean'),
    Delay_Rate    = ('Is_Delayed','mean'),
    Total_Sales   = ('Sales','sum')
).reset_index()
state_df['Avg_Lead_Time'] = state_df['Avg_Lead_Time'].round(1)
state_df['Delay_Rate']    = (state_df['Delay_Rate'] * 100).round(1)
state_df['Risk_Score']    = (
    normalize(state_df['Avg_Lead_Time']) * 0.5 +
    normalize(state_df['Shipments'])     * 0.5
) * 100
state_df['Risk_Score']   = state_df['Risk_Score'].round(1)
state_df['State_Code']   = state_df['State/Province'].map(us_states)
state_df_sorted          = state_df.sort_values('Risk_Score', ascending=False)

# ── Header ────────────────────────────────────────────────────
st.markdown("## Geographic Shipping Analysis")

c1, c2, c3, c4 = st.columns(4)

def kpi(col, label, value, color="#4fc3f7"):
    col.markdown(f"""
    <div>
        <div style='font-size:0.68rem;color:rgba(255,255,255,0.45);
                    text-transform:uppercase;letter-spacing:1px;'>{label}</div>
        <div style='font-size:1.5rem;font-weight:700;color:{color};'>{value}</div>
    </div>""", unsafe_allow_html=True)

highest_risk = state_df_sorted.iloc[0]['State/Province']
peak_lead    = state_df['Avg_Lead_Time'].max()

kpi(c1, "States Analyzed",   str(df['State/Province'].nunique()))
kpi(c2, "Highest Risk State", highest_risk)
kpi(c3, "Peak Avg Lead Time", f"{peak_lead:.0f} days")
kpi(c4, "Total Shipments",    f"{len(df):,}")

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["US Shipping Map", "Bottleneck Analysis", "State Rankings"])

with tab1:
    st.markdown("#### US Shipping Efficiency Heatmap")
    st.caption("Average lead time by state")

    fig1 = px.choropleth(
        state_df.dropna(subset=['State_Code']),
        locations='State_Code',
        locationmode='USA-states',
        color='Avg_Lead_Time',
        hover_name='State/Province',
        hover_data={
            'Shipments'    : True,
            'Avg_Lead_Time': True,
            'Delay_Rate'   : True
        },
        color_continuous_scale=[
            [0.0, '#00bcd4'],
            [0.3, '#4fc3f7'],
            [0.6, '#f39c12'],
            [0.8, '#e67e22'],
            [1.0, '#e74c3c']
        ],
        scope='usa',
        labels={'Avg_Lead_Time':'Lead Time (days)'}
    )
    fig1.update_layout(
        height=520,
        paper_bgcolor='rgba(0,0,0,0)',
        geo=dict(
            bgcolor='rgba(0,0,0,0)',
            landcolor='rgba(30,50,80,0.4)',
            subunitcolor='rgba(255,255,255,0.2)',
            showlakes=False
        ),
        coloraxis_colorbar=dict(
            title='Lead Time<br>(days)',
            tickfont=dict(color='white'),
            titlefont=dict(color='white')
        )
    )
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.markdown("#### Bottleneck Analysis")
    st.caption("States with high volume AND high lead time are the biggest bottlenecks")

    col1, col2 = st.columns(2)

    with col1:
        top15_risk = state_df_sorted.head(15)
        fig2 = px.bar(top15_risk,
                      x='Risk_Score', y='State/Province',
                      orientation='h',
                      color='Risk_Score',
                      color_continuous_scale=[
                          [0,'#f39c12'],[0.5,'#e67e22'],[1,'#e74c3c']
                      ],
                      text='Risk_Score',
                      title='Top 15 High-Risk States',
                      labels={'Risk_Score':'Risk Score','State/Province':'State'})
        fig2.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        fig2.update_yaxes(autorange='reversed')
        fig2.update_layout(
            height=480, coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.scatter(
            state_df,
            x='Shipments', y='Avg_Lead_Time',
            color='Risk_Score', size='Shipments',
            hover_name='State/Province',
            color_continuous_scale='RdYlGn_r',
            title='Volume vs Lead Time — Bottleneck Quadrant',
            labels={
                'Shipments'    :'Shipment Volume',
                'Avg_Lead_Time':'Avg Lead Time (Days)'
            }
        )
        med_vol  = state_df['Shipments'].median()
        med_lead = state_df['Avg_Lead_Time'].median()
        fig3.add_vline(x=med_vol,  line_dash='dash',
                       line_color='rgba(255,255,255,0.3)')
        fig3.add_hline(y=med_lead, line_dash='dash',
                       line_color='rgba(255,255,255,0.3)')
        fig3.update_layout(
            height=480,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False), yaxis=dict(showgrid=False)
        )
        st.plotly_chart(fig3, use_container_width=True)

    # Regional comparison
    st.markdown("#### Regional Performance")
    region_df = df.groupby('Region').agg(
        Shipments     = ('Lead_Time','count'),
        Avg_Lead_Time = ('Lead_Time','mean'),
        Delay_Rate    = ('Is_Delayed','mean')
    ).reset_index()
    region_df['Avg_Lead_Time'] = region_df['Avg_Lead_Time'].round(1)
    region_df['Delay_Rate']    = (region_df['Delay_Rate'] * 100).round(1)

    col3, col4 = st.columns(2)
    with col3:
        fig4 = px.bar(region_df.sort_values('Avg_Lead_Time'),
                      x='Region', y='Avg_Lead_Time',
                      color='Region', text='Avg_Lead_Time',
                      title='Avg Lead Time by Region (Days)',
                      labels={'Avg_Lead_Time':'Avg Lead Time (Days)'})
        fig4.update_traces(texttemplate='%{text:.0f}d', textposition='outside')
        fig4.update_layout(showlegend=False,
                           plot_bgcolor='rgba(0,0,0,0)',
                           paper_bgcolor='rgba(0,0,0,0)',
                           xaxis=dict(showgrid=False),
                           yaxis=dict(showgrid=False))
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        fig5 = px.bar(region_df.sort_values('Delay_Rate', ascending=False),
                      x='Region', y='Delay_Rate',
                      color='Delay_Rate', text='Delay_Rate',
                      color_continuous_scale='YlOrRd',
                      title='Delay Rate by Region (%)',
                      labels={'Delay_Rate':'Delay Rate (%)'})
        fig5.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig5.update_layout(coloraxis_showscale=False,
                           plot_bgcolor='rgba(0,0,0,0)',
                           paper_bgcolor='rgba(0,0,0,0)',
                           xaxis=dict(showgrid=False),
                           yaxis=dict(showgrid=False))
        st.plotly_chart(fig5, use_container_width=True)

with tab3:
    st.markdown("#### State Rankings")
    st.caption("All states ranked by bottleneck risk score")

    display_state = state_df_sorted[[
        'State/Province','Shipments','Avg_Lead_Time','Delay_Rate','Risk_Score'
    ]].copy()
    display_state.index = range(1, len(display_state)+1)
    display_state.columns = [
        'State','Shipments','Avg Lead Time (days)','Delay Rate (%)','Risk Score'
    ]
    st.dataframe(display_state, use_container_width=True, height=520)