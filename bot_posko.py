import os
import re
import sys
import random
from datetime import datetime, timedelta, timezone
import requests
from playwright.sync_api import sync_playwright

EMAIL = os.environ.get("POSKO_EMAIL", "").strip()
PASSWORD = os.environ.get("POSKO_PASSWORD", "").strip()
TG_TOKEN = os.environ.get("TELEGRAM_TOKEN", "").strip()
TG_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# ==========================================================
# LINK FOLDER GOOGLE DRIVE STOK 7 HARI
# ==========================================================
FOLDER_URLS = {
    "siang": "https://drive.google.com/drive/folders/1JZ3oF9j2quXlarQqcQqz9GhpwMbekQVA",
    "malam": "https://drive.google.com/drive/folders/1PPFrBZ7c8kQThXGi2f-BE4sFAXi5uaRU",
    "dimtaq": "https://drive.google.com/drive/folders/1L1wdZfq6DOKCukFTlE-qxN_m3Z-Z-KNa",
}

# ==========================================================
# 1. VARIASI PATROLI SABHARA (QW1.10) - SIANG & MALAM
# ==========================================================
DAFTAR_RUTE_SIANG = [
    "MAKO - BRI - PASAR - BPD - BNI - MANDIRI - MAKO",
    "MAKO - PASAR - BRI - BNI - MANDIRI - BPD - MAKO",
    "MAKO - MANDIRI - BNI - PASAR - BRI - SPBU - MAKO",
    "MAKO - SPBU - BRI - PASAR - BPD - MANDIRI - MAKO",
    "MAKO - BPD - PASAR - BRI - MANDIRI - BNI - MAKO",
    "MAKO - BNI - BRI - PASAR - MANDIRI - BPD - MAKO",
    "MAKO - TUGU BINTANG - PASAR - BRI - BPD - SPBU - MAKO",
]

DAFTAR_RUTE_MALAM = [
    "MAKO - BRI - BPD - BNI - MANDIRI - SPBU - MAKO",
    "MAKO - SPBU - MANDIRI - BNI - BRI - PASAR - MAKO",
    "MAKO - MANDIRI - BRI - PASAR - BPD - BNI - MAKO",
    "MAKO - PASAR - BPD - BRI - BNI - MANDIRI - MAKO",
    "MAKO - BNI - MANDIRI - SPBU - BRI - BPD - MAKO",
    "MAKO - TUGU BINTANG - BRI - BPD - SPBU - ALAS MBOGO - MAKO",
]

