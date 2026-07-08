"""
MedLabDB — queries.py
Wszystkie funkcje pobierające dane z bazy.
Zwracają DataFrame gotowe do użycia w Streamlit.
"""

import pandas as pd
from sqlalchemy import text
from database import ENGINE


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _query(sql: str, params: dict = {}) -> pd.DataFrame:
    """Pomocnik: wykonuje zapytanie SQL i zwraca DataFrame."""
    with ENGINE.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)


# ─────────────────────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────────────────────

def get_statystyki_ogolne() -> dict:
    """
    Zwraca podstawowe liczby do wyświetlenia na dashboardzie:
    ilu pacjentów, ile badań, ile wyników poza normą.
    """
    df = _query("""
        SELECT
            (SELECT COUNT(*) FROM pacjenci)                             AS liczba_pacjentow,
            (SELECT COUNT(*) FROM badania)                              AS liczba_badan,
            (SELECT COUNT(*) FROM v_wyniki_z_flagami WHERE flaga = 'POZA NORMĄ') AS poza_norma,
            (SELECT COUNT(*) FROM wyniki)                               AS wszystkich_wynikow
    """)
    # Zamieniamy jeden wiersz DataFrame na słownik — wygodniejsze w Streamlit
    return df.iloc[0].to_dict()


def get_ostatnie_badania(limit: int = 10) -> pd.DataFrame:
    """
    Zwraca ostatnie badania posortowane od najnowszego.
    Używane na dashboardzie jako podgląd aktywności.
    """
    return _query("""
        SELECT
            b.id            AS id_badania,
            p.id            AS pacjent_id,
            p.plec,
            p.rok_urodzenia,
            b.data_badania,
            COUNT(w.id)     AS liczba_parametrow
        FROM badania b
        JOIN pacjenci p ON b.id_pacjenta = p.id
        JOIN wyniki w   ON w.id_badania  = b.id
        GROUP BY b.id
        ORDER BY b.data_badania DESC
        LIMIT :limit
    """, {"limit": limit})


def get_rozklad_flag() -> pd.DataFrame:
    """
    Liczy ile wyników jest OK, a ile poza normą — dla wykresu kołowego na dashboardzie.
    """
    return _query("""
        SELECT flaga, COUNT(*) AS liczba
        FROM v_wyniki_z_flagami
        GROUP BY flaga
    """)


# ─────────────────────────────────────────────────────────────
# PACJENCI
# ─────────────────────────────────────────────────────────────

def get_wszyscy_pacjenci() -> pd.DataFrame:
    """
    Lista wszystkich pacjentów z liczbą wykonanych badań.
    Używana na stronie Pacjenci do tabeli przeglądowej.
    """
    return _query("""
        SELECT
            p.id,
            p.plec,
            p.rok_urodzenia,
            COUNT(DISTINCT b.id) AS liczba_badan,
            MIN(b.data_badania)  AS pierwsze_badanie,
            MAX(b.data_badania)  AS ostatnie_badanie
        FROM pacjenci p
        LEFT JOIN badania b ON b.id_pacjenta = p.id
        GROUP BY p.id
        ORDER BY p.id
    """)


def get_karta_pacjenta(pacjent_id: int) -> pd.DataFrame:
    """
    Pobiera wszystkie wyniki danego pacjenta z flagami.
    Zwraca tabelę gotową do wyświetlenia jako karta pacjenta.
    Używa widoku v_wyniki_z_flagami zdefiniowanego w database.py.
    """
    return _query("""
        SELECT
            data_badania,
            parametr,
            ROUND(wartosc, 2)    AS wartosc,
            jednostka,
            ROUND(norma_min, 2)  AS norma_min,
            ROUND(norma_max, 2)  AS norma_max,
            flaga
        FROM v_wyniki_z_flagami
        WHERE pacjent_id = :pid
        ORDER BY data_badania DESC, parametr
    """, {"pid": pacjent_id})


def get_liczba_anomalii_pacjenta(pacjent_id: int) -> pd.DataFrame:
    """
    Dla danego pacjenta: ile razy każdy parametr wypadł poza normą.
    Używane do wykresu słupkowego na karcie pacjenta.
    """
    return _query("""
        SELECT
            parametr,
            COUNT(*) AS poza_norma_count
        FROM v_wyniki_z_flagami
        WHERE pacjent_id = :pid AND flaga = 'POZA NORMĄ'
        GROUP BY parametr
        ORDER BY poza_norma_count DESC
    """, {"pid": pacjent_id})


