# BAB III — METODE PENELITIAN

> **Draft.** Bagian bertanda **[ISI]** diisi setelah pelabelan dan validasi selesai. Semua angka parameter di bab ini diambil dari kode sumber (`closeness.py`, `patterns.py`, `main.py`). Jika parameter di kode diubah, angka di bab ini harus diperbarui juga.

## 3.1 Gambaran Umum Sistem

Penelitian ini membangun fitur analisis percakapan WhatsApp pada aplikasi web Lumora (FastAPI, PostgreSQL). Fitur ini menghasilkan tiga keluaran untuk setiap percakapan dua orang:

1. **Skor kedekatan** (0–100) beserta kategorinya dan tren per bulan.
2. **Pola komunikasi** berbasis kerangka Gottman, dihitung per orang.
3. **Narasi AI** (opsional) yang merangkum pola percakapan dengan merujuk dua keluaran di atas.

Pendekatan yang dipakai adalah **berbasis aturan (*rule-based*) dan leksikon**, bukan model pembelajaran mesin yang dilatih. Tidak ada data berlabel yang dipakai untuk menentukan parameter. Bobot dan ambang batas ditetapkan secara heuristik, lalu diuji terhadap penilaian manusia pada tahap validasi (subbab 3.7).

Alur pemrosesan:

```
Ekspor chat (.txt/.zip)
  → parsing baris pesan
  → penyaringan dua peserta paling aktif
  → ekstraksi metrik perilaku dan pencocokan leksikon
  → skor kedekatan + tren bulanan + pola komunikasi
  → (opsional) narasi AI
  → penyimpanan angka agregat (isi pesan dibuang)
```

## 3.2 Data

### 3.2.1 Sumber data

Data berupa **20 ekspor percakapan WhatsApp** dua orang (*Export chat → Without media*) yang dikumpulkan anggota kelompok dari percakapan pribadi mereka, dengan persetujuan pihak yang terlibat. Panjang percakapan berkisar antara 10 sampai sekitar 26.700 pesan, dengan rentang waktu 1 hari sampai sekitar 2 tahun.

### 3.2.2 Perlindungan privasi

- Data mentah disimpan hanya di komputer lokal (folder `sampel-chat/`) dan dikecualikan dari repositori Git.
- Di aplikasi, isi pesan hanya diproses selama satu *request*. Basis data hanya menyimpan angka agregat dan **alias** peserta yang diisi pengguna, bukan nama asli.
- Pada laporan dan narasi AI, isi pesan tidak dikutip.
- Jika narasi AI diaktifkan (dengan persetujuan terpisah), hanya sampel potongan pesan (maksimal 48 potongan, masing-masing ≤ 220 karakter) yang dikirim ke penyedia AI.

## 3.3 Pra-pemrosesan

1. **Parsing.** Setiap baris dicocokkan dengan pola regex format ekspor WhatsApp (`tanggal, jam - pengirim: isi`). Baris lanjutan dan baris sistem yang tidak cocok diabaikan.
2. **Deteksi format tanggal.** Urutan hari/bulan (DD/MM atau MM/DD) ditentukan dari tanggal yang tidak ambigu (misalnya 25/03 hanya mungkin DD/MM), berdasarkan suara terbanyak di seluruh ekspor.
3. **Penyaringan peserta.** Hanya dua pengirim dengan jumlah pesan terbanyak yang dianalisis.
4. **Penanda media.** Pesan berupa penanda media atau pesan terhapus (misalnya `<Media omitted>`, `tidak disertakan`, `This message was deleted`) tidak dihitung sebagai pesan teks pada komponen berbasis kata.
5. **Sesi percakapan.** Jeda **≥ 6 jam** antar pesan dianggap awal percakapan baru. Jeda tersebut tidak dihitung sebagai waktu balas.

## 3.4 Skor Kedekatan

### 3.4.1 Rumus

Skor kedekatan $S$ adalah jumlah berbobot dari enam komponen:

$$S = \operatorname{round}\left(\sum_{i=1}^{6} w_i \cdot s_i\right), \qquad \sum w_i = 100$$

Setiap komponen $s_i \in [0, 1]$ dihitung dengan penskalaan linear terpotong:

$$s_i = \min\left(1, \max\left(0, \frac{x_i - a_i}{b_i - a_i}\right)\right)$$

