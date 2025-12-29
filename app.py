import streamlit as st
import sqlite3
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Radar Roma", page_icon="🚌", layout="wide")

# Inizializza i preferiti nella sessione del browser
if 'preferiti' not in st.session_state:
    st.session_state.preferiti = []

def get_tempi_reali(palina_id):
    url = f"https://muoversiaroma.it/api/v1/stops/{palina_id}/arrivals"

    # Headers completi per sembrare un browser reale
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Referer': 'https://muoversiaroma.it/it/mappa',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        # Usiamo requests.Session per gestire i cookie (come un vero browser)
        with requests.Session() as s:
            response = s.get(url, headers=headers, timeout=7)

            if response.status_code == 200:
                dati = response.json()
                # Cerchiamo la lista degli arrivi nel JSON
                arrivi_raw = dati.get('arrivals', [])

                if not arrivi_raw:
                    return [{"line": "Oggi", "direction": "Nessuna corsa programmata", "wait": "-"}]

                risultati = []
                for b in arrivi_raw:
                    risultati.append({
                        "line": b.get('line', '?'),
                        "direction": b.get('destination', 'Destinazione non nota'),
                        "wait": f"{b.get('time', '0')} min"
                    })
                return risultati
            else:
                # Caso in cui il server risponde ma con errore (es. 404 o 500)
                return [{"line": "OFF", "direction": "Servizio momentaneamente sospeso", "wait": "!"}]
    except Exception as e:
        # Caso in cui il server non risponde proprio (timeout)
        return [{"line": "ATTESA", "direction": "Riconnessione ai server Roma...", "wait": "..."}]

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
