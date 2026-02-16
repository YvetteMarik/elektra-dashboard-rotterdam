import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO

# 1. Pagina instellingen (MOET als eerste regel na de imports)
st.set_page_config(layout="wide", page_title="Elektra Monitor Rotterdam")

# 2. De "Master" CSS (Met dubbele ringen en kleuren)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    
    html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, span, label {
        color: white !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #1a1c24 !important;
        border-right: 1px solid #3e4452;
    }

    /* Basis styling voor de cirkels */
    .metric-container {
        display: flex;
        justify-content: space-around;
        gap: 15px;
        margin: 40px 0;
    }
    
    .metric-circle {
        position: relative;
        width: 190px;
        height: 190px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;
        background-color: rgba(26, 28, 36, 0.8);
        z-index: 1;
    }

    /* De binnenste lichtgrijs/zwarte ring */
    .metric-circle::after {
        content: "";
        position: absolute;
        top: 8px;
        left: 8px;
        right: 8px;
        bottom: 8px;
        border-radius: 50%;
        border: 2px solid rgba(150, 150, 150, 0.2); 
        z-index: -1;
    }

    /* Buitenste gekleurde ringen */
    .blue-ring { border: 6px solid #00d4ff; box-shadow: 0 0 15px rgba(0, 212, 255, 0.3); }
    .green-ring { border: 6px solid #2ecc71; box-shadow: 0 0 15px rgba(46, 204, 113, 0.3); }
    .orange-ring { border: 6px solid #e67e22; box-shadow: 0 0 15px rgba(230, 126, 34, 0.3); }

    .m-label { 
        color: #bbbbbb !important; 
        font-size: 11px; 
        text-transform: uppercase; 
        margin-bottom: 5px;
        letter-spacing: 1px;
    }
    .m-value { 
        color: #ffffff !important; 
        font-size: 24px; 
        font-weight: bold !important;
    }

    .stDownloadButton button {
        background-color: #1a1c24 !important;
        color: white !important;
        border: 1px solid #00d4ff !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Data genereren (Gecorrigeerd voor stabiliteit)
@st.cache_data
def load_data():
    ids = [f"RTM-{i:03d}" for i in range(1, 201)]
    df_locs = pd.DataFrame({
        'Aansluiting_ID': ids,
        'lat': np.random.uniform(51.88, 51.95, 200),
        'lon': np.random.uniform(4.42, 4.52, 200)
    })
    
    date_rng = pd.date_range(start='2020-01-01', end='2026-12-31', freq='D')
    # Simulatie data voor de actieve selectie
    return df_locs, date_rng

df_locaties, date_range = load_data()

# 4. SIDEBAR
logo_url = "https://upload.wikimedia.org/wikipedia/commons/5/53/Gemeente_Rotterdam.svg"
st.sidebar.markdown(f'<div style="text-align: center; padding: 10px;"><img src="{logo_url}" width="160"></div><hr style="border: 0.5px solid #3e4452;">', unsafe_allow_html=True)

st.sidebar.subheader("INSTELLINGEN")
selected_year = st.sidebar.selectbox("Selecteer Jaar:", [2020, 2021, 2022, 2023, 2024, 2025, 2026], index=6)
selected_id = st.sidebar.selectbox("Selecteer Aansluitpunt:", df_locaties['Aansluiting_ID'])

# 5. DATA FILTERING (Simulatie per gekozen punt)
np.random.seed(int(selected_id.split('-')[1]) + selected_year)
filtered_df = pd.DataFrame({
    'Timestamp': date_range[date_range.year == selected_year],
    'Watt': np.random.randint(200, 1500, size=len(date_range[date_range.year == selected_year]))
})

# 6. HEADER & CIRKELS
st.markdown(f"<h1>⚡ Monitor: {selected_id} ({selected_year})</h1>", unsafe_allow_html=True)

huidig_verbruik = filtered_df['Watt'].iloc[-1]
gem_verbruik = int(filtered_df['Watt'].mean())
totaal_jaar = round(filtered_df['Watt'].sum() / 1000, 1)

st.markdown(f"""
    <div class="metric-container">
        <div class="metric-circle blue-ring">
            <div class="m-label">Laatste Meting</div>
            <div class="m-value">{huidig_verbruik} W</div>
        </div>
        <div class="metric-circle green-ring">
            <div class="m-label">Gemiddelde</div>
            <div class="m-value">{gem_verbruik} W</div>
        </div>
        <div class="metric-circle orange-ring">
            <div class="m-label">Totaal Jaar</div>
            <div class="m-value">{totaal_jaar} kWh</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 7. LAYOUT: KAART & GRAFIEK
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Locatie overzicht")
    df_locaties['color'] = df_locaties['Aansluiting_ID'].apply(lambda x: 'Geselecteerd' if x == selected_id else 'Overig')
    fig_map = px.scatter_mapbox(df_locaties, lat="lat", lon="lon", 
                                color='color', color_discrete_map={'Geselecteerd': '#FF4B4B', 'Overig': '#00d4ff'},
                                zoom=11, mapbox_style="open-street-map", hover_name='Aansluiting_ID')
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig_map, use_container_width=True)

with col_right:
    st.subheader("Verbruiksanalyse")
    period = st.radio("Kies weergave:", ["Dag", "Week", "Maand"], horizontal=True, label_visibility="collapsed")
    
    plot_df = filtered_df.set_index('Timestamp')
    if period == "Week": plot_df = plot_df.resample('W').mean().reset_index()
    elif period == "Maand": plot_df = plot_df.resample('M').mean().reset_index()
    else: plot_df = plot_df.reset_index()

    fig_line = px.area(plot_df, x='Timestamp', y='Watt', template="plotly_dark")
    fig_line.update_traces(line_color='#00d4ff', fillcolor='rgba(0, 212, 255, 0.1)')
    fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
    st.plotly_chart(fig_line, use_container_width=True)

    towrite = BytesIO()
    filtered_df.to_excel(towrite, index=False, engine='openpyxl')
    st.download_button(label="📥 Download Jaardata (Excel)", data=towrite.getvalue(), 
                       file_name=f"Verbruik_{selected_id}_{selected_year}.xlsx", mime="application/vnd.ms-excel")