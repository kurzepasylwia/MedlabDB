"""
MedLabDB — warstwa bazy danych
SQLite + SQLAlchemy ORM
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float,
    Date, ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import declarative_base, relationship, Session
from datetime import date  # używane w danych badań
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "medlabdb.sqlite")
ENGINE = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Base = declarative_base()


# ─────────────────────────────────────────────
# MODELE
# ─────────────────────────────────────────────

class Pacjent(Base):
    __tablename__ = "pacjenci"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    plec           = Column(String(1), nullable=False)   # 'M' / 'K'
    rok_urodzenia  = Column(Integer,   nullable=False)

    badania = relationship("Badanie", back_populates="pacjent", cascade="all, delete")

    __table_args__ = (
        CheckConstraint("plec IN ('M','K')", name="chk_plec"),
    )


class Parametr(Base):
    __tablename__ = "parametry"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    nazwa      = Column(String(50),  nullable=False, unique=True)
    jednostka  = Column(String(20),  nullable=False)
    norma_min_K = Column(Float, nullable=True)   # norma dla kobiet
    norma_max_K = Column(Float, nullable=True)
    norma_min_M = Column(Float, nullable=True)   # norma dla mężczyzn
    norma_max_M = Column(Float, nullable=True)

    wyniki = relationship("Wynik", back_populates="parametr")


class Badanie(Base):
    __tablename__ = "badania"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    id_pacjenta = Column(Integer, ForeignKey("pacjenci.id"), nullable=False)
    data_badania = Column(Date,   nullable=False)

    pacjent = relationship("Pacjent", back_populates="badania")
    wyniki  = relationship("Wynik",   back_populates="badanie", cascade="all, delete")


class Wynik(Base):
    __tablename__ = "wyniki"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    id_badania   = Column(Integer, ForeignKey("badania.id"),   nullable=False)
    id_parametru = Column(Integer, ForeignKey("parametry.id"), nullable=False)
    wartosc      = Column(Float,   nullable=False)

    badanie   = relationship("Badanie",  back_populates="wyniki")
    parametr  = relationship("Parametr", back_populates="wyniki")


# ─────────────────────────────────────────────
# WIDOK SQL
# ─────────────────────────────────────────────

VIEW_SQL = """
CREATE VIEW IF NOT EXISTS v_wyniki_z_flagami AS
SELECT
    p.id            AS pacjent_id,
    p.plec,
    p.rok_urodzenia,
    b.data_badania,
    par.nazwa       AS parametr,
    par.jednostka,
    w.wartosc,
    CASE p.plec
        WHEN 'K' THEN par.norma_min_K
        ELSE par.norma_min_M
    END AS norma_min,
    CASE p.plec
        WHEN 'K' THEN par.norma_max_K
        ELSE par.norma_max_M
    END AS norma_max,
    CASE
        WHEN p.plec = 'K' AND (w.wartosc < par.norma_min_K OR w.wartosc > par.norma_max_K) THEN 'POZA NORMĄ'
        WHEN p.plec = 'M' AND (w.wartosc < par.norma_min_M OR w.wartosc > par.norma_max_M) THEN 'POZA NORMĄ'
        ELSE 'OK'
    END AS flaga
