# WWTP Acoustic Safety — Prompt Mühendisliği Bulguları
## "AI'ya NE Söylediğin, NE KADAR Söylediğinden Daha Önemli"
> **Test Tarihi:** 3 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Ses:** TTS tabanlı (Google TTS + endüstriyel gürültü)
> **Test Sayısı:** 3 farklı prompt versiyonu, toplam 15 sahne çalıştırması

---

## 1. PROMPT EVRİMİ — ÜÇ VERSİYON

Bu proje boyunca üç farklı prompt yaklaşımı test edildi. Her biri aynı model ve aynı TTS sesler ile çalıştırıldı. Sonuçlar, prompt mühendisliğinin LLM tabanlı güvenlik sistemlerinde ne kadar kritik olduğunu kanıtlıyor.

### Versiyon 1 — Agresif PROTOCOL (~500 kelime)

Bu ilk prompt, modeli koruyucu bir güvenlik görevlisi gibi çalıştırmaya çalışıyordu. İçinde lokasyon bilgisi, operasyon detayı, sahne-spesifik güvenlik protokolü, 7 detaylı kural, hayatta kalma eşikleri ve şu kritik cümle vardı: "Missing a real human distress signal is catastrophically worse than a false alarm" — yani "insanı kaçırmak yanlış alarmdan kötü, şüphede alarm ver."

Sonuçlar dramatik oldu. Model her seste insan sesi halüsinasyonu yaptı. Pompada "shouting_help" dedi (S1: 7 FP), metalik seste "muffled_call" dedi (S3: 7 FP), hatta S5'te adam daha düşmeden alarm verdi (distress öncesi 2 FP). Ama aynı zamanda gerçek insan sesini de tespit edebildi — S4'te maskeli sesi 0.85-0.90 confidence ile buldu, S5'te chunk 6'da çığlığı 0.85 ile duydu. Yani agresif prompt'un iki yüzü vardı: hem halüsinasyon yarattı hem de gerçek tespiti sağladı.

### Versiyon 2 — Pasif PROTOCOL (~100 kelime)

Bu prompt, halüsinasyonu temizlemek amacıyla yazıldı. Tüm güvenlik baskısı kaldırıldı, kurallar 5 kısa maddeye indirildi ve şu kritik cümle eklendi: "If unsure whether a sound is human or mechanical, do NOT alarm" — yani "emin değilsen alarm VERME."

Halüsinasyon tamamen temizlendi. S1'de 12 chunk boyunca sıfır alarm, confidence hep 1.00 ile "kesinlikle insan yok" dedi. S3'te de aynı mükemmel sonuç. Ama bedeli ağır oldu — model S2'de "Help! Yardım!" sesini duyamadı (12 chunk sıfır alarm), S4'te maskeli sesi duyamadı (12 chunk sıfır alarm), S5'te boğulan insanı duyamadı (12 chunk sıfır alarm). "Emin değilsen alarm verme" kuralı modeli tamamen kapattı.

### Versiyon 3 — Nötr PROTOCOL (~120 kelime)

Bu prompt, iki uç noktanın ortasını bulmak için tasarlandı. Ne "şüphede alarm ver" ne "şüphede alarm verme" diyor. Bunun yerine modele şunu söylüyor: "Duyduğunu dürüstçe raporla, güven skorunu kullan." Confidence kılavuzu ile modele bir çerçeve veriliyor — 0.8 üstü kesin insan sesi, 0.4-0.7 olası ses, 0-0.3 insan yok. Böylece model borderline sinyallerde alarm verebilir ama confidence'ı orta tutarak debouncing katmanına karar bırakır.

Bu versiyonun test sonuçları bekleniyor.

---

## 2. KARŞILAŞTIRMA TABLOSU

### Agresif vs Pasif — Aynı Ses, Farklı Prompt

