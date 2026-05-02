import streamlit as st
import pandas as pd

# ── NOTE: No self-imports here. This file IS utils.py.
#    The line  `from utils import ...`  must NEVER appear inside utils.py itself.


@st.cache_data
def load_data():
    df = pd.read_csv("data/dataset.csv")
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y')
    df['Ship Date']  = pd.to_datetime(df['Ship Date'],  format='%d-%m-%Y')
    df['Lead_Time']  = (df['Ship Date'] - df['Order Date']).dt.days
    df = df[df['Lead_Time'] >= 0]                                    # drop invalid
    df['Profit_Margin'] = (df['Gross Profit'] / df['Sales'] * 100).round(2)

    # Delay flag  (top-25 % lead times = delayed)
    threshold = df['Lead_Time'].quantile(0.75)
    df['Is_Delayed'] = (df['Lead_Time'] > threshold).astype(int)

    # Route column so pages can do df['Route'] directly
    df['Route'] = df['Division'] + ' → ' + df['State/Province']

    return df


def build_route_df(df):
    """Aggregate per Division→State route metrics used by Route Efficiency
    and Route Drill-Down pages."""
    if len(df) == 0:
        return pd.DataFrame(columns=[
            'Route', 'Division', 'State/Province',
            'Avg_Lead_Time', 'Total_Shipments', 'Total_Sales',
            'Delay_Rate', 'Avg_Efficiency',
        ])

    threshold = df['Lead_Time'].quantile(0.75)

    route = (
        df.groupby(['Division', 'State/Province'], as_index=False)
        .agg(
            Avg_Lead_Time = ('Lead_Time', 'mean'),
            Total_Shipments = ('Lead_Time', 'count'),   # renamed from Volume
            Total_Sales   = ('Sales',     'sum'),
            Delay_Rate    = ('Lead_Time', lambda x: (x > threshold).mean() * 100),
        )
    )
    route['Route'] = route['Division'] + ' → ' + route['State/Province']

    lt_min, lt_max = route['Avg_Lead_Time'].min(), route['Avg_Lead_Time'].max()
    lt_range = lt_max - lt_min + 1e-9
    route['lt_norm']       = 1 - (route['Avg_Lead_Time'] - lt_min) / lt_range
    route['Avg_Efficiency'] = (route['lt_norm'] * (1 - route['Delay_Rate'] / 100)).round(6)
    route = route.drop(columns=['lt_norm'])

    return route.sort_values('Avg_Lead_Time').reset_index(drop=True)