$x_i$ adalah nilai terukur, $a_i$ adalah batas bawah (nilai 0), dan $b_i$ adalah batas atas (nilai penuh). Untuk kecepatan balas, arahnya dibalik ($s = 1 - \text{skala}$), karena balasan yang lebih cepat bernilai lebih tinggi.

### 3.4.2 Komponen

| No | Komponen | Bobot $w_i$ | Nilai terukur $x_i$ | $a_i$ (nilai 0) | $b_i$ (nilai penuh) |
|---|---|---|---|---|---|
| 1 | Frekuensi chat | 25 | Rata-rata pesan per hari aktif (hari yang memiliki ≥ 1 pesan) | 5 | 60 |
| 2 | Konsistensi | 15 | Hari aktif ÷ jumlah hari dari pesan pertama sampai terakhir | 0,05 | 0,70 |
| 3 | Keseimbangan pesan | 20 | Proporsi pesan dari peserta yang lebih jarang menulis | 0,15 | 0,45 |
| 4 | Kecepatan balas | 20 | Rata-rata median waktu balas kedua peserta (detik) | ≥ 10.800 (3 jam) → 0 | ≤ 120 (2 menit) → penuh |
| 5 | Inisiatif | 10 | Proporsi percakapan yang dimulai peserta yang lebih jarang memulai | 0,10 | 0,40 |
| 6 | Kata hangat | 10 | Proporsi pesan teks yang mengandung kata hangat atau tawa | 0,02 | 0,15 |

Catatan definisi:

- **Waktu balas** dihitung ketika pengirim berganti dan jedanya < 6 jam. Median diambil per peserta, lalu dirata-ratakan.
- **Memulai percakapan** berarti mengirim pesan pertama ekspor atau pesan pertama setelah jeda ≥ 6 jam.
- **Kata hangat** dicocokkan sebagai kata utuh (tanpa membedakan huruf besar/kecil). Contohnya *makasih, terima kasih, kangen, semangat, sayang*, tawa (*wkwk, haha, hehe*), dan emoji hati. Pencocokan kata utuh mencegah kesalahan seperti "sadar" terbaca sebagai "sad".

### 3.4.3 Kategori

| Skor | Kategori |
|---|---|
| 0–34 | Distant |
| 35–54 | Casual |
| 55–74 | Close |
| 75–100 | Very close |

### 3.4.4 Tren bulanan

1. Setiap bulan kalender dihitung skornya dengan rumus yang sama, hanya dari pesan bulan tersebut. Konsistensi pada bulan pertama dan terakhir dihitung terhadap hari yang benar-benar tercakup ekspor, sehingga bulan yang tidak penuh tidak dirugikan.
2. Bulan dengan **< 20 pesan**, atau yang hanya berisi pesan dari satu peserta, tidak diberi skor.
3. Jika terdapat minimal 3 bulan yang memiliki skor, ditentukan $k = \max(1, \lfloor n/3 \rfloor)$, lalu dihitung selisih $\Delta$ antara rata-rata $k$ bulan terakhir dan rata-rata $k$ bulan pertama.
4. Arah tren: **naik** jika $\Delta \ge 8$, **turun** jika $\Delta \le -8$, dan **stabil** jika di antaranya.

## 3.5 Pola Komunikasi (Kerangka Gottman)

### 3.5.1 Kategori

Kategori diturunkan dari penelitian Gottman tentang interaksi pasangan:

| Kategori | Makna | Contoh frasa leksikon |
|---|---|---|
| Criticism | Keluhan yang dibingkai sebagai kekurangan orang lain | *kamu selalu, kamu gak pernah, you always* |
| Contempt | Hinaan, ejekan, merendahkan | *bodoh, sok tau, dasar kamu* |
| Defensiveness | Membalikkan keluhan atau menyangkal peran | *bukan salah aku, kan kamu yang* |
| Stonewalling | Menutup percakapan | *capek ngomong, males bahas, terserah deh* |
| Repair attempts | Usaha meredakan konflik | *maaf, sorry, aku salah* |
| Positif | Terima kasih, afeksi, dukungan | *makasih, semangat, kangen* |
| Negatif | Kekesalan, kekecewaan | *kesel, kecewa, marah* |

Empat kategori pertama disebut *Four Horsemen*.

### 3.5.2 Leksikon dan pencocokan

