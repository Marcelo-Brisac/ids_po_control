import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST     = os.getenv("CASHFLOW_DB_HOST",     "186.195.54.70")
DB_PORT     = os.getenv("CASHFLOW_DB_PORT",     "20000")
DB_NAME     = os.getenv("CASHFLOW_DB_NAME",     "sienge")
DB_USER     = os.getenv("CASHFLOW_DB_USER",     "cashflow_app")
DB_PASSWORD = os.getenv("CASHFLOW_DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
