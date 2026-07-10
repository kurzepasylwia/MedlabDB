"""
MedLabDB — pages/1_Pacjenci.py
Strona: Pacjenci

Co tu robimy:
1. Wyświetlamy tabelę wszystkich pacjentów
2. Użytkownik wybiera pacjenta z listy rozwijanej
3. Pokazujemy kartę wyników tego pacjenta
4. Kolorujemy wiersze — zielony OK / czerwony POZA NORMĄ
5. Wykres słupkowy — które parametry najczęściej poza normą
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from queries import (
    get_wszyscy_pacjenci,
    get_karta_pacjenta,
    get_liczba_anomalii_pacjenta,
)

# ─────────────────────────────────────────────────────────────
# KONFIGURACJA STRONY
# Każdy plik w pages/ musi mieć własne set_page_config()
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pacjenci · MedLabDB",
    page_icon="👤",
    layout="wide",
)

# ─────────────────────────────────────────────────────────────
# CSS — taki sam styl jak w app.py
# Kopiujemy go do każdej strony żeby wygląd był spójny
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

[data-testid="stSidebar"] { background-color: #0f1729; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
/* Ukryj domyślną nawigację Streamlit (automatyczne menu z pages/) */
[data-testid="stSidebarNav"] {
    display: none !important;
}


h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
    color: #0f172a;
}

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

.main .block-container {
    padding-top: 2rem;
    background-color: #f8fafc;
}

/* Karta pacjenta — box z informacjami */
.pacjent-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px 24px;
    margin-bottom: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.pacjent-card h3 {
    margin-top: 0;
    color: #0f172a;
    font-size: 1.1rem;
}

.info-row {
    display: flex;
    gap: 2rem;
    flex-wrap: wrap;
}

.info-item {
    display: flex;
    flex-direction: column;
}

.info-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #94a3b8;
}

.info-value {
    font-size: 1rem;
    font-weight: 500;
    color: #1e293b;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# SIDEBAR
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
# NAGŁÓWEK
# ─────────────────────────────────────────────────────────────

st.title("👤 Pacjenci")
st.markdown("Przeglądaj listę pacjentów i szczegółowe wyniki badań.")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 1 — TABELA WSZYSTKICH PACJENTÓW
# get_wszyscy_pacjenci() zwraca DataFrame z kolumnami:
# id, plec, rok_urodzenia, liczba_badan, pierwsze_badanie, ostatnie_badanie
# ─────────────────────────────────────────────────────────────

st.markdown("### Wszyscy pacjenci")

df_pacjenci = get_wszyscy_pacjenci()

# Zmieniamy nazwy kolumn na czytelne
df_pacjenci_display = df_pacjenci.rename(columns={
    "id":               "ID",
    "plec":             "Płeć",
    "rok_urodzenia":    "Rok ur.",
    "liczba_badan":     "Liczba badań",
    "pierwsze_badanie": "Pierwsze badanie",
    "ostatnie_badanie": "Ostatnie badanie",
})

st.dataframe(
    df_pacjenci_display,
    use_container_width=True,
    hide_index=True,
    height=230,
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 2 — WYBÓR PACJENTA
# st.selectbox() tworzy listę rozwijaną
# Budujemy słownik: "Pacjent #1 (K, ur. 1985)" → 1
# Dzięki temu użytkownik widzi czytelny opis, a my mamy id
# ─────────────────────────────────────────────────────────────

st.markdown("### Karta pacjenta")

# Tworzymy opcje do selectboxa
opcje = {
    f"Pacjent #{row['id']} · {row['plec']} · ur. {row['rok_urodzenia']}": row["id"]
    for _, row in df_pacjenci.iterrows()
}

wybrany_label = st.selectbox(
    "Wybierz pacjenta:",
    options=list(opcje.keys()),
    index=0,   # domyślnie zaznaczony pierwszy pacjent
)

# Pobieramy id wybranego pacjenta ze słownika
pacjent_id = opcje[wybrany_label]

# ─────────────────────────────────────────────────────────────
# KARTA PACJENTA — box z informacjami
# Filtrujemy dane wybranego pacjenta z df_pacjenci
# ─────────────────────────────────────────────────────────────

pacjent_row = df_pacjenci[df_pacjenci["id"] == pacjent_id].iloc[0]

# Obliczamy wiek na podstawie roku urodzenia
from datetime import date
wiek = date.today().year - pacjent_row["rok_urodzenia"]

plec_label = "Kobieta" if pacjent_row["plec"] == "K" else "Mężczyzna"

# HTML box z informacjami o pacjencie
st.markdown(f"""
<div class="pacjent-card">
    <h3>🪪 Pacjent #{pacjent_id}</h3>
    <div class="info-row">
        <div class="info-item">
            <span class="info-label">Płeć</span>
            <span class="info-value">{plec_label}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Rok urodzenia</span>
            <span class="info-value">{pacjent_row['rok_urodzenia']}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Wiek</span>
            <span class="info-value">{wiek} lat</span>
        </div>
        <div class="info-item">
            <span class="info-label">Liczba badań</span>
            <span class="info-value">{pacjent_row['liczba_badan']}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Pierwsze badanie</span>
            <span class="info-value">{pacjent_row['pierwsze_badanie']}</span>
        </div>
        <div class="info-item">
            <span class="info-label">Ostatnie badanie</span>
            <span class="info-value">{pacjent_row['ostatnie_badanie']}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# METRYKI PACJENTA
