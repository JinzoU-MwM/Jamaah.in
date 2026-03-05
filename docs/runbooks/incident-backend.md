# Backend Incident Runbook

## Scope

Gunakan runbook ini saat terjadi incident backend produksi: error spike, latency spike, atau cost spike Gemini.

## 1) Triage Cepat (0-5 menit)

1. Cek dashboard:
   - `HTTP error rate`
   - `HTTP p95 latency`
   - `Gemini calls rate`
   - `Gemini cache hit ratio`
2. Tentukan klasifikasi incident:
   - `availability` (5xx naik tajam)
   - `performance` (latency tinggi)
   - `cost` (Gemini call volume melonjak)

## 2) Investigasi (5-20 menit)

1. Ambil sampel request dari log dengan `request_id`.
2. Cek endpoint yang paling berkontribusi pada:
   - `http_errors_total`
   - `http_request_duration_seconds`
3. Untuk incident AI:
   - cek rasio `gemini_cache_requests_total{result="hit|miss"}`
   - cek apakah ada perubahan `prompt_version` / `model`.

## 3) Mitigasi

1. Error spike:
   - rollback deploy terakhir jika regresi jelas.
   - aktifkan feature flag untuk mematikan jalur bermasalah.
2. Latency spike:
   - throttle endpoint berat.
   - kurangi concurrency OCR sementara.
3. Cost spike Gemini:
   - verifikasi persistent cache aktif.
   - naikkan TTL cache AI sementara.
   - limit request burst dari endpoint OCR.

## 4) Verifikasi Recovery

1. Error rate kembali < 3% selama 10 menit.
2. p95 latency turun ke baseline.
3. Gemini calls/hour kembali normal dan hit ratio membaik.

## 5) Post-Incident

1. Buat ringkasan:
   - timeline
   - root cause
   - blast radius
   - tindakan perbaikan permanen
2. Buat issue follow-up dengan label `type:ops` dan `prio:P1/P0` sesuai dampak.
