"""
MedLabDB — pages/4_Raport.py
Strona: Raport PDF

Co tu robimy:
1. Użytkownik wybiera pacjenta
2. Pokazujemy podgląd raportu w aplikacji
3. Generujemy profesjonalny PDF z wynikami
4. Użytkownik pobiera PDF przyciskiem Download
"""

import streamlit as st
import pandas as pd
from datetime import date
import io

# ReportLab — biblioteka do tworzenia PDF
# Platypus to "wyższy poziom" ReportLab — układa elementy automatycznie
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

from queries import get_wszyscy_pacjenci, get_dane_do_raportu

# Rejestracja czcionek DejaVuSans z obsługą polskich znaków
# TTFont rejestruje plik .ttf pod nazwą której używamy w stylach
_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")
pdfmetrics.registerFont(TTFont("DejaVuSans",      os.path.join(_FONTS_DIR, "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", os.path.join(_FONTS_DIR, "DejaVuSans-Bold.ttf")))

# ─────────────────────────────────────────────────────────────
# KONFIGURACJA
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Raport · MedLabDB",
    page_icon="📄",
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

st.title("📄 Raport PDF")
st.markdown("Wygeneruj kartę wyników badań dla wybranego pacjenta.")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# WYBÓR PACJENTA
# ─────────────────────────────────────────────────────────────

df_pacjenci = get_wszyscy_pacjenci()

opcje = {
    f"Pacjent #{row['id']} · {row['plec']} · ur. {row['rok_urodzenia']}": row["id"]
    for _, row in df_pacjenci.iterrows()
}

wybrany_label = st.selectbox("Wybierz pacjenta:", options=list(opcje.keys()))
pacjent_id    = opcje[wybrany_label]

# ─────────────────────────────────────────────────────────────
# POBIERAMY DANE DO RAPORTU
# get_dane_do_raportu() zwraca słownik:
# { "pacjent": {...}, "wyniki": DataFrame, "podsumowanie": {...} }
# ─────────────────────────────────────────────────────────────

dane       = get_dane_do_raportu(pacjent_id)
pacjent    = dane["pacjent"]
df_wyniki  = dane["wyniki"]
podsumow   = dane["podsumowanie"]

if df_wyniki.empty:
    st.warning("Brak wyników dla wybranego pacjenta.")
    st.stop()

# ─────────────────────────────────────────────────────────────
# PODGLĄD W APLIKACJI
# ─────────────────────────────────────────────────────────────

st.markdown("### Podgląd raportu")

# Metryki
wiek = date.today().year - pacjent["rok_urodzenia"]
plec_label = "Kobieta" if pacjent["plec"] == "K" else "Mężczyzna"

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Pacjent ID", f"#{pacjent_id}")
with m2:
    st.metric("Płeć / Wiek", f"{plec_label}, {wiek} lat")
with m3:
    st.metric("Liczba badań", podsumow["liczba_badan"])
with m4:
    st.metric("⚠️ Poza normą", podsumow["poza_norma"])

st.markdown("---")

# Tabela wyników z kolorowaniem
st.markdown("#### Wyniki badań")

df_display = df_wyniki.rename(columns={
    "data_badania": "Data",
    "parametr":     "Parametr",
    "wartosc":      "Wartość",
    "jednostka":    "Jednostka",
    "norma_min":    "Norma min",
    "norma_max":    "Norma max",
    "flaga":        "Status",
})

def _kolor(row):
    if row["Status"] == "POZA NORMĄ":
        return ["background-color:#fff1f2; color:#991b1b"] * len(row)
    return ["background-color:#f0fdf4; color:#166534"] * len(row)

st.dataframe(
    df_display.style.apply(_kolor, axis=1),
    use_container_width=True,
    hide_index=True,
    height=400,
)

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# FUNKCJA GENERUJĄCA PDF
#
# Używamy ReportLab Platypus — "story-based" API:
# budujemy listę elementów (story = []),
# a ReportLab sam rozkłada je na strony.
#
# Elementy których używamy:
# - Paragraph  → tekst z formatowaniem
# - Spacer     → pusta przestrzeń
# - Table      → tabela z danymi
# - HRFlowable → pozioma linia
# ─────────────────────────────────────────────────────────────

def generuj_pdf(pacjent_id: int, pacjent: dict, df: pd.DataFrame, podsumow: dict) -> bytes:
    """
    Generuje raport PDF i zwraca go jako bytes.
    bytes to surowe bajty pliku — Streamlit może je wysłać
    do przeglądarki jako plik do pobrania.
    """

    # io.BytesIO() — bufor w pamięci, działa jak plik ale nie zapisuje na dysk
    # Dzięki temu PDF istnieje tylko w RAM i Streamlit może go od razu wysłać
    bufor = io.BytesIO()

    # Dokument A4 z marginesami
    doc = SimpleDocTemplate(
        bufor,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    # --- Style tekstu ---
    styles = getSampleStyleSheet()

    # Definiujemy własne style przez ParagraphStyle
    # basedOn= dziedziczy z istniejącego stylu i nadpisuje wybrane właściwości
    styl_tytul = ParagraphStyle(
        "Tytul",
        basedOn=styles["Normal"],
        fontSize=22,
        fontName="DejaVuSans-Bold",
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
        leading=26,        # leading = wysokość linii — musi być > fontSize
        spaceBefore=0,
        spaceAfter=0,      # odstęp zapewnia Spacer w story
    )

    styl_podtytul = ParagraphStyle(
        "Podtytul",
        basedOn=styles["Normal"],
        fontSize=10,
        fontName="DejaVuSans",
        textColor=colors.HexColor("#64748b"),
        alignment=TA_LEFT,          # też do lewej — nie nachodzi na tytuł
        spaceBefore=0,
        spaceAfter=14,
    )

    styl_sekcja = ParagraphStyle(
        "Sekcja",
        basedOn=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=16,
        spaceAfter=8,
        fontName="DejaVuSans-Bold",
    )

    styl_info = ParagraphStyle(
        "Info",
        basedOn=styles["Normal"],
        fontSize=10,
        fontName="DejaVuSans",
        textColor=colors.HexColor("#334155"),
        spaceAfter=4,
    )

    styl_stopka = ParagraphStyle(
        "Stopka",
        basedOn=styles["Normal"],
        fontSize=8,
        fontName="DejaVuSans",
        textColor=colors.HexColor("#94a3b8"),
        alignment=TA_CENTER,
        spaceBefore=12,
    )

    # --- Budujemy story (lista elementów PDF) ---
    story = []

    # ── NAGŁÓWEK ──
    story.append(Paragraph("MedLabDB", styl_tytul))
    story.append(Spacer(1, 0.4*cm))   # odstęp między tytułem a podtytułem
    story.append(Paragraph(
        f"Raport wyników badań biochemicznych · wygenerowano {date.today().strftime('%d.%m.%Y')}",
        styl_podtytul,
    ))
    story.append(HRFlowable(
        width="100%",
        thickness=2,
        color=colors.HexColor("#0f172a"),
        spaceBefore=4,
        spaceAfter=16,
    ))

    # ── DANE PACJENTA ──
    story.append(Paragraph("Dane pacjenta", styl_sekcja))

    wiek_pdf = date.today().year - pacjent["rok_urodzenia"]
    plec_pdf = "Kobieta" if pacjent["plec"] == "K" else "Mężczyzna"

    # Tabela z danymi pacjenta — 2 kolumny: etykieta | wartość
    dane_pacjenta = [
        ["ID pacjenta",     f"#{pacjent_id}"],
        ["Płeć",            plec_pdf],
        ["Rok urodzenia",   str(pacjent["rok_urodzenia"])],
        ["Wiek",            f"{wiek_pdf} lat"],
        ["Liczba badań",    str(podsumow["liczba_badan"])],
        ["Wyników łącznie", str(podsumow["liczba_wynikow"])],
        ["Poza normą",      str(podsumow["poza_norma"])],
    ]

    tabela_pacjent = Table(dane_pacjenta, colWidths=[5*cm, 10*cm])
    tabela_pacjent.setStyle(TableStyle([
        # FONT — lewa kolumna pogrubiona
        ("FONTNAME",    (0, 0), (0, -1), "DejaVuSans-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "DejaVuSans"),
        ("FONTSIZE",    (0, 0), (-1, -1), 10),
        # KOLOR tekstu
        ("TEXTCOLOR",   (0, 0), (0, -1), colors.HexColor("#64748b")),
        ("TEXTCOLOR",   (1, 0), (1, -1), colors.HexColor("#0f172a")),
        # PADDING — odstępy wewnątrz komórek
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0,0), (-1, -1), 5),
        # LINIE między wierszami
        ("LINEBELOW",   (0, 0), (-1, -2), 0.5, colors.HexColor("#f1f5f9")),
        # VALIGN — wyrównanie pionowe
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(tabela_pacjent)

    # ── TABELA WYNIKÓW ──
    story.append(Paragraph("Wyniki badań", styl_sekcja))

    # Nagłówek tabeli
    naglowek = [["Data", "Parametr", "Wartość", "Jednostka", "Norma min", "Norma max", "Status"]]

    # Wiersze danych
    wiersze = []
    for _, row in df.iterrows():
        wiersze.append([
            str(row["data_badania"]),
            str(row["parametr"]),
            str(row["wartosc"]),
            str(row["jednostka"]),
            str(row["norma_min"]),
            str(row["norma_max"]),
            str(row["flaga"]),
        ])

    # Łączymy nagłówek z wierszami
    dane_tabeli = naglowek + wiersze

    # Szerokości kolumn — suma musi być <= szerokość strony (A4 - marginesy = ~17cm)
    col_widths = [2.4*cm, 3.2*cm, 1.8*cm, 2.0*cm, 2.0*cm, 2.0*cm, 2.8*cm]

    tabela_wyniki = Table(dane_tabeli, colWidths=col_widths, repeatRows=1)
    # repeatRows=1 — nagłówek powtarza się na każdej stronie gdy tabela jest długa

    # Budujemy style tabeli
    style_wyniki = [
        # NAGŁÓWEK
        ("BACKGROUND",   (0, 0), (-1, 0),  colors.HexColor("#0f172a")),
        ("TEXTCOLOR",    (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",     (0, 0), (-1, 0),  "DejaVuSans-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0),  8),
        ("ALIGN",        (0, 0), (-1, 0),  "CENTER"),
        ("TOPPADDING",   (0, 0), (-1, 0),  7),
        ("BOTTOMPADDING",(0, 0), (-1, 0),  7),

        # DANE
        ("FONTNAME",     (0, 1), (-1, -1), "DejaVuSans"),
        ("FONTSIZE",     (0, 1), (-1, -1), 8),
        ("ALIGN",        (0, 1), (-1, -1), "CENTER"),
        ("TOPPADDING",   (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 1), (-1, -1), 5),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),

        # SIATKA
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),

        # ZEBRA — naprzemienne kolory wierszy (łatwiej czytać długie tabele)
        # Ustawiamy dla każdego parzystego wiersza danych (indeks 2, 4, 6...)
    ]

    # Dodajemy kolorowanie wierszy: zielone OK, czerwone POZA NORMĄ
    # oraz zebra dla wierszy OK
    for i, row in enumerate(wiersze):
        row_idx = i + 1   # +1 bo indeks 0 to nagłówek
        if row[-1] == "POZA NORMĄ":
            # Czerwone tło dla wierszy poza normą
            style_wyniki.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#fff1f2")))
            style_wyniki.append(("TEXTCOLOR",  (0, row_idx), (-1, row_idx), colors.HexColor("#991b1b")))
            style_wyniki.append(("FONTNAME",   (0, row_idx), (-1, row_idx), "DejaVuSans-Bold"))
        elif i % 2 == 0:
            # Zebra — co drugi wiersz OK ma jasnoszare tło
            style_wyniki.append(("BACKGROUND", (0, row_idx), (-1, row_idx), colors.HexColor("#f8fafc")))

    tabela_wyniki.setStyle(TableStyle(style_wyniki))
    story.append(tabela_wyniki)

    # ── PODSUMOWANIE ──
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Paragraph("Podsumowanie", styl_sekcja))

    poza = podsumow["poza_norma"]
    total = podsumow["liczba_wynikow"]
    procent_ok = round((total - poza) / total * 100) if total > 0 else 0

    story.append(Paragraph(
        f"Łączna liczba wyników: <b>{total}</b> &nbsp;|&nbsp; "
        f"W normie: <b>{total - poza}</b> &nbsp;|&nbsp; "
        f"Poza normą: <b>{poza}</b> &nbsp;|&nbsp; "
        f"Wyników w normie: <b>{procent_ok}%</b>",
        styl_info,
    ))

    if poza > 0:
        # Lista parametrów poza normą
        parametry_poza = df[df["flaga"] == "POZA NORMĄ"]["parametr"].unique()
        story.append(Paragraph(
            f"Parametry wymagające uwagi: <b>{', '.join(parametry_poza)}</b>",
            ParagraphStyle(
                "Alert",
                basedOn=styl_info,
                fontName="DejaVuSans",
                textColor=colors.HexColor("#991b1b"),
            ),
        ))

    # ── STOPKA ──
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Paragraph(
        "Raport wygenerowany przez system MedLabDB · "
        "Projekt zaliczeniowy — Analityk danych biologiczno-medycznych · "
        f"Data wydruku: {date.today().strftime('%d.%m.%Y')}",
        styl_stopka,
    ))

    # --- Budujemy PDF ---
    # doc.build(story) przetwarza listę elementów i zapisuje do bufora
    doc.build(story)

    # Pobieramy zawartość bufora jako bytes
    bufor.seek(0)
    return bufor.read()


