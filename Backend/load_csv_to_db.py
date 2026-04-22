"""
Script to load house_prices.csv into the PostgreSQL database.
Creates a 'house_prices' table and inserts all rows from the CSV.
"""

import pandas as pd
from sqlalchemy import create_engine

# Database connection settings (from docker/postgres.yml)
DB_NAME = "hpa"
DB_USER = "hpa"
DB_PASSWORD = "hpa"
DB_HOST = "localhost"
DB_PORT = "5432"

CSV_PATH = r"..\house_prices.csv"
TABLE_NAME = "house_prices"

def main():
    # Read CSV
    print(f"Reading CSV from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {list(df.columns)}")

    # Create SQLAlchemy engine
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Test connection
    with engine.connect() as conn:
        print("Connected to PostgreSQL successfully!")

    # Insert data into table (replace if it already exists)
    print(f"Inserting data into '{TABLE_NAME}' table...")
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    print(f"Successfully inserted {len(df)} rows into '{TABLE_NAME}' table!")

    # Verify
    result_df = pd.read_sql(f"SELECT COUNT(*) as count FROM {TABLE_NAME}", engine)
    print(f"Verification: {result_df['count'].iloc[0]} rows in table")

    engine.dispose()

if __name__ == "__main__":
    main()
