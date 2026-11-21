# Panduan Label Kedekatan Chat

Panduan ini dipakai untuk melabeli `colab/closeness_labels.csv` secara manual.
Labelnya membandingkan penilaian manusia dengan skor app. Karena itu, nilailah
dari **kesan kamu sendiri sebagai pembaca**. Jangan menebak cara kerja app.

## Aturan main

1. **Labeli dulu, baru lihat skor app.** Jangan buka hasil app, `closeness.py`,
   atau `closeness_validation_results.csv` sebelum semua anggota selesai.
2. **Jangan diskusi label** dengan anggota lain sampai semua selesai. Kalau ragu,
   putuskan sendiri dan tulis alasannya di catatan pribadi.
3. **Satu baris = satu chat + satu penilai.** Isi `rater` dengan inisialmu dan
   `label` dengan salah satu dari: `Distant`, `Casual`, `Close`, `Very close`.
   Tulis persis seperti itu (angka `1`–`4` juga diterima).
4. **Baca hanya chat yang boleh kamu baca.** Kalau salah satu pihak di chat
   keberatan, lewati chat itu dan kosongkan labelnya.
5. Usahakan **minimal 2 penilai per chat**. Simpan sebagai **CSV (UTF-8)**.
   Jangan ubah kolom `file`.

## Cara menilai

Baca chatnya cukup lama supaya dapat gambaran utuh: awal, tengah, dan bagian
terakhir. Tanyakan ke diri sendiri: *"Kalau dilihat dari chat ini saja, seberapa
dekat dua orang ini?"*

Nilai **hubungannya, bukan banyaknya pesan.** Chat yang panjang tapi isinya
urusan kerja tetap bisa `Distant`. Chat yang pendek tapi hangat dan personal
bisa `Close`.

Hal yang bisa jadi pertimbangan:

- **Isi obrolan:** cuma urusan/logistik, atau ada cerita pribadi, curhat, dan
  candaan internal?
- **Nada:** formal dan sopan berjarak, santai, atau sangat akrab (panggilan
  sayang, ejekan akrab, bahasa "kita banget")?
- **Inisiatif:** dua-duanya sama-sama memulai obrolan, atau hanya satu pihak?
- **Saling peduli:** menanyakan kabar, memberi dukungan, ingat detail hidup
  pihak lain?
- **Keterbukaan:** berani membahas masalah, perasaan, atau hal yang sensitif?

## Definisi level

| Label | Gambaran singkat | Ciri yang biasa terlihat |
|---|---|---|
| **Distant** | Kenal, tapi berjarak. | Obrolan seperlunya: tugas, kerja, transaksi, info. Nada formal atau datar. Jarang ada basa-basi pribadi. Sering ada jeda panjang tanpa obrolan. |
| **Casual** | Akrab secara santai, belum personal. | Nada santai, ada candaan ringan, sesekali ngobrol di luar urusan. Topik masih di permukaan (rencana, info, meme). Jarang curhat. |
| **Close** | Teman dekat. | Sering cerita soal kehidupan masing-masing, saling tanya kabar, ada candaan internal. Ada curhat atau dukungan emosional dan terasa nyaman. Dua arah. |
| **Very close** | Sangat dekat (sahabat, pasangan, keluarga dekat). | Sangat terbuka, termasuk soal hal sensitif. Kontak hampir rutin, gaya bahasa khas berdua, saling mengandalkan. Terasa jelas ada ikatan kuat dari dua pihak. |

## Kalau ragu antara dua level

- Pilih level yang paling cocok untuk **sebagian besar** isi chat, bukan satu
  momen saja.
- Kalau masih seimbang, pilih yang **lebih rendah**. Kedekatan yang kuat
  biasanya terlihat jelas.
- Jangan menilai dari siapa orangnya (misalnya "dia kan teman lama"). Nilai
  hanya dari chat yang kamu baca.
- Kalau chat terlalu sedikit atau tidak bisa dinilai, kosongkan labelnya.

## Privasi

- Jangan menyalin, mengutip, atau screenshot isi chat ke mana pun, termasuk
  grup tugas.
- `sampel-chat/`, `closeness_labels.csv`, dan file hasil sudah masuk
  `.gitignore`. Jangan di-commit dan jangan diunggah.
