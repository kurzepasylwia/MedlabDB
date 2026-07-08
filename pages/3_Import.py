"""
MedLabDB — pages/3_Import.py
Strona: Import danych

Co tu robimy:
1. Użytkownik wgrywa plik CSV lub Excel
2. Walidujemy czy plik ma odpowiednie kolumny
3. Pokazujemy podgląd danych przed zapisem
4. Zapisujemy dane do bazy (tabele: pacjenci, badania, wyniki)
5. Pokazujemy podsumowanie importu

Oczekiwany format pliku:
plec | rok_urodzenia | data_badania | Glukoza | ALT | Kreatynina | ...
K    | 1990          | 2024-03-15   | 95      | 22  | 0.7        | ...

Kolumny biochemiczne są opcjonalne — każda kolumna której nazwa
pasuje do parametru w bazie zostanie zaimportowana.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from database import ENGINE, Pacjent, Badanie, Wynik
from queries import get_lista_parametrow, get_id_parametru, get_wszyscy_pacjenci

# ─────────────────────────────────────────────────────────────
# KONFIGURACJA
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Import · MedLabDB",
    page_icon="📥",
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
.main .block-container {
    padding-top: 2rem;
    background-color: #f8fafc;
}

/* Box z instrukcją formatu pliku */
.format-box {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-left: 4px solid #0ea5e9;
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
}

.format-box h4 {
    margin: 0 0 0.5rem 0;
    color: #0369a1;
    font-family: 'Space Grotesk', sans-serif;
}

/* Box z wynikiem importu */
.result-box {
    background: #f0fdf4;
    border: 1px solid #86efac;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-top: 1rem;
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

st.title("📥 Import danych")
st.markdown("Wczytaj wyniki badań z pliku CSV lub Excel do bazy danych.")
st.markdown("---")

# ─────────────────────────────────────────────────────────────
# INSTRUKCJA FORMATU
# Pobieramy listę parametrów z bazy żeby pokazać użytkownikowi
# jakie nazwy kolumn są obsługiwane
# ─────────────────────────────────────────────────────────────

parametry_w_bazie = get_lista_parametrow()

st.markdown("""
<div class="format-box">
<h4>📋 Wymagany format pliku</h4>
<p>Plik CSV lub Excel musi zawierać następujące kolumny obowiązkowe:</p>
<ul>
    <li><b>plec</b> — wartość <code>K</code> (kobieta) lub <code>M</code> (mężczyzna)</li>
    <li><b>rok_urodzenia</b> — czterocyfrowy rok, np. <code>1990</code></li>
    <li><b>data_badania</b> — format <code>YYYY-MM-DD</code>, np. <code>2024-03-15</code></li>
