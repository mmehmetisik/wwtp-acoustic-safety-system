# WWTP Acoustic Safety — Feature-Text Yaklaşımı Bulguları
## Ses Özellikleri → Metin → LLM Akıl Yürütme Testi
> **Test Tarihi:** 4 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Yöntem:** librosa ile özellik çıkarımı → metin olarak modele gönderme (ses/görüntü yok)

---

## 1. YAKLAŞIM

Modele ses veya görüntü göndermek yerine, her 5 saniyelik chunk'tan librosa ile sayısal özellikler çıkarıldı ve bu sayılar metin olarak modele gönderildi. Model sayıları okuyup akıl yürüterek karar verdi.

Çıkarılan özellikler: RMS enerji (ses şiddeti), zero-crossing rate (gürültü vs tonal), spektral centroid (frekans ağırlık merkezi), spektral bandwidth ve rolloff, MFCC toplam varyansı (konuşma parmak izi), voice band enerji oranı (300-3000Hz), low band enerji oranı (<300Hz), F1 band oranı (400-600Hz), F2 band oranı (1200-1800Hz), formant varlığı (F1 ve F2 birlikte varsa YES), dominant frekans pikleri.

---

## 2. TEST SONUÇLARI

| Chunk | İnsan | Formant | Model Kararı | Doğru mu? | Conf | Süre |
|-------|-------|---------|-------------|-----------|------|------|
| S1 (15-20s) | YOK | NO | NO HUMAN | ✅ | 0.95 | 23.1s |
| S2_pre (10-15s) | YOK | NO | NO HUMAN | ✅ | 0.60 | 9.4s |
| S2_post (30-35s) | VAR | NO | NO HUMAN | ❌ | 0.60 | 9.9s |
| S3 (25-30s) | YOK | YES | HUMAN | ❌ | 0.95 | 9.0s |
| S4_pre (10-15s) | YOK | NO | NO HUMAN | ✅ | 0.95 | 8.9s |
| S4_post (25-30s) | VAR | YES | HUMAN | ✅ | 0.95 | 8.3s |
| S5_pre (10-15s) | YOK | NO | NO HUMAN | ✅ | 0.60 | 8.9s |
| S5_post (30-35s) | VAR | NO | NO HUMAN | ❌ | 0.60 | 9.7s |

**Doğruluk: 5/8 (%62.5)**
**Ortalama süre: 10.9 saniye/chunk**

---

## 3. ANALİZ

### Model Mükemmel Akıl Yürüttü

Modelin mantık zinciri her durumda tutarlı ve doğru:

S1: "Formant NO, F1 0.012, F2 0.003, low band 0.89 → kesinlikle makine" → DOĞRU
S4_post: "Formant YES, MFCC varyansı 959.65, çok yüksek → insan sesi" → DOĞRU
S2_pre: "Formant NO, ZCR 0.33 yüksek → inşaat gürültüsü" → DOĞRU
S3: "Formant YES, MFCC varyansı 1420, ZCR 0.11 → insan sesi" → VERİLEN SAYILARA GÖRE DOĞRU (ama gerçekte yanlış)

Model hiçbir hata yapmadı — verilen sayılara göre her karar mantıksal olarak doğruydu. Sorun modelde değil.

### Sorun Feature Extraction'da

Üç yanlış sonucun hepsinde aynı kök neden: özellik çıkarımı gerçeği yansıtmıyor.

**S2_post (insan VAR ama formant NO):** İnsan sesi (TTS "Help!") inşaat gürültüsünün altında ezilmiş. F1 ratio 0.0262 — eşiğin (0.05) altında. librosa basit enerji oranı hesaplıyor, gürültü altındaki zayıf formantı bulamıyor. İnsan sesi fiziksel olarak sinyalde kaybolmuş.

**S5_post (insan VAR ama formant NO):** Aynı sorun — boğulma çığlığı (kesintili, su efektli) inşaat gürültüsü altında. F1 0.0262, formant NO. Boğulma efektleri (rastgele kesinti, su sesi) formant yapısını daha da bozuyor.

**S3 (insan YOK ama formant YES):** Metal scraping sesi 300-3000Hz aralığında ve düzensiz ritimle tasarlanmış — bilerek insan sesine benzetilmiş. F1 0.0605 ve F2 0.1834 — eşiklerin üstünde. MFCC varyansı 1420 — çok yüksek (metalik darbelerin düzensizliğinden). Sayısal olarak insan sesinden ayırt edilemiyor.

### Temel Bulgu: Sorun Yöntemde Değil, Sinyalde

Dört farklı yaklaşım denendi ve hepsinde aynı sahneler sorun çıkardı:

