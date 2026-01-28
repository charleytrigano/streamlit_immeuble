import streamlit as st
from utils.depenses_ui import depenses_ui

def main():
    st.sidebar.title("Navigation")
    depenses_ui(None)

if __name__ == "__main__":
    main()