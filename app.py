import os
import streamlit as st

st.write("📁 Contenu du dossier courant :")
st.write(os.listdir("."))

st.stop()