import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Monitoring Pemagangan AI", layout="wide")

# =========================
# Judul Aplikasi
# =========================
st.title("Sistem Digital Monitoring Pemagangan Mahasiswa")
st.subheader("Prototype berbasis AI untuk monitoring pemagangan")

st.write("""
Aplikasi ini digunakan untuk:
- mencatat logbook pemagangan mahasiswa
- memantau progres mahasiswa
- membantu manajemen melihat kondisi mahasiswa
- menyiapkan fitur AI early warning
""")

# =========================
# Load Data Mahasiswa
# =========================
mahasiswa_path = "data/mahasiswa.csv"
logbook_path = "data/logbook.csv"

if os.path.exists(mahasiswa_path):
    df_mahasiswa = pd.read_csv(mahasiswa_path)
else:
    df_mahasiswa = pd.DataFrame(columns=["nama", "nim", "divisi", "pembimbing", "status"])

if os.path.exists(logbook_path):
    df_logbook = pd.read_csv(logbook_path)
else:
    df_logbook = pd.DataFrame(columns=["nama", "tanggal", "kegiatan", "progres", "kendala", "kehadiran"])

# =========================
# Form Input Logbook
# =========================
st.header("Form Input Logbook Pemagangan")

with st.form("form_logbook"):
    nama = st.selectbox("Nama Mahasiswa", df_mahasiswa["nama"].tolist() if not df_mahasiswa.empty else [])
    tanggal = st.date_input("Tanggal", value=date.today())
    kegiatan = st.text_area("Kegiatan yang dilakukan")
    progres = st.number_input("Progres Pekerjaan (%)", min_value=0, max_value=100, step=1)
    kendala = st.text_area("Kendala")
    kehadiran = st.selectbox("Kehadiran", ["Hadir", "Izin", "Sakit", "Alpha"])

    submit = st.form_submit_button("Simpan Logbook")

    if submit:
        if nama and kegiatan.strip() != "":
            data_baru = {
                "nama": nama,
                "tanggal": str(tanggal),
                "kegiatan": kegiatan,
                "progres": progres,
                "kendala": kendala,
                "kehadiran": kehadiran
            }

            df_baru = pd.DataFrame([data_baru])
            df_logbook = pd.concat([df_logbook, df_baru], ignore_index=True)
            df_logbook.to_csv(logbook_path, index=False)

            st.success("Logbook berhasil disimpan!")
        else:
            st.warning("Nama dan kegiatan harus diisi.")

# =========================
# Tampilkan Data Mahasiswa
# =========================
st.header("Data Mahasiswa")
st.dataframe(df_mahasiswa, use_container_width=True)

# =========================
# Tampilkan Data Logbook
# =========================
st.header("Data Logbook")
st.dataframe(df_logbook, use_container_width=True)