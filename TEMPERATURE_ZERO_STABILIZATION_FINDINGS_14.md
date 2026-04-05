# WWTP Acoustic Safety — Temperature=0 Stabilizasyon Bulguları
## S5 Non-Determinizm Sorunu Çözüldü — 5/5 Tutarlı Run
> **Test Tarihi:** 5 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Denenen Teknik:** Ollama temperature parametresi 0.1 → 0.0
> **Sonuç:** BAŞARILI — 5 ardışık çalıştırmada birebir aynı sonuç (91.0/100)

---

## 1. PROBLEM

Temperature=0.1 ile S5 sahnesi non-deterministik davranıyordu. Aynı ses dosyası, aynı spektrogram, aynı prompt — ama model bazen farklı karar veriyordu. S5 chunk 6'da (25-30s, boğulma çığlığının başladığı an) bazen 0.80 confidence verip alarm tetikliyordu, bazen 0.30 verip sessiz kalıyordu. Diğer 4 sahne (S1, S2, S3, S4) tamamen tutarlıydı — sorun sadece S5'teydi.

Bu, S5'teki boğulma sesinin karar eşiğinin tam sınırında olmasından kaynaklanıyordu. Sinyal çok zayıf ve kesintili — modelin "evet bu insan sesi" ile "hayır bu gürültü" arasında salınmasına neden oluyordu. Temperature=0.1 bile bu sınırdaki kararda küçük rastgelelik yaratıyordu.

Tutarlılık testi sonuçları (temperature=0.1):

| Run | S1 | S2 | S3 | S4 | S5 | WGT AVG |
|-----|-----|-----|-----|------|------|---------|
| 1 | 60 | 95 | 60 | 100 | 100 | 91.0 |
| 2 | 60 | 95 | 60 | 100 | 0 | 51.0 |
| 3 | 60 | 95 | 60 | 100 | 0 | 51.0 |

S5: 3 çalıştırmadan sadece 1'inde tespit. WGT AVG: 91, 51, 51. Kabul edilemez tutarsızlık.

---

## 2. ÇÖZÜM

Tek değişiklik: `OLLAMA_TEMP = 0.1` → `OLLAMA_TEMP = 0.0`

Temperature=0, modeli her seferinde en yüksek olasılıklı tokeni seçmeye zorlar. Bu, aynı girdi için her seferinde aynı çıktıyı garanti eder (veya çok yakın). Karar eşiğinin sınırındaki S5 sinyali için bu kritik — model artık salınmıyor, her seferinde aynı kararı veriyor.

---

## 3. SONUÇLAR — 5 ARDIŞIK ÇALIŞTIRMA

| Run | S1 | S2 | S3 | S4 | S5 | WGT AVG | S5 Chunk 6 | S5 Verdict |
|-----|-----|-----|-----|------|------|---------|-----------|------------|
| 1 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 2 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 3 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 4 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |
| 5 | 60 | 95 | 60 | 100 | 100 | **91.0** | 0.75 CONFIRMED | CERTAIN SURVIVAL |

5 çalıştırma, 5'i de birebir aynı. 300 chunk (5 run × 60 chunk), toplam sıfır false positive. S5'te her seferinde chunk 6'da 0.75 confidence, speech_call tipi, CONFIRMED alarm. Survival verdict her seferinde CERTAIN SURVIVAL (5s gecikme ≤ 15s eşiği).

---

## 4. NİHAİ KONFİGÜRASYON (DONDURULDU)

Bu konfigürasyon artık nihai ve dondurulmuş durumdadır. Kod değişikliği yapılmayacak.

Mel spektrogram: 300-3000Hz, n_mels=128, power_to_db, magma colormap. 4 few-shot örneği: S1 pompa (sessiz temiz), S2 inşaat (gürültülü temiz), S3 metalik (aldatıcı temiz), S4 maskeli ses (insan var). Chain-of-Thought 3 adımlı analiz: dikey çizgi = mekanik, eğimli yatay bant = formant, sadece formant → alarm. Debouncing: CONFIRM_MIN_ALARMS = 1, CoT zaten FP filtreliyor. Temperature: 0.0 — maksimum determinizm. Survival verdict: delay tabanlı (mutlak zaman değil).

Çalıştırma komutu: `python acoustic_engine.py PROTOCOL --spectrogram`

---

## 5. TEMPERATURE=0'IN ETKİSİ — TEKNİK ANALİZ

Temperature parametresi LLM'in token seçimindeki rastgeleliği kontrol eder. Temperature=1.0'da model olasılık dağılımından rastgele örnekler — yaratıcı ama tahmin edilemez. Temperature=0.0'da model her zaman en yüksek olasılıklı tokeni seçer — deterministik ve tekrarlanabilir.

