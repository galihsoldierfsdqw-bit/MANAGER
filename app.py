import streamlit as st
import requests
import pandas as pd
from io import StringIO
import re
from fpdf import FPDF
from streamlit_google_auth import Authenticate

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="SO Manager Pro", layout="centered", page_icon="📊")

# --- 2. SETUP GOOGLE AUTH ---
# Ganti kredensial jika perlu, pastikan REDIRECT_URI sama persis dengan di Google Console
CLIENT_ID = "477750756502-1jlnusbeg1npj148a4gk33gdrgp5goap.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "https://bvyehrqyum27v2qknkhtvy.streamlit.app"
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# Inisialisasi Authenticate (Gunakan nama parameter standar versi stabil)
auth = Authenticate(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    cookie_name="so_manager_session",
    cookie_key="kunci_rahasia_so_123",
    cookie_expiry_days=1
)

# Jalankan pengecekan status login
auth.check_authentification()

# --- 3. LOGIKA LOGIN ---
if not st.session_state.get('connected'):
    st.title("🔐 Akses Terbatas Staff")
    st.markdown("---")
    st.info("Selamat datang di SO Manager Pro. Silakan login dengan akun Google Anda.")
    auth.login() # Menampilkan tombol 'Login with Google'
    st.stop()
else:
    user_info = st.session_state.get('user_info', {})
    user_email = user_info.get('email')

    # Validasi Daftar Putih Email
    if user_email not in AUTHORIZED_EMAILS:
        st.error(f"Akses Ditolak! Email {user_email} tidak terdaftar.")
        if st.sidebar.button("Keluar / Logout"):
            auth.logout()
        st.stop()

    # Tampilan Sidebar jika berhasil masuk
    st.sidebar.success(f"Login Berhasil")
    st.sidebar.write(f"📧 **{user_email}**")
    if st.sidebar.button("Logout"):
        auth.logout()

# --- 4. FUNGSI PENGOLAH DATA & PDF ---
def clean_to_float(x):
    if pd.isna(x) or str(x).strip() == "": return 0.0
    clean_val = re.sub(r'[^\d.-]', '', str(x))
    try: return float(clean_val)
    except: return 0.0

def format_ribuan(nilai):
    return "{:,.0f}".format(nilai).replace(",", ".")

def generate_pdf(df, id_toko, tgl_so):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Courier", "B", 14)
    pdf.cell(0, 10, f"LAPORAN SELISIH SO - TOKO {id_toko}", ln=True, align='C')
    pdf.set_font("Courier", "B", 10)
    pdf.cell(0, 7, f"TANGGAL: {tgl_so}", ln=True, align='C')
    pdf.cell(0, 5, "="*60, ln=True, align='C')
    
    # Header Tabel Sederhana
    pdf.set_font("Courier", "B", 9)
    pdf.cell(30, 8, "PLU", 1, 0, 'C')
    pdf.cell(110, 8, "NAMA BARANG", 1, 0, 'L')
    pdf.cell(30, 8, "NOMINAL", 1, 1, 'R')

    # Isi Tabel
    pdf.set_font("Courier", "", 9)
    for _, row in df.iterrows():
        # Mengambil kolom berdasarkan urutan jika nama kolom berubah-ubah dari API
        plu = str(row.iloc[0])
        nama = str(row.iloc[2])[:40]
        nominal = format_ribuan(row.iloc[-1])
        
        pdf.cell(30, 7, plu, 1, 0, 'C')
        pdf.cell(110, 7, nama, 1, 0, 'L')
        pdf.cell(30, 7, nominal, 1, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 5. TAMPILAN UTAMA DASHBOARD ---
st.title("📊 SO Manager Dashboard")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    id_toko = st.text_input("🏠 ID Toko", placeholder="Contoh: T777").upper()
with col2:
    tgl_so = st.text_input("📅 Tanggal", placeholder="DD-MM-YYYY")

if st.button("🚀 TARIK DATA SELISIH", use_container_width=True):
    if not id_toko or not tgl_so:
        st.warning("Mohon isi ID Toko dan Tanggal.")
    else:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            with st.spinner('Menarik data dari server...'):
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                df_list = pd.read_html(StringIO(res.text))
                df = max(df_list, key=len)
                
                # Pembersihan Header
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[-1] if 'Unnamed' not in str(c[-1]) else c[0] for c in df.columns]
                
                # Identifikasi kolom selisih (biasanya kolom terakhir)
                last_col = df.columns[-1]
                df[last_col] = df[last_col].apply(clean_to_float)
                
                # Filter data yang ada selisihnya saja
                df_filtered = df[df[last_col] != 0]

                if not df_filtered.empty:
                    st.success(f"Ditemukan {len(df_filtered)} item selisih.")
                    st.dataframe(df_filtered, use_container_width=True)
                    
                    pdf_bytes = generate_pdf(df_filtered, id_toko, tgl_so)
                    st.download_button(
                        label="🖨️ DOWNLOAD HASIL PDF",
                        data=pdf_bytes,
                        file_name=f"SO_{id_toko}_{tgl_so}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.info("Tidak ada data selisih (Data Aman).")
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")