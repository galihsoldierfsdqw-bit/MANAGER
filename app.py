import streamlit as st
import requests
import pandas as pd
from io import StringIO
import re

# --- 1. CONFIG & DATABASE USER ---
st.set_page_config(page_title="SO Manager Pro", layout="centered", page_icon="🔐")

# DAFTAR USER YANG DIIZINKAN (Hanya 2 Orang)
# Ganti username dan password di bawah ini sesuai keinginanmu
USER_DB = {
    "galih_admin": "password_galih_123",
    "staff_khusus": "password_staff_456"
}

# --- 2. LOGIKA LOGIN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
    st.session_state['user_now'] = ""

def login_screen():
    st.title("🛡️ Akses Terbatas SOPRO")
    st.write("Silakan masukkan akun resmi untuk melanjutkan.")
    st.markdown("---")
    
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login Sekarang", use_container_width=True):
        if user_input in USER_DB and USER_DB[user_input] == pass_input:
            st.session_state['authenticated'] = True
            st.session_state['user_now'] = user_input
            st.success(f"Selamat datang, {user_input}!")
            st.rerun()
        else:
            st.error("Username atau Password salah!")

# --- 3. CEK STATUS LOGIN ---
if not st.session_state['authenticated']:
    login_screen()
    st.stop()

# --- 4. TAMPILAN DASHBOARD (Hanya muncul jika login berhasil) ---
st.sidebar.title("👤 Profil")
st.sidebar.write(f"User: **{st.session_state['user_now']}**")
if st.sidebar.button("Keluar Sistem"):
    st.session_state['authenticated'] = False
    st.session_state['user_now'] = ""
    st.rerun()

st.title("📊 SO Dashboard Manager")
st.markdown("---")

# Input Dashboard
col1, col2 = st.columns(2)
with col1:
    id_toko = st.text_input("🏠 ID Toko", placeholder="Txxx").upper()
with col2:
    tgl_so = st.text_input("📅 Tanggal", placeholder="DD-MM-YYYY")

# Tombol Tarik Data
if st.button("🚀 TARIK DATA SELISIH", use_container_width=True):
    if not id_toko or not tgl_so:
        st.warning("Data belum lengkap.")
    else:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            with st.spinner('Menarik data...'):
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                if "Table" in res.text:
                    df_list = pd.read_html(StringIO(res.text))
                    df = max(df_list, key=len)
                    
                    # Clean columns
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [c[-1] if 'Unnamed' not in str(c[-1]) else c[0] for c in df.columns]
                    
                    last_col = df.columns[-1]
                    df[last_col] = df[last_col].apply(lambda x: float(re.sub(r'[^\d.-]', '', str(x))) if pd.notnull(x) else 0.0)
                    df_filtered = df[df[last_col] != 0]

                    if not df_filtered.empty:
                        st.dataframe(df_filtered, use_container_width=True)
                    else:
                        st.info("Data SO Aman.")
                else:
                    st.error("Data tidak ditemukan.")
        except Exception as e:
            st.error(f"Koneksi Gagal: {e}")
