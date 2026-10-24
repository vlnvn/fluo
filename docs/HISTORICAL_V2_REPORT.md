# FLUO P1 v2 — Hasil eksperimen sintetis dan batas operasional

**Status 24 Oktober 2026:** bukti *synthetic replay* untuk ML dan decision-support tersedia; **tidak ada validasi industri atau klaim penghematan nyata**. Tidak ada otomatisasi valve, boiler, atau recovery.

## Ringkasan

- Input: 13 kolom telemetri dari simulator fisika sizing sepenuhnya sintetis; label ground truth hanya digunakan sebagai target training supervised (split TRAIN) dan untuk evaluasi, **tidak pernah sebagai fitur inference**.
- Model baru: `HistGradientBoostingClassifier`, dilatih di dataset v1 TRAIN (konfigurasi A/B) pada fitur rasio residual, smoothing, perubahan steam dan variabilitas. Target belajar adalah **tanda defisit teramati** (kejadian kehilangan fisik ATAU meter return underreading), **bukan konfirmasi penyebab fisik**.
- Tiga seed pengembangan terpisah untuk seleksi ambang, dua seed yang tidak digunakan tuning untuk pengujian terkunci. Pada setiap seed pengujian ada lima konfigurasi fiktif (A–E), termasuk konfigurasi baru D/E. Semua memakai keluarga simulator yang sama.
- Frozen threshold AI = 0,90 (skor classifier yang **tidak terkalibrasi sebagai probabilitas kebocoran**); filter 5 dari 10 menit, valid production + warmup + konektivitas. Baseline tetap: fixed-ratio 0,15 dan physics residual 0,09 dengan persistence sama. Threshold dipilih/ditetapkan sebelum membaca label locked.

## Hasil pada LOCKED synthetic evaluation

| Metode | Deteksi episode fisik | Delay disturbance memicu alarm | Bias meter memicu alarm | Klaster alarm pada clean window | Median delay deteksi |
|---|---:|---:|---:|---:|---:|
| Fixed ratio | 68/68 | 18/18 | 18/18 | 146 | 6 menit |
| Physics residual | 66/68 | 18/18 | 18/18 | 0 | 12 menit |
| ML signature | **66/68** | **2/18** | 18/18 | **0** | **10 menit** |

Total locked: 172,800 baris, 103,287 menit yang memenuhi gate, 1347.2 jam valid *clean* setelah episode dan jendela ±45 menit dikecualikan. '0 klaster' berlaku **hanya pada clean window**, bukan semua baris berlabel normal.

**Missed**: 2/68 physical loss `trap_blowthrough` pada CFG_C. **Delay nuisance**: 2/18. Model tidak boleh diklaim sempurna. Sebaran kejadian masih diatur generator, sehingga interval kepercayaan yang dihitung tidak dapat dipakai memperkirakan sensitivitas di industri.

### Temuan penting stress test POST-HOC

Pada sensor asli synthetic locked, setelah efek kejadian, model dapat mengeluarkan warning di baris yang berlabel `none`: misalnya 240 dan 230 menit per seed pada 45.852/45.702 menit observed normal (termasuk aftereffects); tercatat 38 dan 39 cluster masing-masing. Evaluasi utama memakai jendela bersih yang lebih konservatif untuk menilai false warning di luar aftereffects. **Kedua pengukuran harus disampaikan bersama** agar tidak menipu.

Jika flowmeter return selalu underread 10%, model memicu >32 ribu warning-minute di masing-masing seed. Ini berarti **kalibrasi/pemeriksaan instrumentasi dan commissioning yang diverifikasi sebelum penggunaan nyata adalah WAJIB**. Stress test dilakukan setelah evaluasi locked, bukan hasil prospektif.

### Keterbatasan identifikasi

Meter bias dan kehilangan fisik dapat membentuk pola observasi yang identik; tanpa informasi sensor tambahan, inspeksi atau tindakan pembuktian, penyebabnya **tidak dapat diidentifikasi secara unik**. Maka keluaran AI adalah *investigate return deficit, cause unconfirmed*, memprioritaskan verifikasi meter dan mode sebelum inspeksi return/drain/steam trap. Recovery hanya setelah kajian kualitas kondensat dan otorisasi engineer.

## Perbedaan dari model v1

- V1 Isolation Forest (unsupervised) gagal mendeteksi 0/2 dan 0/5 physical event pada dua test dataset lama dengan ambang validation q99; hasil test lama **sudah dilihat**, tidak dapat menjadi evaluasi prospektif v2.
- V2 menggunakan supervised synthetic target dan kalibrasi melalui seed pengembangan, lalu diuji pada set baru. V1 dan V2 **tidak sama metode pelatihan maupun test set**; jangan menyebut rasio skor mereka sebagai kenaikan produksi yang terukur.

## Status TKT

Dukungan konseptual TKT 3 lebih kuat: ada data/simulator, pelatihan nyata, baseline, uji negatif, prototipe inference dan QA decision-support. Bukti integrasi perangkat IoT fisik, sensor industri, kalibrasi fasilitas, dan penilaian laboratorium TKT4 masih belum ada; **jangan mengklaim TKT4 lengkap**. Prototipe aplikasi *synthetic replay* dapat dilanjutkan ke web.

## Gate penerapan

- GO: riset berbasis simulasi, demonstrasi replay, komponen inference + advice read-only, perbandingan baseline.
- NO-GO: alarm produksi, diagnosis kebocoran pasti, pilot tanpa persetujuan, pengembalian kondensat otomatis, klaim hemat air/energi.
- Wajib berikutnya untuk fasilitas nyata: kebutuhan meter dan P&ID, kalibrasi, validasi model shift/domain, quality test kondensat dan engineer safety review.

## Referensi dasar generator (bukan data operasional)

- forbes_marshall_case: https://www.forbesmarshall.com/country-highlights-indonesia/optimising-energy-and-efficiency-at-a-textile-plant-in-western-indonesia/
- steam_table: https://www.spiraxsarco.com/learn-about-steam/steam-engineering-principles-and-heat-transfer/what-is-steam
- flash: https://www.spiraxsarco.com/learn-about-steam/condensate-recovery/flash-steam
- doe: https://www.osti.gov/biblio/15000711
- unido_atira: https://downloads.unido.org/ot/47/89/4789812/10001-15000_10251.pdf

## Cara reproduce

Gunakan Python 3 dan `pip install -r requirements.txt` di root paket. Jalankan `python run_fluo_v2.py` untuk melatih ulang dan mengevaluasi; `python qa_and_demo.py` untuk QA dan contoh output P2; `python robustness_stress.py` untuk stress sensor pascahasil. Kode `prepare_cohorts.py` meregenerasi data dev/locked memakai generator original; seed dibekukan, namun proses ini tidak cepat. Data dev/locked sudah disertakan agar audit langsung bisa dilakukan.

**Catatan reproducibility:** SciPy/sklearn menggunakan float dalam implementasi model, lintas versi library bisa sedikit berubah; gunakan versi pada file `frozen_experiment_config.json` untuk membandingkan. Semua data hanya synthetic engineering scenarios.
