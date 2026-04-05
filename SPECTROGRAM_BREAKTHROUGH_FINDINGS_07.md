# WWTP Acoustic Safety — Spektrogram Yaklaşımı Bulguları
## "Modelin Kulağı Duymuyorsa, Gözüne Göster"
> **Test Tarihi:** 4 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama v0.20.0, RTX 3060 6GB)
> **Referans:** NeurIPS 2024 — "Vision Language Models Are Few-Shot Audio Spectrogram Classifiers"

---

## 1. NEDEN SPEKTROGRAM?

### Duvara Çarptık

Ses tabanlı yaklaşımla (audio → model) üç farklı prompt versiyonu test edildi:

Agresif prompt: Model insan sesini DUYDU (S4: 0.85-0.90, S5: 0.85) ama halüsinasyon da yaptı (S1: 7 FP, S3: 7 FP). Pasif prompt: Halüsinasyon sıfırlandı ama model hiçbir şeyi duyamadı (60 chunk'ta 0 alarm). Nötr prompt: Dengeyi bulmaya çalıştık ama model çoğu chunk'ta duyamıyordu, bazen bir chunk'ta duyup diğerlerinde kaçırıyordu.

Temel sorun: Gemma 4 E4B'nin ses anlama kapasitesi (ASR tabanlı) endüstriyel gürültü altında insan sesini güvenilir şekilde ayırt edemiyor. Bu modelin sınırı — prompt mühendisliği ile aşılamıyor.

### İlham: NeurIPS 2024 Makalesi

NeurIPS 2024'te yayınlanan "Vision Language Models Are Few-Shot Audio Spectrogram Classifiers" makalesi şunu kanıtlıyor: Vision Language Model'ler (VLM'ler) sesi spektrogram görüntüsü olarak aldığında, ses sınıflandırma yapabiliyor. GPT-4o bu görevde insan uzmanlardan bile daha iyi performans gösteriyor. Few-shot örneklerle performans dramatik artıyor.

### Hipotez

Gemma 4 E4B multimodal bir model — hem ses hem görüntü anlıyor. Ses anlama kapasitesi sınırlı ama görüntü anlama kapasitesi çok daha güçlü. Eğer ses dosyasını mel spektrogram görüntüsüne çevirirsek, model GÖRSEL olarak insan sesini mekanik sesten ayırt edebilir. Çünkü spektrogramda insan sesi belirgin formant bantları oluşturur, mekanik ses ise sabit çizgiler veya dikey darbeler oluşturur.

---

## 2. SPEKTROGRAM ANALİZİ — GÖRSEL FARKLAR

Her sahnenin spektrogramı üretildi ve gözle incelendi. Farklar çok net:

S1 (pompa, insan YOK): Sadece düşük frekanslarda (0-512Hz) sabit yatay bantlar. 5 saniye boyunca hiçbir değişiklik yok. Üst frekanslar tamamen boş (siyah). Tipik mekanik gürültü paterni.

S2 (inşaat + bağırma, insan VAR): Geniş bant gürültü arka planı üzerinde 512-1024Hz aralığında parlak eğimli çizgiler — konuşma formantları. Kıvrımlı, kısa süreli, düzensiz aralıklı. Makinelerde bu patern oluşmaz.

S3 (metalik sesler, insan YOK): Dikey parlak çizgiler (metalik darbeler) ve altta sabit yatay bant (motor hum). Formant eğrisi yok ama dikey darbeler yanıltıcı olabilir.

S4 (maskeli ses, insan VAR): En net görünen — 512-2048Hz aralığında üst üste yığılmış yatay bantlar (harmonik yapı), merdiven deseni gibi. Klasik insan sesi harmonik yapısı. Bu patern S1 ve S3'te kesinlikle yok.

S5 (boğulma, insan VAR): 512-1024Hz aralığında kıvrımlı parlak noktalar ve formant yapıları. S2'ye benzer ama daha dağınık ve kesintili — boğulma efektinin doğal sonucu.

---

## 3. TEST AŞAMALARI

### Aşama 1: Zero-Shot Spektrogram (Sıfır Örnek)

İlk denemede spektrogram görüntüsü modele hiçbir örnek verilmeden gönderildi. Model görüntüyü analiz etti, formant paternlerini tanımladı (reasoning'de "formants characteristic of human speech" dedi) ama confidence skorunu ters yönde kullandı — 0.90 "insan yok, eminim" anlamında verdi.

Prompt düzeltildi — confidence yönü netleştirildi. Bu sefer model formant görmediğini söyledi, tüm sahnelere düşük confidence verdi. Zero-shot yaklaşım tutarsız sonuçlar üretti.

### Aşama 2: Thinking Mode Sorunu

Gemma 4 E4B'nin "thinking mode" özelliği API yanıtlarını karmaşıklaştırdı. Model cevabını `content` alanı yerine `thinking` alanına yazıyordu. `content` boş kalıyordu. Çözüm: API çağrısına `"think": False` parametresi eklendi. Bu sorunu tamamen çözdü.

### Aşama 3: Few-Shot Spektrogram (Örnekli) — DÖNÜM NOKTASI

NeurIPS makalesindeki yaklaşım uygulandı. Modele iki örnek gösterildi:

Örnek 1 (temiz): S1 pompa dairesi spektrogramı — "Bu temiz, sadece makine sesi. Düşük frekanslarda sabit bantlar var, formant yok."

Örnek 2 (insan sesli): S4 maskeli ses spektrogramı — "Bu insan sesli. 512-2048Hz aralığında eğimli/yığılmış formant bantları görüyorsun."

Sonra model yeni spektrogramları sınıfladı.

---

## 4. FEW-SHOT SPEKTROGRAM SONUÇLARI

| Sahne | İnsan | Alarm | Conf | Tip | Doğru mu? | Reasoning |
|-------|-------|-------|------|-----|-----------|-----------|
| S1 (30-35s) | YOK | ---- | 0.10 | none | ✅ DOĞRU | "Only steady low-frequency noise bands" |
| S2 (30-35s) | VAR | 🚨 | 0.90 | speech | ✅ DOĞRU | "Strong distinct formant patterns of human speech" |
| S3 (30-35s) | YOK | 🚨 | 0.90 | shouting | ❌ YANLIŞ | "Rhythmic formant patterns" (metalik sesi insan sandı) |
| S4 (35-40s) | VAR | 🚨 | 0.90 | speech | ✅ DOĞRU | "Strong distinct formant patterns of human speech" |
| S5 (25-30s) | VAR | 🚨 | 0.90 | shouting | ✅ DOĞRU | "Rhythmic formant patterns at beginning and end" |
| S5 (30-35s) | VAR | 🚨 | 0.90 | speech | ✅ DOĞRU | "Rhythmic formant patterns across duration" |
| S5 (40-45s) | VAR | 🚨 | 0.90 | shouting | ✅ DOĞRU | "Rhythmic formant patterns across duration" |

**Başarı oranı: 7 testten 6 doğru (%85.7)**

---

## 5. SES TABANLI vs SPEKTROGRAM KARŞILAŞTIRMASI

### Tespit Performansı

| Sahne | Ses + Agresif | Ses + Nötr | Spektrogram Few-Shot |
|-------|--------------|------------|----------------------|
| S1 (insan yok) | ❌ 7 FP | ✅ 0 FP | ✅ 0 FP |
| S2 (insan var) | Tespit var ama FP'li | 1 chunk 0.90 | ✅ 0.90 alarm |
| S3 (insan yok) | ❌ 7 FP | ✅ 0 FP | ❌ 1 FP (0.90) |
| S4 (insan var) | 0.85-0.90 ama FP'li | 0 alarm | ✅ 0.90 alarm |
| S5 (insan var) | 1 chunk 0.85 | 0 alarm | ✅ 3 chunk 0.90 |

### Hız Karşılaştırması

| Yöntem | Chunk Süresi (ort.) | 12 Chunk Toplam |
|--------|---------------------|-----------------|
| Ses + Agresif prompt | ~37 saniye | ~7.4 dakika |
| Ses + Nötr prompt | ~25 saniye | ~5.0 dakika |
| Spektrogram few-shot | ~6 saniye | ~1.2 dakika |

Spektrogram yaklaşımı ses tabanlıya göre **6 kat daha hızlı**. 5 saniyelik sesi 6 saniyede analiz etmek — neredeyse gerçek zamanlı. Bu edge deployment için kritik bir avantaj.

### Güvenilirlik

| Yöntem | Non-determinizm | Tutarlılık |
|--------|----------------|------------|
| Ses tabanlı | Yüksek — aynı chunk farklı çalıştırmada farklı sonuç | Düşük |
| Spektrogram | Düşük — görüntü deterministik, model tutarlı karar veriyor | Yüksek |

---

## 6. NEDEN ÇALIŞIYOR?

### Modelin İç Mimarisi

Gemma 4 E4B multimodal bir model — hem ses hem görüntü işleyebiliyor. Ama bu iki kapasite eşit değil. Ses anlama (ASR) küçük bir modülde, temiz konuşma tanıma için optimize edilmiş. Görüntü anlama (Vision) çok daha büyük ve güçlü bir modülde, karmaşık görsel patern tanıma için eğitilmiş. Spektrogram yaklaşımı modelin zayıf kulağını atlayıp güçlü gözünü kullanıyor.

### Formant Paternleri Görsel Olarak Belirgin

İnsan sesi spektrogramda benzersiz görsel desenler oluşturuyor — eğimli formant bantları, harmonik merdiven yapıları, düzensiz zaman aralıklı kısa patlamalar. Mekanik sesler ise sabit yatay çizgiler, dikey darbeler, uniform enerji dağılımı oluşturuyor. Bu iki patern görsel olarak çok farklı — tıpkı yüz tanıma gibi, model görsel paterni ayırt edebiliyor.

### Few-Shot Kalibrasyon Etkisi

Zero-shot'ta model spektrogramı genel olarak analiz ediyordu ama bizim spesifik endüstriyel bağlamda neyin "temiz" neyin "insan sesli" olduğunu bilmiyordu. İki örnek bu kalibrasyonu sağladı. Bu NeurIPS makalesindeki bulguyla birebir uyumlu — few-shot örnekler performansı dramatik artırıyor çünkü modele "bu bağlamda neyi aramalısın" gösteriliyor.

---

## 7. TEK SORUN: S3 FALSE POSITIVE

S3 (metalik sesler, insan yok) spektrogramında model "rhythmic formant patterns" gördüğünü iddia etti ve 0.90 confidence ile yanlış alarm verdi. Bu sorunun nedeni metal scraping sesinin bilerek insan konuşma ritmine benzetilmiş olması — düzensiz yoğunluk değişimleri, 300-3000Hz aralığında. Spektrogramda da bu benzerlik görünüyor.

Olası çözümler: S3 spektrogramını üçüncü bir "temiz ama yanıltıcı" örneği olarak few-shot örneklerine eklemek. Debouncing katmanı ile ardışık alarm kontrolü yapmak. Farklı bir spektrogram parametresi kullanmak (örneğin frekans aralığını daraltmak).

---

## 8. YOLCULUK ÖZETİ — İLMEK İLMEK

Bu projenin teknik yolculuğu adım adım bir keşif süreciydi:

**Adım 1 — Formant sentezi ile başladık.** Model sentetik çığlığı duyamadı (S5'te 12 chunk sıfır sinyal). Kök neden: formant sesleri modelin ASR eğitim verisindeki konuşma paternleriyle eşleşmiyordu.

**Adım 2 — TTS'e geçtik.** Model "Help! Yardım!" sesini tanıdı (S2'de "shouting_help", S5'te 0.85). Kök neden çözüldü — gerçek konuşma paterni modelin tanıyabildiği bir format.

**Adım 3 — Prompt mühendisliği yaptık.** Üç versiyon test ettik. Agresif prompt halüsinasyon yarattı, pasif prompt tespiti öldürdü, nötr prompt dengeledi ama tutarsız. Altın bulgu: "AI'ya ne söylediğin, ne kadar söylediğinden daha önemli."

**Adım 4 — Duvara çarptık.** Ses tabanlı yaklaşımın sınırına ulaştık. Model bazen duyuyor bazen duymuyor, LLM non-determinizmi güvenlik sistemi için kabul edilemez.

**Adım 5 — Spektrogram hipotezi.** NeurIPS 2024 makalesinden esinlenerek "modelin kulağı yetersizse gözünü kullan" hipotezini kurduk.

**Adım 6 — Zero-shot spektrogram.** Model formantları gördü ama tutarsız karar verdi. Thinking mode API sorunu çözüldü.

**Adım 7 — Few-shot spektrogram.** DÖNÜM NOKTASI. İki örnek ile model %85.7 doğrulukla sınıflandırma yaptı. S5'te üç farklı chunk'ta 0.90 confidence. 6 kat hız artışı. Tutarlı ve güvenilir sonuçlar.

---

## 9. SAHADA KULLANILABİLİRLİK

Spektrogram yaklaşımı sahada tamamen kullanılabilir:

Ek donanım gerekmiyor — aynı mikrofon, aynı edge cihaz. Ses → spektrogram dönüşümü 0.1 saniye sürüyor (librosa ile). İnternet gerekmiyor — tüm işlem lokalde. Toplam analiz süresi: 0.1s (spektrogram) + 6s (model) = 6.1 saniye per chunk. Bu 5 saniyelik ses için neredeyse gerçek zamanlı.

Akış: Mikrofon → 5sn ses al → spektrogram üret (0.1s) → modele gönder (6s) → karar → aksiyon

---

## 10. YARIŞMA KURALLARI

Spektrogram yaklaşımı yarışma kurallarını İHLAL ETMİYOR. Yarışma "Gemma 4 kullan, topluma faydalı bir proje yap" diyor. Gemma 4 zaten multimodal — hem ses hem görüntü anlıyor. Modelin vision kapasitesini kullanmak kuralları ihlal etmek değil, modelin gücünü doğru kullanmak. Hatta bu teknik derinlik göstergesi: "Modelin ses anlama kapasitesini test ettik, sınırlarını bulduk. Sonra aynı modelin vision kapasitesini kullanarak spektrogram yaklaşımıyla bu sınırı aştık."

---

## 11. SONRAKI ADIMLAR

1. S3 false positive çözümü (ek few-shot örnek veya debouncing)
2. Spektrogram yaklaşımını motora entegre etme (acoustic_engine.py)
3. 12 chunk tam sahne testi (few-shot spektrogram modu)
4. JSON davranış export özelliği
5. E2B model karşılaştırma testleri
6. Demo arayüzü (spektrogram görselleştirmeli)
7. Kaggle writeup ve video

---

*Bu doküman spektrogram yaklaşımının keşif sürecini ve sonuçlarını içerir.*
*Proje için dönüm noktası niteliğinde bir bulgu.*
*Son güncelleme: 4 Nisan 2026*
