# 🧬 MedLabDB

**System zarządzania i analizy wyników badań laboratoryjnych pacjentów**

Projekt zaliczeniowy — kierunek Analityk danych biologiczno-medycznych

---

## Opis projektu

MedLabDB to aplikacja webowa napisana w Pythonie, służąca do przechowywania, zarządzania i analizy wyników badań biochemicznych pacjentów. System umożliwia wczytywanie danych z plików CSV/Excel, porównywanie wyników z normami referencyjnymi z uwzględnieniem płci pacjenta, śledzenie trendów parametrów w czasie oraz generowanie raportów PDF.

Projekt jest zgodny z zasadą minimalizacji danych (RODO art. 5 ust. 1 lit. c) — pacjent identyfikowany jest wyłącznie przez numer ID, płeć i rok urodzenia, bez przechowywania danych osobowych.

---

## Stos technologiczny

| Technologia | Wersja | Zastosowanie |
|---|---|---|
| Python | 3.11+ | język programowania |
| SQLite | wbudowany | relacyjna baza danych |
| SQLAlchemy | 2.x | ORM — połączenie Python ↔ baza |
| Streamlit | najnowsza | interfejs webowy aplikacji |
| Pandas | najnowsza | przetwarzanie danych, DataFrame |
| Plotly | najnowsza | interaktywne wykresy |
| ReportLab | najnowsza | generowanie raportów PDF |
| OpenPyXL | najnowsza | obsługa plików Excel |

---

## Struktura projektu

```
medlabdb/
│
├── database.py            # Definicja bazy danych, modele, dane testowe
├── queries.py             # Funkcje pobierające dane z bazy (warstwa danych)
├── app.py                 # Strona główna — Dashboard
│
├── pages/
│   ├── 1_Pacjenci.py      # Przeglądanie kart pacjentów i wyników
│   ├── 2_Analiza.py       # Wykresy trendów i porównania
│   ├── 3_Import.py        # Import danych z pliku CSV/Excel
│   └── 4_Raport.py        # Generowanie raportów PDF
│
├── fonts/
│   ├── DejaVuSans.ttf     # Czcionka z obsługą polskich znaków (PDF)
│   └── DejaVuSans-Bold.ttf
│
├── medlabdb.sqlite        # Plik bazy danych SQLite (tworzony automatycznie)
├── requirements.txt       # Lista zależności Python
│
└── przykladowe_dane.csv            # Przykładowy plik do importu (5 pacjentów)
    przykladowe_dane_rozszerzone.csv # Większy plik testowy (20 pacjentów)
```

---

## Schemat bazy danych

```
┌─────────────┐       ┌──────────────────────┐
│  pacjenci   │       │      parametry       │
│─────────────│       │──────────────────────│
│ id (PK)     │       │ id (PK)              │
│ plec        │       │ nazwa                │
│ rok_urodz.  │       │ jednostka            │
└──────┬──────┘       │ norma_min_K          │
       │              │ norma_max_K          │
       │ 1:N          │ norma_min_M          │
       ▼              │ norma_max_M          │
┌─────────────┐       └──────────┬───────────┘
│   badania   │                  │
│─────────────│                  │ 1:N
│ id (PK)     │       ┌──────────▼───────────┐
│ id_pacjenta │◄──────│        wyniki        │
│ data_badania│  1:N  │──────────────────────│
└─────────────┘       │ id (PK)              │
                       │ id_badania (FK)      │
                       │ id_parametru (FK)    │
                       │ wartosc              │
                       └──────────────────────┘

VIEW: v_wyniki_z_flagami
→ łączy wszystkie 4 tabele
→ automatycznie oblicza flagę OK / POZA NORMĄ
   (z uwzględnieniem płci pacjenta)
```

---

## Instalacja i uruchomienie

### 1. Sklonuj lub pobierz projekt

```bash
cd ~/Desktop
# rozpakuj folder medlabdb
cd medlabdb
```

### 2. Utwórz i aktywuj wirtualne środowisko

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Zainstaluj zależności

```bash
pip install -r requirements.txt
```

### 4. Zainicjalizuj bazę danych

```bash
python3 database.py
```

Powinnaś zobaczyć:
```
✅ Baza zainicjalizowana — dane testowe wstawione.
```

### 5. Uruchom aplikację

```bash
streamlit run app.py
```

Aplikacja otworzy się automatycznie w przeglądarce pod adresem:
```
http://localhost:8501
```

---

## Format pliku importu (CSV/Excel)

Plik musi zawierać kolumny obowiązkowe oraz dowolną liczbę kolumn z parametrami:

| plec | rok_urodzenia | data_badania | Glukoza | ALT | Kreatynina | ... |
|------|--------------|-------------|---------|-----|-----------|-----|
| K | 1990 | 2024-03-15 | 95.0 | 22.0 | 0.7 | ... |
| M | 1975 | 2024-03-15 | 105.0 | 38.0 | 1.1 | ... |

**Obsługiwane parametry:** Glukoza, Kreatynina, ALT, AST, Bilirubina, Mocznik, Cholesterol, Trójglicerydy, Sód, Potas

---

## Funkcjonalności

- **Dashboard** — przegląd statystyk systemu, rozkład wyników OK/poza normą, ostatnia aktywność
- **Pacjenci** — lista pacjentów, karta pacjenta z kolorowanymi wynikami, wykres anomalii
- **Analiza** — wykres trendu parametru w czasie z pasem normy referencyjnej, statystyki opisowe, porównanie między pacjentami
- **Import** — wczytanie pliku CSV lub Excel z walidacją danych i podglądem przed zapisem
- **Raport PDF** — generowanie karty wyników z kolorowaniem, podsumowaniem i stopką

---

## Autor

Sylwia Kurzępa
