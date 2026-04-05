# WWTP Acoustic Safety System — Ses Dosyaları Açıklaması
## 5 Sahne × 60 Saniye — TTS Tabanlı Üretim
> **Üretim Yöntemi:** Endüstriyel gürültü (numpy/scipy) + İnsan sesi (Google TTS)
> **Format:** 16kHz, Mono, PCM_16, WAV
> **Üretim Aracı:** audio_generator_tts.py
> **Seed:** 42 (gürültü bileşenleri tekrarlanabilir, TTS deterministik)

---

## S1 — Pompa Dairesi, Normal Operasyon
**Dosya:** `S1_pump_room_normal.wav`
**İnsan:** YOK
**Amaç:** Yanlış alarm (false positive) direnci testi. Model bu seste "insan yok" demeli.

Bu sahne tamamen mekanik seslerden oluşuyor. 60 saniye boyunca hiçbir değişiklik yok, baştan sona aynı monoton endüstriyel uğultu devam ediyor. Baskın ses 120Hz frekanslı santrifüj pompa hum'ı — derin, kalın, sürekli bir "hmmmmm" tonu. Bunun üzerine 240Hz ve 360Hz harmonikler binmiş, sese hafif bir metalik karakter katıyor. Arka planda 50-300Hz aralığında pink noise var, bu boru titreşimlerini simüle ediyor — düşük frekanslı, sürekli bir rumble. Motor drone 150Hz'de ayrı bir ton ekliyor, 50-250Hz aralığında brown noise ile desteklenmiş. Tüm frekanslar 250Hz'in altında tutulmuş — bu bilinçli bir tasarım kararı çünkü insan sesi 300Hz'den başlar. Böylece model mekanik sesi insan sesiyle karıştırmamalı.

Dinlediğinde duyacağın şey: sıkıcı, değişmeyen, düşük frekanslı bir fabrika uğultusu. Hiçbir ani ses yok, hiçbir ritim değişikliği yok, hiçbir insan sesi yok. Bu tam olarak bir pompa dairesinin gerçek sesi — 7/24 aynı monoton gürültü.

---

## S2 — İnşaat Alanı, İnsan Bağırıyor
**Dosya:** `S2_construction_human.wav`
**İnsan:** VAR (25. saniyeden itibaren)
**Amaç:** Yoğun gürültü altında insan sesini tespit etme testi.

Bu sahne iki bölümden oluşuyor. İlk 25 saniye sadece yoğun inşaat gürültüsü var. Beton mikseri 200-2000Hz aralığında ritmik bir döngüde çalışıyor (0.5Hz modülasyon — yani 2 saniyede bir yükselip alçalıyor). Ekskavatör düşük frekanslı ağır darbe sesleri yapıyor, düzensiz aralıklarla "güm güm" vuruyor. Pnömatik matkap en rahatsız edici ses — 1000Hz üstünde keskin, yüksek frekanslı "tatatata" darbeleri, 20Hz hızında. Metal çarpma sesleri rastgele aralıklarla geliyor, 500-8000Hz aralığında kısa ve sert çınlamalar. Bu dört ses birlikte kaotik, yoğun ve rahatsız edici bir inşaat ortamı oluşturuyor.

25. saniyeden itibaren bu gürültünün altına gerçek insan sesi karışıyor. Google TTS ile üretilmiş "Help! Help me!" (İngilizce) ve "Yardım! Yardım edin!" (Türkçe) sesleri 3 saniye aralıklarla dönüşümlü tekrarlanıyor. Sesler doğal TTS tonu ile üretilmiş, pitch shift uygulanmamış — modelin tanıyabileceği gerçek konuşma paterni korunmuş. Her çığlığın başında hafif bir yükseliş var (bağırmaya başlama), ortasında sabit seviye (bağırma), sonunda düşüş (nefes alma). Mix ağırlığı 0.35 — yani insan sesi inşaat gürültüsünün altında, duyulabilir ama baskın değil. Kulağını zorlarsan kelimeleri seçebilirsin ama rahat bir şekilde duyamazsın. Bu tam olarak gerçek hayattaki durumu simüle ediyor: adam bağırıyor ama inşaat gürültüsü bastırıyor.

---

## S3 — Havuz Kenarı, Yanlış Alarm Testi
**Dosya:** `S3_pool_false_alarm.wav`
**İnsan:** YOK
**Amaç:** Yanıltıcı mekanik sesleri insan sesinden ayırt etme testi.