| Sahne | Ses Tabanlı | Spektrogram | Feature-Text | Ortak Sorun |
|-------|-------------|-------------|--------------|-------------|
| S1 | ✅ (nötr) | ✅ | ✅ | Sorun yok — çok farklı sinyal |
| S2 pre | ✅ (nötr) | ✅ (filtreli) | ✅ | Sorun yok — temiz gürültü |
| S2 post | ❌ (çoğu) | ✅ (filtreli!) | ❌ | İnsan sesi gürültüde ezilmiş |
| S3 | Karışık | ❌ | ❌ | Metalik ses insan sesine benziyor |
| S4 pre | ✅ (nötr) | ❌ (FP) | ✅ | Sessiz ortam — kolay |
| S4 post | Karışık | ✅ | ✅ | Sessiz ortamda formant net |
| S5 post | ❌ (çoğu) | ✅ (filtreli!) | ❌ | Boğulma sesi gürültüde ezilmiş |

Dikkat çekici: Spektrogram yaklaşımı S2_post ve S5'i doğru tespit etti ama feature-text yapamadı. Bu demek ki görsel patern tanıma (spektrogram), tek tek sayılardan daha fazla bilgi taşıyor. İnsan gözü (ve vision model) bir görüntüdeki eğimli formant çizgilerini görebiliyor ama bu çizgiler basit enerji oranlarına indirgendiğinde kayboluyor.

---

## 4. YÖNTEMLER ARASI KARŞILAŞTIRMA

| Metrik | Ses Tabanlı | Spektrogram (filtreli) | Feature-Text |
|--------|-------------|------------------------|--------------|
| S2 en iyi skor | 0/100 | **95/100** | Kaçırdı |
| S5 tespit | Bazen 0.85 | Tespit var (FP'li) | Kaçırdı |
| S1 FP | Prompt'a bağlı | 0 | 0 |
| S3 FP | Prompt'a bağlı | Var | Var |
| S4 tespit | Bazen 0.85 | Tespit var (FP'li) | ✅ 0.95 doğru |
| Hız (chunk) | 25-37s | 6-7s | 9-10s |
| Determinizm | Düşük | Orta | Yüksek |
| Halüsinasyon | Yüksek (agresif) | Orta | Düşük |

**En iyi genel performans: Frekans filtrelemeli spektrogram (S2: 95/100)**
**En güvenilir "insan yok" tespiti: Feature-text (formant NO → kesin karar)**
**En hızlı: Spektrogram (6-7s/chunk)**

---

## 5. ANAHTAR İÇGÖRÜLER

### İçgörü 1: Her Yöntem Farklı Bir Şeyde İyi

Ses tabanlı: Model bazen gerçek konuşmayı duyuyor ama tutarsız.
Spektrogram: Görsel paternleri iyi tanıyor ama FP'lere açık.
Feature-text: Sayısal kurallara mükemmel uyuyor ama sinyaldeki ince detayları kaçırıyor.

Hiçbiri tek başına yeterli değil. Ama her birinin güçlü tarafı farklı.

### İçgörü 2: Gürültülü Ortamda İnsan Sesi Tespiti Zor Bir Problem

Bu Gemma 4'ün sınırlaması değil, problemin doğası. 95dB inşaat gürültüsü altında insan sesi fiziksel olarak maskeleniyor. Basit özellik çıkarımı (librosa enerji oranları) bu maskelemeyi aşamıyor. Spektrogram görsel yaklaşımı kısmen aşabiliyor çünkü formant çizgileri gürültü içinde bile görsel olarak seçilebiliyor.

### İçgörü 3: S4 Feature-Text İçin İdeal Senaryo

Sessiz ortam (underground ambient, 52dB) + insan sesi → formant net çıkıyor, MFCC varyansı yüksek, model 0.95 confidence ile doğru karar veriyor. Bu, feature-text yaklaşımının düşük gürültülü ortamlarda mükemmel çalışacağını kanıtlıyor.

### İçgörü 4: Model Verilen Veriye Göre Mantıken Doğru Karar Veriyor

8 testten hiçbirinde model mantık hatası yapmadı. S3'te "formant YES + MFCC yüksek → insan" demesi verilen sayılara göre doğru — sorun sayıların gerçeği yansıtmaması. Bu, "LLM reasoning çalışıyor ama girdi kalitesi kritik" bulgusunu destekliyor.

---

## 6. PROJE GENELİNDE EN İYİ KONFİGÜRASYONLAR

| Sıra | Yöntem | WGT AVG | En İyi Sahne | En Zayıf |
|------|--------|---------|-------------|----------|
| 1 | Spektrogram filtreli 4-örnek | 27.0 | S2: 95 | S3: 0 (FP) |
| 2 | Ses + Nötr prompt | 12.0 | S1: 60, S3: 60 | S2/S4/S5: 0 |
| 3 | Spektrogram 2-örnek | 8.0 | S1: 60 | Her yer FP |
| 4 | Feature-text | Test edilmedi (POC) | S4: doğru | S2/S5: kaçırdı |
| 5 | Ses + Agresif prompt | 3.0 | S3: 60 (debounce) | S1: 0 (7 FP) |

---

*Bu doküman feature-text yaklaşımının POC test sonuçlarını içerir.*
*Temel bulgu: Model kusursuz akıl yürütüyor ama sorun sinyalin kendisinde — gürültü altında formant kaybolması.*
*Son güncelleme: 4 Nisan 2026*
