# WWTP Acoustic Safety — PCEN + Spectral Subtraction Denemesi
## Başarısız Deneme ve Geri Dönüş Kararı
> **Test Tarihi:** 5 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Denenen Teknik:** PCEN (Per-Channel Energy Normalization) + Spectral Subtraction
> **Sonuç:** BAŞARISIZ — önceki konfigürasyona geri dönüldü

---

## 1. NE DENENDİ?

S5'teki non-determinizm sorununu çözmek için iki sinyal işleme tekniği birlikte uygulandı.

Birincisi PCEN: Kaggle ses yarışmalarında standart olan Per-Channel Energy Normalization tekniği. `librosa.power_to_db` yerine `librosa.pcen` kullanıldı. PCEN sürekli arka plan gürültüsünü bastırıp anlık zayıf sinyalleri güçlendirmek için tasarlanmış — teoride boğulma çığlığını daha belirgin yapması bekleniyordu.

İkincisi spectral subtraction: Her sahnenin ilk 5 saniyesi (sadece ortam gürültüsü) "gürültü profili" olarak hesaplandı. Sonraki chunk'lardan bu profil çıkarıldı. Teoride inşaat gürültüsü spektrogramdan silinip insan sesi formantları öne çıkmalıydı.

---

## 2. SONUÇLAR

| Sahne | Önceki (power_to_db) | PCEN + Subtraction | Değişim |
|-------|---------------------|-------------------|---------|
| S1 | 60 | 60 | Aynı |
| S2 | 95 | **0** | ❌ Çöktü |
| S3 | 60 | 60 | Aynı |
| S4 | 100 | 100 | Aynı |
| S5 | 0 (non-det) | 0 | Aynı — düzelmedi |
| WGT AVG | 51.0* | 32.0 | ❌ Geriledi |

*51.0 = S5 0 olan run'daki skor

S2, 95'ten 0'a düştü — bu projenin en başarılı sahnesini tamamen kaybettik. S5 düzelmedi — hâlâ sıfır tespit.

---

## 3. NEDEN BAŞARISIZ OLDU?

Temel neden çok basit: inşaat gürültüsü ile insan sesi aynı frekans bandında (300-3000Hz). Spectral subtraction "bu banttaki enerjiyi çıkar" dediğinde inşaat gürültüsüyle birlikte insan sesini de çıkardı. S2'de TTS "Help! Yardım!" sesi tam da bu bantta — gürültüyle birlikte silindi.

PCEN de benzer bir etki yarattı. PCEN sürekli sinyalleri bastırıyor — ama inşaat gürültüsü de insan bağırması da bu bantta sürekli enerji üretiyor. PCEN ikisini de bastırdı.

Bu, projenin temel bulgusunu bir kez daha doğruladı: "Sorun modelde değil, sinyalde." İnsan sesi ve endüstriyel gürültü aynı frekans bandını paylaşıyor. Birini çıkarmaya çalışırken diğerini de çıkarıyorsun. Bu fiziksel bir kısıtlama — DSP ile aşılamıyor, çünkü ayırt edici fark frekans değil, görsel patern (formant eğrileri vs düz gürültü bantları).

---

## 4. GERİ DÖNÜŞ KARARI

PCEN ve spectral subtraction geri alındı. Sistem önceki çalışan konfigürasyona döndürüldü:

Spektrogram: `librosa.power_to_db(S, ref=np.max)` — standart dB ölçekleme
Frekans filtresi: 300-3000Hz (korundu)
Few-shot: 3 temiz + 1 insan (korundu)
Chain-of-Thought: 3 adımlı (korundu)
Debouncing: CONFIRM_MIN_ALARMS = 1 (korundu)

Bu konfigürasyon S1:60, S2:95, S3:60, S4:100 sonuçlarını tutarlı olarak veriyor. S5 non-deterministik — bazen 100, bazen 0.

---

## 5. ALINAN DERS

Gürültü çıkarma (noise subtraction) ve sinyal güçlendirme (PCEN) teknikleri, gürültü ve sinyal farklı frekans bantlarında olduğunda çalışır. Örneğin düşük frekanslı pompa gürültüsünü (120Hz) çıkarıp yüksek frekanslı insan sesini (500-3000Hz) korumak mümkündür — zaten 300-3000Hz frekans filtremiz bunu yapıyor.

Ama gürültü ve sinyal aynı frekans bandında olduğunda (inşaat gürültüsü + insan sesi, ikisi de 300-3000Hz) spectral subtraction işe yaramaz. Ayırt edici fark frekans değil — temporal ve harmonik yapı. İnsan sesi eğimli formant çizgileri ve heceli ritim üretir, gürültü düz bantlar ve rastgele enerji üretir. Bu farkı sinyal işleme değil, görsel patern tanıma (spektrogram + VLM) yakalıyor.

Bu bulgu, projenin spektrogram yaklaşımını neden seçtiğini ve neden çalıştığını güçlendiriyor: modelin gücü frekans ayrımında değil, görsel patern ayrımında.

---

## 6. S5 İÇİN SONRAKI DENEMELER

PCEN + subtraction işe yaramadığına göre S5 için farklı yaklaşımlar denenecek:

Sıradaki deneme: Ollama temperature parametresini 0.1'den 0.0'a düşürmek. Bu modelin non-determinizmini azaltır. S5'te 0.30 ile 0.80 arasındaki salınımı daraltabilir. Diğer sahneleri etkilemez çünkü zaten tutarlı sonuç veriyorlar.

Sonraki deneme: Audio pre-emphasis filtresi. Spektrogram üretmeden önce `librosa.effects.preemphasis` uygulayarak yüksek frekansları hafifçe güçlendirmek. PCEN gibi agresif değil, sinyali silmez, sadece formant bölgesini biraz öne çıkarır.

---

*Bu doküman PCEN + spectral subtraction denemesinin başarısızlığını ve geri dönüş kararını belgelemektedir.*
*Temel bulgu: Gürültü ve sinyal aynı frekans bandında olduğunda spectral subtraction işe yaramaz — ayırt edici fark görsel paternde, frekansta değil.*
*Son güncelleme: 5 Nisan 2026*
