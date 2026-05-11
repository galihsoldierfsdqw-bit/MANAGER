import streamlit as st
import requests
import pandas as pd
from io import StringIO
from streamlit_google_auth import Authenticate
import inspect

# --- 1. CONFIG ---
st.set_page_config(page_title="SO Manager Pro", layout="centered")

CLIENT_ID = "477750756502-1jlnusbeg1npj148a4gk33gdrgp5goap.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "https://bvyehrqyum27v2qknkhtvy.streamlit.app"
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# --- 2. DYNAMIC INITIALIZATION (ANTI-ERROR) ---
# Kode ini mengecek langsung ke dalam library parameter apa yang diminta
sig = inspect.signature(Authenticate.__init__)
params = sig.parameters.keys()

auth_kwargs = {}

# Cek apakah pakai client_id atau secret_id atau build_id
if 'client_id' in params:
    auth_kwargs['client_id'] = CLIENT_ID
    auth_kwargs['client_secret'] = CLIENT_SECRET
elif 'secret_id' in params:
    auth_kwargs['secret_id'] = CLIENT_ID
    auth_kwargs['secret_password'] = CLIENT_SECRET
elif 'build_id' in params:
    auth_kwargs['build_id'] = CLIENT_ID
    auth_kwargs['build_password'] = CLIENT_SECRET

# Cek cookie key
if 'cookie_key' in params: auth_kwargs['cookie_key'] = "secret_key_123"
elif 'key' in params: auth_kwargs['key'] = "secret_key_123"

# Cek redirect uri
if 'redirect_uri' in params: auth_kwargs['redirect_uri'] = REDIRECT_URI
elif 'urls' in params: auth_kwargs['urls'] = [REDIRECT_URI]

auth_kwargs['cookie_name'] = "so_manager_auth"

# Inisialisasi otomatis
auth = Authenticate(**auth_kwargs)
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
id_toko = st.text_input("ID Toko").upper()
tgl_so = st.text_input("Tanggal (DD-MM-YYYY)")

if st.button("TARIK DATA"):
    if id_toko and tgl_so:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            df = pd.read_html(StringIO(res.text))[0]
            st.dataframe(df)
        except Exception as e:
            st.error(f"Error: {e}")