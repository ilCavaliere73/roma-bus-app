import streamlit as st
import sqlite3
import folium
from streamlit_folium import st_folium
import requests

# Nel file app.py su GitHub
st.set_page_config(page_title="Roma Mobility Dispatcher", page_icon="📡", layout="wide")
st.title("📡 Roma Mobility Dispatcher")
st.markdown("---") # Una linea elegante per separare il titolo

# Inizializza i preferiti nella sessione del browser
if 'preferiti' not in st.session_state:
    st.session_state.preferiti = []

def get_tempi_reali(palina_id):
    import json
    # URL originale che vogliamo raggiungere
    target_url = f"https://muoversiaroma.it/api/v1/stops/{palina_id}/arrivals"
    
    # Proxy per superare il blocco CORS/DataCenter
    proxy_url = f"https://api.allorigins.win/get?url={requests.utils.quote(target_url)}"
    
    # Headers che inviamo al proxy (che a sua volta li userà o li maschererà)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(proxy_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # AllOrigins incapsula la risposta originale in una stringa chiamata 'contents'
            raw_content = response.json().get('contents')
            
            if not raw_content:
                return [{"line": "!", "direction": "Dati non disponibili dal proxy", "wait": "Riprova"}]
                
            dati = json.loads(raw_content)
            arrivals = dati.get('arrivals', []) or dati.get('results', [])
            
            if not arrivals:
                return [{"line": "Info", "direction": "Nessun bus in arrivo", "wait": "-"}]
            
            return [
                {
                    "line": a.get('line', '?'),
                    "direction": a.get('destination', 'Ignota'),
                    "wait": f"{a.get('time', '0')} min"
                } for a in arrivals
            ]
        else:
            return [{"line": "Err", "direction": f"Proxy Error {response.status_code}", "wait": "X"}]
            
    except Exception as e:
        # Se anche il proxy fallisce, mostriamo un pulsante di emergenza
        st.error("Il sistema centrale di Roma non risponde.")
        st.link_button("Apri Orari Ufficiali (Muoversi a Roma)", 
                       f"https://muoversiaroma.it/it/paline/percorso-linea?id_palina={palina_id}")
        return [{"line": "Link", "direction": "Usa il tasto sopra", "wait": "↗️"}]
        
def cerca_fermata(testo):
    conn = sqlite3.connect('trasporti_roma.db')
    cursor = conn.cursor()
    query = "SELECT palina_id, nome, lat, lon FROM fermate WHERE palina_id = ? OR nome LIKE ? LIMIT 5"
    cursor.execute(query, (testo, f'%{testo}%'))
    res = cursor.fetchall()
    conn.close()
    return res

st.title("🚌 Roma Radar: Dashboard Trasporti")

# --- SIDEBAR PER I PREFERITI ---
with st.sidebar:
    st.header("⭐ I Miei Preferiti")
    if not st.session_state.preferiti:
        st.write("Non hai ancora salvato fermate.")
    else:
        for pref in st.session_state.preferiti:
            if st.button(f"📍 {pref['nome']}", key=f"pref_{pref['id']}"):
                st.session_state.search_query = str(pref['id'])

# --- CORPO PRINCIPALE ---
col1, col2 = st.columns([1, 1])

with col1:
    query_input = st.text_input("Cerca fermata (Nome o Codice):", key="search_input", value=st.session_state.get('search_query', ''))

    if query_input:
        risultati = cerca_fermata(query_input)
        for r in risultati:
            with st.expander(f"📍 {r[1]} ({r[0]})", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"Mostra Arrivi", key=f"t_{r[0]}"):
                        arrivi = get_tempi_reali(r[0])
                        for a in arrivi:
                            st.info(f"**{a['line']}** → {a['direction']}: **{a['wait']}**")
                with col_b:
                    if st.button("⭐ Salva", key=f"s_{r[0]}"):
                        if r[0] not in [p['id'] for p in st.session_state.preferiti]:
                            st.session_state.preferiti.append({'id': r[0], 'nome': r[1]})
                            st.toast("Salvato nei preferiti!")

with col2:
    center = [41.896, 12.482]
    m = folium.Map(location=center, zoom_start=15)
    st_folium(m, width=500, height=450, key="map")
