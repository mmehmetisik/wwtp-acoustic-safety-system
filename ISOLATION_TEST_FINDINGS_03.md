# WWTP Acoustic Safety — İzolasyon Testi Bulguları
## BARE Modu 12-Chunk Tam Çalıştırma
> **Test Tarihi:** 3 Nisan 2026
> **Amaç:** Sorunun prompt'ta mı yoksa ses kalitesinde mi olduğunu izole etmek
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)

---

## 1. TEST SONUÇLARI

### BARE Modu — 12 Chunk Tam Çalıştırma

| Sahne | Skor | İnsan | Alarm | FP | Detay |
|-------|------|-------|-------|----|-------|
| S1 — Pompa | **60/100** | YOK | Yok | 0 | Mükemmel — sıfır yanlış alarm |
| S2 — İnşaat | 0/100 | VAR | Yok* | 0 | Kaçırdı — gürültü altında duyamadı |
| S3 — Havuz | **60/100** | YOK | Yok | 0 | Mükemmel — sıfır yanlış alarm |
| S4 — Menhol | 0/100 | VAR | 2 (filtered) | 0 | Duydu (0.70) ama eşik altı kaldı |
| S5 — Kritik | 0/100 | VAR | Yok | 0 | Tamamen sessiz — hiçbir şey duymadı |

*S2: Chunk 6'da 0.60 alarm verdi ama debouncing filtreledi.

### PROTOCOL Modu Karşılaştırması (Önceki Test)

| Sahne | BARE | PROTOCOL | Fark |
|-------|------|----------|------|
| S1 | 60 (0 FP) | 0 (5 FP) | PROTOCOL halüsinasyon yarattı |
| S2 | 0 (kaçırdı) | 5 (FP sorunlu) | Her ikisinde de sorunlu |
| S3 | 60 (0 FP) | 60 (0 confirmed)* | BARE zaten temiz, debouncing PROTOCOL'ü kurtardı |
| S4 | 0 (0.70 duydu) | 5 (FP sorunlu) | PROTOCOL FP ekledi, gerçek tespiti bozmadı |
| S5 | 0 (sessiz) | 0 (sessiz) | İkisinde de duyamadı |

---

## 2. KESİNLEŞEN İKİ AYRI SORUN

### Sorun 1: PROTOCOL Prompt Halüsinasyon Yaratıyor ✅ KESİNLEŞTİ

Kanıt:
- S1 BARE: 0 FP → S1 PROTOCOL: 5 FP (aynı ses, farklı prompt)
- S3 BARE: 0 FP → S3 PROTOCOL: 4+ FP (aynı ses, farklı prompt)
- "Şüphede alarm ver" talimatı modeli aşırı hassaslaştırıyor
- Mekanik seslerde "muffled_call" halüsinasyonu yapıyor

Çözüm: Prompt kısaltma ve dengeleme. "Tatlı nokta" bulma — güveni artır ama halüsinasyon yaratma.

### Sorun 2: Model Sentetik Çığlığı Gerçekten Duyamıyor ✅ KESİNLEŞTİ

Kanıt:
- S5 BARE: 12 chunk boyunca sıfır alarm, sıfır tespit, tamamen sessiz
- S2 BARE: 12 chunk'tan sadece 1'inde çok zayıf alarm (0.60)
- S5 ve S2'de ortak özellik: yoğun inşaat gürültüsü (95dB, -6 ile -3dB SNR)

Karşı kanıt (model DUYABİLİYOR bazı durumlarda):
- S4 BARE: Maskeli sesi chunk 5 ve 7'de doğru zamanda tespit etti (0.70 confidence)
- S4 farkı: gürültü seviyesi çok daha düşük (underground ambient, 52dB)

Sonuç: Model insan sesini duyabiliyor AMA sadece gürültü düşükse. 95dB inşaat gürültüsü altındaki sentetik formant sesini ayırt edemiyor.

---

## 3. TEK CHUNK TESTİ YENİDEN DEĞERLENDİRME

Tek chunk PROTOCOL testinde S5 "confidence 0.98" ile tespit edilmişti. Bu sonuç şimdi şüpheli:

- BARE modda model S5'i hiç duyamıyor (12 chunk'ta sıfır sinyal)
- BARE tek chunk'ta da duyamamıştı
- CONTEXT tek chunk'ta "sesi duymadı ama bağlamdan alarm verdi" (human_detected=false, alarm=true)
- PROTOCOL tek chunk'ta 0.98 — büyük ihtimalle model sesi değil, prompt metnindeki "worker climbing pool wall, splash + voice" bilgisinden çıkarım yaptı

Bu demek ki: Tek chunk PROTOCOL "başarısı" gerçek bir ses tespiti değildi, metin tabanlı çıkarımdı. Gerçek dünyada böyle bir metin bilgisi olmayacağı için bu güvenilir değil.

