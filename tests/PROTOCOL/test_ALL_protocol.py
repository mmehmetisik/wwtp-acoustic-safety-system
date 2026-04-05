"""
TEST — PROTOCOL MODU (Tüm Sahneler)
=====================================
En yüksek bağlam seviyesi. Modele verilen:
  - Lokasyon bilgisi
  - Operasyon durumu
  - TAM GÜVENLİK PROTOKOLÜ

Güvenlik protokolü modele şunu söylüyor:
  "İnsan sesi olabilecek her şeyde alarm ver.
   Yanlış alarm vermek, insanı kaçırmaktan İYİDİR."

BARE modda 3 sahne kaçırıldı. CONTEXT modda ne oldu bilmiyoruz henüz.
PROTOCOL mod son şansımız — bu da yetmezse, model bu göreve hazır değil.

Kullanım:
  python tests/test_ALL_protocol.py

Author: Mehmet ISIK | Data Scientist | Adana ASKI | Kaggle Grandmaster
Date  : April 2026
"""

import os, io, json, base64, struct, time, sys
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "gemma4:e4b"
AUDIO_DIR  = os.path.join("dataset", "audio")
CHUNK_SEC  = 5

# ═══════════════════════════════════════════════════════════════
# SAHNE TANIMLARI — Lokasyon + operasyon + güvenlik protokolü
# ═══════════════════════════════════════════════════════════════

SCENES = [
    {
        "scene_id": "S1",
        "title": "Pompa Dairesi — Normal Operasyon",
        "file": "S1_pump_room_normal.wav",
        "chunk_idx": 0,
        "chunk_time": "0-5 sn",
        "human_present": False,
        "expected": "İnsan YOK → alarm YOK",
        "location": "Pump station, basement level, Ceyhan WWTP",
        "operation": "Routine wastewater pumping. Duty pump 1 and 2 running at 85% capacity. Saturday morning shift.",
        "protocol": "Normal operation. No restricted access zones active. Standard monitoring.",
    },
    {
        "scene_id": "S2",
        "title": "İnşaat Alanı — İnsan Bağırıyor",
        "file": "S2_construction_human.wav",
        "chunk_idx": 5,
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "İnsan VAR → alarm VER",
        "location": "Construction site adjacent to aeration tanks, Ceyhan WWTP",
        "operation": "Weekend construction work on new sludge press building. 12-person crew on site. High noise environment. Saturday 10:00.",
        "protocol": "Construction zone active. PPE required. Noise level exceeds 85dB — hearing protection mandatory. Restricted access to operational areas.",
    },
    {
        "scene_id": "S3",
        "title": "Havuz Kenarı — Yanlış Alarm Testi",
        "file": "S3_pool_false_alarm.wav",
        "chunk_idx": 3,
        "chunk_time": "15-20 sn",
        "human_present": False,
        "expected": "İnsan YOK → alarm YOK",
        "location": "Secondary clarifier pool edge, Ceyhan WWTP",
        "operation": "Secondary clarifier sludge scraper bridge running normal cycle. Automatic operation. No personnel in restricted zone.",
        "protocol": "Pool edge restricted zone. Scraper bridge active — no personnel permitted within 2 meters of pool edge during bridge operation.",
    },
    {
        "scene_id": "S4",
        "title": "Menhol Galeri — Maskeli İşçi",
        "file": "S4_manhole_masked.wav",
        "chunk_idx": 5,
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "İnsan VAR → alarm VER + CONFINED SPACE RESCUE",
        "location": "Underground sewer gallery, manhole access point MH-07, Ceyhan WWTP",
        "operation": "Confined space entry permit issued for gallery inspection. Single worker with respirator. Entry logged at 09:45. Buddy system in place — surface attendant monitoring.",
        "protocol": (
            "CONFINED SPACE PROTOCOL ACTIVE. "
            "Continuous atmospheric monitoring required. "
            "Worker check-in every 10 minutes. "
            "If no response within 15 minutes, initiate rescue. "
            "Microphone monitoring active at manhole MH-07. "
            "ANY muffled or distorted voice pattern from gallery microphone MUST trigger confined space rescue protocol."
        ),
    },
    {
        "scene_id": "S5",
        "title": "Durultma Havuzu — GERÇEK KAZA SAHNESİ",
        "file": "S5_pool_critical.wav",
        "chunk_idx": 5,
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "İnsan VAR → ALARM + ESTOP + EMERGENCY",
        "location": "Primary clarifier pool, Ceyhan WWTP",
        "operation": "Saturday construction work on new press building. Heavy machinery operating adjacent to clarifier pool. Worker observed climbing pool wall at approximately 09:52. Clarifier bridge scraper in automatic operation. No safety observer assigned to pool perimeter.",
        "protocol": (
            "RESTRICTED ZONE. Pool edge access prohibited during construction operations. "
            "Clarifier pool: low buoyancy water — standard swimming survival times do not apply. "
            "IMMEDIATE RESPONSE REQUIRED if any person enters pool. "
            "E-STOP: clarifier bridge, initiate rescue protocol, call emergency services. "
            "CRITICAL: Missing a real human distress signal is catastrophically worse than a false alarm. "
            "If you detect ANY sound that COULD be human distress — alarm IMMEDIATELY. "
            "For pool locations: any large water splash followed by voice MUST trigger ESTOP_POOL_BRIDGE. "
            "Detection within 15 seconds = certain survival. Within 30 seconds = probable survival. "
            "Beyond 30 seconds = unlikely survival."
        ),
    },
]


