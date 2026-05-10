import streamlit as st
import requests
import pandas as pd
from io import StringIO
import re
from fpdf import FPDF
from streamlit_google_auth import Authenticate

# --- 1. CONFIG & GOOGLE AUTH SETUP ---
st.set_page_config(page_title="SO Manager Pro", layout="centered", page_icon="📊")

# Kredensial Google
CLIENT_ID = "477750756502-1jlnusbeg1npj148a4gk33gdrgp5goap.apps.googleusercontent.com"
CLIENT_SECRET = "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"
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# Inisialisasi dengan parameter TERBARU (Menghindari TypeError)
auth = Authenticate(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    cookie_name="so_auth_status",
    cookie_key="secret_key_so_manager",
    redirect_uri="https://bvyehrqyum27v2qknkhtvy.streamlit.app"
)

# Jalankan pengecekan login
auth.check_authentification()

# --- 2. LOGIKA GERBANG LOGIN ---
if not st.session_state.get('connected'):
    st.title("🔐 Akses Terbatas Staff")
    st.markdown("---")
    st.warning("Silakan login menggunakan akun Google terdaftar untuk melanjutkan.")
    auth.login()
    st.stop()
else:
    user_email = st.session_state.get('user_info', {}).get('email')
    
    # Validasi Daftar Putih Email
    if user_email not in AUTHORIZED_EMAILS:
        st.error(f"Akses Ditolak! Email {user_email} tidak memiliki izin.")
        if st.sidebar.button("Keluar / Logout"):
            auth.logout()
        st.stop()

    # Tampilan Sidebar jika berhasil masuk
    st.sidebar.success(f"Login Berhasil")
    st.sidebar.write(f"📧 **{user_email}**")
    if st.sidebar.button("Logout"):
        auth.logout()

# --- 3. FUNGSI PENGOLAH DATA & PDF ---
def clean_to_float(x):
    if pd.isna(x) or str(x).strip() == "": return 0.0
    clean_val = re.sub(r'[^\d.-]', '', str(x))
    try: return float(clean_val)
    except: return 0.0

def format_ribuan(nilai):
    return "{:,.0f}".format(nilai).replace(",", ".")

def generate_pdf(df, id_toko, tgl_so, col_rack, col_nama, col_selisih, col_plu):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Courier", "B", 14)
    pdf.cell(0, 10, f"LAPORAN SELISIH SO - TOKO {id_toko}", ln=True, align='C')
    pdf.set_font("Courier", "B", 10)
    pdf.cell(0, 7, f"TANGGAL: {tgl_so} | DICETAK: {user_email}", ln=True, align='C')
    pdf.cell(0, 5, "="*60, ln=True, align='C')
    
    # Header Tabel
    pdf.set_font("Courier", "B", 9)
    pdf.cell(25, 8, "PLU", 1, 0, 'C')
    pdf.cell(20, 8, "RAK", 1, 0, 'C')
    pdf.cell(100, 8, "NAMA BARANG", 1, 0, 'L')
    pdf.cell(25, 8, "NOMINAL", 1, 0, 'R')
    pdf.cell(20, 8, "CEK", 1, 1, 'C')

    # Isi Tabel
    pdf.set_font("Courier", "", 9)
    for _, row in df.iterrows():
        pdf.cell(25, 7, str(row[col_plu]), 1, 0, 'C')
        pdf.cell(20, 7, str(row[col_rack])[:6], 1, 0, 'C')
        pdf.cell(100, 7, str(row[col_nama])[:45], 1, 0, 'L')
        pdf.cell(25, 7, format_ribuan(row[col_selisih]), 1, 0, 'R')
        pdf.cell(20, 7, "[  ]", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- 4. TAMPILAN UTAMA DASHBOARD ---
st.title("📊 SO Manager Dashboard")
st.info("Masukkan detail toko untuk menarik data selisih Stock Opname.")

col1, col2 = st.columns(2)
with col1:
    id_toko = st.text_input("🏠 ID Toko (Contoh: T777)", placeholder="Masukkan kode toko...").upper()
with col2:
    tgl_so = st.text_input("📅 Tanggal (DD-MM-YYYY)", placeholder="Contoh: 11-05-2026")

if st.button("🚀 TARIK DATA SELISIH", use_container_width=True):
    if not id_toko or not tgl_so:
        st.warning("Mohon isi ID Toko dan Tanggal terlebih dahulu.")
    else:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            with st.spinner('Menghubungkan ke server Alfastore...'):
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                if res.status_code == 200:
                    df_list = pd.read_html(StringIO(res.text))
                    df = max(df_list, key=len)
                    
                    # Pembersihan Header
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = [c[-1] if 'Unnamed' not in str(c[-1]) else c[0] for c in df.columns]
                    df.columns = [str(c).strip().upper() for c in df.columns]

                    # Identifikasi Kolom
                    col_plu = next((c for c in df.columns if 'PLU' in c), None)
                    col_nama = next((c for c in df.columns if 'NAMA' in c), None)
                    col_rack = next((c for c in df.columns if 'RACK' in c or 'RAK' in c), None)
                    col_selisih = next((c for c in df.columns if 'SELISIH' in c or 'NOMINAL' in c), None)

                    # Filter Selisih
                    df[col_selisih] = df[col_selisih].apply(clean_to_float)
                    df_filtered = df[df[col_selisih] != 0].sort_values(by=[col_rack, col_nama])

                    if not df_filtered.empty:
                        st.success(f"Berhasil menarik {len(df_filtered)} item selisih.")
                        st.dataframe(df_filtered, use_container_width=True)
                        
                        # Tombol Cetak
                        pdf_bytes = generate_pdf(df_filtered, id_toko, tgl_so, col_rack, col_nama, col_selisih, col_plu)
                        st.download_button(
                            label="🖨️ DOWNLOAD HASIL (PDF)",
                            data=pdf_bytes,
                            file_name=f"SO_{id_toko}_{tgl_so}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    else:
                        st.balloons()
                        st.info("Luar biasa! Tidak ditemukan selisih pada data ini.")
                else:
                    st.error("Gagal terhubung ke server. Cek kembali ID Toko atau Tanggal.")
        except Exception as e:
            st.error(f"Terjadi kesalahan teknis: {e}")