</ul>
<p>Następnie dowolne kolumny z nazwami parametrów biochemicznych, np.:</p>
</div>
""", unsafe_allow_html=True)

# Tabela przykładowa
df_przyklad = pd.DataFrame([
    {
        "plec": "K",
        "rok_urodzenia": 1990,
        "data_badania": "2024-03-15",
        "Glukoza": 95.0,
        "ALT": 22.0,
        "Kreatynina": 0.7,
        "Cholesterol": 185.0,
    },
    {
        "plec": "M",
        "rok_urodzenia": 1975,
        "data_badania": "2024-03-15",
        "Glukoza": 105.0,
        "ALT": 38.0,
        "Kreatynina": 1.1,
        "Cholesterol": 210.0,
    },
])

st.dataframe(df_przyklad, use_container_width=True, hide_index=True)

# Pokazujemy listę wszystkich obsługiwanych parametrów
with st.expander("📊 Lista obsługiwanych parametrów biochemicznych"):
    cols = st.columns(4)
    for i, param in enumerate(parametry_w_bazie):
        cols[i % 4].markdown(f"• {param}")

st.markdown("---")

# ─────────────────────────────────────────────────────────────
# UPLOAD PLIKU
# st.file_uploader() — gotowy komponent do wgrywania plików
# type= ogranicza jakie rozszerzenia są akceptowane
# ─────────────────────────────────────────────────────────────

st.markdown("### Wgraj plik")

plik = st.file_uploader(
    "Wybierz plik CSV lub Excel:",
    type=["csv", "xlsx", "xls"],
    help="Maksymalny rozmiar pliku: 200MB",
)

# ─────────────────────────────────────────────────────────────
# PRZETWARZANIE PLIKU
# Wszystko poniżej wykonuje się tylko gdy plik został wgrany
# ─────────────────────────────────────────────────────────────

if plik is not None:

    # --- Wczytanie pliku do DataFrame ---
    # Rozpoznajemy typ pliku po rozszerzeniu nazwy
    try:
        if plik.name.endswith(".csv"):
            # sep=";" bo polskie Excele często zapisują CSV z średnikiem
            # Próbujemy najpierw z przecinkiem, potem ze średnikiem
            try:
                df_raw = pd.read_csv(plik, sep=",")
                # Sprawdzamy czy kolumny wczytały się poprawnie
                if len(df_raw.columns) == 1:
                    plik.seek(0)   # cofamy wskaźnik pliku na początek
                    df_raw = pd.read_csv(plik, sep=";")
            except Exception:
                plik.seek(0)
                df_raw = pd.read_csv(plik, sep=";")
        else:
            df_raw = pd.read_excel(plik)

        st.success(f"✅ Plik wczytany: **{plik.name}** ({len(df_raw)} wierszy)")

    except Exception as e:
        st.error(f"❌ Nie udało się wczytać pliku: {e}")
        st.stop()   # st.stop() zatrzymuje dalsze wykonywanie strony

    # --- WALIDACJA KOLUMN OBOWIĄZKOWYCH ---
    # Sprawdzamy czy wszystkie wymagane kolumny są w pliku
    kolumny_wymagane = {"plec", "rok_urodzenia", "data_badania"}
    kolumny_w_pliku  = set(df_raw.columns)
    brakujace        = kolumny_wymagane - kolumny_w_pliku

    if brakujace:
        st.error(
            f"❌ Brakuje wymaganych kolumn: **{', '.join(brakujace)}**\n\n"
            f"Kolumny w pliku: {', '.join(df_raw.columns)}"
        )
        st.stop()

    # --- ROZPOZNANIE KOLUMN PARAMETRÓW ---
    # Kolumny parametrów = wszystkie kolumny które NIE są obowiązkowe
    # i których nazwa pasuje do parametru w bazie
    kolumny_meta      = {"plec", "rok_urodzenia", "data_badania"}
    kolumny_w_pliku_p = set(df_raw.columns) - kolumny_meta
    kolumny_parametry = [k for k in kolumny_w_pliku_p if k in parametry_w_bazie]
    kolumny_nieznane  = [k for k in kolumny_w_pliku_p if k not in parametry_w_bazie]

    if not kolumny_parametry:
        st.error(
            "❌ Nie znaleziono żadnych kolumn z parametrami biochemicznymi.\n\n"
            f"Kolumny w pliku: {', '.join(kolumny_w_pliku_p)}\n\n"
            f"Dostępne parametry: {', '.join(parametry_w_bazie)}"
        )
        st.stop()

    # Informacja o rozpoznanych kolumnach
    st.info(
        f"✅ Rozpoznano **{len(kolumny_parametry)}** parametrów: "
        f"{', '.join(kolumny_parametry)}"
    )

    if kolumny_nieznane:
        st.warning(
            f"⚠️ Pominięte kolumny (nieznane parametry): "
            f"{', '.join(kolumny_nieznane)}"
        )

    # --- WALIDACJA DANYCH ---
    bledy = []

    # Sprawdzamy kolumnę plec
    niepoprawna_plec = df_raw[~df_raw["plec"].isin(["K", "M"])]
    if not niepoprawna_plec.empty:
        bledy.append(
            f"Wiersze {list(niepoprawna_plec.index + 2)}: "
            f"niepoprawna wartość w kolumnie 'plec' (dozwolone: K, M)"
        )

    # Sprawdzamy rok urodzenia — musi być między 1900 a bieżącym rokiem
    rok_biezacy = datetime.now().year
    niepoprawny_rok = df_raw[
        (df_raw["rok_urodzenia"] < 1900) |
        (df_raw["rok_urodzenia"] > rok_biezacy)
    ]
    if not niepoprawny_rok.empty:
        bledy.append(
            f"Wiersze {list(niepoprawny_rok.index + 2)}: "
            f"niepoprawny rok urodzenia"
        )

    # Sprawdzamy format daty
    try:
        df_raw["data_badania"] = pd.to_datetime(df_raw["data_badania"])
    except Exception:
        bledy.append(
            "Kolumna 'data_badania' zawiera niepoprawny format daty. "
            "Użyj formatu YYYY-MM-DD."
        )

    if bledy:
        st.error("❌ Znaleziono błędy w danych:")
        for b in bledy:
            st.markdown(f"• {b}")
        st.stop()

    # ─────────────────────────────────────────────────────────
    # PODGLĄD DANYCH
    # Pokazujemy użytkownikowi co zostanie zaimportowane
    # zanim faktycznie zapiszemy do bazy
    # ─────────────────────────────────────────────────────────

    st.markdown("---")
    st.markdown("### Podgląd danych")
    st.markdown(f"Zostanie zaimportowanych **{len(df_raw)}** wierszy:")

    st.dataframe(
        df_raw[["plec", "rok_urodzenia", "data_badania"] + kolumny_parametry],
        use_container_width=True,
        hide_index=True,
        height=250,
    )

    # ─────────────────────────────────────────────────────────
    # PRZYCISK IMPORTU
    # st.button() zwraca True tylko w momencie kliknięcia
    # use_container_width=True — przycisk zajmuje całą szerokość
    # ─────────────────────────────────────────────────────────

    st.markdown("---")

    if st.button(
        "💾 Importuj dane do bazy",
        type="primary",
        use_container_width=True,
    ):
        # --- ZAPIS DO BAZY ---
        # Używamy Session z SQLAlchemy — to "transakcja":
        # albo wszystko się zapisze, albo nic (przy błędzie rollback)
        #
        # Dla każdego wiersza pliku:
        # 1. Tworzymy nowego Pacjenta (każdy wiersz = nowy pacjent)
        # 2. Tworzymy Badanie powiązane z pacjentem
        # 3. Dla każdego parametru tworzymy Wynik

        licznik_pacjentow = 0
        licznik_wynikow   = 0
        bledy_zapisu      = []

        # st.progress() — pasek postępu (0.0 do 1.0)
        pasek = st.progress(0, text="Importowanie danych...")

        try:
            with Session(ENGINE) as session:
                for i, row in df_raw.iterrows():
                    try:
                        # Krok 1 — nowy pacjent
                        pacjent = Pacjent(
                            plec=row["plec"],
                            rok_urodzenia=int(row["rok_urodzenia"]),
                        )
                        session.add(pacjent)
                        session.flush()   # flush przypisuje id bez commit —
                                          # potrzebujemy pacjent.id do badania

                        # Krok 2 — badanie
                        badanie = Badanie(
                            id_pacjenta=pacjent.id,
                            data_badania=row["data_badania"].date(),
                        )
                        session.add(badanie)
                        session.flush()   # potrzebujemy badanie.id do wyników

                        # Krok 3 — wyniki dla każdego parametru
                        for nazwa_param in kolumny_parametry:
                            wartosc = row[nazwa_param]

                            # Pomijamy puste komórki (NaN)
                            if pd.isna(wartosc):
                                continue

                            id_param = get_id_parametru(nazwa_param)
                            if id_param is None:
                                continue

                            wynik = Wynik(
                                id_badania=badanie.id,
                                id_parametru=id_param,
                                wartosc=float(wartosc),
                            )
                            session.add(wynik)
                            licznik_wynikow += 1

                        licznik_pacjentow += 1

                    except Exception as e:
                        bledy_zapisu.append(f"Wiersz {i + 2}: {e}")

                    # Aktualizujemy pasek postępu
                    pasek.progress(
                        (i + 1) / len(df_raw),
                        text=f"Importowanie... {i + 1}/{len(df_raw)}",
                    )

                # commit — zapisuje wszystko do bazy na raz
                session.commit()

        except Exception as e:
            st.error(f"❌ Błąd podczas zapisu do bazy: {e}")
            st.stop()

        # --- PODSUMOWANIE ---
        pasek.empty()   # ukrywamy pasek postępu po zakończeniu

        if bledy_zapisu:
            st.warning(f"⚠️ Wystąpiły błędy w {len(bledy_zapisu)} wierszach:")
            for b in bledy_zapisu:
                st.markdown(f"• {b}")

        st.markdown(f"""
        <div class="result-box">
            <h3 style="margin:0 0 0.5rem 0; color:#166534;">✅ Import zakończony!</h3>
            <p style="margin:0; color:#15803d;">
                Zaimportowano <b>{licznik_pacjentow}</b> pacjentów
                i <b>{licznik_wynikow}</b> wyników badań.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Odświeżamy cache Streamlit żeby nowe dane były widoczne
        # na innych stronach aplikacji
        st.cache_data.clear()

# ─────────────────────────────────────────────────────────────
# SEKCJA DOLNA — stan bazy po imporcie
# ─────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown("### Stan bazy danych")

df_pacjenci = get_wszyscy_pacjenci()
st.markdown(f"Aktualnie w bazie: **{len(df_pacjenci)}** pacjentów")
st.dataframe(
    df_pacjenci.rename(columns={
        "id":               "ID",
        "plec":             "Płeć",
        "rok_urodzenia":    "Rok ur.",
        "liczba_badan":     "Badania",
        "pierwsze_badanie": "Pierwsze",
        "ostatnie_badanie": "Ostatnie",
    }),
    use_container_width=True,
    hide_index=True,
    height=220,
)