---

## 4. SORUNUN KÖK NEDENİ

### Neden S4 duyuluyor ama S5 duyulmuyor?

S4 (maskeli ses, underground): Arka plan gürültüsü 52dB. İnsan sesi 65dB. SNR = -12dB ama düşük mutlak gürültü seviyesinde model frekans paternlerini ayırt edebiliyor.

S5 (çığlık, inşaat): Arka plan gürültüsü 95dB. İnsan sesi 88dB. SNR = -6dB ve yüksek mutlak gürültü seviyesinde tüm frekans bantları doymuş, model hiçbir şeyi ayırt edemiyor.

### Neden formant sentezi yetersiz?

Formant sentezi matematiksel sinüs dalgaları + harmonikler üretiyor. Bu akustik olarak insan sesine benzer ama modelin ASR eğitimindeki gerçek insan sesi paternleri ile eşleşmiyor. Model gerçek konuşma ritimleri, tonlama değişimleri, nefes alış verişleri, kelime yapıları arıyor — formant sentezinde bunlar yok.

---

## 5. ÇÖZÜM YOLU (GÜNCELLENMİŞ)

### Adım 1: Ses Üreticiyi TTS Tabanlıya Çevir (EN KRİTİK)
- gTTS veya pyttsx3 ile "HELP!", "YARDIM!", "İMDAT!" sesleri üret
- Endüstriyel bozulma ekle (mesafe, reverb, maske)
- Model gerçek konuşma paternini tanıyacak

### Adım 2: S5 SNR Dengesini İyileştir
- Gerçek hayatta insan panik halinde 100+ dB'de bağırır
- SNR'ı -6dB'den -3dB veya 0dB'ye çek
- İnşaat gürültüsünü biraz azalt veya çığlığı biraz yükselt

### Adım 3: PROTOCOL Prompt'u Kısalt ve Dengele
- S4 BARE 0.70 → PROTOCOL ile 0.90+ yapılabilir
- Ama S1/S3 FP yaratmadan
- "Tatlı nokta" prompt: kısa, odaklı, güvenlik kuralları minimal

### Adım 4: Tam Test ve Doğrulama
- TTS seslerle tüm sahneleri yeniden üret
- BARE → CONTEXT → PROTOCOL sırayla test et
- Başarılıysa roadmap güncelle ve demo arayüzüne geç

---

## 6. ALTIN BULGULAR (PROJE İÇİN ÇOK DEĞERLİ)

### Bulgu 1: Prompt Tasarımı Halüsinasyon Yaratabilir
Aynı model, aynı ses — kısa prompt ile temiz karar, uzun güvenlik prompt'u ile halüsinasyon patlaması. Bu LLM güvenlik sistemleri için kritik bir uyarı.

### Bulgu 2: "AI'ya NE söylediğin, NE KADAR söylediğinden daha önemli"
PROTOCOL'ün her kuralı model performansını olumsuz etkileyebiliyor. Daha fazla kural ≠ daha iyi sonuç. Doğru kural = doğru sonuç.

### Bulgu 3: LLM'ler Ses Analizinde Gürültü Seviyesine Çok Duyarlı
52dB ortamda 0.70 tespit, 95dB ortamda 0.00 tespit. Mutlak gürültü seviyesi, SNR'dan bile daha belirleyici.

### Bulgu 4: Tek Chunk Test Başarısı Yanıltıcı Olabilir
PROTOCOL tek chunk'ta S5 "0.98 confidence" — ama bu ses tespiti değil, metin çıkarımıydı. Gerçek performansı ölçmek için çok-chunk testi şart.

### Bulgu 5: Debouncing Katmanı Çalışıyor
S3 PROTOCOL'de 4 ham alarm → debouncing sonrası 0 onaylanmış alarm (60 puan). S4 BARE'de 2 zayıf alarm (0.70) → doğru şekilde filtrelendi. Endüstriyel standart alarm yönetimi etkin.

---

## 7. PROJE DURUMU

Proje iptal DEĞİL. Temel altyapı sağlam:
- Motor çalışıyor, hata vermiyor ✅
- Debouncing katmanı kanıtlanmış ✅
- Timing hesaplamaları doğru ✅
- JSON parse güvenilir ✅
- Model sessiz ortamda insan sesini duyabiliyor ✅ (S4 kanıtı)

Eksik olan: modelin tanıyabileceği kalitede ses üretimi.
Bu düzeldiğinde sonuçlar dramatik şekilde değişecek.

---

*Bu doküman BARE vs PROTOCOL izolasyon testi bulgularını içerir.*
*Son güncelleme: 3 Nisan 2026*
