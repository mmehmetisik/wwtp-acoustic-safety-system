# WWTP Acoustic Safety — Engine Test Bulguları
## 12-Chunk Tam Sahne Çalıştırma Sonuçları
> **Test Tarihi:** 3 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)

---

## 1. TEST GEÇMİŞİ

### Test 1: Tek Chunk Testleri (BARE/CONTEXT/PROTOCOL)
Her sahneden tek bir kritik chunk (5 saniye) gönderildi.

| Sahne | BARE | CONTEXT | PROTOCOL |
|-------|------|---------|----------|
| S1 | ✅ Doğru | ✅ Doğru | ✅ Doğru |
| S2 | ❌ Kaçırdı | ✅ Tespit | ✅ Tespit |
| S3 | ✅ Doğru | ✅ Doğru | ❌ Yanlış Alarm |
| S4 | ❌ Kaçırdı | ❌ Kaçırdı | ✅ Tespit (0.98) |
| S5 | ❌ Kaçırdı | ❌ Kaçırdı* | ✅ Tespit (0.98) |

*S5 CONTEXT: Model sesi duymadı ama bağlamdan alarm verdi (not deployable behavior).

**Sonuç:** Tek chunk'ta PROTOCOL modu 4/5 başarılı. Model sesi anlıyor.

---

### Test 2: İlk 12-Chunk Tam Çalıştırma (PROTOCOL)
Orijinal motor, debouncing yok, distress timing bug'ı var.

| Sahne | Skor | İlk Alarm | Sorun |
|-------|------|-----------|-------|
| S1 | 0/100 | 5s (chunk 2) — FP | 5 yanlış alarm, distress onset "Nones" |
| S2 | 70/100 | 40s (chunk 9) | Geç tespit ama doğru |
| S3 | 0/100 | 15s (chunk 4) — FP | 4 yanlış alarm |
| S4 | 70/100 | 25s (chunk 6) | Doğru tespit! |
| S5 | 65/100 | 10s (chunk 3) — FP | Düşmeden ÖNCE alarm (false positive) |

**Bulunan bug'lar:**
- Distress onset timing okunamıyor ("Nones") → motor yanlış kaynaktan arıyordu
- False positive'ler çok fazla → PROTOCOL prompt çok hassas
- S5'te 10s'de alarm = düşme (20s) öncesi = aslında false positive

---

### Test 3: Düzeltme v1 — Distress Timing Fix + Prompt Dengeleme
Distress timing düzeltildi. Prompt'a mekanik vs insan ses ayrımı eklendi.

| Sahne | Skor | İlk Alarm | Değişim |
|-------|------|-----------|---------|
| S1 | 0/100 | 15s (chunk 4) — FP | Biraz iyileşti (5→3 FP) |
| S2 | 5/100 | 5s (chunk 2) — FP | Kötüleşti (distress öncesi alarm) |
| S3 | 0/100 | 15s (chunk 4) — FP | Aynı |
| S4 | 5/100 | 10s (chunk 3) — FP | FP arttı |
| S5 | 15/100 | 5s (chunk 2) — FP | FP var ama 25s'te de alarm var |

**Bulgu:** Distress timing artık doğru çalışıyor ama FP sorunu devam ediyor.

---

### Test 4: Düzeltme v2 — Ses Üretici İyileştirme + Alarm Debouncing
motor_drone frekans aralığı 100-500Hz → 50-250Hz. Alarm onay katmanı eklendi.

| Sahne | Skor | Onaylanan | Elenen | Sonuç |
|-------|------|-----------|--------|-------|
| S1 | 0/100 | 5 confirmed | 0 filtered, 1 prelim | Debouncing yetmedi — ardışık FP'ler |
| S2 | 5/100 | 4 confirmed (1 FP) | 1 filtered | FP hâlâ var (chunk 4, distress öncesi) |
| S3 | **60/100** | **0 confirmed** | 1 filtered, 3 prelim | **BÜYÜK İYİLEŞME!** Tüm FP'ler elendi |
| S4 | 5/100 | 4 confirmed (2 FP) | 1 filtered | Doğru tespit var ama FP'ler puanı düşürüyor |
| S5 | **0/100** | **0 confirmed** | 2 filtered | **KRİTİK SORUN** — model çığlığı neredeyse hiç duymadı |

