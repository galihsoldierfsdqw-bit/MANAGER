import streamlit as st
import requests
import pandas as pd
from io import StringIO
import re
from fpdf import FPDF
from streamlit_google_auth import Authenticate

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SO Manager Pro", layout="centered", page_icon="📊")

# --- 2. AUTH SETUP (ANTI-ERROR SYSTEM) ---
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# Data Kredensial Baru Kamu
C_ID = "165764912623-cm8a144tj1motalk0uu4o4nbrrohfa1i.apps.googleusercontent.com"
C_SECRET = "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"
R_URI = "https://bvyehrqyum27v2qknkhtvy.streamlit.app"

auth = None

# Percobaan Otomatis agar tidak kena TypeError
try:
    # Cara 1: Menggunakan Posisi (Urutan) - Sering berhasil di versi 1.1.8
    auth = Authenticate(
        'client_secrets.json',
        "so_manager_session",
        "kunci_rahasia_so_123",
        1
    )
except:
    try:
        # Cara 2: Menggunakan Nama Parameter Standar
        auth = Authenticate(
            client_id=C_ID,
            client_secret=C_SECRET,
            redirect_uri=R_URI,
            cookie_name="so_manager_session",
            key="kunci_rahasia_so_123",
            cookie_expiry_days=1
        )
    except Exception as e:
        st.error(f"Sistem Gagal Memuat Modul Auth: {e}")
        st.stop()

# Jalankan pengecekan status login
if auth:
    auth.check_authentification()

# --- 3. LOGIKA GERBANG LOGIN ---
if not st.session_state.get('connected'):
    st.title("🔐 Akses Staff SOPRO")
    st.markdown("---")
    st.info("Silakan login dengan akun Google Anda.")
    # Tombol Login
    auth.login()
    st.stop()
else:
    user_info = st.session_state.get('user_info', {})
    user_email = user_info.get('email')

    # Validasi Daftar Putih
    if user_email not in AUTHORIZED_EMAILS:
        st.error(f"Akses Ditolak! Email {user_email} tidak terdaftar di sistem.")
        if st.sidebar.button("Keluar / Logout"):
            auth.logout()
        st.stop()

    # Sidebar Dashboard
    st.sidebar.success(f"Login Berhasil")
    st.sidebar.write(f"📧 **{user_email}**")
    if st.sidebar.button("Logout"):
        auth.logout()

# --- 4. FUNGSI PENGOLAH DATA ---
def clean_to_float(x):
    if pd.isna(x) or str(x).strip() == "": return 0.0
    clean_val = re.sub(r'[^\d.-]', '', str(x))
    try: return float(clean_val)
    except: return 0.0

# --- 5. TAMPILAN UTAMA DASHBOARD ---
st.title("📊 SO Dashboard Manager")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    id_toko = st.text_input("🏠 ID Toko", placeholder="Contoh: T777").upper()
with col2:
    tgl_so = st.text_input("📅 Tanggal", placeholder="DD-MM-YYYY")

if st.button("🚀 TARIK DATA SELISIH", use_container_width=True):
    if not id_toko or not tgl_so:
        st.warning("Isi ID Toko dan Tanggal dulu ya.")
    else:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            with st.spinner('Menarik data dari Alfastore...'):
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                df_list = pd.read_html(StringIO(res.text))
                df = max(df_list, key=len)
                
                # Bersihkan Header
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[-1] if 'Unnamed' not in str(c[-1]) else c[0] for c in df.columns]
                
                # Filter data selisih
                last_col = df.columns[-1]
                df[last_col] = df[last_col].apply(clean_to_float)
                df_filtered = df[df[last_col] != 0]

                if not df_filtered.empty:
                    st.success(f"Ditemukan {len(df_filtered)} item selisih.")
                    st.dataframe(df_filtered, use_container_width=True)
                else:
                    st.info("Tidak ada data selisih (Data Aman).")
        except Exception as e:
            st.error(f"Gagal mengambil data: {e}")
