import streamlit as st
import pandas as pd


@st.cache_data(ttl=0)
def load_data():
    df = pd.read_csv("data/dataset.csv")
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d-%m-%Y')
    df['Ship Date']  = pd.to_datetime(df['Ship Date'],  format='%d-%m-%Y')
    df['Lead_Time']  = (df['Ship Date'] - df['Order Date']).dt.days
    df['Profit_Margin'] = (df['Gross Profit'] / df['Sales'] * 100).round(2)

    factory_map = {
        'Wonka Bar - Nutty Crunch Surprise' : "Lot's O' Nuts",
        'Wonka Bar - Fudge Mallows'         : "Lot's O' Nuts",
        'Wonka Bar -Scrumdiddlyumptious'    : "Lot's O' Nuts",
        'Wonka Bar - Milk Chocolate'        : "Wicked Choccy's",
        'Wonka Bar - Triple Dazzle Caramel' : "Wicked Choccy's",
        'Laffy Taffy'                       : 'Sugar Shack',
        'SweeTARTS'                         : 'Sugar Shack',
        'Nerds'                             : 'Sugar Shack',
        'Fun Dip'                           : 'Sugar Shack',
        'Fizzy Lifting Drinks'              : 'Sugar Shack',
        'Everlasting Gobstopper'            : 'Secret Factory',
        'Lickable Wallpaper'                : 'Secret Factory',
        'Wonka Gum'                         : 'Secret Factory',
        'Hair Toffee'                       : 'The Other Factory',
        'Kazookles'                         : 'The Other Factory',
    }
    df['Factory'] = df['Product Name'].map(factory_map).fillna('Unknown')
    df['Route']   = df['Division'] + ' → ' + df['State/Province']

    threshold        = df['Lead_Time'].median() + 0.5 * df['Lead_Time'].std()
    df['Is_Delayed'] = df['Lead_Time'] > threshold
    df['Threshold']  = threshold
    return df