- Leksikon disimpan di tabel `chat_keywords` sehingga dapat diubah tanpa mengubah kode. Isi bawaannya ada di `patterns.py`.
- Leksikon sengaja memakai **frasa spesifik**, bukan kata tunggal yang umum. Misalnya "kamu selalu" dipakai, bukan "selalu". Kata sehari-hari seperti *selalu, hmm, gapapa, capek, terserah* tidak dihitung, karena lebih sering bermakna netral.
- Frasa dicocokkan sebagai kata utuh, dan spasi di dalam frasa boleh lebih dari satu.
- Satu pesan dihitung **satu kali per kategori**, berapa pun jumlah frasa yang cocok.

### 3.5.3 Ukuran

Untuk setiap peserta dan kategori dihitung:

- jumlah pesan teks yang cocok ($c$), dan
- laju per 100 pesan teks: $r = 100 \cdot c / n_{\text{teks}}$.

Sebuah kategori *Four Horsemen* diberi tanda **"worth noticing"** jika $c \ge 3$ **dan** $r \ge 0{,}5$. Syarat ganda ini mencegah beberapa kecocokan kebetulan dalam percakapan panjang ikut ditandai.

Rasio positif terhadap negatif:

$$\text{rasio} = \frac{c_{\text{positif}} + c_{\text{repair}}}{c_{\text{negatif}} + \sum c_{\text{Four Horsemen}}}$$

Rasio ini tidak didefinisikan jika penyebutnya nol. Rasio 5 : 1 yang sering dikutip dari Gottman berlaku untuk diskusi konflik, bukan percakapan sehari-hari, sehingga tidak dipakai sebagai ambang.

Keluaran ini disajikan sebagai pola kata untuk bahan refleksi, **bukan penilaian terhadap karakter seseorang**.

## 3.6 Narasi AI (Opsional)

Jika pengguna memberi persetujuan, aplikasi mengirim permintaan *zero-shot* ke model bahasa besar (penyedia yang kompatibel dengan OpenAI Responses API, atau Gemini). Isi permintaannya:

- statistik agregat seluruh ekspor (jumlah pesan, waktu balas, aktivitas bulanan, topik berbasis kata kunci),
- skor kedekatan beserta komponen dan trennya, serta hasil pola komunikasi (alias dan angka saja),
- sampel potongan pesan (subbab 3.2.2).

Instruksi kepada model meminta keluaran JSON yang konsisten dengan skor dan kategori dari aplikasi. Model hanya boleh membahas pola yang bertanda *worth noticing*, sebagai pola kata. Model dilarang mengutip pesan, mendiagnosis, menebak perasaan tersembunyi, atau menyebut seseorang *red flag*. Model tidak dilatih ulang dan tidak dipakai untuk menghitung skor.

## 3.7 Rancangan Validasi

### 3.7.1 Pelabelan manual

Setiap percakapan dilabeli secara independen oleh **minimal dua anggota** ke salah satu dari empat kategori (Distant, Casual, Close, Very close). Pelabelan mengikuti panduan `colab/PANDUAN_LABEL.md`, dengan aturan:

- Penilaian didasarkan pada **kesan pembaca** terhadap isi, nada, inisiatif, kepedulian, dan keterbukaan dalam chat, bukan pada banyaknya pesan.
- Pelabelan dilakukan **sebelum** melihat skor aplikasi, dan tanpa diskusi antar penilai.
- Percakapan yang tidak dapat dinilai boleh dikosongkan.

Label konsensus per percakapan ditentukan dengan suara terbanyak. Jika seri, dipakai median level (level tengah bawah).

Perlu dicatat bahwa aplikasi mengukur **perilaku** percakapan (frekuensi, keseimbangan, kecepatan, inisiatif), sedangkan label manusia mengukur **kedekatan yang dirasakan dari isi**. Validasi ini menguji sejauh mana perilaku percakapan dapat menjadi proksi kedekatan yang dipersepsikan manusia.

### 3.7.2 Metrik

Dihitung dengan `colab/validate_closeness.py`:

| Metrik | Definisi |
|---|---|
| Akurasi persis | Proporsi percakapan dengan kategori aplikasi = label konsensus |
| Akurasi ±1 level | Proporsi dengan selisih kategori ≤ 1 level |
| Rata-rata selisih level | $\frac{1}{N}\sum \lvert \text{level}_{\text{app}} - \text{level}_{\text{manusia}} \rvert$, dengan level 0–3 |
| Korelasi Spearman ($\rho$) | Korelasi peringkat antara skor 0–100 aplikasi dan level label manusia (peringkat rata-rata untuk nilai sama) |
| Kesepakatan antar penilai | Proporsi percakapan (dengan ≥ 2 penilai) yang semua penilainya memberi label sama |
| Matriks kebingungan | Distribusi label manusia (baris) terhadap kategori aplikasi (kolom) |

