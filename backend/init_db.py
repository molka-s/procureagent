"""Script d'initialisation des tables et données de la base PostgreSQL."""
import sys
from pathlib import Path

# Assure que le dossier backend est dans sys.path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.db import executer_script_sql, engine, text


def main():
    chemin_sql = backend_dir / "db" / "init.sql"
    print(f"--> Connexion a la base de donnees ({engine.url.render_as_string(hide_password=True)})...")
    print(f"--> Execution du script SQL : {chemin_sql}")
    executer_script_sql(str(chemin_sql))

    with engine.connect() as conn:
        res = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        ).fetchall()
        tables = [r[0] for r in res]
        print(f"[OK] {len(tables)} tables initialisees avec succes : {', '.join(tables)}")


if __name__ == "__main__":
    main()