# ─────────────────────────────────────────────────────────────
# ANALIZA TRENDÓW
# ─────────────────────────────────────────────────────────────

def get_trend_parametru(pacjent_id: int, parametr: str) -> pd.DataFrame:
    """
    Historia wartości konkretnego parametru w czasie dla danego pacjenta.
    Używana do wykresu liniowego trendu — np. jak zmieniała się glukoza przez rok.
    Zwraca też normy, żeby móc narysować poziome linie referencyjne na wykresie.
    """
    return _query("""
        SELECT
            data_badania,
            ROUND(wartosc, 2)    AS wartosc,
            jednostka,
            ROUND(norma_min, 2)  AS norma_min,
            ROUND(norma_max, 2)  AS norma_max,
            flaga
        FROM v_wyniki_z_flagami
        WHERE pacjent_id = :pid AND parametr = :par
        ORDER BY data_badania
    """, {"pid": pacjent_id, "par": parametr})


def get_dostepne_parametry(pacjent_id: int) -> list:
    """
    Zwraca listę parametrów, które kiedykolwiek były zbadane u danego pacjenta.
    Używana do wypełnienia selectboxa wyboru parametru na stronie Analiza.
    """
    df = _query("""
        SELECT DISTINCT parametr
        FROM v_wyniki_z_flagami
        WHERE pacjent_id = :pid
        ORDER BY parametr
    """, {"pid": pacjent_id})
    return df["parametr"].tolist()


def get_porownanie_parametru(parametr: str) -> pd.DataFrame:
    """
    Dla wybranego parametru: średnia wartość u wszystkich pacjentów,
    z podziałem na płeć. Do wykresu porównawczego między pacjentami.
    """
    return _query("""
        SELECT
            pacjent_id,
            plec,
            rok_urodzenia,
            ROUND(AVG(wartosc), 2) AS srednia_wartosc,
            COUNT(*)               AS liczba_pomiarow,
            ROUND(norma_min, 2) AS norma_min,
            ROUND(norma_max, 2) AS norma_max
        FROM v_wyniki_z_flagami
        WHERE parametr = :par
        GROUP BY pacjent_id
        ORDER BY pacjent_id
    """, {"par": parametr})


# ─────────────────────────────────────────────────────────────
# IMPORT CSV
# ─────────────────────────────────────────────────────────────

def get_lista_parametrow() -> list:
    """
    Zwraca nazwy wszystkich parametrów zdefiniowanych w bazie.
    Używana przy walidacji importowanego pliku CSV —
    sprawdzamy czy kolumny w pliku pasują do znanych parametrów.
    """
    df = _query("SELECT nazwa FROM parametry ORDER BY nazwa")
    return df["nazwa"].tolist()


def get_id_parametru(nazwa: str) -> int | None:
    """
    Zwraca id parametru po jego nazwie.
    Potrzebne przy zapisie wyników z CSV do tabeli wyniki.
    """
    df = _query("SELECT id FROM parametry WHERE nazwa = :n", {"n": nazwa})
    return int(df.iloc[0]["id"]) if not df.empty else None


# ─────────────────────────────────────────────────────────────
# PDF
# ─────────────────────────────────────────────────────────────

def get_dane_do_raportu(pacjent_id: int) -> dict:
    """
    Zbiera wszystkie dane potrzebne do wygenerowania raportu PDF:
    - informacje o pacjencie
    - pełna tabela wyników z flagami
    - podsumowanie (ile poza normą, ile badań)
    """
    pacjent_df = _query("""
        SELECT id, plec, rok_urodzenia FROM pacjenci WHERE id = :pid
    """, {"pid": pacjent_id})

    wyniki_df = get_karta_pacjenta(pacjent_id)

    podsumowanie = {
        "liczba_badan":    wyniki_df["data_badania"].nunique(),
        "liczba_wynikow":  len(wyniki_df),
        "poza_norma":      (wyniki_df["flaga"] == "POZA NORMĄ").sum(),
    }

    return {
        "pacjent":      pacjent_df.iloc[0].to_dict() if not pacjent_df.empty else {},
        "wyniki":       wyniki_df,
        "podsumowanie": podsumowanie,
    }