Bu sahne bilerek aldatıcı tasarlanmış. 60 saniye boyunca insan yok ama bazı sesler insan sesine benziyor. Arka planda hafif bir havuz suyu sesi var — düşük seviyeli, sakin bir pink noise (2000Hz altı). Bunun üzerine köprü kazıyıcı motoru 180Hz'de yavaş bir uğultu yapıyor, 0.1Hz modülasyonla (10 saniyede bir hafifçe yükselip alçalıyor).

Yanıltıcı sesler şunlar: Metal sürtme sesi 300-3000Hz aralığında düzensiz yoğunluk değişimleri gösteriyor. Bu ses bilerek insan konuşma ritmine benzetilmiş — bazen yüksek bazen düşük, bazen kısa bazen uzun, tıpkı bir insanın konuşurken ses tonunu değiştirmesi gibi. Zincir şıkırtıları 500-5000Hz'de rastgele klik sesleri çıkarıyor. Ve en aldatıcı olan metal çarpma sesi: 800-3000Hz aralığında 0.35 saniye süren tek darbeler, exponansiyel sönümle. Bu ses kısa bir insan çığlığına benziyor — keskin başlangıç, hızlı sönüm. 4 adet rastgele yerleştirilmiş.

Dinlediğinde "bu insan mı makine mi" diye tereddüt edebilirsin ama 60 saniye boyunca hiçbir gerçek insan sesi, kelime veya konuşma paterni yok. Tüm sesler mekanik kaynaklı.

---

## S4 — Menhol Galeri, Maskeli İşçi (Zayıf Sinyal)
**Dosya:** `S4_manhole_masked.wav`
**İnsan:** VAR (20. saniyeden itibaren)
**Amaç:** Çok zor koşullarda zayıf insan sesi tespiti. En zor sahne.

Bu sahne yeraltı ortamını simüle ediyor. İlk 20 saniye sessiz ve ürkütücü bir ambiyans var. Uzaktan gelen su akışı sesi — düşük frekanslı, sürekli, 500Hz altında pink noise. Havalandırma uğultusu — 120Hz'de ince bir sinüs tonu. Ve damla sesleri — 600Hz'de rastgele aralıklarla (0.5-3 saniye) gelen kısa, keskin "tık" sesleri, hızla sönümlenen. Bu üç ses birlikte karanlık, nemli, derin bir beton galerinin atmosferini oluşturuyor.

20. saniyeden itibaren bu sessiz ortama boğuk bir insan sesi karışıyor. Google TTS ile üretilmiş "Help! Help me!" (İngilizce) ve "Yardım! Yardım edin!" (Türkçe) sesleri 4 saniye aralıklarla tekrarlanıyor. Ama bu sesler iki katmanlı bozulmadan geçmiş: birincisi 2000Hz low-pass filtre — bu respiratör maske etkisini simüle ediyor, yüksek frekansları keserek sesi boğuk ve uzaktan geliyormuş gibi yapıyor. İkincisi 1.2 saniyelik reverb — beton tünel yankısı eklenmiş, ses dalgalanarak, yankılanarak geliyor, kelimelerin sınırları bulanıklaşıyor.

Dinlediğinde 20. saniyeden sonra "bir şey var ama ne olduğunu anlamıyorum" hissi almalısın. Türkçe "Yardım" kelimesi İngilizce "Help"ten biraz daha anlaşılır çünkü Türkçe TTS artikülasyonu daha belirgin. Ama her iki dilde de kelimeleri net anlamak zor — bu tamamen tasarım gereği. Gerçek hayatta 6 metre derinlikte beton galeride, ağzında maske olan bir insanın sesini böyle duyarsın.

---

## S5 — Durultma Havuzu, GERÇEK KAZA SAHNESİ (Kritik)
**Dosya:** `S5_pool_critical.wav`
**İnsan:** VAR (20. saniyede düşme, 25. saniyeden itibaren çığlık)
**Amaç:** Projenin kalbi. "O adam hayatta kalır mıydı?" sorusunun cevabı.

Bu sahne üç bölümden oluşuyor ve gerçek bir olayı yeniden yaratıyor.

**0-20. saniye — Normal inşaat operasyonu.** S2 ile aynı türde inşaat gürültüsü ama farklı rastgele paternlerle (farklı seed kullanılıyor, bu yüzden birebir aynı değil). Beton mikseri, ekskavatör, pnömatik matkap ve metal çarpma sesleri. Ağırlıklar biraz farklı — ekskavatör daha baskın (daha yakında), mikseri biraz daha sessiz. Bu 20 saniye boyunca her şey normal, tehlike yok. Tıpkı o cumartesi sabahı gibi.

