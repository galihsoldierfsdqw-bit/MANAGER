import streamlit as st
import requests
import pandas as pd
from io import StringIO, BytesIO
import re
from fpdf import FPDF
from datetime import datetime
from streamlit_google_auth import Authenticate

# --- 1. CONFIG & GOOGLE AUTH SETUP ---
st.set_page_config(page_title="SO Manager Pro - Google Auth", layout="centered")

# Kredensial Google Console Anda
CLIENT_ID = "477750756502-1jlnusbeg1npj148a4gk33gdrgp5goap.apps.googleusercontent.com"
CLIENT_SECRET = "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"

# Daftar email yang diizinkan
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# Inisialisasi Google Auth dengan parameter terbaru
auth = Authenticate(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    cookie_name="so_manager_auth",
    cookie_key="secret_key_so_manager", 
    redirect_uri="https://bvyehrqyum27v2qknkhtvy.streamlit.app"
)

# Jalankan pengecekan autentikasi
auth.check_authentification()

# --- 2. LOGIKA LOGIN ---
if not st.session_state.get('connected'):
    st.title("🔐 Akses Terbatas Staff")
    st.info("Silakan login menggunakan akun Google yang terdaftar untuk mengakses data SO.")
    auth.login()
    st.stop()
else:
    user_email = st.session_state.get('user_info', {}).get('email')
    
    # Cek apakah email terdaftar di daftar izin
    if user_email not in AUTHORIZED_EMAILS:
        st.error(f"Maaf, email {user_email} tidak memiliki izin akses.")
        if st.sidebar.button("Logout"):
            auth.logout()
        st.stop()

    # Jika berhasil login, tampilkan info di sidebar
    st.sidebar.write(f"Logged in: **{user_email}**")
    if st.sidebar.button("Logout"):
        auth.logout()

# --- 3. HELPER FUNCTIONS ---
def clean_to_float(x):
    if pd.isna(x) or str(x).strip() == "": return 0.0
    clean_val = re.sub(r'[^\d.-]', '', str(x))
    try: return float(clean_val)
    except: return 0.0

def format_ribuan(nilai):
    return "{:,.0f}".format(nilai).replace(",", ".")

def generate_pdf_portrait(df, id_toko, tgl_so, col_rack, col_nama, col_selisih, col_plu):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Courier", "B", 14)
    pdf.cell(0, 10, f"LAPORAN SELISIH SO - TOKO {id_toko}", ln=True)
    pdf.set_font("Courier", "B", 12)
    pdf.cell(0, 7, f"TANGGAL: {tgl_so}", ln=True)
    pdf.cell(0, 5, "="*55, ln=True)
    
    # Header Tabel
    pdf.set_font("Courier", "B", 11)
    pdf.cell(30, 10, "PLU", 0, 0, 'L')
    pdf.cell(25, 10, "RAK", 0, 0, 'L')
    pdf.cell(85, 10, "NAMA BARANG", 0, 0, 'L')
    pdf.cell(30, 10, "SLSH", 0, 0, 'R')
    pdf.cell(20, 10, " REV", 0, 1, 'L')
    pdf.cell(0, 2, "-"*75, ln=True)

    for _, row in df.iterrows():
        pdf.set_font("Courier", "B", 11)
        y_before = pdf.get_y()
        pdf.cell(30, 9, str(row[col_plu]), 0, 0, 'L')
        pdf.cell(25, 9, str(row[col_rack])[:10], 0, 0, 'L')
        
        x_nama = pdf.get_x()
        pdf.multi_cell(85, 9, str(row[col_nama])[:40], 0, 'L')
        y_after = pdf.get_y()
        
        pdf.set_xy(x_nama + 85, y_before)
        pdf.cell(30, 9, format_ribuan(row[col_selisih]), 0, 0, 'R')
        pdf.cell(20, 9, " [__]", 0, 1, 'R')
        pdf.set_y(y_after)
        pdf.cell(0, 1, "_"*95, ln=True)
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. MAIN DASHBOARD ---
st.title("📊 SO Manager Dashboard")

tab1, tab2 = st.tabs(["🚀 Tarik Data SO", "📜 Histori"])

with tab1:
    col_a, col_b = st.columns(2)
    with col_a: id_toko = st.text_input("ID Toko").upper()
    with col_b: tgl_so = st.text_input("Tanggal (DD-MM-YYYY)")

    if st.button("TAMPILKAN DATA", use_container_width=True):
        if id_toko and tgl_so:
            url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
            try:
                with st.spinner('Menarik data...'):
                    res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                    if res.status_code == 200:
                        df_list = pd.read_html(StringIO(res.text))
                        df = max(df_list, key=len)
                        
                        if isinstance(df.columns, pd.MultiIndex):
                            df.columns = [c[-1] if 'Unnamed' not in str(c[-1]) else c[0] for c in df.columns]
                        df.columns = [str(c).strip().upper() for c in df.columns]

                        col_plu = next((c for c in df.columns if 'PLU' in c), None)
                        col_nama = next((c for c in df.columns if 'NAMA' in c), None)
                        col_rack = next((c for c in df.columns if 'RACK' in c or 'RAK' in c), None)
                        col_selisih = next((c for c in df.columns if 'SELISIH' in c or 'NOMINAL' in c), None)

                        df[col_selisih] = df[col_selisih].apply(clean_to_float)
                        df = df[df[col_selisih] != 0].sort_values(by=[col_rack, col_nama])

                        if not df.empty:
                            st.success(f"Ditemukan {len(df)} item selisih.")
                            st.dataframe(df, use_container_width=True)
                            
                            pdf_bytes = generate_pdf_portrait(df, id_toko, tgl_so, col_rack, col_nama, col_selisih, col_plu)
                            st.download_button("🖨️ CETAK PDF", pdf_bytes, f"SO_{id_toko}.pdf", use_container_width=True)
                        else:
                            st.warning("Tidak ada selisih.")
            except Exception as e:
                st.error(f"Error: {e}")