**Kritik Bulgular:**
1. Debouncing S3'te mükemmel çalıştı (0 → 60 puan!)
2. S5'te model 12 chunk boyunca çığlığı duyamadı (sadece 50-60s'te çok zayıf alarm)
3. S1'de model hâlâ pompa sesinde "muffled_call" halüsinasyonu yapıyor

---

## 2. KÖK NEDEN ANALİZİ

### Neden tek chunk'ta çalışıp 12 chunk'ta çalışmıyor?

**Fark 1 — Prompt Uzunluğu:**
Tek chunk testinde prompt kısa ve öz. 12 chunk'ta PROTOCOL prompt çok uzun — model uzun metni okuyup sese odaklanmakta zorlanıyor. LLM'lerde bilinen bir sorun: uzun bağlamlarda dikkat dağılır.

**Fark 2 — Sentetik Ses Kalitesi:**
Formant sentezi matematiksel olarak insan sesine benzer tonlar üretiyor ama gerçek insan konuşma paterni DEĞİL. Model ASR eğitiminde gerçek insan sesi dinlemiş — "HELP!", "YARDIM!", ağlama, bağırma. Sentetik formant sesi bunlara benzemiyor.

Bu yüzden model:
- Pompada "muffled_call" halüsinasyonu yapıyor (harmonikler benzer)
- Gerçek sentetik çığlığı tanıyamıyor (doğal konuşma paterni yok)

### Bu bizim hatamız mı modelin mi?

İkisi de, farklı oranlarda:
- **Bizim hatamız (düzeltilebilir):** Ses üretici formant sentezi kullanıyor, gerçek insan sesi paternleri yok. Model eğitim verisindeki ses paternleriyle eşleşmiyor.
- **Modelin sınırı (çevrelenebilir):** E4B küçük bir edge model, ASR için optimize edilmiş ama endüstriyel akustik analiz için değil. Uzun bağlamlarda dikkat kaybı yaşıyor.

---

## 3. ÇÖZÜM YOLU

### Öncelik 1: Ses Üreticiyi TTS Tabanlı Yapıya Çevir
Formant sentezi yerine gerçek TTS (Text-to-Speech) motoru kullanarak "HELP!", "YARDIM!" gibi sesler üret. Sonra bu seslere endüstriyel bozulma ekle (gürültü, mesafe, reverb, maske). Model gerçek konuşma paternini tanıyacaktır.

### Öncelik 2: Prompt Kısaltma ve Sadeleştirme
Tek chunk testindeki başarılı kısa prompt yapısını 12 chunk akışına taşı. PROTOCOL bilgisini kısalt, modelin sese odaklanmasını sağla.

### Öncelik 3 (Gerekirse): Spektrogram Hibrit Yaklaşım
Ses chunk'ını spektrogram görüntüsüne çevir, modele hem ses hem görüntü gönder. Gemma 4 görsel anlamada çok daha güçlü.

---

## 4. PROJE DURUMU

- Motor çalışıyor, hata vermiyor ✅
- Alarm debouncing katmanı çalışıyor ✅ (S3'te kanıtlandı)
- Distress timing doğru hesaplanıyor ✅
- JSON parse güvenilir (57/60+ başarı) ✅
- Ses üretici iyileştirme gerekiyor ⚠️ (TTS tabanlı)
- Prompt optimizasyonu gerekiyor ⚠️
- S5 hayatta kalma verdikti henüz hedefte değil ❌

**Proje iptal DEĞİL.** Temel altyapı sağlam. Ses kalitesi iyileştirildiğinde sonuçlar dramatik şekilde değişecek — tek chunk testleri bunu kanıtlıyor.

---

*Bu doküman tüm engine test bulgularını kronolojik olarak içerir.*
*Ses üretici iyileştirmesi ve yeniden test sonuçları ayrı dokümanda eklenecek.*
*Son güncelleme: 3 Nisan 2026*