**20-25. saniye — Düşme olayı.** 20. saniyede bir gümbürtü ve ardından büyük bir su sıçraması duyulur. Gümbürtü 100-2000Hz aralığında kısa bir gürültü patlaması — havuz duvarına çarpma sesi, 0.3 saniye sürüyor ve hızla sönüyor. Hemen ardından su sıçraması başlıyor — 200-5000Hz aralığında geniş bantlı bir gürültü, önce hızla yükseliyor (suyun patlaması) sonra 2 saniye içinde yavaşça sönüyor (su yüzeyinin sakinleşmesi). 20. saniyeden itibaren ayrıca panik su çırpınması sesleri başlıyor — düzensiz aralıklarla (0.3-1.5 saniye) gelen kısa su sıçramaları, batıp çıkan bir insanın el kol hareketlerini simüle ediyor. Bu sesler 60. saniyeye kadar devam ediyor.

**25-60. saniye — Boğulma çığlığı.** Bu kısım projenin en kritik sesidir. Google TTS ile üretilmiş kısa panik cümleleri var: "Help! Help!", "Yardım!", "Help me!", "İmdat!", "Somebody!", "Yardım edin!" — ama bunlar temiz konuşma olarak değil, boğulma efektleriyle bozulmuş durumda.

Boğulma efektleri şunlar: Birincisi, her cümlenin rastgele %30 ile %100'ü duyuluyor — geri kalanı kesilmiş çünkü kişi su altına batmış. Bazen sadece "Hel-" duyarsın, "Help" tamamlanmadan ses kesilir. İkincisi, ses düzensiz olarak açılıp kapanıyor — hızlı bir yükseliş (su yüzeyine çıkma, nefes kapma), kısa bir düz kısım (yüzeyde bağırma), sonra yavaş düşüş (tekrar batma). Üçüncüsü, cümlelerin yarısında üzerine su gürültüsü biniyor — 200-2000Hz aralığında kısa su patlamaları, ağza su girmiş ve boğuluyor efekti. Dördüncüsü, zamanlama tamamen düzensiz — bazen 1.5 saniye aralıkla hızlı hızlı (yüzeyde panikle nefes alıp bağırıyor), bazen 3-5 saniye tamamen sessizlik (su altında, bağıramıyor).

Tüm bunlar 95dB inşaat gürültüsünün altında. Mix ağırlığı 0.40 — yani inşaat gürültüsü hâlâ baskın ama insan sesi de duyulabilir seviyede. Dinlediğinde inşaat gürültüsü devam ederken arada kesik kesik, boğuk, bazen yarıda kalan "Help!" ve "Yardım!" sesleri duyarsın. Bazıları su sesiyle karışmış, bazıları birden kesilmiş. Bu, havuza düşmüş ve boğulmakta olan bir insanın gerçekçi akustik simülasyonudur.

---

## GENEL NOTLAR

**Ses Kalitesi Felsefesi:** İnsan sesleri için Google TTS kullanılmıştır (gerçek konuşma paternleri). Gemma 4 E4B'nin ASR motoru gerçek insan konuşmasını tanımak üzere eğitilmiştir — TTS sesleri bu eğitim verisiyle uyumludur. Endüstriyel gürültüler ise numpy/scipy ile matematiksel olarak üretilmiştir (sinüs dalgaları, filtreler, rastgele gürültü). Bu hibrit yaklaşım hem gerçekçi ses üretimi hem de tam kontrol ve tekrarlanabilirlik sağlar.

**Etik Not:** Gerçek bir boğulma sesi kaydı etik olarak mümkün değildir. Bu sesler 10+ yıllık saha deneyiminden alınan akustik parametrelerle (frekans, dB, SNR) üretilmiştir. Tüm değerler gerçek tesis ölçümlerine dayanmaktadır.

**Tekrarlanabilirlik:** Gürültü bileşenleri Seed=42 ile üretilir — aynı parametrelerle her zaman aynı sonuç. TTS bileşenleri deterministiktir — aynı metin, aynı dil, aynı ses.

---

*Bu doküman 5 ses dosyasının içeriğini detaylı olarak açıklar.*
*Demo arayüzünde, videoda ve writeup'ta bu açıklamalar referans alınacaktır.*
*Son güncelleme: 3 Nisan 2026*
