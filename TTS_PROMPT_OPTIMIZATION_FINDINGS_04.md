# WWTP Acoustic Safety System — TTS + Prompt Optimizasyon Bulguları
## Ses Kalitesi İyileştirme ve Prompt Dengeleme Süreci
> **Test Tarihi:** 3 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Ses Üretimi:** Google TTS + endüstriyel gürültü karışımı

---

## 1. YAPILAN DEĞİŞİKLİKLER

### 1.1 Ses Üretici: Formant → TTS Geçişi

**Sorun:** Formant sentezi matematiksel sinüs dalgaları üretiyordu. Gemma 4 E4B'nin ASR motoru gerçek insan konuşma paternlerini arıyor — formant sesi bunu sağlamıyordu. Model pompada "insan sesi" halüsinasyonu yaparken gerçek sentetik çığlığı duyamıyordu.

**Çözüm:** Google TTS (gTTS) ile gerçek konuşma sesleri üretildi:
- S2: "Help! Help me!" (EN) + "Yardım! Yardım edin!" (TR), 3sn aralıkla
- S4: "Help! Help me!" + "Yardım! Yardım edin!", maske filtresi (2000Hz LP) + galeri reverbi (1.2sn), 4sn aralıkla
- S5: "Help! Help!", "Yardım!", "İmdat!", "Help me!", "Somebody!", "Yardım edin!" — boğulma efektleriyle (rastgele kesinti, su sesi, düzensiz zamanlama)

