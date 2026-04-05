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

## 5. NÖTR PROMPT TESTİ — SONUÇLAR

### 5.1 İlk Çalıştırma (Ses Weight: S2=0.35, S4=0.6, S5=0.40)

| Sahne | İnsan | Skor | Sinyal | Detay |
|-------|-------|------|--------|-------|
| S1 | YOK | **60/100** | 0 alarm | Mükemmel — sıfır FP |
| S2 | VAR | 0/100 | 1 alarm (PRELIM) | Chunk 7: shouting_help, 0.85, [+5s] — DUYDU ama tek izole |
| S3 | YOK | **60/100** | 0 alarm | Mükemmel — sıfır FP |
| S4 | VAR | 0/100 | 2 filtered | Chunk 3: 0.65, Chunk 7: 0.50 — zayıf sinyal |
| S5 | VAR | 0/100 | 0 alarm | Sıfır sinyal |

### 5.2 İkinci Çalıştırma (Ses Weight Artırılmış: S2=0.55, S4=0.8, S5=0.60)

| Sahne | İnsan | Skor | Sinyal | Detay |
|-------|-------|------|--------|-------|
| S1 | YOK | **60/100** | 1 filtered (0.60) | Debouncing doğru filtreledi |
| S2 | VAR | 0/100 | 1 alarm (PRELIM) | Chunk 11: shouting_help, 0.90, [+25s] — DUYDU ama tek izole |
| S3 | YOK | **60/100** | 3 filtered (0.30-0.50) | Debouncing hepsini filtreledi |
| S4 | VAR | 0/100 | 0 alarm | Bu sefer hiç sinyal yok (non-determinizm) |
| S5 | VAR | 0/100 | 3 filtered (0.50-0.55) | Chunk 6 [+5s], Chunk 11 [+30s] — DUYUYOR ama güven düşük |

### 5.3 Nötr Prompt Analizi

Nötr prompt halüsinasyonu tamamen temizledi — S1 ve S3'te her iki çalıştırmada da sıfır onaylanmış FP. Debouncing düşük güvenli sporadic alarmları başarıyla filtreliyor.

Model gerçek insan sesini DUYUYOR ama tutarsız ve düşük güvenle:
- S2'de her iki çalıştırmada da tek bir chunk'ta yüksek güvenle tespit (0.85-0.90)
- S5'te düşük güvenle (0.50-0.55) sinyal geliyor ama debouncing filtreliyor
- S4'te bazen duyuyor (0.50-0.65), bazen hiç duymuyor (non-determinizm)

Temel sorun: model sesi fark ediyor ama yeterli güvenle ve yeterli sayıda chunk'ta tespit edemiyor. Bu modelin ses anlama kapasitesinin sınırı — prompt optimizasyonu ile çözülemiyor.

---

## 6. KARŞILAŞTIRMA: ÜÇ PROMPT + İKİ SES SEVİYESİ

### En İyi Sonuçlar (Sahne Bazında)

| Sahne | En İyi Skor | Hangi Konfigürasyon | Not |
|-------|-------------|---------------------|-----|
| S1 | 60/100 | Nötr prompt (her iki ses) | Sıfır FP |
| S2 | 0/100 | Tümü başarısız | En iyi sinyal: Nötr prompt, 0.90 ama tek chunk |
| S3 | 60/100 | Nötr prompt / Agresif+debouncing | Sıfır confirmed FP |
| S4 | 5/100 | Agresif prompt + TTS | 0.85-0.90 ile doğru tespit ama FP'li |
| S5 | 5/100 | Agresif prompt + TTS | Chunk 6'da 0.85, [+5s] ama FP'li |

### Kritik Gözlem: Agresif vs Nötr Trade-off

Agresif prompt ile model DUYUYOR (S4: 0.85-0.90, S5: 0.85) ama halüsinasyon da yapıyor (S1: 7 FP).
Nötr prompt ile model DUYMUYOR (çoğu chunk'ta) ama halüsinasyon da yapmıyor.
Arada mükemmel bir denge bulmak bu modelin kapasitesiyle çok zor.

Bu bir "duvar" — modelin ses anlama yeteneğinin sınırına ulaşıldı. Çözüm prompt veya ses seviyesi ayarında değil, farklı bir teknik yaklaşımda olabilir (spektrogram hibrit, multi-pass, sıcaklık ayarı vb.)

---

## 7. LLM NON-DETERMİNİZM BULGUSU

Aynı ses, aynı prompt, farklı çalıştırma — farklı sonuçlar:
- S1 nötr prompt: 1. çalıştırma 0 alarm, 2. çalıştırma 1 alarm (0.60, filtrelendi)
- S3 nötr prompt: 1. çalıştırma 0 alarm, 2. çalıştırma 3 alarm (0.30-0.50, hepsi filtrelendi)
- S4 nötr prompt: 1. çalıştırma 2 alarm (0.50-0.65), 2. çalıştırma 0 alarm
- S2 nötr prompt: 1. çalıştırma chunk 7'de tespit, 2. çalıştırma chunk 11'de tespit

Bu "stochastic inference" — LLM'lerin iç sampling mekanizması her çalıştırmada küçük farklılıklar üretir. Debouncing katmanı bu belirsizliği yönetmek için kritik. Güvenlik-kritik sistemlerde LLM non-determinizmini yönetmek ayrı bir mühendislik katmanı gerektirir.

---

## 8. PROJE DURUMU VE SONRAKI ADIMLAR

Prompt optimizasyonu ve ses seviyesi ayarı ile ulaşılabilecek maksimum noktaya gelindi. İlerlemek için farklı teknik yaklaşımlar araştırılacak:

- Spektrogram hibrit yaklaşım (ses → görüntü → modelin vision kapasitesi)
- Multi-pass analiz (aynı chunk'ı birden fazla kez gönder, çoğunluk oyu)
- Ollama sıcaklık (temperature) ayarı (daha deterministik çıktı)
- Ses ön-işleme (insan ses frekanslarını güçlendirme)

---

*Bu doküman prompt mühendisliği sürecinin tüm bulgularını ve keşiflerini içerir.*
*Son güncelleme: 3 Nisan 2026*