Güvenlik sistemi için bu kritik bir tasarım kararıdır. Bir insan hayatı söz konusu olduğunda modelin "bazen tespit etmesi" kabul edilemez. Aynı koşullarda aynı kararı vermesi gerekir. Temperature=0 bunu garanti ediyor.

S1-S4'te bu değişiklik herhangi bir etki yaratmadı çünkü bu sahnelerdeki sinyaller karar eşiğinden çok uzaktaydı — S1/S3'te 0.10-0.20 (kesinlikle alarm yok), S2/S4'te 0.75-0.90 (kesinlikle alarm var). Temperature=0 ile 0.1 arasında fark yoktu.

S5'te ise sinyal tam karar eşiğinin sınırında. Temperature=0.1'de model bazen 0.75 (alarm), bazen 0.30 (alarm yok) veriyordu. Temperature=0'da model tutarlı olarak 0.75 veriyor. Bu, modelin "en yüksek olasılıklı kararının" alarm olduğunu gösteriyor — temperature=0.1'deki rastgelelik bu kararı bazen bozuyordu.

---

## 6. BAŞARISIZ DENEME — PCEN + SPECTRAL SUBTRACTION

Temperature=0'dan önce S5 sorununu sinyal işleme ile çözmeye çalıştık. PCEN (Per-Channel Energy Normalization) ile `power_to_db` yerine dinamik gürültü bastırma uygulandı. Spectral subtraction ile her sahnenin ilk 5 saniyesindeki ortam gürültüsü profili çıkarılıp sonraki chunk'lardan çıkarıldı.

Sonuç: S2 95'ten 0'a düştü. S5 düzelmedi. Temel neden: inşaat gürültüsü ile insan sesi aynı frekans bandında (300-3000Hz). Gürültüyü çıkarırken insan sesini de çıkardık. Bu deneme geri alındı ve ayrı bir bulgu dokümanı olarak belgelendi (PCEN_SUBTRACTION_FAILED_FINDINGS.md).

Bu başarısızlık önemli bir bulguyu pekiştirdi: projenin başarısı frekans ayrımına değil, görsel patern ayrımına dayanıyor. İnsan sesi ve gürültü aynı frekans bandında olsa bile, spektrogramda farklı görsel paternler üretiyor (formant eğrileri vs düz gürültü bantları). Model bu görsel farkı yakalıyor — frekans filtreleme veya gürültü çıkarma ile değil, VLM'in patern tanıma kapasitesi ile.

---

## 7. SKOR EVRİMİ — PROJENIN TÜMT YOLCULUĞU

| Aşama | Yöntem | WGT AVG | Milestone |
|-------|--------|---------|-----------|
| 1 | Ses + Agresif prompt | 3.0 | İlk test |
| 2 | Ses + Nötr prompt | 12.0 | FP temizlendi |
| 3 | Spektrogram 2-örnek | 8.0 | Binary tuzağı |
| 4 | Spektrogram 4-örnek filtreli | 27.0 | S2 rekoru |
| 5 | Spektrogram + CoT | 32.0 | S4 tam puan |
| 6 | CoT + Debounce=1 | 91.0 | S5 tespit (non-det) |
| 7 | PCEN + Subtraction | 32.0 | ❌ Başarısız, geri alındı |
| **8** | **CoT + Debounce=1 + Temp=0** | **91.0** | **✅ 5/5 tutarlı — NİHAİ** |

3.0'dan 91.0'a: 30 kat iyileşme. Ve artık tutarlı — 5 ardışık çalıştırmada birebir aynı sonuç.

---

## 8. SONUÇ

Temperature=0 değişikliği projenin son ve belirleyici hamlesiydi. S5'teki non-determinizm sorunu tek bir parametre değişikliğiyle çözüldü — sinyal işleme karmaşıklığına gerek kalmadı. Bu, LLM tabanlı güvenlik sistemlerinde önemli bir tasarım prensibi: hayat kurtarma kararlarında rastgelelik kabul edilemez, temperature=0 zorunludur.

Motor artık dondurulmuştur. Proje paketleme aşamasına geçiyor: demo arayüzü, video çekimi, Kaggle writeup, GitHub repo hazırlama.

"5 çalıştırma, 300 chunk, sıfır false positive, her seferinde aynı sonuç. Adam hayatta kalıyor."

---

*Bu doküman temperature=0 stabilizasyon bulgularını içerir.*
*Nihai PROTOCOL skoru: 91.0/100 | S5 Survival Verdict: CERTAIN SURVIVAL (5/5 tutarlı)*
*Son güncelleme: 5 Nisan 2026*
