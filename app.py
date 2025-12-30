import streamlit as st
import sqlite3
import folium
from streamlit_folium import st_folium
import requests

st.set_page_config(page_title="Roma Mobility Dispatcher", page_icon="📡", layout="wide")

# --- TITOLO E LOGICA OPERATORI ---
st.title("📡 Roma Mobility Dispatcher")

# Inizializziamo lo stato dell'operatore se non esiste
if 'operatore' not in st.session_state:
    st.session_state.operatore = "TUTTI"
if 'preferiti' not in st.session_state:
    st.session_state.preferiti = []

# --- PULSANTI OPERATORI ---
st.write("Seleziona un operatore per filtrare la ricerca:")
c1, c2, c3, c4 = st.columns(4)
with c1:
    if st.button("🔴 ATAC", use_container_width=True): st.session_state.operatore = "ATAC"
with c2:
    if st.button("🔵 Roma TPL", use_container_width=True): st.session_state.operatore = "TPL"
with c3:
    if st.button("🟢 Cotral", use_container_width=True): st.session_state.operatore = "COTRAL"
with c4:
    if st.button("⚪ Tutti", use_container_width=True): st.session_state.operatore = "TUTTI"

st.info(f"Filtro attivo: **{st.session_state.operatore}**")
st.markdown("---")

# --- FUNZIONI ---
def get_tempi_reali(palina_id):
    url_live = f"https://romamobile.it/paline/?nav=2&Submit=Cerca&cerca={palina_id}"
    st.info(f"📡 Recupero dati in corso per la Palina {palina_id}...")
    st.components.v1.iframe(url_live, height=500, scrolling=True)
    return []

def cerca_fermata(testo, operatore):
    conn = sqlite3.connect('trasporti_roma.db')
    cursor = conn.cursor()
    
    # Se un operatore è selezionato, aggiungiamo il filtro alla query SQL
    if operatore == "TUTTI":
        query = "SELECT palina_id, nome, lat, lon FROM fermate WHERE palina_id = ? OR nome LIKE ? LIMIT 5"
        params = (testo, f'%{testo}%')
    else:
        # Nota: Assicurati che nella tua tabella 'fermate' ci sia una colonna 'operatore'
        query = "SELECT palina_id, nome, lat, lon FROM fermate WHERE (palina_id = ? OR nome LIKE ?) AND operatore = ? LIMIT 5"
        params = (testo, f'%{testo}%', operatore)
        
    cursor.execute(query, params)
    res = cursor.fetchall()
    conn.close()
    return res

# --- SIDEBAR ---
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
        risultati = cerca_fermata(query_input, st.session_state.operatore)
        if not risultati:
            st.warning("Nessuna fermata trovata con questo filtro.")
        for r in risultati:
            with st.expander(f"📍 {r[1]} ({r[0]})", expanded=True):
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button(f"Mostra Arrivi", key=f"t_{r[0]}"):
                        get_tempi_reali(r[0])
                with col_b:
                    if st.button("⭐ Salva", key=f"s_{r[0]}"):
                        if r[0] not in [p['id'] for p in st.session_state.preferiti]:
                            st.session_state.preferiti.append({'id': r[0], 'nome': r[1]})
                            st.toast("Salvato!")

with col2:
    # Se c'è un risultato, centra la mappa sulla prima fermata trovata
    center = [41.896, 12.482]
    zoom = 12
    if query_input and risultati:
        center = [risultati[0][2], risultati[0][3]]
        zoom = 16
        
    m = folium.Map(location=center, zoom_start=zoom)
    
    # Aggiunge i marker per i risultati trovati
    if query_input:
        for r in risultati:
            folium.Marker([r[2], r[3]], popup=r[1]).add_to(m)
            
    st_folium(m, width=500, height=450, key="map")