# ─────────────────────────────────────────────────────────────
# PRZYCISK GENEROWANIA PDF
# ─────────────────────────────────────────────────────────────

st.markdown("### Pobierz raport")

col_btn1, col_btn2 = st.columns([1, 3])

with col_btn1:
    if st.button("🔄 Generuj PDF", type="primary", use_container_width=True):
        # st.spinner() — kręcące się kółko podczas generowania
        with st.spinner("Generowanie raportu..."):
            try:
                pdf_bytes = generuj_pdf(pacjent_id, pacjent, df_wyniki, podsumow)

                # Zapisujemy PDF w st.session_state — to pamięć sesji Streamlit
                # Przechowuje dane między kliknięciami przycisków na tej samej stronie
                st.session_state["pdf_bytes"]    = pdf_bytes
                st.session_state["pdf_pacjent"]  = pacjent_id

                st.success("✅ PDF wygenerowany! Kliknij przycisk pobierania poniżej.")

            except Exception as e:
                st.error(f"❌ Błąd generowania PDF: {e}")

# Przycisk pobierania pojawia się tylko gdy PDF jest już wygenerowany
# i dotyczy aktualnie wybranego pacjenta
if (
    "pdf_bytes" in st.session_state
    and st.session_state.get("pdf_pacjent") == pacjent_id
):
    with col_btn1:
        st.download_button(
            label="📥 Pobierz PDF",
            data=st.session_state["pdf_bytes"],
            file_name=f"raport_pacjent_{pacjent_id}_{date.today()}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
