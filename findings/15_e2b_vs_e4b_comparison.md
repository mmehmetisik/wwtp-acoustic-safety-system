# WWTP Acoustic Safety — Gemma 4 E2B vs E4B Model Karşılaştırması
## 2 Milyar mı, 4 Milyar mı? Edge AI İçin Minimum Model Boyutu
> **Test Tarihi:** 6 Nisan 2026
> **Modeller:** Gemma 4 E2B (2B parametre) vs Gemma 4 E4B (4B parametre)
> **Runtime:** Ollama v0.20.0, RTX 3060 6GB, tamamen yerel
> **Koşullar:** Aynı ses dosyaları, aynı spektrogram, aynı few-shot örnekler, aynı CoT prompt, aynı debouncing, aynı temperature=0. Tek fark: model boyutu.

---

## 1. NEDEN BU TESTİ YAPTIK?

Yarışma (Gemma 4 Good Hackathon) özellikle "E2B and E4B models for edge-based solutions" diyor. Biz tüm optimizasyonu E4B üzerinde yaptık ve 91.0/100 skora ulaştık. Ama kritik bir soru vardı: "Aynı pipeline daha küçük modelle çalışır mı?"

Bu soru sadece akademik değil — pratik. E2B daha küçük (2B vs 4B parametre), daha hızlı (chunk başı ~6s vs ~7s), daha az RAM kullanıyor. Eğer E2B de çalışsaydı, Raspberry Pi Zero gibi çok daha ucuz donanımlara deploy edilebilirdi. Ama çalışmadı — ve neden çalışmadığı projenin en öğretici bulgularından biri.

---

## 2. SONUÇLAR — FELAKET SEVİYESİNDE FARK

### Ana Skor Tablosu

| Sahne | Açıklama | İnsan | E4B Skor | E4B FP | E2B Skor | E2B FP |
|-------|----------|-------|----------|--------|----------|--------|
| S1 | Pompa dairesi (sessiz, insan yok) | YOK | **60** | 0 | **0** | 12 |
| S2 | İnşaat + bağırma | VAR | **95** | 0 | **0** | 5 |
| S3 | Metalik ses (insan yok) | YOK | **60** | 0 | **0** | 12 |
| S4 | Maskeli işçi (zayıf sinyal) | VAR | **100** | 0 | **0** | 4 |
| S5 | GERÇEK KAZA (boğulma) | VAR | **100** | 0 | **5** | 4 |
| **WGT AVG** | | | **91.0** | **0** | **2.0** | **37** |

### Detaylı Karşılaştırma

| Metrik | E2B (2B) | E4B (4B) | Fark |
|--------|----------|----------|------|
| Weighted Average | 2.0 | 91.0 | **45.5x** |
| Toplam False Positive | 37/60 | 0/60 | **∞ iyileşme** |
| Toplam Doğru Tespit | Anlamsız (her yere alarm) | 8/60 (hedefli) | — |
| S5 Survival Verdict | "CERTAIN" ama sahte | CERTAIN (gerçek) | — |
| CoT Reasoning | Çalışmıyor | Çalışıyor | Kritik fark |
| Chunk Başı Süre | ~6.2s | ~7.0s | E2B %12 hızlı |
| Tutarlılık | Tutarlı (ama tutarlı yanlış) | 7/7 tutarlı doğru | — |

---

## 3. E2B NE YAPTI? (Detaylı Analiz)

### E2B'nin Davranışı: "Her Şeye Alarm Ver"

E2B 5 sahnede toplam 60 chunk analiz etti. 60 chunk'ın **60'ında** alarm verdi. Her sahnede, her chunk'ta, insan olsun olmasın, gürültü olsun olmasın — 0.90-0.95 confidence ile "speech" tespit ettiğini iddia etti.

Bu, benchmark tasarımındaki "naive baseline — always alarm" senaryosunun birebir karşılığı. `answer_key.json`'daki hesaplamaya göre naive always-alarm baseline'ın tahmini skoru: 20. E2B bunun bile altında kaldı: **2.0**.

### Sahne Bazlı Analiz

**S1 — Pompa Dairesi (İnsan YOK):**
E4B: 12 chunk, 0 alarm, 0 FP → 60/100.
E2B: 12 chunk, 12 alarm, 12 FP → 0/100.
E2B sadece pompa sesi olan sahnede 12 kez "speech" dedi. CoT talimatını ("dikey çizgi = mekanik, yatay bant = formant") tamamen görmezden geldi.

**S2 — İnşaat + İnsan Sesi:**
E4B: İnsan olmayan 5 chunk'ta sessiz, chunk 6'da alarm (doğru), chunk 12'de alarm (doğru) → 95/100.
E2B: 12 chunk'ın 12'sinde alarm. İnsan olmayan chunk 1-5'te de alarm (5 FP). İnsan var mı yok mu fark etmiyor → 0/100.