# ═══════════════════════════════════════════════════════════════
# WAV OKUMA VE CHUNK ÇIKARMA
# ═══════════════════════════════════════════════════════════════

def read_wav(path):
    with open(path, 'rb') as f:
        riff = f.read(4)
        if riff != b'RIFF':
            raise ValueError("WAV dosyası değil")
        f.read(4)
        wave = f.read(4)
        if wave != b'WAVE':
            raise ValueError("WAVE formatı değil")
        sr, num_channels, bits_per_sample, data_bytes = 16000, 1, 16, b''
        while True:
            chunk_id = f.read(4)
            if len(chunk_id) < 4: break
            chunk_size_data = f.read(4)
            if len(chunk_size_data) < 4: break
            chunk_sz = struct.unpack('<I', chunk_size_data)[0]
            if chunk_id == b'fmt ':
                fmt_data = f.read(chunk_sz)
                num_channels = struct.unpack('<H', fmt_data[2:4])[0]
                sr = struct.unpack('<I', fmt_data[4:8])[0]
                bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0]
            elif chunk_id == b'data':
                data_bytes = f.read(chunk_sz)
            else:
                f.read(chunk_sz)
    return sr, data_bytes, num_channels, bits_per_sample


def extract_chunk_as_wav(path, chunk_idx, chunk_sec=5):
    sr, data_bytes, num_channels, bits_per_sample = read_wav(path)
    bytes_per_sample = bits_per_sample // 8
    bytes_per_frame = bytes_per_sample * num_channels
    chunk_frames = chunk_sec * sr
    chunk_bytes = chunk_frames * bytes_per_frame
    start = chunk_idx * chunk_bytes
    chunk = data_bytes[start:start + chunk_bytes]
    if len(chunk) < chunk_bytes:
        chunk = chunk + b'\x00' * (chunk_bytes - len(chunk))
    if num_channels == 2:
        mono = bytearray()
        for i in range(0, len(chunk), bytes_per_frame):
            mono.extend(chunk[i:i + bytes_per_sample])
        chunk = bytes(mono)
    buf = io.BytesIO()
    byte_rate = sr * 1 * bits_per_sample // 8
    block_align = 1 * bits_per_sample // 8
    data_size = len(chunk)
    buf.write(b'RIFF')
    buf.write(struct.pack('<I', 36 + data_size))
    buf.write(b'WAVE')
    buf.write(b'fmt ')
    buf.write(struct.pack('<I', 16))
    buf.write(struct.pack('<H', 1))
    buf.write(struct.pack('<H', 1))
    buf.write(struct.pack('<I', sr))
    buf.write(struct.pack('<I', byte_rate))
    buf.write(struct.pack('<H', block_align))
    buf.write(struct.pack('<H', bits_per_sample))
    buf.write(b'data')
    buf.write(struct.pack('<I', data_size))
    buf.write(chunk)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


# ═══════════════════════════════════════════════════════════════
# PROTOCOL MODU PROMPT OLUŞTURUCU
# ═══════════════════════════════════════════════════════════════

