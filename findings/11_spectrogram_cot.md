# WWTP Acoustic Safety — Chain-of-Thought Spektrogram Bulguları
## 3-Adımlı Düşünme Talimatı ile Spektrogram Analizi
> **Test Tarihi:** 5 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Yöntem:** Mel Spektrogram (300-3000Hz) + 4 Few-Shot + Chain-of-Thought Prompt
> **Önceki en iyi WGT AVG:** 27.0 → Bu test: **32.0** (Yeni proje rekoru)

---

## 1. NE DEĞİŞTİ?

Önceki testten tek fark: son classify mesajına 3 adımlı düşünme talimatı eklendi.

**Adım 1:** "Dikey parlak çizgiler veya spike'lar var mı? Varsa bunlar metalik darbeler veya mekanik geçişler — insan sesi DEĞİL."

**Adım 2:** "500-2000Hz aralığında eğimli veya kıvrımlı yatay bantlar var mı? Bunlar merdiven veya kemer gibi görünür — bunlar konuşma formantları."

**Adım 3:** "SADECE Adım 2'deki formant paternini görüyorsan VE bunlar Adım 1'deki dikey spike'lar DEĞİLSE alarm ver."

Few-shot örnekleri, frekans filtresi (300-3000Hz), 3 temiz + 1 insan — hepsi aynı.

---

## 2. TEST SONUÇLARI

| Sahne | İnsan | Skor | FP | Confirmed | İlk Alarm | Detay |
|-------|-------|------|-----|-----------|-----------|-------|
| S1 | YOK | **60/100** | 0 | 0 | — | Mükemmel — 12 chunk sıfır alarm |
| S2 | VAR (25s) | 0/100 | 0 | 0 | — | 2 PRELIM (chunk 6, 12) ama debouncing düşürdü |
| S3 | YOK | **60/100** | 0 | 0 | — | **S3 ÇÖZÜLDÜ!** 12 chunk sıfır alarm |
| S4 | VAR (20s) | **100/100** | 0 | 5 | 25s [+5s] | **PROJE REKORU — TAM PUAN!** |
| S5 | VAR (20s) | 0/100 | 0 | 0 | — | 1 PRELIM (chunk 6) ama debouncing düşürdü |

**Weighted Average: 32.0/100** (Yeni proje rekoru)
**Toplam süre: 7.1 dakika**

---

## 3. REKOR SAHNELER

### S4: 100/100 — Proje Tarihindeki İlk Tam Puan

Detection Accuracy: +40/40 (distress sonrası 5 chunk doğru tespit)
Time to Detection: 30/30 (ilk alarm 25s, distress 20s, +5s gecikme)
False Alarm Control: 20/20 (distress öncesi sıfır FP — 5 chunk hepsi temiz)
Action Quality: 10/10 (INITIATE_CONFINED_SPACE_RESCUE — menhol galerisi için doğru)

Bu sonuç chain-of-thought'un etkisini net gösteriyor. Önceki testte S4'te 3 FP vardı (chunk 2-3-4). Bu testte hepsi temizlendi — model "dikey çizgiler var mı?" diye bakıp underground ambient seslerini doğru filtreledi.

### S3: 60/100 — FP Tamamen Temizlendi

Önceki testte 9 confirmed FP vardı. Bu testte sıfır. Chain-of-thought'un "dikey çizgiler = metalik darbeler, alarm VERME" kuralı metalik sesleri tamamen filtreledi. Model artık "ekran dolu = insan" demiyor, "dikey mi yatay mı" diye bakıyor.

---

## 4. TRADE-OFF ANALİZİ

### S2 ve S5: Chain-of-Thought Modeli Çok Temkinli Yaptı

S2'de model chunk 6'da formant gördü (0.75 speech_call) ve chunk 12'de tekrar (0.90). Ama aradaki 5 chunk'ta 0.20 verdi. Debouncing ardışık alarm istiyor — chunk 6 tek kaldı, PRELIM yapıldı. Chunk 12 de tek kaldı, PRELIM yapıldı. Sonuç: 0 confirmed, 0/100.

S5'te aynı durum — chunk 6'da 0.80 alarm ama tek chunk, PRELIM oldu.

