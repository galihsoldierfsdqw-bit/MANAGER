import streamlit as st
import requests
import pandas as pd
from io import StringIO
import re
from fpdf import FPDF

# --- 1. SIMPLE LOGIN SYSTEM ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "staff123": # GANTI PASSWORD DISINI
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔐 Akses Terbatas")
        st.text_input("Masukkan Password Staff", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password Salah!", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password():
    st.stop()

# --- 2. FUNGSI HELPER ---
def clean_to_float(x):
    if pd.isna(x) or str(x).strip() == "": return 0.0
    clean_val = re.sub(r'[^\d.-]', '', str(x))
    try: return float(clean_val)
    except: return 0.0

def generate_pdf(df, id_toko, tgl_so):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Courier", "B", 14)
    pdf.cell(0, 10, f"LAPORAN SELISIH SO - {id_toko}", ln=True, align='C')
    pdf.set_font("Courier", "", 10)
    pdf.cell(0, 10, f"Tanggal SO: {tgl_so}", ln=True, align='C')
    pdf.cell(0, 5, "-"*50, ln=True, align='C')
    
    for _, row in df.iterrows():
        # Ambil kolom secara dinamis
        txt = f"{row.iloc[0]} | {row.iloc[1]} | {str(row.iloc[2])[:20]} | {row.iloc[-1]}"
        pdf.cell(0, 8, txt.encode('latin-1', 'replace').decode('latin-1'), ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 3. MAIN DASHBOARD ---
st.title("📊 SO Manager Dashboard")
st.sidebar.success("✅ Login Berhasil")
if st.sidebar.button("Log Out"):
    st.session_state["password_correct"] = False
    st.rerun()

col1, col2 = st.columns(2)
with col1:
    id_toko = st.text_input("🏠 ID Toko").upper()
with col2:
    tgl_so = st.text_input("📅 Tanggal (DD-MM-YYYY)")

if st.button("🚀 TARIK DATA SELISIH", use_container_width=True):
    if id_toko and tgl_so:
        url = f"https://app.alfastore.co.id/prd/api/rpt/laporan_so/prosentase_so?storeId={id_toko}&dateSo={tgl_so}"
        try:
            with st.spinner('Menarik data...'):
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                df_list = pd.read_html(StringIO(res.text))
                df = max(df_list, key=len)
                
                # Pembersihan Header
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[-1] if 'Unnamed' not in str(c[-1]) else c[0] for c in df.columns]
                
                # Filter Selisih
                last_col = df.columns[-1]
                df[last_col] = df[last_col].apply(clean_to_float)
                df_filtered = df[df[last_col] != 0]

                if not df_filtered.empty:
                    st.success(f"Ditemukan {len(df_filtered)} item selisih.")
                    st.dataframe(df_filtered, use_container_width=True)
                    
                    pdf_bytes = generate_pdf(df_filtered, id_toko, tgl_so)
                    st.download_button("🖨️ DOWNLOAD PDF", pdf_bytes, f"SO_{id_toko}.pdf", use_container_width=True)
                else:
                    st.info("Tidak ada selisih ditemukan.")
        except Exception as e:
            st.error(f"Gagal menarik data: {e}")