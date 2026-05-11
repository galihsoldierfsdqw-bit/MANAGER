import streamlit as st
import requests
import pandas as pd
from io import StringIO
import re
from fpdf import FPDF
from streamlit_google_auth import Authenticate

# --- 1. CONFIG & GOOGLE AUTH SETUP ---
st.set_page_config(page_title="SO Manager Pro", layout="centered", page_icon="📊")

CLIENT_ID = "477750756502-1jlnusbeg1npj148a4gk33gdrgp5goap.apps.googleusercontent.com"
CLIENT_SECRET = "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"
REDIRECT_URI = "https://bvyehrqyum27v2qknkhtvy.streamlit.app"
AUTHORIZED_EMAILS = ["galihsoldierfsdqw@gmail.com"]

# Inisialisasi KHUSUS VERSI 1.1.8 (Sesuai Log Anda)
auth = Authenticate(
    build_id=CLIENT_ID,              # Di versi 1.1.8 namanya build_id
    build_password=CLIENT_SECRET,    # Di versi 1.1.8 namanya build_password
    cookie_name="so_auth_status",
    key="secret_key_so_manager",
    urls=[REDIRECT_URI]
)

# Jalankan pengecekan login
auth.check_authentification()

# --- 2. LOGIKA LOGIN ---
if not st.session_state.get('connected'):
    st.title("🔐 Akses Terbatas Staff")
    st.warning("Silakan login menggunakan akun Google.")
    auth.login()
    st.stop()
else:
    user_email = st.session_state.get('user_info', {}).get('email')
    if user_email not in AUTHORIZED_EMAILS:
        st.error(f"Email {user_email} tidak terdaftar.")
        if st.sidebar.button("Logout"):
            auth.logout()
        st.stop()
    st.sidebar.success("Login Berhasil")
    st.sidebar.write(f"📧 **{user_email}**")
    if st.sidebar.button("Logout"):
        auth.logout()

# --- 3. FUNGSI PENGOLAH DATA ---
def clean_to_float(x):
    if pd.isna(x) or str(x).strip() == "": return 0.0
    clean_val = re.sub(r'[^\d.-]', '', str(x))
    try: return float(clean_val)
    except: return 0.0

def generate_pdf(df, id_toko, tgl_so, col_rack, col_nama, col_selisih, col_plu):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", "B", 12)
    pdf.cell(0, 10, f"LAPORAN SELISIH SO - {id_toko}", ln=True)
    pdf.set_font("Courier", "", 10)
    for _, row in df.iterrows():
        txt = f"{row[col_plu]} | {row[col_rack][:5]} | {row[col_nama][:20]} | {row[col_selisih]}"
        pdf.cell(0, 8, txt, ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. MAIN DASHBOARD ---
st.title("📊 SO Manager Dashboard")
id_toko = st.text_input("🏠 ID Toko").upper()
tgl_so = st.text_input("📅 Tanggal (DD-MM-YYYY)")

if st.button("🚀 TARIK DATA"):
    if id_toko and tgl_so:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            df_list = pd.read_html(StringIO(res.text))
            df = max(df_list, key=len)
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[-1] if 'Unnamed' not in str(c[-1]) else c[0] for c in df.columns]
            df.columns = [str(c).strip().upper() for c in df.columns]

            c_plu = next(c for c in df.columns if 'PLU' in c)
            c_nama = next(c for c in df.columns if 'NAMA' in c)
            c_rak = next(c for c in df.columns if 'RAK' in c or 'RACK' in c)
            c_slsh = next(c for c in df.columns if 'SELISIH' in c or 'NOMINAL' in c)

            df[c_slsh] = df[c_slsh].apply(clean_to_float)
            df = df[df[c_slsh] != 0].sort_values(by=[c_rak])

            st.dataframe(df, use_container_width=True)
            pdf_bytes = generate_pdf(df, id_toko, tgl_so, c_rak, c_nama, c_slsh, c_plu)
            st.download_button("🖨️ DOWNLOAD PDF", pdf_bytes, f"SO_{id_toko}.pdf")
        except Exception as e:
            st.error(f"Error: {e}")