**Neden?** CoT talimatı "SADECE formant görürsen alarm ver" diye katı bir kural koydu. Model gürültülü sahnelerde (S2, S5) formantları bazı chunk'larda görüyor bazılarında görmüyor — non-determinizm hâlâ var. Sonuç olarak alarm izole kalıyor ve debouncing filtreliyor.

### Karşılaştırma: CoT Var vs Yok

| Sahne | CoT Yok (önceki) | CoT Var (bu test) |
|-------|-------------------|-------------------|
| S1 | 60 | 60 (aynı) |
| S2 | **95** | 0 (bozuldu) |
| S3 | 0 | **60** (düzeldi!) |
| S4 | 0 | **100** (mükemmel!) |
| S5 | 5 | 0 (bozuldu) |
| WGT AVG | 27.0 | **32.0** (arttı!) |

CoT olmadan: Model agresif → S2/S5'te çok alarm (doğru tespit + FP) → S3/S4'te de çok alarm (FP)
CoT ile: Model temkinli → S3/S4'te sıfır FP (doğru) → S2/S5'te de az alarm (kaçırma)

WGT AVG 32.0 > 27.0 çünkü S3 ve S4'teki kazanç (60 + 100 = 160 puan) S2 ve S5'teki kayıptan (95 + 5 = 100 puan) daha büyük.

---

## 5. "SORUN MODELDE DEĞİL, SİNYALDE" — DEVAM EDEN TEMEL BULGU

Bu test serisi boyunca ortaya çıkan en önemli bulgu: hangi yöntemi kullanırsak kullanalım (ses, spektrogram, feature-text, chain-of-thought), aynı sahneler sorun çıkarıyor.

**Kolay sahneler (her yöntem çalışıyor):**
- S1 pompa: Çok farklı sinyal, her yöntem doğru tanıyor
- S4 maskeli ses: Sessiz ortamda formant net, CoT ile 100/100

**Zor sahneler (hiçbir yöntem tutarlı çalışmıyor):**
- S2 inşaat + bağırma: İnsan sesi 95dB gürültüde eziliyor
- S5 boğulma: Kesintili çığlık + su efekti + inşaat gürültüsü
- S3 metalik ses: Formant benzeri frekans paterni (aldatıcı)

Bu dağılım yöntemden bağımsız — sinyalin fiziksel doğasından kaynaklanıyor. Gürültü altında insan sesini tespit etmek, modelin değil problemin sınırlaması.

---

## 6. PROJE GENELİ SKOR EVRİMİ

| Test | S1 | S2 | S3 | S4 | S5 | WGT AVG | Milestone |
|------|-----|-----|-----|-----|-----|---------|-----------|
| Ses + Agresif | 0 | 0 | 60 | 5 | 5 | 3.0 | İlk test |
| Ses + Nötr | 60 | 0 | 60 | 0 | 0 | 12.0 | FP temizlendi |
| Spektrogram 2-örnek | 60 | 0 | 0 | 0 | 5 | 8.0 | Binary tuzağı |
| Spektrogram 4-örnek filtreli | 60 | **95** | 0 | 0 | 5 | 27.0 | S2 rekoru |
| **Spektrogram 4-örnek + CoT** | 60 | 0 | **60** | **100** | 0 | **32.0** | **S4 tam puan** |

3.0 → 32.0: Başlangıçtan **10 kattan fazla iyileşme.**

---

## 7. SONRAKI ADIMLAR İÇİN DÜŞÜNCELER

İdeal senaryo: CoT'un S3/S4 başarısı + CoT olmayanın S2/S5 başarısını birleştirmek. Bu iki konfigürasyonun güçlü taraflarını tek bir sistemde kullanmak mümkün olabilir:

Seçenek A: Debouncing eşiğini düşürmek — PRELIM alarmları da kabul etmek, böylece S2/S5'teki tek chunk alarmları geçerli olur.

Seçenek B: İki geçişli sistem — önce CoT ile tarama (S3/S4 FP temizle), sonra CoT olmadan şüpheli chunk'ları tekrar değerlendir.

Seçenek C: Sahne bazlı kalibrasyon — farklı mikrofon lokasyonları için farklı prompt ayarları.

---

*Bu doküman chain-of-thought spektrogram test sonuçlarını içerir.*
*S4'te 100/100 proje rekoru — CoT modeli S3 FP'sini tamamen temizledi.*
*Temel bulgu tekrarı: "Sorun modelde değil, sinyalde."*
*Son güncelleme: 5 Nisan 2026*
