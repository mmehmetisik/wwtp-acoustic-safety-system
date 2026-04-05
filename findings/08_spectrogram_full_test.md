# WWTP Acoustic Safety — Spektrogram Tam Sahne Testi Bulguları
## 12-Chunk Few-Shot Spektrogram Sonuçları
> **Test Tarihi:** 4 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Yöntem:** Mel Spektrogram + Few-Shot Vision (2 örnek: S1 temiz, S4 insan sesli)

---

## 1. TEST SONUÇLARI

| Sahne | İnsan | Alarm | Confirmed | FP | Skor | Süre |
|-------|-------|-------|-----------|-----|------|------|
| S1 — Pompa | YOK | 0/12 | 0 | 0 | **60/100** | 2.1 dk |
| S2 — İnşaat | VAR (25s) | 12/12 | 12 | 5 | 0/100 | 1.3 dk |
| S3 — Havuz | YOK | 12/12 | 12 | 12 | 0/100 | 1.3 dk |
| S4 — Menhol | VAR (20s) | 12/12 | 12 | 4 | 0/100 | 1.3 dk |
| S5 — Kritik | VAR (20s) | 12/12 | 12 | 4 | 5/100 | 1.4 dk |

**Toplam süre: 7.5 dakika (ses tabanlı ile 28 dakikaydı)**
**Genel skor: 2.7/100**

---

## 2. NE OLDU?

Model S1 (pompa) dışında her sahnede her chunk'a 0.90 confidence ile alarm verdi. S1'in spektrogramı diğerlerinden çok farklı görünüyor — sadece düşük frekanslarda sabit bantlar, üst kısım tamamen boş. Model bunu doğru tanıdı.

Ama S2, S3, S4, S5'in spektrogramları birbirine benziyor — hepsinde geniş bantlı enerji dağılımı, dikey ve yatay paternler var. Model ikili sınıflandırma yapıyor: "S1'e benziyorsa temiz, S1'e benzemiyorsa insan sesi." Bu çok kaba bir ayrım ve işe yaramıyor.

Few-shot ile sadece iki örnek verildi: biri çok temiz (S1 pompa — düşük frekanslı sabit bantlar), biri çok belirgin insan sesli (S4 maskeli ses — net formant yapıları). Model bu iki uç noktayı öğrendi ama aralarındaki nüansları ayırt edemiyor. İnşaat gürültüsünün geniş bantlı spektrogramını da "formant" olarak yorumluyor.

---

## 3. POC TESTİ vs TAM TEST FARKI

Proof-of-concept testinde (tek chunk) 7 testten 6'sı doğruydu (%85.7). Tam 12-chunk testinde ise S1 dışında hepsi yanlış. Neden?

POC testinde her sahne için tek bir özenle seçilmiş chunk test edildi — en belirgin farkı gösteren zaman dilimi. Tam testte 12 ardışık chunk var — bazıları çok belirsiz (distress öncesi inşaat gürültüsü). Model belirsiz chunk'larda "emin değilim ama S1'e benzemiyor, o zaman alarm" diyor.

Ayrıca POC testinde S2, S3, S4 için farklı zaman dilimleri seçildi (30-35s, 25-30s, 35-40s). Tam testte her sahnenin 0-5s chunk'ı da dahil — bu chunk'larda henüz insan sesi yok ama inşaat gürültüsü var, model yine alarm veriyor.

---

## 4. TEMELDEKİ SORUN

Few-shot yaklaşımı ile model bir "binary classifier" gibi davranıyor: "S1'e benziyor mu?" Eğer benzemiyorsa otomatik olarak "insan sesi var" diyor. Bu yaklaşım yetersiz çünkü endüstriyel ortamda birçok farklı gürültü türü var ve hepsi S1'den farklı görünüyor ama hiçbirinde insan sesi yok.

Çözüm daha fazla few-shot örneği eklemek olabilir (inşaat gürültüsü temiz, metalik ses temiz, vs.) ama bu her yeni gürültü türü için yeni örnek gerektirir — ölçeklenebilir değil.

---

## 5. HIZDA İYİLEŞME (Tek Olumlu Sonuç)

Spektrogram yaklaşımı ses tabanlıdan 4-6 kat daha hızlı:

| Yöntem | Chunk süresi | 5 sahne toplam |
|--------|-------------|----------------|
| Ses + Agresif prompt | ~37 saniye | 37.1 dakika |
| Ses + Nötr prompt | ~25 saniye | 25-28 dakika |
| Spektrogram few-shot | ~6 saniye | 7.5 dakika |

---

## 6. PROJE GENELİNDEKİ EN İYİ SONUÇLAR

Tüm testler boyunca elde edilen en iyi sahne bazında sonuçlar:

| Sahne | En İyi Skor | Konfigürasyon | Not |
|-------|-------------|---------------|-----|
| S1 | 60/100 | Nötr prompt + TTS veya Spektrogram | Sıfır FP |
| S2 | 0/100 | Hiçbir konfigürasyon başarılı olamadı | En iyi sinyal: Nötr prompt, tek chunk 0.90 |
| S3 | 60/100 | Nötr prompt + TTS veya Pasif prompt + TTS | Sıfır FP |
| S4 | 5/100 | Agresif prompt + TTS | 0.85-0.90 doğru tespit ama FP'li |
| S5 | 5-15/100 | Agresif prompt + TTS | Chunk 6'da 0.85 ama FP'ler puanı düşürdü |

En iyi genel skor: Nötr prompt + TTS = 12.0 WGT AVG (S1:60, S2:0, S3:60, S4:0, S5:0)
Agresif prompt + TTS = 3.0 WGT AVG (S1:0, S2:0, S3:60, S4:5, S5:5) — ama gerçek tespit var

Hiçbir konfigürasyon ile tatmin edici bir genel skor elde edilemedi.

---

## 7. DÜRÜST DEĞERLENDİRME

### Ne Çalıştı
- TTS ses üretimi (model gerçek konuşmayı formant'tan daha iyi tanıyor)
- Debouncing katmanı (sporadic FP'leri filtreliyor)
- Distress timing hesaplaması (doğru çalışıyor)
- Motor altyapısı (hata vermiyor, güvenilir)
- Spektrogram hız artışı (6x daha hızlı)
- Prompt mühendisliği bulguları (agresif vs pasif vs nötr)

### Ne Çalışmadı
- Ses tabanlı yaklaşımla güvenilir tespit (model çoğu chunk'ta duyamıyor)
- Spektrogram few-shot ile doğru sınıflandırma (model binary classifier gibi davranıyor)
- Halüsinasyon ile tespit arasında denge bulmak (biri düzeldiğinde diğeri bozuluyor)
- Genel skor (en iyi durumda 12/100)

### Temel Sınırlama
Gemma 4 E4B küçük bir edge model (4B parametre). Endüstriyel gürültü altında insan sesi tespiti bu modelin kapasitesinin ötesinde bir görev. Model bazı durumlarda sesi fark edebiliyor ama güvenilir ve tutarlı bir şekilde ayırt edemiyor. Bu modelin hatası değil — görev, modelin eğitim kapsamının dışında.

---

*Bu doküman spektrogram tam sahne test sonuçlarını ve proje genelindeki durumu dürüstçe belgelemektedir.*
*Son güncelleme: 4 Nisan 2026*