Kesepakatan antar penilai menjadi acuan batas atas yang realistis: jika sesama manusia hanya sepakat pada X% percakapan, akurasi aplikasi tidak dapat diharapkan jauh di atas X%.

### 3.7.3 Kalibrasi

Jika matriks kebingungan menunjukkan aplikasi konsisten menilai lebih tinggi (atau lebih rendah) daripada manusia, batas kategori (subbab 3.4.3) disesuaikan. Karena jumlah sampel kecil (20 percakapan), kalibrasi dibatasi pada batas kategori. Bobot komponen tidak diubah, untuk mengurangi risiko *overfitting*. Hasil sebelum dan sesudah kalibrasi dilaporkan.

### 3.7.4 Hasil

**[ISI setelah validasi]**

| Metrik | Nilai |
|---|---|
| Jumlah percakapan berlabel | **[ISI]** |
| Jumlah penilai | **[ISI]** |
| Akurasi persis | **[ISI]** |
| Akurasi ±1 level | **[ISI]** |
| Rata-rata selisih level | **[ISI]** |
| Spearman $\rho$ | **[ISI]** |
| Kesepakatan antar penilai | **[ISI]** |

## 3.8 Pengujian Perangkat Lunak

Logika analisis diuji dengan 27 *unit test* (`python -m unittest discover tests`), yang mencakup:

- penskalaan dan batas kategori skor kedekatan;
- pencocokan kata utuh, termasuk kasus yang **tidak boleh** cocok (misalnya "hugo", "capek kuliah", "terserah");
- pengabaian penanda media dan aturan jeda 6 jam;
- tren naik, turun, dan stabil, bulan tanpa data, dan bulan yang tidak penuh;
- syarat *worth noticing*, rasio positif-negatif, dan pengabaian peserta ketiga;
- isi permintaan ke narasi AI. Panggilan AI diganti tiruan (*mock*), sehingga pengujian tidak mengirim data ke luar, dan dipastikan tidak ada nama asli yang ikut terkirim.

## 3.9 Etika

- Percakapan hanya dianalisis dengan persetujuan pihak yang terlibat. Aplikasi mewajibkan pengguna mencentang pernyataan izin sebelum mengunggah.
- Hasil disajikan sebagai pola deskriptif untuk refleksi, bukan diagnosis atau vonis.
- Isi percakapan tidak disimpan, tidak dikutip, dan tidak dipublikasikan.

## 3.10 Keterbatasan

1. **Parameter heuristik.** Bobot dan ambang ditetapkan peneliti, bukan dipelajari dari data, sehingga bisa saja tidak optimal untuk populasi lain.
2. **Proksi perilaku.** Frekuensi dan kecepatan balas dipengaruhi faktor di luar kedekatan, misalnya pekerjaan, zona waktu, dan kebiasaan memakai aplikasi lain.
3. **Leksikon tidak memahami konteks.** Pencocokan kata tidak bisa membedakan candaan dari hinaan, sarkasme, atau negasi ("bukan bodoh"). Ejaan tidak baku di luar leksikon juga tidak terdeteksi.
4. **Teori dari konteks berbeda.** Kerangka Gottman berasal dari observasi pasangan dalam diskusi tatap muka, bukan dari teks chat.
5. **Sampel kecil.** 20 percakapan dari lingkaran sosial anggota kelompok belum mewakili populasi umum. Beberapa sampel juga sangat pendek (10–12 pesan).
6. **Media tidak dianalisis.** Foto, stiker, dan pesan suara hanya terlihat sebagai penanda.
7. **Narasi AI non-deterministik.** Keluaran model dapat berbeda pada permintaan yang sama, dan tidak dievaluasi secara kuantitatif dalam penelitian ini.

Pengembangan selanjutnya yang dapat dilakukan setelah data berlabel lebih banyak: pengelompokan tanpa label (misalnya K-Means) atas fitur yang sama sebagai pembanding, atau klasifikasi terawasi jika jumlah label memadai.
