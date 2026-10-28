import os
import sys
import psycopg
from psycopg import sql

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings


def create_database_if_not_exists(
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "postgres",
    dbname: str = "hisabai_db",
) -> bool:
    print(f"Connecting to PostgreSQL at {host}:{port} as user '{user}'...")
    try:
        # Connect to default maintenance database 'postgres' with autocommit
        conn = psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname="postgres",
            autocommit=True,
        )
        with conn.cursor() as cur:
            # Check if database already exists
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
            exists = cur.fetchone() is not None
            if exists:
                print(f"Database '{dbname}' already exists.")
            else:
                print(f"Creating database '{dbname}'...")
                cur.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(sql.Identifier(dbname)))
                print(f"Database '{dbname}' created successfully.")
        conn.close()
        return True
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return False


def apply_schema(
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "postgres",
    dbname: str = "hisabai_db",
) -> bool:
    schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema.sql")
    if not os.path.exists(schema_path):
        print(f"Schema file not found at {schema_path}")
        return False

    print(f"Applying schema from {schema_path} to database '{dbname}'...")
    try:
        conn = psycopg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
            autocommit=True,
        )
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with conn.cursor() as cur:
            cur.execute(schema_sql)
            # List created tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]
            print(f"Successfully applied schema. Verified tables in public schema ({len(tables)}):")
            for table in tables:
                print(f"  - {table}")

        conn.close()
        return True
    except Exception as e:
        print(f"Error applying schema: {e}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create HisabAI database and apply schema")
    parser.add_argument("--host", default="localhost", help="PostgreSQL host")
    parser.add_argument("--port", type=int, default=5432, help="PostgreSQL port")
    parser.add_argument("--user", default="postgres", help="PostgreSQL user")
    parser.add_argument("--password", default=None, help="PostgreSQL password")
    parser.add_argument("--dbname", default="hisabai_db", help="Target database name")

    args = parser.parse_args()

    # Fallback to env password if not passed
    password = args.password or os.getenv("PGPASSWORD") or os.getenv("POSTGRES_PASSWORD") or "postgres"

    success = create_database_if_not_exists(
        host=args.host,
        port=args.port,
        user=args.user,
        password=password,
        dbname=args.dbname,
    )

    if success:
        apply_schema(
            host=args.host,
            port=args.port,
            user=args.user,
            password=password,
            dbname=args.dbname,
        )