| Sahne | İnsan | Agresif (500 kel) | Pasif (100 kel) | Fark |
|-------|-------|-------------------|-----------------|------|
| S1 — Pompa | YOK | 0/100 (7 FP) | **60/100** (0 FP) | Pasif halüsinasyonu temizledi |
| S2 — İnşaat | VAR | 0/100 (FP'li tespit) | 0/100 (hiç duyamadı) | İkisinde de başarısız |
| S3 — Havuz | YOK | 0/100 (7 FP) | **60/100** (0 FP) | Pasif halüsinasyonu temizledi |
| S4 — Menhol | VAR | 5/100 (doğru tespit var) | 0/100 (hiç duyamadı) | Agresif en azından duydu |
| S5 — Kritik | VAR | 5/100 (doğru tespit var) | 0/100 (hiç duyamadı) | Agresif en azından duydu |

### Davranış Karşılaştırması — Chunk Bazında Detay

S4 Menhol sahnesinde agresif prompt'un davranışı: Chunk 6'da (25-30s) muffled_call, confidence 0.85, INITIATE_CONFINED_SPACE_RESCUE. Chunk 7'de (30-35s) muffled_call, confidence 0.90. Chunk 9'da (40-45s) muffled_call, confidence 0.90. Model maskeli sesi doğru zamanda, doğru aksiyonla, yüksek güvenle tespit etti.

Aynı S4 sahnesinde pasif prompt'un davranışı: 12 chunk boyunca hepsi "none", confidence hep 1.00 ile "kesinlikle insan yok." Model aynı sesi dinliyor ama "emin değilsen alarm verme" kuralı yüzünden hiçbir şeyi bildirmiyor.

S5 Kritik sahnesinde agresif prompt'un davranışı: Chunk 6'da (25-30s) muffled_call, confidence 0.85, [+5s]. Düşmeden 5 saniye sonra ilk gerçek tespit. Bu, eski formant sesle sıfır sinyal alırken TTS ile ilk kez elde edilen gerçek bir başarıydı.

Aynı S5 sahnesinde pasif prompt'un davranışı: 12 chunk boyunca sıfır sinyal. Model boğulan insanın TTS çığlığını bile duymadı.

### Hız Karşılaştırması

| Mod | Prompt Uzunluğu | Chunk Süresi (ort.) | Toplam Süre (5 sahne) |
|-----|-----------------|---------------------|----------------------|
| BARE | ~100 kelime | ~22 saniye | 22.4 dakika |
| Pasif PROTOCOL | ~100 kelime | ~24 saniye | 25.0 dakika |
| Agresif PROTOCOL | ~500 kelime | ~37 saniye | 37.1 dakika |

Prompt uzunluğu doğrudan çıkarım süresini etkiliyor. Kısa prompt %35 daha hızlı çalışıyor. Bu edge deployment senaryosunda (Raspberry Pi, Jetson Nano) kritik bir fark — her saniye hayat kurtarabilir.

---

## 3. ALTIN BULGULAR

### Bulgu 1: "AI'ya NE Söylediğin, NE KADAR Söylediğinden Daha Önemli"

Bu projenin en değerli keşfi bu cümlede özetleniyor. Aynı model, aynı ses dosyası, aynı donanım — tek değişken prompt. 500 kelimelik prompt 7 yanlış alarm üretirken, 100 kelimelik prompt sıfır yanlış alarm üretiyor. Ama 500 kelimelik prompt gerçek tehlikeyi tespit edebilirken, 100 kelimelik prompt hiçbir şeyi duyamıyor.

Bu, LLM tabanlı güvenlik sistemleri için kritik bir tasarım prensibi: prompt uzunluğu ile halüsinasyon oranı arasında doğrudan bir ilişki var. Daha fazla kural yazmak modeli daha güvenli yapmıyor, aksine daha kırılgan yapıyor. Doğru kural sayısı ve doğru ifade biçimi, kural miktarından önemli.

### Bulgu 2: Tek Kelime Tüm Davranışı Değiştirebilir

"Do NOT alarm" cümlesi modeli tamamen kapattı. Tüm 60 chunk'ta (5 sahne × 12 chunk) tek bir alarm bile vermedi. Hepsi "none", confidence hepsi 1.00. Tek bir olumsuz talimat, modelin tüm algılama kapasitesini sıfırladı. Bu, prompt mühendisliğinin ne kadar hassas bir iş olduğunu gösteriyor.

### Bulgu 3: LLM'leri Kendi Kararına Bırakmak Gerekiyor

İki uç noktanın başarısızlığından çıkan ders şu: modele ne "alarm ver" ne "alarm verme" demek en doğrusu. Bunun yerine "duyduğunu raporla, güven skorunu kullan" demek, modeli kendi yargısıyla çalıştırıyor. Karar otoritesini modelden alıp post-processing katmanına (debouncing) vermek daha güvenilir — çünkü debouncing deterministik kurallara dayalı, halüsinasyona açık değil.

### Bulgu 4: Çok Katmanlı Savunma Şart

Tek katmanlı yaklaşım (sadece prompt VEYA sadece debouncing) yetersiz. Doğru mimari şu: prompt modele sesi dinletir ve dürüst raporlama yaptırır, debouncing katmanı düşük güvenli alarmları filtreler, ardışık onay kuralı sporadic halüsinasyonları eler. Bu üç katman birlikte çalışınca hem yanlış alarm azalır hem gerçek tespit korunur.

### Bulgu 5: Tek Chunk Testi ile Tam Sahne Testi Farklı Şeyler Ölçer

Tek chunk testinde PROTOCOL modu S4 ve S5'i 0.98 confidence ile tespit etmişti. Ama 12 chunk tam sahne testinde aynı prompt halüsinasyon patlaması yarattı. Tek chunk testi "model bu sesi anlıyor mu" sorusuna cevap verir ama "sistem güvenilir mi" sorusuna cevap vermez. Gerçek performans değerlendirmesi için tam sahne testi şart.

---

## 4. PROMPT MÜHENDİSLİĞİ SPEKTRUMU

Bu proje boyunca prompt mühendisliğinde bir spektrum keşfedildi. Bir uçta agresif talimatlar var: "Her şeye alarm ver, kaçırma." Bu uçta yanlış alarm patlar. Diğer uçta pasif talimatlar var: "Emin değilsen alarm verme." Bu uçta hiçbir şeyi duyamaz. Ortada nötr yaklaşım var: "Duyduğunu raporla, güven skorunu kullan." Tatlı nokta burada olmalı — model kendi duyduğuna göre karar verir, kesinliği confidence skoruyla ifade eder, son kararı deterministik post-processing katmanı verir.

Bu spektrum endüstriyel AI sistemleri için genel bir tasarım prensibi olarak sunulabilir. LLM tabanlı herhangi bir güvenlik sistemi (yangın, gaz kaçağı, izinsiz giriş) aynı dengeyle karşılaşacaktır.

---

## 5. NÖTR PROMPT TESTİ

**Durum:** Nötr PROTOCOL prompt (~120 kelime) ile test çalışıyor.

Prompt yaklaşımı: Ne "alarm ver" ne "alarm verme" — "duyduğunu raporla."
Confidence kılavuzu eklendi: 0.8+ kesin, 0.4-0.7 olası, 0-0.3 yok.
Debouncing katmanı 0.75 eşiği ile filtre yapacak.

**Beklentiler:** S1 ve S3'te düşük FP (pasif prompt'taki temizlik korunmalı), S4 ve S5'te orta-yüksek confidence ile tespit (agresif prompt'taki duyma kapasitesi geri gelmeli), debouncing ile son karar doğru olmalı.

