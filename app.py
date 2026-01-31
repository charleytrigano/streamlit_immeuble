


import os
import sys
import streamlit as st

st.write("📂 CWD =", os.getcwd())
st.write("📁 FICHIERS =", os.listdir("."))
st.write("🐍 sys.path =", sys.path)




st.write("📁 Contenu du dossier courant :")
st.write(os.listdir("."))

st.stop()