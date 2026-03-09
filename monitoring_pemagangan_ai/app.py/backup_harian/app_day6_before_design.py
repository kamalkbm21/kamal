import streamlit as st
import pandas as pd
import os
from datetime import date

st.set_page_config(page_title="Monitoring Pemagangan AI", layout="wide")

MAHASISWA_PATH = "data/mahasiswa.csv"
LOGBOOK_PATH = "data/logbook.csv"

# =========================
# Fungsi bantu
# =========================
def load_data(path, columns):
    if os.path.exists(path):
        df = pd.read_csv(path)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[columns]
    return pd.DataFrame(columns=columns)

def prepare_logbook(df):
    df_copy = df.copy()
    if not df_copy.empty:
        df_copy["tanggal"] = pd.to_datetime(df_copy["tanggal"], errors="coerce")
        df_copy["progres"] = pd.to_numeric(df_copy["progres"], errors="coerce").fillna(0)
        df_copy["kendala"] = df_copy["kendala"].fillna("").astype(str)
        df_copy["kehadiran"] = df_copy["kehadiran"].fillna("").astype(str)
    return df_copy

def ada_kendala(teks):
    teks = str(teks).strip().lower()
    daftar_tidak_ada_kendala = ["", "-", "tidak ada", "aman", "none", "no"]
    return teks not in daftar_tidak_ada_kendala

def analisis_status_mahasiswa(df_logbook, df_mahasiswa):
    hasil = []

    if df_logbook.empty:
        return pd.DataFrame(columns=[
            "nama", "divisi", "pembimbing", "jumlah_laporan", "rata_progres",
            "jumlah_kendala", "jumlah_alpha", "status_ai", "rekomendasi", "tanggal_terakhir"
        ])

    for nama, grup in df_logbook.groupby("nama"):
        grup = grup.sort_values("tanggal")
        data_terakhir = grup.iloc[-1]

        jumlah_laporan = len(grup)
        rata_progres = round(grup["progres"].mean(), 2)
        jumlah_kendala = int(grup["kendala"].apply(ada_kendala).sum())
        jumlah_alpha = int((grup["kehadiran"] == "Alpha").sum())
        kendala_terakhir = str(data_terakhir["kendala"])
        kehadiran_terakhir = str(data_terakhir["kehadiran"])
        tanggal_terakhir = data_terakhir["tanggal"]

        info_mahasiswa = df_mahasiswa[df_mahasiswa["nama"] == nama]
        if not info_mahasiswa.empty:
            divisi = info_mahasiswa.iloc[0]["divisi"]
            pembimbing = info_mahasiswa.iloc[0]["pembimbing"]
        else:
            divisi = "-"
            pembimbing = "-"

        # =========================
        # Logika AI sederhana
        # =========================
        if jumlah_alpha >= 1 or rata_progres < 40:
            status_ai = "Perlu Evaluasi"
            rekomendasi = "Lakukan evaluasi langsung dengan pembimbing dan tinjau kembali target magang."
        elif jumlah_kendala >= 2 or rata_progres < 70:
            status_ai = "Perlu Perhatian"
            rekomendasi = "Perlu monitoring lebih dekat dan pembinaan pada progres atau kendala mahasiswa."
        else:
            status_ai = "Aman"
            rekomendasi = "Performa stabil. Pertahankan konsistensi pelaporan dan progres kerja."

        # Koreksi berdasarkan kondisi laporan terakhir
        if kehadiran_terakhir == "Alpha":
            status_ai = "Perlu Evaluasi"
            rekomendasi = "Terdapat status Alpha pada laporan terakhir. Segera lakukan evaluasi dengan pembimbing."
        elif ada_kendala(kendala_terakhir) and status_ai == "Aman":
            status_ai = "Perlu Perhatian"
            rekomendasi = "Ada kendala pada laporan terakhir. Perlu tindak lanjut ringan dari pembimbing."

        hasil.append({
            "nama": nama,
            "divisi": divisi,
            "pembimbing": pembimbing,
            "jumlah_laporan": jumlah_laporan,
            "rata_progres": rata_progres,
            "jumlah_kendala": jumlah_kendala,
            "jumlah_alpha": jumlah_alpha,
            "status_ai": status_ai,
            "rekomendasi": rekomendasi,
            "tanggal_terakhir": tanggal_terakhir
        })

    df_hasil = pd.DataFrame(hasil).sort_values(["status_ai", "nama"])
    return df_hasil

