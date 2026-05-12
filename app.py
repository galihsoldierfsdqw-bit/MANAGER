import streamlit as st
import requests
import pandas as pd
from io import StringIO
import re
from fpdf import FPDF
from streamlit_google_auth import Authenticate

# --- 1. CONFIG ---
st.set_page_config(page_title="SO Manager Pro", layout="centered", page_icon="📊")

# --- 2. AUTH SETUP ---
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# Inisialisasi menggunakan file JSON
# Kita gunakan try-except agar tidak error saat proses build di Streamlit Cloud
try:
    auth = Authenticate(
        secret_id='client_secrets.json',
        cookie_name="so_manager_session",
        key="kunci_rahasia_so_123",
        cookie_expiry_days=1
    )
except Exception as e:
    st.error(f"Gagal inisialisasi Auth: {e}")
    st.stop()

auth.check_authentification()

# --- 3. LOGIN LOGIC ---
if not st.session_state.get('connected'):
    st.title("🔐 Akses Staff SOPRO")
    st.info("Silakan login dengan akun Google Anda.")
    auth.login()
    st.stop()
else:
    user_info = st.session_state.get('user_info', {})
    user_email = user_info.get('email')

    if user_email not in AUTHORIZED_EMAILS:
        st.error(f"Akses Ditolak! Email {user_email} tidak terdaftar.")
        if st.sidebar.button("Logout"):
            auth.logout()
        st.stop()

    st.sidebar.success(f"User: {user_email}")
    if st.sidebar.button("Logout"):
        auth.logout()

# --- 4. DATA LOGIC (API ALFASTORE) ---
st.title("📊 SO Dashboard")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    id_toko = st.text_input("🏠 ID Toko").upper()
with col2:
    tgl_so = st.text_input("📅 Tanggal (DD-MM-YYYY)")

if st.button("🚀 TARIK DATA SELISIH", use_container_width=True):
    if id_toko and tgl_so:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            with st.spinner('Loading...'):
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                df = pd.read_html(StringIO(res.text))[0]
                
                # Pembersihan kolom terakhir (Nominal Selisih)
                last_col = df.columns[-1]
                df[last_col] = df[last_col].apply(lambda x: float(re.sub(r'[^\d.-]', '', str(x))) if pd.notnull(x) else 0.0)
                
                df_filtered = df[df[last_col] != 0]
                
                if not df_filtered.empty:
                    st.dataframe(df_filtered, use_container_width=True)
                else:
                    st.success("Data Aman, tidak ada selisih.")
        except Exception as e:
            st.error(f"Error: {e}")