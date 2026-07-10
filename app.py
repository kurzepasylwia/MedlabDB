"""
MedLabDB — app.py
Główny plik aplikacji Streamlit.
Streamlit czyta ten plik jako pierwszy — tu definiujemy:
- wygląd całej aplikacji (kolory, czcionki, layout)
- stronę główną (Dashboard)
- nawigację między stronami (Streamlit robi to automatycznie
  na podstawie plików w folderze pages/)
"""

import streamlit as st
from queries import (
    get_statystyki_ogolne,
    get_ostatnie_badania,
    get_rozklad_flag,
)
import plotly.express as px

# ─────────────────────────────────────────────────────────────
# KONFIGURACJA STRONY
# Musi być PIERWSZYM wywołaniem Streamlit w pliku.
# layout="wide" — aplikacja zajmuje całą szerokość ekranu
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="MedLabDB",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CSS — STYL CAŁEJ APLIKACJI
# st.markdown z unsafe_allow_html=True pozwala wstrzyknąć
# własny CSS który nadpisuje domyślny styl Streamlit
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
/* Import czcionki Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

/* Główne tło i czcionka aplikacji */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar — lewy panel nawigacji */
[data-testid="stSidebar"] {
    background-color: #0f1729;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* Ukryj domyślną nawigację Streamlit (automatyczne menu z pages/) */
[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Nagłówki w sidebarze */
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #7dd3fc !important;
    font-family: 'Space Grotesk', sans-serif;
}

/* Główny nagłówek strony */
h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.5px;
}

h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500;
    color: #1e293b;
}

/* Kafelki metryk — st.metric() */
[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* Tabela danych */
[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}

/* Tło głównej zawartości */
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    background-color: #f8fafc;
}

/* Linia oddzielająca sekcje */
hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 1.5rem 0;
}

/* Badge statusu */
.badge-ok {
    background: #dcfce7;
    color: #166534;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

.badge-alert {
    background: #fee2e2;
    color: #991b1b;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True) #streamlit normalnie blokuje html

# ─────────────────────────────────────────────────────────────
# SIDEBAR — lewy panel
# Pojawia się na każdej stronie aplikacji
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧬 MedLabDB")
    st.markdown("System analizy wyników badań biochemicznych")
    st.markdown("---")
    st.page_link("app.py",              label="🏠 Dashboard")
    st.page_link("pages/1_Pacjenci.py", label="👤 Pacjenci")
    st.page_link("pages/2_Analiza.py",  label="📈 Analiza")
    st.page_link("pages/3_Import.py",   label="📥 Import danych")
    st.page_link("pages/4_Raport.py",   label="📄 Raport PDF")
    st.markdown("---")
    st.caption("Projekt zaliczeniowy · Analityk danych biologiczno-medycznych")


# ─────────────────────────────────────────────────────────────
# DASHBOARD — strona główna
# ─────────────────────────────────────────────────────────────

st.title("🏠 Dashboard")
st.markdown("Przegląd systemu i ostatnia aktywność.")
st.markdown("---")

# ── Pobieramy dane z bazy przez queries.py ──
# get_statystyki_ogolne() zwraca słownik z 4 liczbami
stats = get_statystyki_ogolne()

# ── KAFELKI METRYK ──
# st.columns(4) dzieli wiersz na 4 równe kolumny
# w każdej kolumnie wstawiamy st.metric() — gotowy "kafelek"
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="👤 Pacjenci",
        value=stats["liczba_pacjentow"],
    )

with col2:
    st.metric(
        label="🔬 Badania",
        value=stats["liczba_badan"],
    )

with col3:
    st.metric(
        label="📊 Wyniki łącznie",
        value=stats["wszystkich_wynikow"],
    )

with col4:
    st.metric(
        label="⚠️ Poza normą",
        value=stats["poza_norma"],
        # delta pokazuje zmianę — ujemna liczba = czerwony kolor
        # tutaj: ile wyników jest nieprawidłowych (chcemy żeby było 0)
        delta=f"-{stats['poza_norma']} wymagających uwagi",
        delta_color="inverse",
    )

st.markdown("---")

# ── DWIE KOLUMNY: wykres + tabela ──
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("### Rozkład wyników")

    # get_rozklad_flag() zwraca DataFrame z kolumnami: flaga, liczba
    df_flagi = get_rozklad_flag()

    # Wykres kołowy Plotly
    # color_discrete_map — ręcznie przypisujemy kolory do wartości
    fig_pie = px.pie(
        df_flagi,
        names="flaga",
        values="liczba",
        color="flaga",
        color_discrete_map={
            "OK":         "#22c55e",   # zielony
            "POZA NORMĄ": "#ef4444",   # czerwony
        },
        hole=0.45,   # hole > 0 = wykres "donut" zamiast pełnego koła
    )
    fig_pie.update_layout(
        margin=dict(t=20, b=20, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        paper_bgcolor="rgba(0,0,0,0)",  # przezroczyste tło
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        showlegend=True,
    )
    fig_pie.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont_size=13,
    )
    # use_container_width=True — wykres zajmuje całą szerokość kolumny
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.markdown("### Ostatnie badania")

    # get_ostatnie_badania() zwraca DataFrame — ostatnie 10 badań
    df_ostatnie = get_ostatnie_badania(10)

    # Zmieniamy nazwy kolumn na czytelne po polsku
    # to tylko zmiana wyświetlana — nie wpływa na bazę danych
    df_ostatnie = df_ostatnie.rename(columns={
        "id_badania":        "Nr badania",
        "pacjent_id":        "ID pacjenta",
        "plec":              "Płeć",
        "rok_urodzenia":     "Rok ur.",
        "data_badania":      "Data badania",
        "liczba_parametrow": "Parametrów",
    })

    st.dataframe(
        df_ostatnie,
        use_container_width=True,
        hide_index=True,           # ukrywamy indeks (0,1,2...) z lewej
        height=350,
    )