FROM wyniki w
JOIN badania b   ON w.id_badania   = b.id
JOIN pacjenci p  ON b.id_pacjenta  = p.id
JOIN parametry par ON w.id_parametru = par.id;
"""


# ─────────────────────────────────────────────
# INICJALIZACJA I SEED
# ─────────────────────────────────────────────

def init_db():
    """Tworzy tabele i widok, wstawia dane testowe."""
    Base.metadata.create_all(ENGINE)
    with ENGINE.connect() as conn:
        conn.execute(text(VIEW_SQL))
        conn.commit()

    with Session(ENGINE) as s:
        if s.query(Parametr).count() == 0:
            _seed(s)


def _seed(s: Session):
    # --- Parametry biochemiczne ---
    parametry = [
        Parametr(nazwa="Glukoza",      jednostka="mg/dL",  norma_min_K=70, norma_max_K=99,  norma_min_M=70,  norma_max_M=99),
        Parametr(nazwa="Kreatynina",   jednostka="mg/dL",  norma_min_K=0.5, norma_max_K=0.9, norma_min_M=0.7, norma_max_M=1.2),
        Parametr(nazwa="ALT",          jednostka="U/L",    norma_min_K=7,  norma_max_K=35,  norma_min_M=7,   norma_max_M=45),
        Parametr(nazwa="AST",          jednostka="U/L",    norma_min_K=10, norma_max_K=35,  norma_min_M=10,  norma_max_M=40),
        Parametr(nazwa="Bilirubina",   jednostka="mg/dL",  norma_min_K=0.2, norma_max_K=1.2, norma_min_M=0.2, norma_max_M=1.2),
        Parametr(nazwa="Mocznik",      jednostka="mg/dL",  norma_min_K=15, norma_max_K=40,  norma_min_M=15,  norma_max_M=45),
        Parametr(nazwa="Cholesterol",  jednostka="mg/dL",  norma_min_K=0,  norma_max_K=200, norma_min_M=0,   norma_max_M=200),
        Parametr(nazwa="Trójglicerydy",jednostka="mg/dL",  norma_min_K=0,  norma_max_K=150, norma_min_M=0,   norma_max_M=150),
        Parametr(nazwa="Sód",          jednostka="mmol/L", norma_min_K=136, norma_max_K=145, norma_min_M=136, norma_max_M=145),
        Parametr(nazwa="Potas",        jednostka="mmol/L", norma_min_K=3.5, norma_max_K=5.1, norma_min_M=3.5, norma_max_M=5.1),
    ]
    s.add_all(parametry)
    s.flush()

    par = {p.nazwa: p for p in parametry}

    # --- Pacjenci testowi ---
    pacjenci = [
        Pacjent(plec="K", rok_urodzenia=1985),
        Pacjent(plec="M", rok_urodzenia=1972),
        Pacjent(plec="K", rok_urodzenia=1991),
        Pacjent(plec="M", rok_urodzenia=1968),
        Pacjent(plec="K", rok_urodzenia=2000),
    ]
    s.add_all(pacjenci)
    s.flush()

    # --- Badania i wyniki (3 wizyty na pacjenta) ---
    seed_data = [
        # (pacjent_idx, data, {parametr: wartość})
        (0, date(2024, 1, 10), {"Glukoza":95, "Kreatynina":0.7,"ALT":22,"AST":25,"Bilirubina":0.8,"Mocznik":30,"Cholesterol":185,"Trójglicerydy":120,"Sód":140,"Potas":4.2}),
        (0, date(2024, 6,  5), {"Glukoza":102,"Kreatynina":0.8,"ALT":40,"AST":38,"Bilirubina":1.0,"Mocznik":34,"Cholesterol":210,"Trójglicerydy":165,"Sód":139,"Potas":4.5}),
        (0, date(2025, 1, 20), {"Glukoza":110,"Kreatynina":0.9,"ALT":55,"AST":48,"Bilirubina":1.3,"Mocznik":38,"Cholesterol":220,"Trójglicerydy":180,"Sód":138,"Potas":4.8}),

        (1, date(2024, 2, 14), {"Glukoza":88, "Kreatynina":1.0,"ALT":30,"AST":28,"Bilirubina":0.6,"Mocznik":28,"Cholesterol":175,"Trójglicerydy":100,"Sód":142,"Potas":3.9}),
        (1, date(2024, 8, 22), {"Glukoza":105,"Kreatynina":1.1,"ALT":38,"AST":35,"Bilirubina":0.9,"Mocznik":35,"Cholesterol":195,"Trójglicerydy":140,"Sód":141,"Potas":4.1}),
        (1, date(2025, 2,  3), {"Glukoza":130,"Kreatynina":1.3,"ALT":50,"AST":45,"Bilirubina":1.1,"Mocznik":42,"Cholesterol":215,"Trójglicerydy":190,"Sód":143,"Potas":5.3}),

        (2, date(2024, 3,  8), {"Glukoza":78, "Kreatynina":0.6,"ALT":18,"AST":20,"Bilirubina":0.5,"Mocznik":22,"Cholesterol":160,"Trójglicerydy":80, "Sód":137,"Potas":3.7}),
        (2, date(2024, 9, 15), {"Glukoza":82, "Kreatynina":0.7,"ALT":20,"AST":22,"Bilirubina":0.7,"Mocznik":25,"Cholesterol":170,"Trójglicerydy":95, "Sód":138,"Potas":3.8}),
        (2, date(2025, 3,  1), {"Glukoza":85, "Kreatynina":0.6,"ALT":19,"AST":21,"Bilirubina":0.6,"Mocznik":24,"Cholesterol":168,"Trójglicerydy":90, "Sód":139,"Potas":3.9}),

        (3, date(2024, 4, 20), {"Glukoza":99, "Kreatynina":1.2,"ALT":44,"AST":39,"Bilirubina":1.0,"Mocznik":43,"Cholesterol":198,"Trójglicerydy":148,"Sód":140,"Potas":4.0}),
        (3, date(2024, 10,10), {"Glukoza":115,"Kreatynina":1.4,"ALT":60,"AST":55,"Bilirubina":1.4,"Mocznik":50,"Cholesterol":220,"Trójglicerydy":200,"Sód":144,"Potas":5.0}),
        (3, date(2025, 4,  5), {"Glukoza":125,"Kreatynina":1.6,"ALT":75,"AST":68,"Bilirubina":1.8,"Mocznik":58,"Cholesterol":238,"Trójglicerydy":230,"Sód":146,"Potas":5.4}),

        (4, date(2024, 5, 12), {"Glukoza":72, "Kreatynina":0.5,"ALT":12,"AST":15,"Bilirubina":0.4,"Mocznik":18,"Cholesterol":155,"Trójglicerydy":70, "Sód":136,"Potas":3.6}),
        (4, date(2024, 11,28), {"Glukoza":75, "Kreatynina":0.6,"ALT":14,"AST":16,"Bilirubina":0.5,"Mocznik":20,"Cholesterol":158,"Trójglicerydy":75, "Sód":137,"Potas":3.7}),
        (4, date(2025, 5,  8), {"Glukoza":74, "Kreatynina":0.6,"ALT":13,"AST":15,"Bilirubina":0.5,"Mocznik":19,"Cholesterol":157,"Trójglicerydy":72, "Sód":136,"Potas":3.6}),
    ]

    for pac_idx, dt, wartosci in seed_data:
        b = Badanie(id_pacjenta=pacjenci[pac_idx].id, data_badania=dt)
        s.add(b)
        s.flush()
        for nazwa, val in wartosci.items():
            s.add(Wynik(id_badania=b.id, id_parametru=par[nazwa].id, wartosc=val))

    s.commit()
    print("✅ Baza zainicjalizowana — dane testowe wstawione.")


if __name__ == "__main__":
    init_db()