def add_sidebar_filters(df):

    # ── Sidebar CSS ──────────────────────────────────────────
    st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a2f4e 0%, #1e3a5f 60%, #22437a 100%);
    }
    section[data-testid="stSidebar"] * { color: white !important; }
    .sidebar-logo { text-align:center; padding:20px 10px 10px 10px; }
    .sidebar-logo p { color:rgba(255,255,255,0.7) !important; font-size:0.78rem; margin:4px 0 0 0; }
    .sidebar-divider { border:none; border-top:1px solid rgba(255,255,255,0.2); margin:12px 0; }
    .filter-label { color:rgba(255,255,255,0.6) !important; font-size:0.72rem; font-weight:600;
                    letter-spacing:1.5px; text-transform:uppercase; margin-bottom:4px; }
    section[data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {
        background-color:rgba(255,255,255,0.2) !important; border-radius:6px; }
    .sidebar-footer { text-align:center; padding:10px; color:rgba(255,255,255,0.4) !important; font-size:0.7rem; }
    </style>
    """, unsafe_allow_html=True)

    # ── Logo ─────────────────────────────────────────────────
    st.sidebar.markdown("""
    <div class='sidebar-logo'>
        <img src='https://www.nassaucandy.com/media/logo/default/logo.png'
             style='width:80%;max-width:180px;margin-bottom:8px;filter:brightness(0) invert(1);'>
        <p>Nassau Candy Distributor | 2024-2025</p>
    </div>
    <hr class='sidebar-divider'>
    """, unsafe_allow_html=True)

    # ── Filters ───────────────────────────────────────────────
    st.sidebar.markdown("<p class='filter-label'>Filters</p>", unsafe_allow_html=True)

    # Date Range
    st.sidebar.markdown("<p class='filter-label'>Date Range</p>", unsafe_allow_html=True)
    min_date = df['Order Date'].min().date()
    max_date = df['Order Date'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        label_visibility="collapsed"
    )

    # Region
    st.sidebar.markdown("<p class='filter-label'>Region</p>", unsafe_allow_html=True)
    all_regions = sorted(df['Region'].unique().tolist())
    selected_regions = st.sidebar.multiselect(
        "Region",
        options=all_regions,
        default=st.session_state.get('regions', all_regions),
        label_visibility="collapsed"
    )

    # State / Province
    st.sidebar.markdown("<p class='filter-label'>State / Province</p>", unsafe_allow_html=True)
    all_states = ["All States"] + sorted(df['State/Province'].unique().tolist())
    selected_state = st.sidebar.selectbox(
        "State",
        options=all_states,
        index=0,
        label_visibility="collapsed"
    )

    # Ship Mode
    st.sidebar.markdown("<p class='filter-label'>Ship Mode</p>", unsafe_allow_html=True)
    all_modes = sorted(df['Ship Mode'].unique().tolist())
    selected_modes = st.sidebar.multiselect(
        "Ship Mode",
        options=all_modes,
        default=st.session_state.get('modes', all_modes),
        label_visibility="collapsed"
    )

    # Lead-Time Threshold
    st.sidebar.markdown("<p class='filter-label'>Lead-Time Threshold (Days)</p>", unsafe_allow_html=True)
    min_lt = int(df['Lead_Time'].min())
    max_lt = int(df['Lead_Time'].max())
    lt_range = st.sidebar.slider(
        "Lead Time",
        min_value=min_lt,
        max_value=max_lt,
        value=(min_lt, max_lt),
        label_visibility="collapsed"
    )

    # Save to session state
    st.session_state['regions'] = selected_regions
    st.session_state['modes']   = selected_modes

    # ── Apply Filters ─────────────────────────────────────────
    filtered = df.copy()

    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            (filtered['Order Date'].dt.date >= start_date) &
            (filtered['Order Date'].dt.date <= end_date)
        ]

    if selected_regions:
        filtered = filtered[filtered['Region'].isin(selected_regions)]

    if selected_state != "All States":
        filtered = filtered[filtered['State/Province'] == selected_state]

    if selected_modes:
        filtered = filtered[filtered['Ship Mode'].isin(selected_modes)]

    filtered = filtered[
        (filtered['Lead_Time'] >= lt_range[0]) &
        (filtered['Lead_Time'] <= lt_range[1])
    ]

    # ── Project Info ──────────────────────────────────────────
    st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div style="background:rgba(255,255,255,0.07);border-radius:10px;padding:14px;margin-top:6px;">'

        '<p style="font-size:0.65rem;font-weight:700;letter-spacing:1.5px;'
        'text-transform:uppercase;color:rgba(255,255,255,0.5);margin-bottom:12px;">PROJECT INFO</p>'

        '<p style="font-size:0.65rem;color:rgba(255,255,255,0.4);'
        'text-transform:uppercase;margin:0;">ORGANIZATION</p>'
        '<p style="font-size:0.82rem;font-weight:700;margin-bottom:10px;">'
        '<a href="https://www.unifiedmentor.com" target="_blank" '
        'style="color:white;text-decoration:none;">'
        'Unified Mentor ↗</a></p>'

        '<p style="font-size:0.65rem;color:rgba(255,255,255,0.4);'
        'text-transform:uppercase;margin:0;">INSTRUCTOR</p>'
        '<p style="font-size:0.82rem;font-weight:700;margin-bottom:10px;">'
        '<a href="https://www.linkedin.com/in/saiprasad-kagne" target="_blank" '
        'style="color:white;text-decoration:none;">'
        'Saiprasad Kagne ↗</a></p>'

        '<p style="font-size:0.65rem;color:rgba(255,255,255,0.4);'
        'text-transform:uppercase;margin:0;">ANALYST</p>'
        '<p style="font-size:0.82rem;font-weight:700;margin-bottom:4px;">'
        '<a href="https://github.com/MohammadAkbar1" target="_blank" '
        'style="color:white;text-decoration:none;">'
        'Mohammad Akbar ↗</a></p>'

        '</div>',
        unsafe_allow_html=True
    )


    # ── Footer ────────────────────────────────────────────────
    st.sidebar.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="sidebar-footer">Nassau Candy Distributor<br>Logistics Analytics · 2024-2025</div>',
        unsafe_allow_html=True
    )

    return filtered