**Sonuçlar bu bölüme eklenecek.**

---

## 6. TTS GEÇİŞİNİN ETKİSİ (ÖNCEKİ TEST VERİLERİ)

TTS geçişi prompt sorunlarından bağımsız olarak kanıtlanmış bir iyileştirme sağladı. Agresif prompt ile formant sesler kullanıldığında S5'te 12 chunk boyunca sıfır sinyal geliyordu. TTS seslere geçildiğinde aynı agresif prompt ile S5 chunk 6'da 0.85 confidence ile tespit yapıldı. S2'de model formant sesle hep "muffled_call" derken TTS sesle "shouting_help" dedi — gerçek konuşma paternini tanıdı. S4'te formant sesle BARE modda 0.70 alınırken, TTS sesle agresif PROTOCOL'da 0.85-0.90 alındı.

Bu veriler TTS geçişinin başarılı olduğunu kesin olarak kanıtlıyor. Model gerçek konuşma paternlerini formant sentezinden çok daha iyi tanıyor.

---

## 7. PROJE DURUMU

Motor çalışıyor, TTS ses üretici çalışıyor, debouncing katmanı kanıtlanmış, distress timing doğru hesaplanıyor, JSON parse güvenilir. Prompt optimizasyonunda iki uç nokta test edildi ve belgelendi. Nötr prompt testi devam ediyor. Sonuca göre prompt finalize edilecek veya bir iterasyon daha yapılacak.

Prompt finalize olduktan sonra sıradaki adımlar: JSON export özelliği (her run sonrası detaylı davranış kaydı), E2B model karşılaştırma testleri, demo arayüzü tasarımı, video çekimi ve Kaggle writeup.

---

*Bu doküman prompt mühendisliği sürecinin tüm bulgularını ve keşiflerini içerir.*
*Nötr prompt test sonuçları eklenecektir.*
*Son güncelleme: 3 Nisan 2026*
