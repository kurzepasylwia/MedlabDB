"""
MedLabDB — pages/2_Analiza.py
Strona: Analiza

Co tu robimy:
1. Wykres liniowy — trend wybranego parametru w czasie dla pacjenta
   (z liniami norm referencyjnych)
2. Wykres porównawczy — średnie wartości parametru u wszystkich pacjentów
3. Tabela statystyk opisowych dla wybranego pacjenta
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from queries import (
    get_wszyscy_pacjenci,
    get_dostepne_parametry,
    get_trend_parametru,
    get_porownanie_parametru,
    get_karta_pacjenta,
)

# ─────────────────────────────────────────────────────────────
# KONFIGURACJA
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Analiza · MedLabDB",
    page_icon="📈",
    layout="wide",
)

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
.chart-container {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
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

st.title("📈 Analiza")
st.markdown("Trendy parametrów w czasie i porównanie między pacjentami.")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 1 — WYBÓR PACJENTA I PARAMETRU
# Dwie listy rozwijane obok siebie w dwóch kolumnach
# Wybór parametru jest dynamiczny — zależy od wybranego pacjenta
# (get_dostepne_parametry zwraca tylko te parametry które ten
#  pacjent ma w swojej historii badań)
# ─────────────────────────────────────────────────────────────

df_pacjenci = get_wszyscy_pacjenci()

# Słownik: opis → id (tak samo jak w 1_Pacjenci.py)
opcje_pacjentow = {
    f"Pacjent #{row['id']} · {row['plec']} · ur. {row['rok_urodzenia']}": row["id"]
    for _, row in df_pacjenci.iterrows()
}

col_sel1, col_sel2 = st.columns(2)

with col_sel1:
    wybrany_label = st.selectbox(
        "Wybierz pacjenta:",
        options=list(opcje_pacjentow.keys()),
    )
    pacjent_id = opcje_pacjentow[wybrany_label]

with col_sel2:
    # Parametry zależą od wybranego pacjenta — pobieramy dynamicznie
    dostepne = get_dostepne_parametry(pacjent_id)
    wybrany_parametr = st.selectbox(
        "Wybierz parametr:",
        options=dostepne,
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 2 — WYKRES TRENDU
# get_trend_parametru() zwraca DataFrame z kolumnami:
# data_badania | wartosc | jednostka | norma_min | norma_max | flaga
#
# Używamy plotly.graph_objects (go) zamiast plotly.express (px)
# bo potrzebujemy narysować KILKA linii na jednym wykresie:
# - linia główna z wartościami pacjenta
# - pozioma linia normy minimalnej
# - pozioma linia normy maksymalnej
# - wypełnienie obszaru między normami (go.Scatter z fill)
# px nie obsługuje łatwo wielu warstw, go daje pełną kontrolę
# ─────────────────────────────────────────────────────────────

df_trend = get_trend_parametru(pacjent_id, wybrany_parametr)

st.markdown(f"### Trend: {wybrany_parametr}")

if df_trend.empty:
    st.warning("Brak danych dla wybranego pacjenta i parametru.")
else:
    jednostka  = df_trend["jednostka"].iloc[0]
    norma_min  = df_trend["norma_min"].iloc[0]
    norma_max  = df_trend["norma_max"].iloc[0]

    # --- Budujemy wykres warstwa po warstwie (go.Figure) ---
    fig_trend = go.Figure()

    # WARSTWA 1 — wypełnienie obszaru normy (zielony pas)
    # Rysujemy dwie niewidoczne linie (norma_min i norma_max)
    # i wypełniamy przestrzeń między nimi kolorem
    # "tonexty" = wypełnij do poprzedniej linii (norma_min)
    fig_trend.add_trace(go.Scatter(
        x=df_trend["data_badania"],
        y=[norma_min] * len(df_trend),
        mode="lines",
        line=dict(width=0),          # linia niewidoczna
        showlegend=False,
        hoverinfo="skip",            # nie pokazuj tooltipa dla tej linii
    ))
    fig_trend.add_trace(go.Scatter(
        x=df_trend["data_badania"],
        y=[norma_max] * len(df_trend),
        mode="lines",
        line=dict(width=0),
        fill="tonexty",              # wypełnij do poprzedniej linii
        fillcolor="rgba(34,197,94,0.12)",  # przezroczysty zielony
        showlegend=True,
        name="Zakres normy",
        hoverinfo="skip",
    ))

    # WARSTWA 2 — linia z wartościami pacjenta
    # Każdy punkt kolorujemy osobno w zależności od flagi
    kolory_punktow = [
        "#ef4444" if f == "POZA NORMĄ" else "#3b82f6"
        for f in df_trend["flaga"]
    ]

    fig_trend.add_trace(go.Scatter(
        x=df_trend["data_badania"],
        y=df_trend["wartosc"],
        mode="lines+markers",        # linia + punkty
        name=wybrany_parametr,
        line=dict(color="#3b82f6", width=2.5),
        marker=dict(
            size=10,
            color=kolory_punktow,    # każdy punkt ma swój kolor
            line=dict(width=2, color="white"),  # białe obramowanie punktu
        ),
        # Tooltip — co wyświetla się po najechaniu na punkt
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"{wybrany_parametr}: %{{y}} {jednostka}<br>"
            "<extra></extra>"        # usuwa domyślną nazwę trace w tooltipie
        ),
    ))

    # WARSTWA 3 — poziome linie norm (przerywane)
    fig_trend.add_hline(
        y=norma_min,
        line_dash="dash",
        line_color="#94a3b8",
        line_width=1.5,
        annotation_text=f"Min: {norma_min}",
        annotation_position="bottom right",
        annotation_font_color="#64748b",
    )
    fig_trend.add_hline(
        y=norma_max,
        line_dash="dash",
        line_color="#94a3b8",
        line_width=1.5,
        annotation_text=f"Max: {norma_max}",
        annotation_position="top right",
        annotation_font_color="#64748b",
    )

    fig_trend.update_layout(
        xaxis_title="Data badania",
        yaxis_title=f"{wybrany_parametr} [{jednostka}]",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(t=40, b=40, l=10, r=10),
        xaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
        hovermode="x unified",       # tooltip dla wszystkich punktów w tej samej dacie
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    # Informacja pod wykresem — zakres normy
    st.caption(
        f"Zakres referencyjny dla {wybrany_parametr}: "
        f"**{norma_min} – {norma_max} {jednostka}**"
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 3 — STATYSTYKI OPISOWE
# pd.DataFrame.describe() liczy automatycznie:
# count, mean, std, min, 25%, 50%, 75%, max
# Filtrujemy tylko wybrany parametr i zaokrąglamy do 2 miejsc
# ─────────────────────────────────────────────────────────────

st.markdown(f"### Statystyki: {wybrany_parametr}")

if not df_trend.empty:
    col_s1, col_s2 = st.columns([1, 2])

    with col_s1:
        # Podstawowe metryki
        wartosci = df_trend["wartosc"]

        s1, s2 = st.columns(2)
        with s1:
            st.metric("Średnia", f"{wartosci.mean():.2f} {jednostka}")
            st.metric("Minimum", f"{wartosci.min():.2f} {jednostka}")
        with s2:
            st.metric("Mediana", f"{wartosci.median():.2f} {jednostka}")
            st.metric("Maksimum", f"{wartosci.max():.2f} {jednostka}")

    with col_s2:
        # Pełna tabela describe() — pandas liczy to automatycznie
        df_desc = (
            df_trend[["wartosc"]]
            .describe()
            .rename(columns={"wartosc": wybrany_parametr})
            .rename(index={
                "count": "Liczba pomiarów",
                "mean":  "Średnia",
                "std":   "Odch. standardowe",
                "min":   "Minimum",
                "25%":   "1. kwartyl (25%)",
                "50%":   "Mediana (50%)",
                "75%":   "3. kwartyl (75%)",
                "max":   "Maksimum",
            })
            .round(2)
        )
        st.dataframe(df_desc, use_container_width=True)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# SEKCJA 4 — PORÓWNANIE MIĘDZY PACJENTAMI
# get_porownanie_parametru() zwraca średnią wartość
# danego parametru dla każdego pacjenta
# Pokazujemy wykres słupkowy z linią normy
# ─────────────────────────────────────────────────────────────

st.markdown(f"### Porównanie: {wybrany_parametr} u wszystkich pacjentów")

df_por = get_porownanie_parametru(wybrany_parametr)

if df_por.empty:
    st.warning("Brak danych do porównania.")
else:
    # Tworzymy etykiety dla osi X
    df_por["etykieta"] = df_por.apply(
        lambda r: f"#{int(r['pacjent_id'])} ({r['plec']}, {int(r['rok_urodzenia'])})",
        axis=1,
    )

    # Kolorujemy słupki — czerwony jeśli średnia poza normą
    df_por["kolor"] = df_por.apply(
        lambda r: "#ef4444"
        if r["srednia_wartosc"] < r["norma_min"] or r["srednia_wartosc"] > r["norma_max"]
        else "#3b82f6",
        axis=1,
    )

    norma_min_por = df_por["norma_min"].iloc[0]
    norma_max_por = df_por["norma_max"].iloc[0]
    jednostka_por = df_trend["jednostka"].iloc[0] if not df_trend.empty else ""

    fig_por = go.Figure()

    # Słupki — każdy ma swój kolor
    fig_por.add_trace(go.Bar(
        x=df_por["etykieta"],
        y=df_por["srednia_wartosc"],
        marker_color=df_por["kolor"],
        text=df_por["srednia_wartosc"].round(2),
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            f"Średnia: %{{y:.2f}} {jednostka_por}<br>"
            "<extra></extra>"
        ),
        name="Średnia wartość",
    ))

    # Linie norm
    fig_por.add_hline(
        y=norma_min_por,
        line_dash="dash", line_color="#22c55e", line_width=1.5,
        annotation_text=f"Min normy: {norma_min_por}",
        annotation_position="bottom left",
        annotation_font_color="#15803d",
    )
    fig_por.add_hline(
        y=norma_max_por,
        line_dash="dash", line_color="#ef4444", line_width=1.5,
        annotation_text=f"Max normy: {norma_max_por}",
        annotation_position="top left",
        annotation_font_color="#991b1b",
    )

    fig_por.update_layout(
        xaxis_title="Pacjent",
        yaxis_title=f"Średnia wartość [{jednostka_por}]",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=13),
        showlegend=False,
        margin=dict(t=40, b=40, l=10, r=10),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
    )

    st.plotly_chart(fig_por, use_container_width=True)
    st.caption(
        f"🔵 Niebieski = wartość w normie &nbsp;|&nbsp; "
        f"🔴 Czerwony = wartość poza normą &nbsp;|&nbsp; "
        f"Norma: {norma_min_por} – {norma_max_por} {jednostka_por}"
    )