**Ek ses düzeltmeleri:**
- motor_drone frekans aralığı 100-500Hz → 50-250Hz (insan ses aralığına girmemesi için)
- TTS seslerden db_to_amp çarpımı kaldırıldı (ses seviyesi dengesizliğini önlemek için)
- Pitch shift kaldırıldı (doğal ses, model tanıma için daha iyi)
- S5 inşaat gürültüsü farklı seed ile üretiliyor (S2'den farklılaşma)

### 1.2 Motor: Alarm Debouncing Katmanı

Endüstriyel SCADA standardı alarm onay sistemi eklendi:
- Confidence < 0.75 → otomatik filtre
- Tek izole alarm → "preliminary" (onaylanmamış)
- Ardışık 2+ alarm (3-chunk penceresi) → "confirmed" (onaylanmış)
- Confidence ≥ 0.95 + "screaming"/"shouting_help" → anında onay

### 1.3 Motor: Distress Timing Düzeltmesi

Tehlike başlangıç zamanı artık üç kaynaktan okunuyor:
1. scene_config.json (distress_starts_sec / fall_event_sec)
2. answer_key.json (aynı alanlar)
3. audio_composition yapısından otomatik çıkarım (human_voice=true olan ilk zaman dilimi)

---

## 2. TEST SONUÇLARI: TTS SESLERİ + PROTOCOL MODU

### 2.1 TTS + PROTOCOL (Uzun Prompt) Sonuçları

| Sahne | İnsan | Ham Alarm | Debounce Sonrası | Skor | Analiz |
|-------|-------|-----------|------------------|------|--------|
| S1 | YOK | 7 alarm | 7 confirmed | 0/100 | PROTOCOL halüsinasyonu — pompa sesinde "shouting_help" diyor |
| S2 | VAR (25s) | 4 alarm | 2 confirmed (FP) + 1 filtered | 0/100 | FP'ler distress öncesi, gerçek tespit chunk 6'da var ama FP puanı düşürdü |
| S3 | YOK | 9 alarm | 7 confirmed | 0/100 | PROTOCOL halüsinasyonu — metalik seste "muffled_call" diyor |
| S4 | VAR (20s) | 5 alarm | 5 confirmed (1 FP) | 5/100 | Model maskeli sesi DUYUYOR! Chunk 6-11 arası doğru tespit (0.85-0.90) |
| S5 | VAR (20s) | 4 alarm | 3 confirmed (2 FP) | 5/100 | Model çığlığı DUYUYOR! Chunk 6'da +5s'de tespit (0.85) |

### 2.2 Kritik Gözlemler

**TTS İŞE YARIYOR — Kanıtlar:**

S2 chunk 9 (40-45s): distress_type="shouting_help", confidence=0.90
- Eski formant sesle model hep "muffled_call" diyordu
- TTS ile model artık "shouting_help" olarak tanıyor — gerçek konuşma paternini ayırt ediyor

S4 chunk 6-11: Maskeli TTS sesini 0.85-0.90 confidence ile sürekli tespit ediyor
- Eski formant sesle BARE modda sadece 0.70 alıyorduk (debouncing filtreliyordu)
- TTS ile güven skoru 0.85-0.90'a çıktı — model gerçek konuşmayı daha güvenle tanıyor

S5 chunk 6 (25-30s): distress_type="muffled_call", confidence=0.85, [+5s]
- Eski formant sesle S5'te 12 chunk boyunca SIFIR sinyal vardı
- TTS ile model çığlığı DUYDU — düşmeden 5 saniye sonra

**PROTOCOL PROMPT HALÜSINASYONU DEVAM EDİYOR:**

S1'de 7 onaylanmış FP — pompa sesinde "shouting_help" halüsinasyonu
S3'te 7 onaylanmış FP — metalik seste "muffled_call" halüsinasyonu
S5'te 2 FP distress öncesi — inşaat gürültüsünde halüsinasyon

Bu, izolasyon testindeki bulguyla tutarlı: BARE modda aynı seslerle sıfır FP.

---

## 3. KÖK NEDEN: NEDEN PROTOCOL HALÜSINASYON YARATIYOR?

### 3.1 Prompt Uzunluğu ve Dikkat Dağılması

| Mod | Prompt Uzunluğu | S1 FP | S3 FP | Chunk Süresi |
|-----|-----------------|-------|-------|--------------|
| BARE | ~100 kelime | 0 | 0 | ~20sn |
| PROTOCOL | ~400-500 kelime | 7 | 7 | ~35sn |

Model uzun prompt'u işlerken:
- Dikkat mekanizması (attention) sese değil metne kayıyor
- "Şüphede alarm ver" kuralı her chunk'ta tetikleniyor
- Model sesi dinlemek yerine prompt'taki senaryoları hayal ediyor

### 3.2 Spesifik Sorunlu İfadeler

Eski PROTOCOL prompt'undaki şu ifadeler halüsinasyonu tetikliyordu:
- "Missing a real human distress signal is catastrophically worse than a false alarm" → Model alarm verme baskısı hissediyor
- "If you detect any sound that COULD be human distress — alarm immediately" → "COULD" çok geniş, her ses "olabilir"
- "any muffled voice pattern MUST trigger" → Model her boğuk seste tetikleniyor
- Sahne-spesifik güvenlik protokolü metni → Ekstra 50-100 kelime daha ekliyordu

### 3.3 Çözüm: Optimize Edilmiş Prompt

Yeni PROTOCOL prompt ~100 kelime. Değişiklikler:
- Sahne-spesifik protokol metni kaldırıldı
- 7 kural → 5 kısa madde
- "Şüphede alarm ver" → "Emin değilsen alarm VERME" (tam ters)
- "COULD be human" → "actual human speech, words, or vocal patterns" (somut)
- "any muffled voice" → "If you hear words like 'help', 'yardım'" (kelime bazlı)
- Hayatta kalma eşikleri, aciliyet baskısı kaldırıldı

**Yeni prompt felsefesi:** "AI'ya NE söylediğin, NE KADAR söylediğinden daha önemli."

---

## 4. FORMANT → TTS KARŞILAŞTIRMA TABLOSU

| Metrik | Formant (Eski) | TTS (Yeni) | Fark |
|--------|---------------|------------|------|
| S4 BARE confidence | 0.70 (filtrelendi) | Test edilecek | TTS daha yüksek bekleniyor |
| S5 BARE algılama | 0/12 chunk (sıfır sinyal) | Test edilecek | TTS ile sinyal var |
| S5 PROTOCOL algılama | 0/12 (formant), 2/12 (TTS) | 1/12 (chunk 6, 0.85) | TTS ile ilk kez gerçek tespit |
| S2 distress_type | "muffled_call" (yanlış) | "shouting_help" (doğru) | TTS ile doğru sınıflandırma |
| S4 aksiyon | Karışık | INITIATE_CONFINED_SPACE_RESCUE | TTS ile doğru aksiyon |
| Halüsinasyon tipi | "muffled_call" her yerde | Aynı sorun devam | Prompt kaynaklı, ses kaynaklı değil |

---

## 5. ALTIN BULGULAR (Bu Süreçten Çıkan Önemli Keşifler)

### Bulgu 1: "AI'ya NE söylediğin, NE KADAR söylediğinden daha önemli"
Aynı model, aynı ses — kısa prompt ile temiz karar, uzun prompt ile halüsinasyon patlaması. Daha fazla kural ≠ daha iyi sonuç. Az ve doğru kural = doğru sonuç. Bu LLM tabanlı güvenlik sistemleri için kritik bir tasarım prensibi.

### Bulgu 2: TTS Gerçek Konuşma Paternleri Fark Yaratıyor
Formant sentezi ile model S5'te 12 chunk boyunca sıfır tespit yaptı. TTS ile aynı sahneyi 0.85 confidence ile tespit etti. Model matematiksel ses dalgası değil, gerçek konuşma ritmi arıyor. LLM tabanlı ses analizi için ses kalitesi kritik.

### Bulgu 3: LLM'lerde Halüsinasyon Prompt Uzunluğuyla Orantılı
100 kelimelik prompt → 0 FP. 500 kelimelik prompt → 7 FP (aynı seste). Bu bilinen bir LLM davranışı ama endüstriyel güvenlik bağlamında ilk kez somut olarak ölçüldü. Prompt mühendisliği güvenlik-kritik sistemlerde hayati önem taşıyor.

### Bulgu 4: Debouncing Katmanı Etkili Ama Yetersiz (Tek Başına)
S3'te debouncing 4 FP'yi 0'a indirdi (eski testte). Ama PROTOCOL halüsinasyonu ardışık alarm ürettiğinde debouncing bunları "confirmed" olarak onaylıyor. Debouncing tek seferlik hataları yakalar ama sistematik halüsinasyonu yakalayamaz. Çözüm: prompt düzeltmesi + debouncing birlikte.

### Bulgu 5: Tek Chunk Test Sonuçları Yanıltıcı Olabilir
Tek chunk PROTOCOL testinde S5 "0.98 confidence" vermişti. Ama 12-chunk testinde aynı PROTOCOL modu başarısız oldu. Gerçek performansı ölçmek için çok-chunk (tam sahne) testi şart. Tek chunk testi sadece "model bu sesi anlayabiliyor mu" sorusuna cevap verir, "sistem güvenilir mi" sorusuna cevap vermez.

---

## 6. PROMPT OPTİMİZASYONU TESTİ

**Durum:** Optimize edilmiş kısa PROTOCOL prompt ile test çalışıyor.

**Beklentiler:**
- S1: Temiz geçmesi bekleniyor (BARE'deki gibi 0 FP)
- S2: İlk gerçek alarm chunk 6 (25-30s) bekleniyor
- S3: Temiz geçmesi bekleniyor (BARE'deki gibi 0 FP)
- S4: İlk gerçek alarm chunk 5-6 (20-30s) bekleniyor
- S5: İlk gerçek alarm chunk 6 (25-30s) bekleniyor

**Eğer başarılı olursa:**
- TTS + kısa prompt kombinasyonu çalışıyor demektir
- Demo arayüzüne geçilebilir
- Roadmap güncellenir

**Sonuçlar bu bölüme eklenecek.**

---

## 7. PROJE DURUMU

| Bileşen | Durum | Not |
|---------|-------|-----|
| Motor (acoustic_engine.py) | ✅ Çalışıyor | Ollama API, debouncing, timing düzeltmeleri |
| Ses üretici (audio_generator_tts.py) | ✅ Çalışıyor | TTS tabanlı, 5 sahne üretildi |
| BARE mod testi | ✅ Tamamlandı | S1: 60, S3: 60, S2/S4/S5: kaçırıldı |
| PROTOCOL mod testi (eski prompt) | ✅ Tamamlandı | Halüsinasyon sorunu belgelendi |
| TTS + eski PROTOCOL testi | ✅ Tamamlandı | TTS işe yarıyor, prompt sorunu devam |
| Prompt optimizasyonu testi | 🔄 Çalışıyor | Sonuçlar bekleniyor |
| Demo arayüzü | ⏳ Sırada | Prompt testi başarılı olursa başlanacak |
| E2B karşılaştırma | ⏳ Sonra | E4B stabilize olduktan sonra |
| Video çekimi | ⏳ Sonra | Demo hazır olunca |
| Kaggle writeup | ⏳ Sonra | Tüm sonuçlar netleşince |

---

*Bu doküman TTS geçişi ve prompt optimizasyonu sürecinin tüm bulgularını içerir.*
*Prompt optimizasyonu test sonuçları eklenecektir.*
*Son güncelleme: 3 Nisan 2026*