# =========================
# Load data
# =========================
df_mahasiswa = load_data(
    MAHASISWA_PATH,
    ["nama", "nim", "divisi", "pembimbing", "status"]
)

df_logbook = load_data(
    LOGBOOK_PATH,
    ["nama", "tanggal", "kegiatan", "progres", "kendala", "kehadiran"]
)

df_logbook_olah = prepare_logbook(df_logbook)

# =========================
# Judul aplikasi
# =========================
st.title("Sistem Digital Monitoring Pemagangan Mahasiswa")
st.subheader("Prototype berbasis AI dengan fitur Early Warning")

st.write("""
Aplikasi ini digunakan untuk:
- mencatat logbook pemagangan mahasiswa
- memantau progres mahasiswa
- membantu manajemen melihat kondisi mahasiswa
- memberikan status otomatis berbasis AI sederhana
""")

# =========================
# Form input logbook
# =========================
st.header("Form Input Logbook Pemagangan")

daftar_nama = df_mahasiswa["nama"].dropna().tolist()

if len(daftar_nama) == 0:
    st.warning("Data mahasiswa belum tersedia. Isi file mahasiswa.csv terlebih dahulu.")
else:
    with st.form("form_logbook", clear_on_submit=True):
        nama = st.selectbox("Nama Mahasiswa", daftar_nama)
        tanggal = st.date_input("Tanggal", value=date.today())
        kegiatan = st.text_area("Kegiatan yang dilakukan")
        progres = st.number_input("Progres Pekerjaan (%)", min_value=0, max_value=100, step=1)
        kendala = st.text_area("Kendala")
        kehadiran = st.selectbox("Kehadiran", ["Hadir", "Izin", "Sakit", "Alpha"])

        submit = st.form_submit_button("Simpan Logbook")

        if submit:
            if kegiatan.strip() == "":
                st.warning("Kegiatan harus diisi.")
            else:
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
                df_logbook.to_csv(LOGBOOK_PATH, index=False)

                st.success("Logbook berhasil disimpan!")

# Refresh data setelah input
df_logbook = load_data(
    LOGBOOK_PATH,
    ["nama", "tanggal", "kegiatan", "progres", "kendala", "kehadiran"]
)
df_logbook_olah = prepare_logbook(df_logbook)

# =========================
# Dashboard umum
# =========================
st.header("Dashboard Monitoring")

total_mahasiswa = len(df_mahasiswa)
total_laporan = len(df_logbook_olah)
rata_progres_umum = round(df_logbook_olah["progres"].mean(), 2) if not df_logbook_olah.empty else 0
jumlah_hadir = int((df_logbook_olah["kehadiran"] == "Hadir").sum()) if not df_logbook_olah.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Mahasiswa", total_mahasiswa)
col2.metric("Total Laporan", total_laporan)
col3.metric("Rata-rata Progres", f"{rata_progres_umum}%")
col4.metric("Jumlah Hadir", jumlah_hadir)

# =========================
# Analisis AI
# =========================
st.header("Analisis AI - Early Warning")

df_ai = analisis_status_mahasiswa(df_logbook_olah, df_mahasiswa)

