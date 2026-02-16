import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Pagina instellingen
st.set_page_config(layout="wide", page_title="Elektra Monitor Rotterdam")

# 2. De "Agressieve" CSS voor 100% witte tekst overal
st.markdown("""
    <style>
    /* Achtergrond */
    .stApp { background-color: #0e1117 !important; }
    
    /* BASIS: Alles naar wit */
    html, body, [data-testid="stAppViewContainer"] {
        color: white !important;
    }

    /* SPECIFIEK VOOR RADIO BUTTONS (Dag, Week, Maand, Jaar) */
    div[data-testid="stRadio"] label p {
        color: white !important;
        font-size: 16px !important;
    }
    
    /* De tekst naast de rondjes */
    div[data-testid="stMarkdownContainer"] p {
        color: white !important;
    }

    /* Forceer wit op alle koppen en labels */
    h1, h2, h3, .stMarkdown, p, span, label {
        color: white !important;
    }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1a1c24 !important;
        border-right: 1px solid #3e4452;
    }

    /* Metric containers bovenin */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #1a1c24;
        border: 1px solid #3e4452;
        padding: 15px;
        border-radius: 12px;
        flex: 1;
        text-align: center;
    }
    .m-label { color: #bbbbbb; font-size: 14px; text-transform: uppercase; }
    .m-value { color: #ffffff; font-size: 28px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. Data genereren (RTM-001 t/m RTM-200)
@st.cache_data
def get_data():
    ids = [f"RTM-{i:03d}" for i in range(1, 201)]
    df_locs = pd.DataFrame({
        'Aansluiting_ID': ids,
        'lat': np.random.uniform(51.88, 51.95, 200),
        'lon': np.random.uniform(4.42, 4.52, 200)
    })
    date_rng = pd.date_range(start='2020-01-01', end='2026-12-31', freq='D')
    all_data = []
    # Simulatie voor demo
    for id in ids[:50]:
        temp_df = pd.DataFrame({
            'Timestamp': date_rng,
            'Watt': np.random.randint(200, 1500, size=len(date_rng)),
            'Aansluiting_ID': id
        })
        all_data.append(temp_df)
    return df_locs, pd.concat(all_data)

df_locaties, df_verbruik_totaal = get_data()

# 4. SIDEBAR
st.sidebar.markdown("<h2 style='color: white;'>FILTERS</h2>", unsafe_allow_html=True)
selected_year = st.sidebar.selectbox("Jaar:", [2020, 2021, 2022, 2023, 2024, 2025, 2026], index=6)
selected_id = st.sidebar.selectbox("Aansluitpunt:", df_locaties['Aansluiting_ID'])

# 5. DATA FILTERING
filtered_df = df_verbruik_totaal[
    (df_verbruik_totaal['Aansluiting_ID'] == selected_id) & 
    (df_verbruik_totaal['Timestamp'].dt.year == int(selected_year))
]

# 6. TITEL & METRICS
st.markdown(f"<h1 style='color: white;'>⚡ Monitor: {selected_id} ({selected_year})</h1>", unsafe_allow_html=True)

if not filtered_df.empty:
    huidig_verbruik = filtered_df['Watt'].iloc[-1]
    gem_verbruik = int(filtered_df['Watt'].mean())
    totaal_jaar = round(filtered_df['Watt'].sum() / 1000, 1)

    st.markdown(f"""
        <div class="metric-container">
            <div class="metric-box"><div class="m-label">Laatste Meting</div><div class="m-value">{huidig_verbruik} Watt</div></div>
            <div class="metric-box"><div class="m-label">Gemiddelde</div><div class="m-value">{gem_verbruik} Watt</div></div>
            <div class="metric-box"><div class="m-label">Totaal Jaar</div><div class="m-value">{totaal_jaar} kWh</div></div>
        </div>
        """, unsafe_allow_html=True)

    # 7. HOOFD LAYOUT
    col_map, col_chart = st.columns([1, 1])

    with col_map:
        st.markdown("<h3 style='color: white;'>Locatie op Kaart</h3>", unsafe_allow_html=True)
        df_locaties['color'] = df_locaties['Aansluiting_ID'].apply(lambda x: 'Selected' if x == selected_id else 'Other')
        fig_map = px.scatter_mapbox(df_locaties, lat="lat", lon="lon", 
                                    color='color', color_discrete_map={'Selected': '#FF4B4B', 'Other': '#00d4ff'},
                                    zoom=11, mapbox_style="open-street-map", hover_name='Aansluiting_ID')
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_map, use_container_width=True)

    with col_chart:
        st.markdown("<h3 style='color: white;'>Verbruiksanalyse</h3>", unsafe_allow_html=True)
        
        # De weergave knoppen
        period = st.radio("Kies periode:", ["Dag", "Week", "Maand", "Jaar"], horizontal=True, label_visibility="collapsed")
        
        plot_df = filtered_df.set_index('Timestamp')
        if period == "Week":
            plot_df = plot_df.resample('W').mean().reset_index()
        elif period == "Maand" or period == "Jaar":
            plot_df = plot_df.resample('M').mean().reset_index()
        else:
            plot_df = plot_df.reset_index()

        fig_line = px.area(plot_df, x='Timestamp', y='Watt', template="plotly_dark")
        fig_line.update_traces(line_color='#00d4ff', fillcolor='rgba(0, 212, 255, 0.1)')
        fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.info(f"Geen data beschikbaar voor {selected_id} in {selected_year}.")
