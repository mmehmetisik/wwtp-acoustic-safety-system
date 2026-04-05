# WWTP Acoustic Safety — Gemma 4 E4B Test Sonuçları
## BARE vs CONTEXT vs PROTOCOL Karşılaştırması
> **Test Tarihi:** 3 Nisan 2026
> **Model:** Gemma 4 E4B (Ollama, yerel çalışma, RTX 3060 6GB)
> **Test Yöntemi:** Her sahne için tek chunk (5 saniyelik kritik dilim)

---

## 1. BÜYÜK TABLO

| Sahne | İnsan | BARE | CONTEXT | PROTOCOL |
|-------|-------|------|---------|----------|
| S1 — Pompa Dairesi | HAYIR | ✅ Doğru | ✅ Doğru | ✅ Doğru |
| S2 — İnşaat + Bağırma | EVET | ❌ Kaçırdı | ✅ Tespit! | ✅ Tespit! |
| S3 — Havuz Yanlış Alarm | HAYIR | ✅ Doğru | ✅ Doğru | ❌ Yanlış Alarm |
| S4 — Menhol Maskeli | EVET | ❌ Kaçırdı | ❌ Kaçırdı | ✅ Tespit! |
| S5 — Havuz KRİTİK | EVET | ❌ Kaçırdı | ❌ Kaçırdı* | ✅ Tespit! |
| **Başarı** | | **2/5** | **3/5** | **4/5** |
| **Kritik Sahne (S2,S4,S5)** | | **0/3** | **1/3** | **3/3** |

*S5 CONTEXT notu: Model human_detected=false dedi AMA alarm=true ve ESTOP_POOL_BRIDGE verdi. Yani sesi duymadı ama bağlamdan ("worker climbing pool wall") tehlikeyi algılayıp alarm verdi. İlginç bir ara davranış.

---

## 2. S5 HAYATTA KALMA VERDİKTİ

| Mod | İnsan Tespiti | Alarm | Aksiyon | Verdikt |
|-----|---------------|-------|---------|---------|
| BARE | ❌ Hayır | ❌ Hayır | CONTINUE_MONITORING | ★ WOULD NOT HAVE SURVIVED |
| CONTEXT | ❌ Hayır | ✅ Evet | ESTOP_POOL_BRIDGE | ⚠️ Alarm verdi ama sesi duymadı |
| PROTOCOL | ✅ Evet (0.98) | ✅ Evet | ESTOP_POOL_BRIDGE | ★★★ PROBABLE SURVIVAL ★★★ |

**PROTOCOL modda:** Güven skoru 0.98, distress tipi "screaming", aksiyon ESTOP_POOL_BRIDGE, bildirim Operator + Emergency Services. Tespit zamanı 25-30 saniye (düşme anı 20. saniye, gecikme ~5-10 saniye). İyi yüzücü (30sn eşiği) KURTULUR.

---

## 3. MOD MOD ANALİZ

### BARE Modu — "Hiçbir şey bilmeden dinle"
- Başarı: 2/5
- Doğru tespit ettiği: S1 (pompa sesi = mekanik), S3 (metalik ses = mekanik)
- Kaçırdığı: S2, S4, S5 — tüm insan sesleri
- Yorum: Model sessiz ortamları doğru tanıyor ama gürültü altındaki insan sesini hiç duyamıyor. Tıpkı o gün sahada kimsenin duyamadığı gibi. İnsan kulağıyla aynı sonuç.

### CONTEXT Modu — "Neredesin ve ne oluyor bilgisiyle dinle"
- Başarı: 3/5
- BARE'den iyileşme: S2 artık tespit edildi! (+1)
- Hâlâ kaçırdığı: S4, S5
- İlginç bulgu (S5): human_detected=false ama alarm=true. Model sesi duymadı ama bağlamda "worker climbing pool wall" yazıyordu, bunu okuyup tehlike algıladı ve ESTOP verdi. Yani model sesi değil, metni kullanarak karar verdi. Akıllıca ama güvenilir değil — gerçek sistemde böyle metin bilgisi olmayacak.
- Yorum: Bağlam bilgisi orta zorluklu sahneyi (S2) kurtardı ama en zor sahnelerde (S4 maskeli ses, S5 gürültü altında çığlık) yetmedi.

