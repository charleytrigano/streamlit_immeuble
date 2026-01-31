import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from supabase_client import get_supabase_client

st.set_page_config(page_title="Immeuble pilotage", layout="wide")

st.title("Test import utils")

supabase = get_supabase_client()
st.success("✅ Import utils + Supabase OK")