if not df_ai.empty:
    jumlah_aman = int((df_ai["status_ai"] == "Aman").sum())
    jumlah_perhatian = int((df_ai["status_ai"] == "Perlu Perhatian").sum())
    jumlah_evaluasi = int((df_ai["status_ai"] == "Perlu Evaluasi").sum())

    col_ai1, col_ai2, col_ai3 = st.columns(3)
    col_ai1.metric("Aman", jumlah_aman)
    col_ai2.metric("Perlu Perhatian", jumlah_perhatian)
    col_ai3.metric("Perlu Evaluasi", jumlah_evaluasi)

    st.subheader("Ringkasan Status Mahasiswa")
    df_ai_tampil = df_ai.copy()
    df_ai_tampil["tanggal_terakhir"] = pd.to_datetime(df_ai_tampil["tanggal_terakhir"], errors="coerce").dt.strftime("%Y-%m-%d")
    st.dataframe(df_ai_tampil, use_container_width=True)

    st.subheader("Mahasiswa Prioritas Tindakan")
    prioritas = df_ai[df_ai["status_ai"] != "Aman"].copy()
    if not prioritas.empty:
        prioritas["tanggal_terakhir"] = pd.to_datetime(prioritas["tanggal_terakhir"], errors="coerce").dt.strftime("%Y-%m-%d")
        st.dataframe(prioritas, use_container_width=True)
    else:
        st.success("Semua mahasiswa berada pada status Aman.")
else:
    st.info("Belum ada data yang bisa dianalisis AI.")

# =========================
# Filter logbook
# =========================
st.header("Filter Data Logbook")

if not df_logbook_olah.empty:
    colf1, colf2 = st.columns(2)

    with colf1:
        pilihan_nama = ["Semua"] + sorted(df_logbook_olah["nama"].dropna().unique().tolist())
        filter_nama = st.selectbox("Filter berdasarkan nama", pilihan_nama)

    with colf2:
        filter_kehadiran = st.selectbox(
            "Filter berdasarkan kehadiran",
            ["Semua", "Hadir", "Izin", "Sakit", "Alpha"]
        )

    df_filter = df_logbook_olah.copy()

    if filter_nama != "Semua":
        df_filter = df_filter[df_filter["nama"] == filter_nama]

    if filter_kehadiran != "Semua":
        df_filter = df_filter[df_filter["kehadiran"] == filter_kehadiran]

    df_filter_tampil = df_filter.copy()
    df_filter_tampil["tanggal"] = pd.to_datetime(df_filter_tampil["tanggal"], errors="coerce").dt.strftime("%Y-%m-%d")

    st.dataframe(df_filter_tampil, use_container_width=True)
else:
    st.info("Belum ada data logbook yang bisa difilter.")

# =========================
# Grafik monitoring
# =========================
st.header("Grafik Monitoring")

if not df_logbook_olah.empty:
    colg1, colg2 = st.columns(2)

    with colg1:
        st.subheader("Rata-rata Progres per Mahasiswa")
        progres_per_mahasiswa = (
            df_logbook_olah.groupby("nama")["progres"]
            .mean()
            .sort_values(ascending=False)
        )
        st.bar_chart(progres_per_mahasiswa)

    with colg2:
        st.subheader("Jumlah Kehadiran Hadir per Mahasiswa")
        hadir_per_mahasiswa = (
            df_logbook_olah[df_logbook_olah["kehadiran"] == "Hadir"]
            .groupby("nama")
            .size()
            .sort_values(ascending=False)
        )

        if not hadir_per_mahasiswa.empty:
            st.bar_chart(hadir_per_mahasiswa)
        else:
            st.info("Belum ada data kehadiran Hadir.")
else:
    st.info("Belum ada data untuk dibuat grafik.")

# =========================
# Data mentah
# =========================
st.header("Data Mahasiswa")
st.dataframe(df_mahasiswa, use_container_width=True)

st.header("Data Logbook Lengkap")
if not df_logbook_olah.empty:
    df_logbook_tampil = df_logbook_olah.copy()
    df_logbook_tampil["tanggal"] = pd.to_datetime(df_logbook_tampil["tanggal"], errors="coerce").dt.strftime("%Y-%m-%d")
    st.dataframe(df_logbook_tampil, use_container_width=True)
else:
    st.dataframe(df_logbook, use_container_width=True)