def build_protocol_prompt(scene):
    """
    PROTOCOL modu: Modele lokasyon + operasyon + TAM güvenlik protokolü veriliyor.
    Protokol açıkça söylüyor: "Şüphede alarm ver, yanlış alarm insanı kaçırmaktan iyidir."
    """
    return (
        f"You are an AI acoustic safety monitoring system integrated into SCADA "
        f"at Ceyhan Wastewater Treatment Plant (WWTP), Adana, Turkey.\n"
        f"You monitor microphone feeds from critical facility locations in real time.\n\n"
        f"Current monitoring context:\n"
        f"  Location : {scene['location']}\n"
        f"  Operation: {scene['operation']}\n"
        f"  Time     : Saturday morning — weekend shift, reduced personnel\n\n"
        f"SAFETY PROTOCOL:\n"
        f"{scene['protocol']}\n\n"
        f"CRITICAL RULES:\n"
        f"1. Missing a real human distress signal is catastrophically worse than a false alarm.\n"
        f"2. If you detect any sound that COULD be human distress — alarm immediately.\n"
        f"3. For pool locations: any large water splash followed by voice MUST trigger ESTOP_POOL_BRIDGE.\n"
        f"4. For confined spaces: any muffled voice pattern MUST trigger INITIATE_CONFINED_SPACE_RESCUE.\n"
        f"5. Detection within 15 seconds of distress onset = certain survival. Within 30 seconds = probable survival.\n\n"
        f"Listen to this 5-second audio clip carefully.\n"
        f"Respond ONLY with a JSON object, no other text:\n"
        f'{{"human_detected": true/false, "confidence": 0.0-1.0, '
        f'"distress_type": "none/shouting_help/screaming/muffled_call/unknown", '
        f'"alarm": true/false, '
        f'"action": "CONTINUE_MONITORING/NOTIFY_OPERATOR/ESTOP_POOL_BRIDGE/INITIATE_CONFINED_SPACE_RESCUE/CALL_EMERGENCY", '
        f'"notify": [], '
        f'"reasoning": "brief explanation max 2 sentences"}}'
    )


# ═══════════════════════════════════════════════════════════════
# OLLAMA API ÇAĞRISI
# ═══════════════════════════════════════════════════════════════

def call_gemma4(audio_b64, prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt, "images": [audio_b64]}],
        "stream": False,
        "options": {"temperature": 0.1}
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - t0
            if "message" in result and "content" in result["message"]:
                return result["message"]["content"], elapsed, "ok"
            return str(result), elapsed, "unexpected_format"
    except urllib.error.URLError as e:
        return None, time.time() - t0, f"connection_error: {e}"
    except Exception as e:
        return None, time.time() - t0, f"error: {e}"


# ═══════════════════════════════════════════════════════════════
# DEĞERLENDİRME
# ═══════════════════════════════════════════════════════════════

def evaluate(scene, response):
    if not response:
        return "HATA", "Cevap alınamadı"

    r = response.lower()
    human_present = scene["human_present"]

    has_true = '"human_detected": true' in r or '"human_detected":true' in r
    has_false = '"human_detected": false' in r or '"human_detected":false' in r

    if human_present:
        if has_true:
            return "✅ GEÇTİ", "İnsanı tespit etti"
        else:
            return "❌ KAÇIRDI", "False Negative — insanı duyamadı"
    else:
        if has_false:
            return "✅ GEÇTİ", "Doğru: insan yok dedi"
        else:
            return "❌ YANLIŞ ALARM", "False Positive — yanlış alarm verdi"