### PROTOCOL Modu — "Tam güvenlik talimatıyla dinle"
- Başarı: 4/5 (en iyi)
- Tüm kritik sahneler: 3/3 ✅
- S4 kurtarıldı! distress_type: "muffled_call", action: INITIATE_CONFINED_SPACE_RESCUE, confidence: 0.98
- S5 kurtarıldı! distress_type: "screaming", action: ESTOP_POOL_BRIDGE, confidence: 0.98
- S3 yanlış alarm: Model "şüphede alarm ver" kuralını aşırı uyguladı, metalik sesi insan sesi sandı.
- Yorum: Güvenlik protokolü modelin davranışını kökten değiştirdi. "Şüphede alarm ver" talimatı, modeli daha hassas yaptı. Bu S4 ve S5'te hayat kurtardı ama S3'te yanlış alarm üretti. Bu trade-off tam olarak beklenen ve kabul edilebilir: yanlış alarm maliyeti (-10) insanı kaçırma maliyetinden (-40) çok daha düşük.

---

## 4. EN ÖNEMLİ BULGULAR

### Bulgu 1: Bağlam ve Protokol Hayat Kurtarıyor
BARE modda model 0/3 kritik sahneyi tespit etti. PROTOCOL modda 3/3. Aradaki fark sadece prompt'a eklenen güvenlik protokolü. Aynı ses, aynı model, farklı talimat — farklı sonuç: ölüm vs hayatta kalma.

### Bulgu 2: Yanlış Alarm vs İnsanı Kaçırmak Trade-off'u
PROTOCOL modda S3'te yanlış alarm verildi. Bu asimetrik puanlama sistemimizle tutarlı: yanlış alarm -10 puan, insanı kaçırmak -40 puan. Model "şüphede alarm ver" kuralını uyguladı ve bu sayede S4 ve S5'te hayat kurtardı. Bir yanlış alarm karşılığında iki hayat kurtarmak, kabul edilebilir bir trade-off.

### Bulgu 3: S5 CONTEXT'te İlginç Ara Davranış
Model sesi duymadı ama bağlamdan tehlikeyi algıladı. Bu LLM'lerin "multimodal reasoning" kapasitesinin ilginç bir göstergesi — ses kanalından bilgi alamayınca metin kanalından çıkarım yaptı. Ancak gerçek dünya uygulamasında güvenilir değil.

### Bulgu 4: S4 En Zor Sahne — Sadece PROTOCOL Kurtardı
Maskeli/boğuk ses + galeri yankısı kombinasyonu en zor sahne. BARE ve CONTEXT modda model tamamen kaçırdı. Sadece PROTOCOL modda "any muffled voice pattern MUST trigger confined space rescue" talimatı ile tespit edildi. Bu, aşırı zor sinyal koşullarında bile doğru güvenlik talimatının fark yaratabileceğini gösteriyor.

### Bulgu 5: Model Detayları ve Güven Skorları
- PROTOCOL modda S4: confidence 0.98, distress_type "muffled_call", action "INITIATE_CONFINED_SPACE_RESCUE" — mükemmel JSON çıktısı
- PROTOCOL modda S5: confidence 0.98, distress_type "screaming", action "ESTOP_POOL_BRIDGE", notify ["Operator", "Emergency Services"] — mükemmel SCADA entegrasyon çıktısı
- Model sadece tespit yapmakla kalmadı, doğru aksiyonu ve doğru kişileri de önerdi

---

## 5. UYGULAMA İÇİN KARARLAR

Bu test sonuçlarına dayanarak uygulamada şu kararlar alınacak:

1. **Uygulama PROTOCOL modda çalışacak** — en yüksek başarı oranı (4/5, kritik 3/3)
2. **Yanlış alarm riski kabul edilecek** — S3 trade-off'u açıkça belgelenecek
3. **JSON çıktı formatı çalışıyor** — SCADA entegrasyonu için uygun
4. **Tespit süresi ~25-30 saniye** — probable survival eşiği içinde
5. **Demo'da üç mod karşılaştırmalı gösterilecek** — hikayenin gücü bu ilerlemede

---

## 6. VİDEO VE WRITEUP İÇİN KULLANILACAK HİKAYE

"Bağlam olmadan AI de insan kulağı kadar çaresiz.
Ama doğru güvenlik talimatıyla AI, insanın duyamadığını duyabiliyor.

BARE modda: Model duyamadı. Adam hayatta kalmaz.
CONTEXT modda: Model biraz anladı. Ama yetmedi.
PROTOCOL modda: Model duydu. Alarm verdi. ESTOP çalıştı.
Adam hayatta kalırdı.

Sadece mikrofon koymak yetmez.
AI'ya neyi dinlemesi gerektiğini söylemek,
hayat kurtarmak ile kurtaramamak arasındaki farktır."

---

*Bu doküman test sonuçlarının referans kaydıdır.*
*Demo arayüzü, video ve writeup bu verilere dayanacaktır.*
*Son güncelleme: 3 Nisan 2026*