# ==========================================================
# 2. VARIASI PAKET LOKASI & KOORDINAT ASLI DIMTAQ (QW1.14)
# ==========================================================
PAKET_DIMTAQ = [
    {
        "lokasi": "PASAR JATISRONO",
        "koordinat": "(-7.8273937, 111.1285440)",
        "uraian": [
            "Melaksanakan patroli dialogis dan memberikan pembinaan serta imbauan kamtibmas kepada warga maupun pemuda di area Pasar Jatisrono",
            "Melaksanakan patroli rutin serta mengajak masyarakat bersama-sama menjaga keamanan dan ketertiban di lingkungan pasar",
            "Melaksanakan kegiatan pembinaan disiplin dan imbauan kamtibmas secara humanis kepada warga di Pasar Jatisrono",
        ]
    },
    {
        "lokasi": "JALAN SEKITAR PASAR JATISRONO",
        "koordinat": "(-7.8274594, 111.1289731)",
        "uraian": [
            "Melaksanakan patroli rutin dan memberikan imbauan kamtibmas kepada warga serta pemuda di jalan sekitar Pasar Jatisrono",
            "Melaksanakan kegiatan patroli sambang dan pembinaan norma kepada masyarakat guna menjaga situasi tetap aman dan tertib",
            "Melaksanakan patroli dialogis guna mengantisipasi gangguan kamtibmas dan pelanggaran ketertiban umum di sekitar pasar",
        ]
    },
    {
        "lokasi": "JALAN SEKITAR SPBU JATISRONO",
        "koordinat": "(-7.8296862, 111.1607271)",
        "uraian": [
            "Melaksanakan patroli rutin serta memberikan pembinaan kepada pemuda yang ditemui di sekitar SPBU Jatisrono agar menjauhi pelanggaran norma",
            "Melaksanakan patroli dialogis dan menyampaikan pesan kamtibmas kepada warga serta remaja di jalan sekitar SPBU Jatisrono",
            "Melaksanakan kegiatan pembinaan ketertiban masyarakat guna mencegah gangguan keamanan di area sekitar SPBU Jatisrono",
        ]
    },
    {
        "lokasi": "TUGU BINTANG JATISRONO",
        "koordinat": "(-7.8272791, 111.1287683)",
        "uraian": [
            "Melaksanakan patroli pembinaan secara humanis kepada warga dan pemuda di kawasan Tugu Bintang Jatisrono guna menjaga ketertiban umum",
            "Melaksanakan patroli dialogis serta memberikan edukasi dan imbauan kamtibmas kepada remaja yang berkumpul di sekitar Tugu Bintang",
            "Melaksanakan patroli rutin dan pembinaan disiplin masyarakat di area Tugu Bintang Jatisrono agar situasi tetap aman kondusif",
        ]
    },
    {
        "lokasi": "ALAS MBOGO JATISRONO",
        "koordinat": "(-7.8549743, 111.0955813)",
        "uraian": [
            "Melaksanakan patroli rutin dan razia pembinaan di kawasan Alas Mbogo Jatisrono guna mencegah pelanggaran norma serta gangguan kamtibmas",
            "Melaksanakan pemantauan wilayah dan memberikan pembinaan disiplin kepada masyarakat maupun pemuda yang ditemui di sekitar Alas Mbogo",
            "Melaksanakan patroli kewilayahan serta imbauan kamtibmas di area Alas Mbogo Jatisrono guna menciptakan rasa aman bagi masyarakat",
        ]
    }
]

def kirim_notif_telegram(pesan, foto_path=None):
    if not TG_TOKEN or not TG_CHAT_ID:
        return
    daftar_chat_id = [cid.strip() for cid in TG_CHAT_ID.split(",") if cid.strip()]
    for cid in daftar_chat_id:
        try:
            if foto_path and os.path.exists(foto_path):
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
                with open(foto_path, "rb") as f:
                    requests.post(url, data={"chat_id": cid, "caption": pesan[:1000]}, files={"photo": f}, timeout=20)
            else:
                url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
                requests.post(url, data={"chat_id": cid, "text": pesan[:4000]}, timeout=20)
        except Exception as e:
            print(f"Gagal kirim ke Telegram ({cid}):", e)

def tutup_saran_jika_ada(page):
    """Menutup kotak Saran atau keluhan 1 (tombol ×) agar tidak wajib diisi."""
    try:
        tombol_x = page.locator("button:has-text('×')")
        for i in range(tombol_x.count()):
            if tombol_x.nth(i).is_visible():
                tombol_x.nth(i).scroll_into_view_if_needed()
                tombol_x.nth(i).click()
                page.wait_for_timeout(500)
    except Exception:
        pass

def klik_tetap_kirim_jika_ada(page):
    """Otomatis mengklik tombol 'Tetap kirim' jika muncul konfirmasi laporan serupa."""
    try:
        btn_tetap = page.get_by_role("button", name="Tetap kirim")
        if btn_tetap.count() > 0 and btn_tetap.first.is_visible():
            btn_tetap.first.scroll_into_view_if_needed()
            btn_tetap.first.click()
            page.wait_for_timeout(3000)
    except Exception:
        pass

def pilih_alasan_dropdown(page, preferensi_teks=""):
    """Memilih alasan pada dropdown kedua di halaman (Alasan memilih rute / lokasi)."""
    try:
        selects = page.locator("select")
        if selects.count() > 1:
            dropdown = selects.nth(1)
            dropdown.scroll_into_view_if_needed()
            if preferensi_teks and dropdown.locator("option", has_text=preferensi_teks).count() > 0:
                teks_opsi = dropdown.locator("option", has_text=preferensi_teks).first.text_content().strip()
                dropdown.select_option(label=teks_opsi)
            else:
                dropdown.select_option(index=1)
            page.wait_for_timeout(800)
    except Exception as e:
        print("Info pilih alasan:", e)

