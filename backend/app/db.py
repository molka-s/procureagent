"""Module d'accès et session à la base de données relationnelle."""
from contextlib import contextmanager
from app.config import settings

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import declarative_base, sessionmaker
    HAS_SQLALCHEMY = True
    engine = create_engine(
        settings.database_url,
        echo=False,
        pool_pre_ping=True
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
except ImportError:
    HAS_SQLALCHEMY = False
    engine = None
    SessionLocal = None
    Base = None
    def text(q): return q


@contextmanager
def get_db_session():
    """Fournit une session SQLAlchemy avec rollback automatique en cas d'exception."""
    if not HAS_SQLALCHEMY or SessionLocal is None:
        raise RuntimeError("SQLAlchemy n'est pas encore installé dans l'environnement Python.")
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def executer_script_sql(chemin_sql: str) -> None:
    """Exécute un fichier SQL brut (ex: db/init.sql) pour initialiser ou réinitialiser la base."""
    if not HAS_SQLALCHEMY or engine is None:
        raise RuntimeError("SQLAlchemy requis pour exécuter le script SQL.")

    with open(chemin_sql, "r", encoding="utf-8") as f:
        requetes = f.read()

    with engine.begin() as conn:
        for requete in requetes.split(";"):
            req_clean = requete.strip()
            if req_clean:
                conn.execute(text(req_clean))
