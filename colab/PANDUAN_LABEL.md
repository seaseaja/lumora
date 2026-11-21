# Panduan pelabelan level kedekatan

Panduan ini dipakai semua anggota saat mengisi `colab/closeness_labels.csv`, supaya label kita bisa dibandingkan dengan skor Lumora. Kalau tiap orang punya patokan sendiri soal "dekat", angka akurasinya tidak berarti apa-apa.

## Sebelum mulai

- **Izin dulu.** Pakai chat yang orang di dalamnya sudah setuju dianalisis. Export tanpa media (*Export chat → Without media*).
- **Labeli sebelum lihat skor app.** Jangan upload chat ke Lumora atau menjalankan script sebelum labelmu selesai. Kalau sudah lihat skornya, label kita ikut terpengaruh.
- **Jangan diskusi label dengan anggota lain sebelum semua selesai.** Kesepakatan antar penilai juga diukur; kalau sudah berunding, angkanya jadi palsu.
- **Nilai cara mereka berkomunikasi di chat ini saja**, bukan apa yang kamu tahu soal hubungan mereka di luar chat.
- Baca sekilas **minimal 3 bagian**: awal, tengah, dan bulan-bulan terakhir chat.

## Empat level

| Label | Ciri yang terlihat di chat |
|---|---|
| **Distant** | Jarang chat (sesekali dalam sebulan). Sering cuma satu orang yang ngechat. Balasan lama (berjam-jam/berhari-hari). Isinya urusan seperlunya: tanya tugas, info, janjian sekali. |
| **Casual** | Chat beberapa kali seminggu. Dua-duanya ikut, tapi satu orang jelas lebih aktif. Balasan tidak selalu cepat. Obrolan santai ada, tapi jarang panjang atau personal. |
| **Close** | Chat hampir tiap hari atau rutin. Dua-duanya sama-sama mulai obrolan. Balasan biasanya cepat. Ada candaan, cerita pribadi, saling dukung. |
| **Very close** | Chat tiap hari dan panjang. Sangat seimbang. Balasan cepat. Sering ada ungkapan sayang/kangen/terima kasih, cerita hal pribadi, dan saling cek kabar tanpa alasan khusus. |

Kalau ragu di antara dua level, pilih yang **lebih rendah**, lalu tulis alasannya di kolom catatan (lihat di bawah).

## Yang bukan ukuran kedekatan di sini

- **Status hubungan.** Pacar bisa saja jarang chat; teman bisa chat tiap hari. Nilai chat-nya.
- **Pertengkaran.** Orang yang dekat juga bisa bertengkar. Konflik dibahas terpisah di bagian *Communication patterns*.
- **Jumlah stiker/foto.** Media tidak ikut dihitung app.

## Cara mengisi CSV

Satu baris per chat per penilai. Kolom `file` harus sama persis dengan nama file chat.

```csv
file,rater,label
WhatsApp Chat - sampel1.txt,GW,Close
WhatsApp Chat - sampel1.txt,SE,Very close
WhatsApp Chat - sampel2.zip,GW,Distant
```

- `rater`: inisialmu (jangan nama lengkap).
- `label`: `Distant`, `Casual`, `Close`, `Very close`. Boleh juga `1`–`4` atau `jauh` / `biasa` / `dekat` / `sangat dekat`.
- Mau mencatat alasan? Tambahkan kolom `catatan` di paling kanan; script mengabaikannya.

## Berapa banyak?

- **Minimal 20 chat**, idealnya 30 atau lebih, dan sebisa mungkin tersebar di keempat level. Kalau semua sampel chat sahabat dekat, akurasi "Distant" tidak bisa diukur.
- **Minimal 2 penilai per chat**, supaya tingkat kesepakatan antar penilai bisa dihitung. Kalau sesama manusia saja sering beda pendapat, wajar kalau app juga tidak sempurna.

## Setelah semua selesai

```powershell
venv\Scripts\python colab\validate_closeness.py
```

Hasil yang perlu dicatat di laporan: *exact level match*, *within one level*, *Spearman*, *raters fully agree*, dan confusion matrix. Kalau script bilang skor app cenderung terlalu tinggi atau terlalu rendah, batas level di `closeness.py` (`CLOSENESS_LEVELS`) bisa disesuaikan, lalu jalankan `python -m unittest discover tests` untuk memastikan tidak ada yang rusak.

File CSV label dan hasilnya tidak masuk Git, karena nama file chat bisa berisi nama orang.