def isi_link_foto_drive(page, link_foto):
    """Mengisi link Google Drive pada kolom Foto kegiatan."""
    inputs_drive = page.locator("input[placeholder*='Google Drive'], input[placeholder*='drive.google.com']")
    for i in range(inputs_drive.count()):
        if inputs_drive.nth(i).is_visible():
            inputs_drive.nth(i).scroll_into_view_if_needed()
            inputs_drive.nth(i).fill(link_foto)
            break

def ambil_satu_foto_dari_folder(page, kategori):
    folder_url = FOLDER_URLS[kategori]
    kode_utama = folder_url.rstrip("/").split("/")[-1].split("?")[0]
    embed_url = f"https://drive.google.com/embeddedfolderview?id={kode_utama}#list"

    wib_now = datetime.now(timezone(timedelta(hours=7)))
    indeks_hari = wib_now.weekday()

    file_links = []
    try:
        res = requests.get(embed_url, timeout=20)
        ids = re.findall(r"/file/d/([a-zA-Z0-9_-]{25,})/", res.text)
        if not ids:
            ids = re.findall(r'id="entry-([a-zA-Z0-9_-]{25,})"', res.text)

        seen = set()
        for item_id in ids:
            if item_id != kode_utama and item_id not in seen:
                seen.add(item_id)
                file_links.append(f"https://drive.google.com/file/d/{item_id}/view?usp=drivesdk")

        if not file_links:
            page.goto(folder_url, timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
            html = page.content()
            ids2 = re.findall(r'data-id="([a-zA-Z0-9_-]{25,})"', html)
            for item_id in ids2:
                if item_id != kode_utama and item_id not in seen:
                    seen.add(item_id)
                    file_links.append(f"https://drive.google.com/file/d/{item_id}/view?usp=drivesdk")
    except Exception as e:
        print(f"Gagal memindai folder {kategori}:", e)

    if file_links:
        idx_terpilih = indeks_hari % len(file_links)
        link_terpilih = file_links[idx_terpilih]
        return link_terpilih, idx_terpilih + 1, len(file_links)

    return folder_url, 1, 1

def jalankan_robot(mode):
    kirim_notif_telegram(f"🤖 Robot Samapta Posko PBM mulai berjalan (Mode: {mode.upper()})...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 412, "height": 915},
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        page = context.new_page()

        try:
            link_siang, urut_siang, total_siang = ambil_satu_foto_dari_folder(page, "siang") if mode == "siang" else ("", 0, 0)
            link_malam, urut_malam, total_malam = ambil_satu_foto_dari_folder(page, "malam") if mode == "malam" else ("", 0, 0)
            link_dimtaq, urut_dimtaq, total_dimtaq = ambil_satu_foto_dari_folder(page, "dimtaq") if mode in ["siang", "dimtaq"] else ("", 0, 0)

            page.goto("https://poskopbm.polri.go.id/input", timeout=60000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # 1. Login jika diminta
            if page.locator("input[type='password']").count() > 0:
                page.locator("input[type='email'], input[type='text']").first.fill(EMAIL)
                page.locator("input[type='password']").first.fill(PASSWORD)
                page.get_by_role("button", name="Masuk").click()
                page.wait_for_timeout(5000)

            # 2. Isi Identitas & Pilih Jabatan Dirsamapta / Kasat Samapta (2 kegiatan)
            page.get_by_label("Nama dan pangkat pelapor").fill("BRIPKA ABU ZAKARIYA, S.H")
            select_jabatan = page.locator("select").first
            opsi_samapta = select_jabatan.locator("option", has_text="Samapta").first
            teks_jabatan = (opsi_samapta.text_content() or "").strip()
            select_jabatan.select_option(label=teks_jabatan)
            page.wait_for_timeout(2500)

            # ==========================================================
            # 3. EKSEKUSI PATROLI SABHARA (QW1.10 - PAGI 08.00 / MALAM 20.00)
            # ==========================================================
            if mode in ["siang", "malam"]:
                link_patroli = link_siang if mode == "siang" else link_malam
                no_foto = urut_siang if mode == "siang" else urut_malam
                tot_foto = total_siang if mode == "siang" else total_malam
                rute_pilihan = random.choice(DAFTAR_RUTE_SIANG if mode == "siang" else DAFTAR_RUTE_MALAM)

                # Buka form QW1.10 Patroli Sabhara
                if page.get_by_role("button", name="Isi laporan").count() > 0:
                    page.get_by_role("button", name="Isi laporan").nth(0).click()
                else:
                    page.get_by_text("Patroli Sabhara").last.click()
                page.wait_for_timeout(2500)

                # c. Rute patroli dan titik rawan yang dilalui (Wajib)
                inp_rute = page.locator("input[placeholder*='Jalan, kecamatan']")
                if inp_rute.count() > 0:
                    inp_rute.first.scroll_into_view_if_needed()
                    inp_rute.first.fill(rute_pilihan)

                # d. Alasan memilih rute ini -> Pilih 'Jalur rutin patroli' (Wajib)
                pilih_alasan_dropdown(page, "Jalur rutin patroli")

                # f. Jam pelaksanaan kegiatan -> Klik 'Isi jam sekarang' (Wajib)
                btn_jam = page.get_by_role("button", name="Isi jam sekarang")
                if btn_jam.count() > 0:
                    btn_jam.first.scroll_into_view_if_needed()
                    btn_jam.first.click()
                    page.wait_for_timeout(500)

                # k. Jenis kegiatan patroli -> Klik 'Patrol mobile' (Wajib)
                btn_mobile = page.get_by_role("button", name="Patrol mobile")
                if btn_mobile.count() > 0:
                    btn_mobile.first.scroll_into_view_if_needed()
                    btn_mobile.first.click()
                    page.wait_for_timeout(300)

                # l. Alat utama patroli -> Klik 'Mobil patroli' (Wajib)
                btn_mobil = page.get_by_role("button", name="Mobil patroli")
                if btn_mobil.count() > 0:
                    btn_mobil.first.scroll_into_view_if_needed()
                    btn_mobil.first.click()
                    page.wait_for_timeout(300)

                # m. Ada target penindakan atau temuan pada patroli ini? -> Klik 'Tidak ada' (Wajib)
                btn_tidak_ada = page.get_by_role("button", name="Tidak ada", exact=True)
                if btn_tidak_ada.count() > 0:
                    btn_tidak_ada.first.scroll_into_view_if_needed()
                    btn_tidak_ada.first.click()
                    page.wait_for_timeout(500)

                # o. Tutup kotak Saran atau keluhan 1 (×)
                tutup_saran_jika_ada(page)

                # p. Foto kegiatan (Wajib)
                isi_link_foto_drive(page, link_patroli)

                page.wait_for_timeout(1000)
                btn_kirim = page.get_by_role("button", name="Kirim laporan")
                btn_kirim.scroll_into_view_if_needed()
                btn_kirim.click()
                page.wait_for_timeout(2000)

                klik_tetap_kirim_jika_ada(page)
                page.wait_for_timeout(4000)

                ss_patroli = f"bukti_patroli_{mode}.png"
                page.screenshot(path=ss_patroli)
                kirim_notif_telegram(
                    f"✅ Laporan PATROLI {mode.upper()} (QW1.10) berhasil dikirim!\n\n"
                    f"📸 Foto ke-{no_foto} dari {tot_foto} di Folder\n"
                    f"🛣️ Rute: {rute_pilihan}\n"
                    f"🔗 Link Foto: {link_patroli}",
                    ss_patroli
                )

            # ==========================================================
            # 4. EKSEKUSI DIMTAQ EKSTERNAL (QW1.14 - PAGI 08.00)
            # ==========================================================
            if mode in ["siang", "dimtaq"]:
                paket = random.choice(PAKET_DIMTAQ)
                uraian_dimtaq = random.choice(paket["uraian"])

                # Buka form QW1.14 DIMTAQ
                if page.get_by_text("QW1.14").count() > 0:
                    page.get_by_text("QW1.14").last.scroll_into_view_if_needed()
                    page.get_by_text("QW1.14").last.click()
                elif page.get_by_role("button", name="Isi laporan").count() > 1:
                    page.get_by_role("button", name="Isi laporan").nth(1).click()
                page.wait_for_timeout(2500)

                # b. Lokasi DIMTAQ: Nama tempat & Koordinat (Wajib)
                inp_tempat = page.locator("input[placeholder*='Nama tempat']")
                if inp_tempat.count() > 0:
                    inp_tempat.first.scroll_into_view_if_needed()
                    inp_tempat.first.fill(paket["lokasi"])

                inp_koord = page.locator("input[placeholder*='Tempel koordinat']")
                if inp_koord.count() > 0:
                    inp_koord.first.scroll_into_view_if_needed()
                    inp_koord.first.fill(paket["koordinat"])

                # c. Jam pelaksanaan kegiatan -> Klik 'Isi jam sekarang' (Wajib)
                btn_jam = page.get_by_role("button", name="Isi jam sekarang")
                if btn_jam.count() > 0:
                    btn_jam.first.scroll_into_view_if_needed()
                    btn_jam.first.click()
                    page.wait_for_timeout(500)

                # d. Alasan memilih lokasi ini (Wajib)
                pilih_alasan_dropdown(page)

                # j. Tutup kotak Saran atau keluhan 1 (×) terlebih dahulu agar input angka di dalamnya hilang
                tutup_saran_jika_ada(page)

                # e & f. Isi semua kotak angka wajib dengan "0"
                num_inputs = page.locator("input[type='number']")
                for i in range(num_inputs.count()):
                    if num_inputs.nth(i).is_visible():
                        num_inputs.nth(i).scroll_into_view_if_needed()
                        num_inputs.nth(i).fill("0")

                # h. Uraian pelaksanaan kegiatan (Wajib)
                inp_uraian = page.locator("textarea[placeholder*='Contoh: razia']")
                if inp_uraian.count() > 0:
                    inp_uraian.first.scroll_into_view_if_needed()
                    inp_uraian.first.fill(uraian_dimtaq)

                # k. Foto kegiatan (Wajib)
                isi_link_foto_drive(page, link_dimtaq)

                page.wait_for_timeout(1000)
                btn_kirim = page.get_by_role("button", name="Kirim laporan")
                btn_kirim.scroll_into_view_if_needed()
                btn_kirim.click()
                page.wait_for_timeout(2000)

                klik_tetap_kirim_jika_ada(page)
                page.wait_for_timeout(4000)

                ss_dimtaq = "bukti_dimtaq.png"
                page.screenshot(path=ss_dimtaq)
                kirim_notif_telegram(
                    f"✅ Laporan DIMTAQ EKSTERNAL (QW1.14) berhasil dikirim!\n\n"
                    f"📸 Foto ke-{urut_dimtaq} dari {total_dimtaq} di Folder\n"
                    f"📍 Lokasi: {paket['lokasi']} {paket['koordinat']}\n"
                    f"📝 Uraian: {uraian_dimtaq}\n"
                    f"🔗 Link Foto: {link_dimtaq}",
                    ss_dimtaq
                )

        except Exception as e:
            err_ss = "error.png"
            try:
                page.screenshot(path=err_ss)
                kirim_notif_telegram(f"⚠️ Gagal mengirim laporan ({mode}):\n{str(e)}", err_ss)
            except Exception:
                kirim_notif_telegram(f"⚠️ Gagal membuka web ({mode}):\n{str(e)}")
        finally:
            browser.close()

if __name__ == "__main__":
    mode_pilihan = sys.argv[1] if len(sys.argv) > 1 else "siang"
    jalankan_robot(mode_pilihan)