**S3 — Metalik Ses (İnsan YOK):**
E4B: 12 chunk, 0 alarm, 0 FP → 60/100. CoT "dikey çizgi = metalik darbe" kuralını uyguladı.
E2B: 12 chunk, 12 alarm, 12 FP → 0/100. Metalik sesi insan sesi sandı. CoT kuralı çalışmadı.

**S4 — Maskeli İşçi:**
E4B: İnsan olmayan 5 chunk'ta sessiz, chunk 6-12'de 5 doğru alarm → 100/100.
E2B: 12 chunk'ın 12'sinde alarm. İnsan öncesi 4 chunk'ta FP. Doğru tespit var ama FP'ler yüzünden skor 0 → 0/100.

**S5 — Gerçek Kaza:**
E4B: Chunk 6'da 0.75 ile tek doğru alarm, CERTAIN SURVIVAL → 100/100.
E2B: 12 chunk'ın 12'sinde alarm. İnsan öncesi 4 chunk'ta FP. Tespit var ama güvenilmez → 5/100.
E2B'nin S5'te "CERTAIN SURVIVAL" vermesi yanıltıcı — zaten chunk 1'den itibaren alarm veriyor, yani düşme olmasa da alarm verirdi. Bu tespit değil, rastgele alarm.

---

## 4. NEDEN E2B BAŞARISIZ OLDU?

### 4.1 CoT Reasoning Kapasitesi Yetersiz

E4B'nin başarısı Chain-of-Thought 3 adımlı akıl yürütmeye dayanıyor: (1) dikey çizgileri ara → metalik, alarm verme; (2) eğimli yatay bantları ara → formant; (3) sadece formant varsa alarm ver. Bu üç adımlı mantık zinciri E4B'de çalışıyor ama E2B'de çalışmıyor. E2B prompt'taki talimatları takip edemiyor — "SADECE formant görürsen alarm ver" kuralını anlayamıyor.

2 milyar parametre bu seviyede talimat takibi (instruction following) için yetersiz. E2B muhtemelen prompt'un sadece "alarm", "human", "speech" gibi anahtar kelimeleri yakalayıp her spektrograma "speech detected" cevabı veriyor.

### 4.2 Few-Shot Kalibrasyon Çalışmıyor

E4B'ye 4 referans spektrogram gösterdiğimizde (3 temiz + 1 insan), model bu örneklerden öğrenip farklı paternleri ayırt ediyor. E2B aynı örnekleri görüyor ama ayırt etme kapasitesi yok — her spektrogramı "insan var" olarak sınıflandırıyor.

### 4.3 Vision Analiz Kapasitesi Düşük

Spektrogramdaki görsel paternleri (dikey çizgiler vs eğimli bantlar vs düz gürültü) ayırt etmek sofistike görsel analiz gerektiriyor. E2B'nin vision modülü bu inceliği yakalayamıyor. E4B'nin ekstra 2 milyar parametresi tam da bu görsel akıl yürütme kapasitesini sağlıyor.

---

## 5. BU BULGUNUN WRITEUP İÇİN DEĞERİ

Bu karşılaştırma writeup'ın en güçlü teknik argümanlarından biri olacak. İşte neden:

### 5.1 Model Seçiminin Bilinçli Olduğunu Kanıtlıyor

Jüri "neden E4B seçtiniz?" diye sorduğunda cevap hazır: "Çünkü test ettik. E2B aynı pipeline ile 2.0 alıyor, E4B 91.0 alıyor. Fark 45.5 kat. E2B CoT reasoning yapamıyor."

### 5.2 "Daha Küçük Model Daha İyi" Yanılgısını Çürütüyor

Edge AI'da genellikle "küçük model = iyi" algısı var. Bu test, görev karmaşıklığının minimum model boyutu belirlediğini kanıtlıyor. Basit sınıflandırma için E2B yeterli olabilir, ama kural tabanlı akıl yürütme (CoT) için E4B minimum.

### 5.3 Yarışma Kriterlerine Tam Uyuyor

Yarışma "E2B and E4B models for edge-based solutions" diyor. İki modeli de test etmek tam beklentiye uyar. Ayrıca Ollama special track için "best project that utilizes and showcases the capabilities of Gemma 4 running locally via Ollama" — iki modelin karşılaştırması Ollama'nın kapasitesini gösteriyor.

### 5.4 Writeup'ta Nasıl Kullanılmalı

Writeup'ta şu şekilde bir paragraf çok etkili olur:

> "We tested both Gemma 4 E2B (2B parameters) and E4B (4B parameters) with identical pipeline configuration. E2B scored 2.0/100 with 37 false positives across 60 chunks — it alarmed on everything, including silent pump rooms and metallic sounds. E4B scored 91.0/100 with zero false positives. The critical difference: E4B can follow Chain-of-Thought reasoning instructions ('only alarm if formant pattern detected'), while E2B cannot. This establishes E4B as the minimum viable model for safety-critical acoustic reasoning on edge devices."

### 5.5 Jüri Savunması İçin Hazır Cevap

**Soru:** "Neden daha küçük modeli kullanmadınız? Edge'de küçük model daha iyi değil mi?"

**Cevap:** "E2B'yi test ettik. Aynı prompt, aynı veriler — 2.0/100 skor, 37 false positive. Bir güvenlik sisteminde her 5 saniyede yanlış alarm çalan sistem kullanılamaz. E4B'nin ekstra 2B parametresi CoT reasoning kapasitesini veriyor — bu fark hayat kurtarıyor. Edge'de küçük model iyi ama görev karmaşıklığı minimum boyutu belirliyor."

---

## 6. HIZA KARŞILAŞTIRMASI

| Metrik | E2B | E4B |
|--------|-----|-----|
| İlk chunk (cold start) | 26.4s | 26.3s |
| Normal chunk | ~6.2s | ~7.0s |
| Toplam (5 sahne) | 398s (6.6 dk) | 524s (8.7 dk) |

E2B %12 daha hızlı — ama bu hız avantajı anlamsız çünkü model çalışmıyor. Yanlış cevabı hızlı vermek, doğru cevabı yavaş vermekten daha kötü. Bir güvenlik sisteminde 0.8 saniye fark hayat kurtarmaz ama yanlış alarm güveni öldürür.

---

## 7. İKİ MODELİN KARŞILAŞTIRMA MATRİSİ

| Kriter | E2B | E4B | Kazanan |
|--------|-----|-----|---------|
| Skor (WGT AVG) | 2.0 | 91.0 | **E4B** (45.5x) |
| False Positive | 37/60 | 0/60 | **E4B** |
| CoT Reasoning | Çalışmıyor | Çalışıyor | **E4B** |
| Few-Shot Learning | Çalışmıyor | Çalışıyor | **E4B** |
| Hız (chunk/s) | 6.2s | 7.0s | E2B (%12) |
| RAM Kullanımı | ~1.5GB | ~3GB | E2B |
| Model Boyutu | 7.2GB | ~4GB disk | E2B |
| Güvenilirlik | Güvenilmez | 7/7 tutarlı | **E4B** |
| Edge Uyumluluğu | RPi Zero mümkün | RPi 4+ gerekli | E2B |
| Güvenlik Sistemi İçin | **Kullanılamaz** | **Kullanılabilir** | **E4B** |

**Sonuç:** E2B hız ve boyut avantajına rağmen bu görev için tamamen yetersiz. E4B edge deployment için minimum viable model.

---

## 8. ÖNEMLİ İÇGÖRÜ

Bu test projenin temel felsefesini bir kez daha doğruladı: **"Performans artışı modeli büyüterek değil, girdi temsilini modelin güçlü yönleriyle hizalayarak elde edildi."** Ama bu cümlenin bir ön koşulu var — modelin minimum bir akıl yürütme kapasitesine sahip olması gerekiyor. E2B bu ön koşulu karşılamıyor. E4B karşılıyor.

Başka bir deyişle: spektrogram + CoT + debouncing pipeline'ı doğru araç ama bu aracı kullanabilecek minimum zeka E4B seviyesinde. E2B bu aracı kullanamıyor — talimatları anlayamıyor, örneklerden öğrenemiyor, görsel paternleri ayırt edemiyor.

---

## 9. SONUÇ

| Model | WGT AVG | FP | Verdict |
|-------|---------|-----|---------|
| Gemma 4 E2B | 2.0 | 37 | Kullanılamaz — her şeye alarm veriyor |
| Gemma 4 E4B | 91.0 | 0 | CERTAIN SURVIVAL — 7/7 tutarlı |

E2B ile E4B arasındaki fark sadece parametre sayısı değil — reasoning kapasitesi. E4B "düşünebiliyor" (CoT), E2B "düşünemiyor." Güvenlik kritik sistemlerde bu fark hayat meselesi.

"Yanlış cevabı hızlı vermek, doğru cevabı yavaş vermekten daha kötüdür." Bu cümle edge AI model seçiminin özeti.

---

*Bu doküman Gemma 4 E2B vs E4B karşılaştırma test bulgularını içerir.*
*E4B: 91.0/100, 0 FP, CERTAIN SURVIVAL | E2B: 2.0/100, 37 FP, kullanılamaz*
*Son güncelleme: 6 Nisan 2026*
