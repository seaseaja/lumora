# Lumora

Aplikasi web FastAPI untuk tarot, Destiny Matrix, Zodiac/Shio, analisis ekspor WhatsApp, order, dan laporan. Database memakai PostgreSQL melalui SQLModel; Neon bisa dipakai sebagai PostgreSQL ter-host.

## Status database

Skema database sudah didefinisikan di `models.py` dan tabel dibuat otomatis saat aplikasi mulai. File `.env` lokal sudah menunjuk ke project Neon `lumora` (connection string pooled). Konfigurasi PostgreSQL lokal lama disimpan di `.env.local-backup` (tidak di-commit).

## Hubungkan database Neon

1. Buat akun di [Neon](https://neon.com/) dan buat project PostgreSQL. Pilih region yang dekat dengan lokasi aplikasi yang akan di-deploy.
2. Di dashboard project, buka **Connect**, pilih database dan role, lalu salin connection string. Gunakan URL pooled (host berisi `-pooler`) untuk aplikasi web. Jangan kirim atau commit string ini karena mengandung password.
3. Untuk komputer lokal, salin `.env.example` menjadi `.env`, lalu isi `DATABASE_URL` dengan connection string Neon lengkap. Contoh format (bukan kredensial sungguhan):

   ```text
   DATABASE_URL=postgresql://USER:PASSWORD@HOST/DBNAME?sslmode=require
   ```

   Kode mengubah format `postgresql://` Neon menjadi driver `psycopg2` yang digunakan proyek. Pastikan `sslmode=require` tetap ada.
4. Isi `SECRET_KEY` dengan nilai acak yang dibuat memakai `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Isi juga `ADMIN_EMAIL` dan `ADMIN_PASSWORD` milikmu sendiri.
5. Aktifkan virtual environment, install dependency, lalu jalankan:

   ```powershell
   python -m pip install -r requirements.txt
   python seed.py
   uvicorn main:app --reload
   ```

   `seed.py` membuat akun admin awal serta data demo. Startup aplikasi membuat tabel jika belum ada. Bila database sebelumnya berisi tabel dari versi lama, jalankan `python migrate.py` sekali untuk menambah kolom versi baru. Jangan jalankan migrasi terhadap database yang belum kamu pilih dengan sengaja.

## AI untuk Tarot

Tarot dapat memakai OpenAI Responses API untuk memilih spread, membuat preview dan interpretasi setelah checkout, serta menjawab follow-up dalam konteks reading yang sama.

1. Masukkan `OPENAI_API_KEY`, `OPENAI_BASE_URL`, dan `OPENAI_MODEL` di `.env` lokal. `OPENAI_BASE_URL` bersifat opsional dan default ke OpenAI (`https://api.openai.com/v1`). Untuk Pateway gunakan `https://api.pateway.ai/v1` dan model yang tersedia di akun, misalnya `gpt-5.3-codex`.
3. Restart server FastAPI. Saat dipakai tanpa key, draw tetap bekerja memakai arti kartu dari master data, tetapi pilihan spread/follow-up AI tidak aktif.

Pertanyaan dan nama kartu dikirim ke OpenAI hanya jika pengguna menyetujui di form. Request Responses API memakai `store: false`; salinan pertanyaan dan hasil tetap tersimpan di riwayat Lumora. Untuk membatasi pemakaian, setiap akun mendapat maksimal 10 permintaan preview AI per 24 jam dan lima follow-up per reading. API key dan pemakaian API adalah tanggung jawab akun OpenAI pemilik key; pemakaian model dapat dikenakan biaya berdasarkan tarif model. Jangan pernah commit atau membagikan key. Untuk deploy, tambahkan kedua variabel di dashboard environment hosting.

## Import gambar dek Tarot

Master data sudah berisi 78 nama kartu dan arti dasar; gambar dek belum disertakan. Siapkan artwork PNG, JPG, atau WebP yang kamu buat sendiri atau punya izin untuk digunakan. Taruh gambar di `static/tarot_cards/` dan namai berdasarkan nama kartu, dinormalisasi menjadi huruf kecil dengan underscore. Contoh: `The Fool` menjadi `the_fool.jpg`, `Ace of Wands` menjadi `ace_of_wands.webp`.

Lalu jalankan:

```powershell
python migrate.py
python import_tarot_art.py
```

Importer mencocokkan nama file dengan nama kartu, memperbarui `image_url`, dan melaporkan kartu yang belum punya gambar. Jalankan lagi kapan pun setelah menambahkan file. Gambar muncul saat kartu dibuka di halaman Tarot; kartu yang belum punya artwork tetap memakai desain belakang/kartu dasar.

Folder artwork saat ini dikecualikan dari Git karena PDF sumber hanya mengizinkan penggunaan pribadi. Jangan deploy gambar tersebut tanpa izin penggunaan website. Jika nanti memakai deck berlisensi untuk publikasi, hapus pola gambar dari `.gitignore`, commit artwork berlisensi, lalu jalankan importer pada database deployment. Hosting dengan filesystem sementara juga perlu penyimpanan persisten atau object storage agar gambar tidak hilang saat deploy.

## Analisis chat: level kedekatan dan pola komunikasi

Semua analisis ini **rule-based** (aturan dan kamus kata), bukan model machine learning yang dilatih. Isi pesan hanya diproses selama request; yang disimpan hanya angka dan alias.

**Level kedekatan** (`closeness.py`): skor 0–100 dari enam komponen berbobot, yaitu frekuensi chat (25), konsistensi (15), keseimbangan pesan (20), kecepatan balas (20), siapa yang memulai chat (10), dan kata hangat (10). Hasilnya dibagi menjadi Distant (0–34), Casual (35–54), Close (55–74), dan Very close (75+). Tiap bulan juga diberi skor sendiri (bulan dengan kurang dari 20 pesan dilewati) untuk menentukan tren naik / stabil / turun, yang disimpan di `chat_sessions.interest_trend`. Aturan lengkapnya tampil di laporan pada panel *How is this score calculated?*. Batas dan bobotnya ditentukan manual dan perlu divalidasi.

**Pola komunikasi** (`patterns.py`): menghitung per orang berapa pesan yang mengandung frasa criticism, contempt, defensiveness, stonewalling (Four Horsemen, Gottman), repair attempts, serta kata positif dan negatif. Sebuah pola diberi label *worth noticing* hanya jika muncul di minimal 3 pesan dan minimal 0,5 per 100 pesan. Ini bukan vonis tentang seseorang. Kamusnya dibaca dari tabel `chat_keywords`, jadi bisa diubah. `python seed.py` hanya memperbarui kamus yang isinya masih bawaan awal.

**Test:**

```powershell
python -m unittest discover tests
```

**Validasi akurasi level kedekatan:** baca [colab/PANDUAN_LABEL.md](colab/PANDUAN_LABEL.md), taruh export chat di `sampel-chat/`, lalu jalankan `python colab/validate_closeness.py`. Run pertama membuat `colab/closeness_labels.csv` untuk diisi; run berikutnya menampilkan akurasi, korelasi Spearman, kesepakatan antar penilai, dan confusion matrix.

## Deploy: Vercel + Neon (dipakai sekarang)

Production: https://lumora-mu-ruddy.vercel.app

- Deploy ulang: `vercel deploy --prod` dari folder ini (project sudah di-link).
- Environment variable di Vercel (Production): `DATABASE_URL`, `SECRET_KEY` (beda dengan lokal), `COOKIE_SECURE=true`, `GEMINI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`. Ubah lewat `vercel env` atau dashboard.
- Skema/seed tidak dijalankan otomatis di Vercel. Setelah mengubah model, jalankan `python migrate.py` (dan `python seed.py` bila perlu) dari komputer lokal dengan `.env` yang menunjuk ke Neon.
- `.vercelignore` mengecualikan `venv`, `.env*`, dan gambar tarot (lisensi pribadi).
- Avatar disimpan di tabel `user_avatars` (Vercel tidak punya disk permanen).
- Batas body request Vercel 4,5 MB, jadi upload chat WhatsApp di production maksimal ~4,5 MB (kirim .zip agar lebih kecil).
- Checkout tetap simulasi demo.

## Deploy alternatif: Render + Neon

1. Push source code ke repository GitHub-mu. Pastikan `.env` tidak pernah masuk commit (`.gitignore` sudah mengecualikannya).
2. Di Render pilih **New → Web Service**, hubungkan repository, dan isi:

   | Pengaturan | Nilai |
   | --- | --- |
   | Build Command | `pip install -r requirements.txt` |
| Start Command | `python seed.py && uvicorn main:app --host 0.0.0.0 --port $PORT` |

3. Di Environment Render, tambahkan `DATABASE_URL` (connection string Neon), `SECRET_KEY` (nilai acak baru), `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `COOKIE_SECURE=true`, serta `OPENAI_API_KEY`, `OPENAI_BASE_URL`, dan `OPENAI_MODEL` jika ingin AI aktif. `OPENAI_BASE_URL` dapat dikosongkan untuk memakai OpenAI secara langsung.
4. Deploy. Perintah start mengisi master data dan membuat admin pertama dari variabel environment; startup aplikasi membuat tabel yang belum ada. Buka URL Render dan login dengan email/password admin tersebut.

Variabel rahasia dimasukkan melalui halaman Environment penyedia hosting, bukan ditulis ke source code. Lihat [panduan deploy FastAPI Render](https://render.com/docs/deploy-fastapi) dan [environment variables Render](https://render.com/docs/configure-environment-variables).

## Catatan

- Checkout hanya simulasi lokal: tidak memproses pembayaran sungguhan.
- Chat WhatsApp mentah hanya diproses selama request; database menyimpan statistik dan laporan, bukan percakapan mentah.
- Pembacaan Matrix dan Zodiac/Shio adalah hiburan/refleksi.
- Jangan commit `.env`, connection string Neon, atau password.