# ─────────────────────────────────────────────────────────────

df_karta = get_karta_pacjenta(pacjent_id)

liczba_wynikow  = len(df_karta)
liczba_poza     = (df_karta["flaga"] == "POZA NORMĄ").sum()
liczba_ok       = liczba_wynikow - liczba_poza
procent_ok      = round(liczba_ok / liczba_wynikow * 100) if liczba_wynikow > 0 else 0

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("📊 Wszystkich wyników", liczba_wynikow)
with m2:
    st.metric("✅ W normie", liczba_ok)
with m3:
    st.metric("⚠️ Poza normą", liczba_poza)
with m4:
    st.metric("🎯 % w normie", f"{procent_ok}%")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 3 — TABELA WYNIKÓW Z KOLOROWANIEM
# Kolorujemy wiersze: zielony = OK, czerwony = POZA NORMĄ
#
# Streamlit nie ma wbudowanego kolorowania wierszy,
# ale pandas Styler pozwala to zrobić przez CSS.
# Funkcja _kolor_wiersza() sprawdza wartość w kolumnie "flaga"
# i zwraca odpowiedni kolor tła dla całego wiersza.
# ─────────────────────────────────────────────────────────────

st.markdown("### Wyniki badań")

# Filtr daty — pozwala zawęzić widok do konkretnego badania
daty_badan = sorted(df_karta["data_badania"].unique(), reverse=True)

wybrana_data = st.selectbox(
    "Filtruj według daty badania (lub pokaż wszystkie):",
    options=["Wszystkie"] + list(daty_badan),
)

if wybrana_data != "Wszystkie":
    df_filtered = df_karta[df_karta["data_badania"] == wybrana_data].copy()
else:
    df_filtered = df_karta.copy()

# Zmieniamy nazwy kolumn
df_filtered = df_filtered.rename(columns={
    "data_badania": "Data",
    "parametr":     "Parametr",
    "wartosc":      "Wartość",
    "jednostka":    "Jednostka",
    "norma_min":    "Norma min",
    "norma_max":    "Norma max",
    "flaga":        "Status",
})

# Funkcja kolorująca — przyjmuje wiersz (row) i zwraca
# listę styli CSS dla każdej komórki w tym wierszu
def _kolor_wiersza(row):
    if row["Status"] == "POZA NORMĄ":
        # jasnoróżowe tło dla wierszy poza normą
        return ["background-color: #fff1f2; color: #991b1b"] * len(row)
    else:
        # jasnozielone tło dla wyników OK
        return ["background-color: #f0fdf4; color: #166534"] * len(row)

# .style.apply() stosuje funkcję do każdego wiersza (axis=1)
df_styled = df_filtered.style.apply(_kolor_wiersza, axis=1)

st.dataframe(
    df_styled,
    use_container_width=True,
    hide_index=True,
    height=400,
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 4 — WYKRES SŁUPKOWY ANOMALII
# get_liczba_anomalii_pacjenta() zwraca DataFrame:
# parametr | poza_norma_count
# Pokazujemy które parametry najczęściej wypadają poza normą
# ─────────────────────────────────────────────────────────────

df_anomalie = get_liczba_anomalii_pacjenta(pacjent_id)

if df_anomalie.empty:
    # Jeśli brak anomalii — wyświetlamy komunikat zamiast wykresu
    st.success("✅ Brak wyników poza normą dla tego pacjenta.")
else:
    st.markdown("### Parametry poza normą")
    st.markdown("Liczba wyników poza zakresem referencyjnym dla każdego parametru.")

    fig_bar = px.bar(
        df_anomalie,
        x="poza_norma_count",
        y="parametr",
        orientation="h",          # poziomy wykres słupkowy (h = horizontal)
        color="poza_norma_count",  # kolor zależy od liczby anomalii
        color_continuous_scale=[   # im więcej anomalii, tym ciemniejsza czerwień
            [0.0, "#fca5a5"],
            [1.0, "#b91c1c"],
        ],
        labels={
            "poza_norma_count": "Liczba przekroczeń",
            "parametr":         "Parametr",
        },
        text="poza_norma_count",   # liczba wyświetlana na słupku
    )

    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter"),
        showlegend=False,
        coloraxis_showscale=False,  # ukrywamy skalę kolorów obok wykresu
        margin=dict(t=10, b=10, l=0, r=20),
        yaxis=dict(categoryorder="total ascending"),  # sortuj od najmniej do najwięcej
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
    )
    fig_bar.update_traces(
        textposition="outside",
        textfont=dict(size=13, color="#1e293b"),
    )

    st.plotly_chart(fig_bar, use_container_width=True)
