# filepath: d:\PythonPJ\frontend\app.py
import streamlit as st
from pages import login, register, out  # hoặc import các page mới sau này

def main():
    st.set_page_config(page_title="VAA Attendance", layout="wide")
    # Điều hướng hoặc render các page ở đây

if __name__ == "__main__":
    main()