# ═══════════════════════════════════════════════════════════════
# ANA TEST DÖNGÜSÜ
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 65}")
    print(f"  WWTP Acoustic Safety — PROTOCOL MODU TESTİ")
    print(f"  Tüm 5 sahne, tam güvenlik protokolü ile")
    print(f"{'═' * 65}")
    print(f"  Bu en yüksek bağlam seviyesi.")
    print(f"  Model artık güvenlik kurallarını da biliyor:")
    print(f"  'Şüphede alarm ver. Yanlış alarm > insanı kaçırmak'")
    print(f"{'═' * 65}\n")

    results = []

    for scene in SCENES:
        sid = scene["scene_id"]
        print(f"{'─' * 65}")
        print(f"  {sid} — {scene['title']}")
        print(f"  Chunk: {scene['chunk_time']} | İnsan: {'EVET' if scene['human_present'] else 'HAYIR'}")
        print(f"  Beklenen: {scene['expected']}")
        print(f"{'─' * 65}")

        audio_path = os.path.join(AUDIO_DIR, scene["file"])
        if not os.path.exists(audio_path):
            print(f"  [HATA] Dosya bulunamadı: {audio_path}\n")
            results.append({"scene": sid, "result": "HATA", "detail": "Dosya yok"})
            continue

        audio_b64 = extract_chunk_as_wav(audio_path, scene["chunk_idx"], CHUNK_SEC)

        prompt = build_protocol_prompt(scene)
        print(f"  Gemma 4 E4B'ye gönderiliyor (PROTOCOL mod)...")
        response, elapsed, status = call_gemma4(audio_b64, prompt)

        print(f"  Süre: {elapsed:.1f}s | Durum: {status}")
        if response:
            display = response[:300].replace('\n', ' ')
            print(f"  Cevap: {display}")

        verdict, detail = evaluate(scene, response)
        print(f"  → {verdict} — {detail}")
        print()

        results.append({
            "scene": sid,
            "result": verdict,
            "detail": detail,
            "elapsed": elapsed,
            "response": response
        })

    # ═══════════════════════════════════════════════════════════
    # ÖZET TABLO
    # ═══════════════════════════════════════════════════════════

    print(f"\n{'═' * 65}")
    print(f"  PROTOCOL MODU — ÖZET SONUÇLAR")
    print(f"{'═' * 65}")
    print(f"  {'Sahne':<8} {'İnsan':<8} {'Sonuç':<20} {'Detay'}")
    print(f"  {'─' * 58}")

    for r in results:
        scene_data = next(s for s in SCENES if s["scene_id"] == r["scene"])
        human = "EVET" if scene_data["human_present"] else "HAYIR"
        print(f"  {r['scene']:<8} {human:<8} {r['result']:<20} {r['detail']}")

    # 3 mod karşılaştırması
    print(f"\n{'─' * 65}")
    print(f"  BARE → CONTEXT → PROTOCOL KARŞILAŞTIRMASI")
    print(f"{'─' * 65}")
    print(f"  BARE modda    : S1 ✅, S2 ❌, S3 ✅, S4 ❌, S5 ❌")
    print(f"  CONTEXT modda : (yarın test edilecek)")
    print(f"  PROTOCOL modda: sonuçlar yukarıda")

    passed_critical = sum(
        1 for r in results
        if r["scene"] in ["S2", "S4", "S5"] and "GEÇTİ" in r["result"]
    )
    total_passed = sum(1 for r in results if "GEÇTİ" in r["result"])

    print(f"\n  Toplam başarı     : {total_passed}/5")
    print(f"  Kritik sahne başarı: {passed_critical}/3")

    if passed_critical == 3:
        print(f"\n  🎉 PROTOCOL mod TÜM kritik sahneleri kurtardı!")
        print(f"  Güvenlik protokolü AI'ın hayat kurtarmasını sağlıyor.")
    elif passed_critical > 0:
        print(f"\n  👍 PROTOCOL mod bazı sahneleri kurtardı.")
    else:
        print(f"\n  ⚠️  PROTOCOL mod da yetmedi. Prompt optimizasyonu gerekebilir.")

    # ═══════════════════════════════════════════════════════════
    # S5 — BÜYÜK SORU
    # ═══════════════════════════════════════════════════════════

    s5_result = next((r for r in results if r["scene"] == "S5"), None)
    if s5_result:
        print(f"\n{'═' * 65}")
        print(f"  ★ S5 — BÜYÜK SORU: HAYATTA KALIR MIYDI? ★")
        print(f"{'═' * 65}")
        if "GEÇTİ" in s5_result["result"]:
            print(f"  Model tespit yaptı. Tespit zamanı: 25-30 saniye.")
            print(f"  Düşme anı: 20. saniye. Gecikme: ~5-10 saniye.")
            print(f"")
            print(f"  ★★★ HAYATTA KALMA VERDİKTİ: PROBABLE SURVIVAL ★★★")
            print(f"")
            print(f"  İyi yüzücü (30sn eşiği): KURTULUR ✅")
            print(f"  Zayıf yüzücü (15sn eşiği): BELİRSİZ ⚠️")
            print(f"")
            print(f"  O gün orada güvenlik protokolü ile çalışan bir")
            print(f"  Gemma 4 sistemi olsaydı, adam büyük ihtimalle")
            print(f"  HAYATTA KALIRDI.")
        else:
            print(f"  ★ WOULD NOT HAVE SURVIVED ★")
            print(f"  Güvenlik protokolü bile yetmedi.")
            print(f"  Model, 95dB gürültü altındaki çığlığı duyamadı.")
            print(f"")
            print(f"  Bu önemli bir bulgu: Mevcut edge AI modelleri,")
            print(f"  aşırı gürültülü endüstriyel ortamlarda henüz")
            print(f"  hayat kurtaracak seviyede değil.")
            print(f"  Ancak bu, bu tür sistemlerin geliştirilmesinin")
            print(f"  ne kadar acil olduğunu gösteriyor.")

    print(f"\n{'═' * 65}")
    print(f"  'Would he have survived if an LLM had been monitoring?'")
    print(f"{'═' * 65}\n")


if __name__ == "__main__":
    main()