def add_sidebar_filters(df):

    st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background: #0f1923 !important;
    }
    section[data-testid="stSidebar"] * { color: white !important; }
    .sidebar-title { font-size:1.3rem; font-weight:700; color:white !important; }
    .sidebar-subtitle { font-size:0.75rem; color:rgba(255,255,255,0.5) !important; margin-top:2px; }
    .nav-label { font-size:0.7rem; font-weight:700; letter-spacing:1.5px;
                 text-transform:uppercase; color:rgba(255,255,255,0.4) !important;
                 margin:16px 0 6px 0; }
    .filter-label { font-size:0.7rem; font-weight:700; letter-spacing:1.5px;
                    text-transform:uppercase; color:rgba(255,255,255,0.4) !important;
                    margin:10px 0 4px 0; }
    .sidebar-divider { border:none; border-top:1px solid rgba(255,255,255,0.1);
                       margin:12px 0; }
    .project-box { background:rgba(255,255,255,0.05); border-radius:8px;
                   padding:12px; margin-top:8px; }
    section[data-testid="stSidebar"] .stMultiSelect span[data-baseweb="tag"] {
        background-color: #e74c3c !important; border-radius:4px; }
    section[data-testid="stSidebar"] .stSelectbox > div { background:rgba(255,255,255,0.07) !important; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.sidebar.markdown("""
    <div style='padding:20px 0 8px 0;'>
        <div class='sidebar-title'>Nassau Logistics</div>
        <div class='sidebar-subtitle'>Shipping Intelligence Platform</div>
    </div>
    <hr class='sidebar-divider'>
    """, unsafe_allow_html=True)

   
    

    # Date Range
    st.sidebar.markdown("<div class='filter-label'>Date Range</div>", unsafe_allow_html=True)
    min_date = df['Order Date'].min().date()
    max_date = df['Order Date'].max().date()
    date_range = st.sidebar.date_input(
        "Date Range", value=(min_date, max_date),
        min_value=min_date, max_value=max_date,
        label_visibility="collapsed"
    )

    # Region
    st.sidebar.markdown("<div class='filter-label'>Region</div>", unsafe_allow_html=True)
    all_regions = sorted(df['Region'].unique().tolist())
    selected_regions = st.sidebar.multiselect(
        "Region", options=all_regions,
        default=st.session_state.get('regions', all_regions),
        label_visibility="collapsed"
    )

    # State
    st.sidebar.markdown("<div class='filter-label'>State / Province</div>", unsafe_allow_html=True)
    all_states = ["All States"] + sorted(df['State/Province'].unique().tolist())
    selected_state = st.sidebar.selectbox(
        "State", options=all_states, index=0,
        label_visibility="collapsed"
    )

    # Ship Mode
    st.sidebar.markdown("<div class='filter-label'>Ship Mode</div>", unsafe_allow_html=True)
    all_modes = sorted(df['Ship Mode'].unique().tolist())
    selected_modes = st.sidebar.multiselect(
        "Ship Mode", options=all_modes,
        default=st.session_state.get('modes', all_modes),
        label_visibility="collapsed"
    )

    # Lead Time
    st.sidebar.markdown("<div class='filter-label'>Lead-Time Threshold (Days)</div>", unsafe_allow_html=True)
    min_lt = int(df['Lead_Time'].min())
    max_lt = int(df['Lead_Time'].max())
    lt_range = st.sidebar.slider(
        "Lead Time", min_value=min_lt, max_value=max_lt,
        value=(min_lt, max_lt), label_visibility="collapsed"
    )

    st.session_state['regions'] = selected_regions
    st.session_state['modes']   = selected_modes

    filtered = df.copy()
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        filtered = filtered[
            (filtered['Order Date'].dt.date >= date_range[0]) &
            (filtered['Order Date'].dt.date <= date_range[1])
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

    # Project info
    st.sidebar.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="project-box">'
        '<p style="font-size:0.65rem;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;'
        'color:rgba(255,255,255,0.4);margin-bottom:10px;">PROJECT INFO</p>'
        '<p style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin:0;">ORGANIZATION</p>'
        '<p style="font-size:0.82rem;font-weight:700;color:white;margin-bottom:8px;">Unified Mentor ↗</p>'
        '<p style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin:0;">INSTRUCTOR</p>'
        '<p style="font-size:0.82rem;font-weight:700;color:white;margin-bottom:8px;">Saiprasad Kagne ↗</p>'
        '<p style="font-size:0.65rem;color:rgba(255,255,255,0.4);text-transform:uppercase;margin:0;">ANALYST</p>'
        '<p style="font-size:0.82rem;font-weight:700;color:white;margin-bottom:4px;">Mohammad Akbar ↗</p>'
        '</div>',
        unsafe_allow_html=True
    )
    st.sidebar.markdown("""
    <div style='padding:16px 0 12px 0; text-align:center;'>
        <a href='https://www.nassaucandy.com' target='_blank'>
            <img src='https://www.nassaucandy.com/media/logo/default/logo.png'
                 style='width:80%;max-width:160px;
                        filter:brightness(0) invert(1);
                        cursor:pointer;'
                 title='Visit Nassau Candy website'>
        </a>
    </div>
    <hr class='sidebar-divider'>
    """, unsafe_allow_html=True)

    return filtered


def build_route_df(df):
    def normalize(s):
        if s.max() == s.min():
            return pd.Series([0.5]*len(s), index=s.index)
        return (s - s.min()) / (s.max() - s.min())

    rdf = df.groupby('Route').agg(
        Division        = ('Division',    'first'),
        Factory         = ('Factory',     'first'),
        Total_Shipments = ('Lead_Time',   'count'),
        Avg_Lead_Time   = ('Lead_Time',   'mean'),
        Min_Lead_Time   = ('Lead_Time',   'min'),
        Max_Lead_Time   = ('Lead_Time',   'max'),
        Std_Dev         = ('Lead_Time',   'std'),
        Total_Sales     = ('Sales',       'sum'),
        Total_Profit    = ('Gross Profit','sum'),
        Delay_Rate      = ('Is_Delayed',  'mean'),
    ).reset_index()

    rdf['Avg_Lead_Time'] = rdf['Avg_Lead_Time'].round(1)
    rdf['Std_Dev']       = rdf['Std_Dev'].round(1).fillna(0)
    rdf['Total_Sales']   = rdf['Total_Sales'].round(2)
    rdf['Delay_Rate']    = (rdf['Delay_Rate'] * 100).round(1)

    rdf['Avg_Efficiency'] = (
        (1 - normalize(rdf['Avg_Lead_Time'])) * 0.5 +
        normalize(rdf['Total_Shipments'])      * 0.3 +
        (1 - normalize(rdf['Delay_Rate']))     * 0.2
    ).round(3)

    return rdf.sort_values('Avg_Lead_Time').reset_index(drop=True)