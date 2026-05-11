import streamlit as st
import requests
import pandas as pd
from io import StringIO
from streamlit_google_auth import Authenticate

# --- 1. CONFIG ---
st.set_page_config(page_title="SO Manager Pro", layout="centered")

CLIENT_ID = "477750756502-1jlnusbeg1npj148a4gk33gdrgp5goap.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "https://bvyehrqyum27v2qknkhtvy.streamlit.app"
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# --- 2. INITIALIZATION (Hanya Parameter Paling Dasar) ---
try:
    # Kita coba format yang paling standar untuk versi 1.1.x
    auth = Authenticate(
        secret_id=CLIENT_ID,
        secret_password=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cookie_name="so_auth",
        key="so_key"
    )
except TypeError:
    # Jika gagal, coba format alternatif tanpa 'key'
    auth = Authenticate(
        secret_id=CLIENT_ID,
        secret_password=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        cookie_name="so_auth"
    )

auth.check_authentification()

# --- 3. LOGIN LOGIC ---
if not st.session_state.get('connected'):
    st.title("🔐 Login Staff")
    auth.login()
    st.stop()
else:
    user_email = st.session_state.get('user_info', {}).get('email')
    if user_email not in AUTHORIZED_EMAILS:
        st.error("Akses Ditolak")
        st.stop()
    
    st.sidebar.success(f"User: {user_email}")
    if st.sidebar.button("Logout"):
        auth.logout()

# --- 4. DATA LOGIC ---
st.title("📊 SO Dashboard")
id_toko = st.text_input("🏠 ID Toko").upper()
tgl_so = st.text_input("📅 Tanggal (DD-MM-YYYY)")

if st.button("🚀 TARIK DATA"):
    if id_toko and tgl_so:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            df = pd.read_html(StringIO(res.text))[0]
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")