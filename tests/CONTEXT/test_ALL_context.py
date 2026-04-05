"""
TEST — CONTEXT MODU (Tüm Sahneler)
====================================
BARE moddan farkı: Modele lokasyon ve operasyon bağlamı veriliyor.
"Sen Ceyhan Arıtma Tesisi'ndeki X lokasyonunu dinliyorsun,
 şu anda Y operasyonu devam ediyor."

BARE modda model 3 sahneyi kaçırdı (S2, S4, S5).
CONTEXT mod bu sonucu değiştirir mi?

Kullanım:
  python tests/test_ALL_context.py

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
# SAHNE TANIMLARI — Her sahne için dosya, chunk ve bağlam bilgisi
# ═══════════════════════════════════════════════════════════════

SCENES = [
    {
        "scene_id": "S1",
        "title": "Pompa Dairesi — Normal Operasyon",
        "file": "S1_pump_room_normal.wav",
        "chunk_idx": 0,       # 0-5 saniye
        "chunk_time": "0-5 sn",
        "human_present": False,
        "expected": "İnsan YOK → alarm YOK",
        # CONTEXT modu bağlam bilgisi (scene_config.json'dan)
        "location": "Pump station, basement level, Ceyhan WWTP",
        "operation": "Routine wastewater pumping. Duty pump 1 and 2 running at 85% capacity. Saturday morning shift.",
    },
    {
        "scene_id": "S2",
        "title": "İnşaat Alanı — İnsan Bağırıyor",
        "file": "S2_construction_human.wav",
        "chunk_idx": 5,       # 25-30 saniye — bağırma başlıyor
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "İnsan VAR → alarm VER",
        "location": "Construction site adjacent to aeration tanks, Ceyhan WWTP",
        "operation": "Weekend construction work on new sludge press building. 12-person crew on site. High noise environment. Saturday 10:00.",
    },
    {
        "scene_id": "S3",
        "title": "Havuz Kenarı — Yanlış Alarm Testi",
        "file": "S3_pool_false_alarm.wav",
        "chunk_idx": 3,       # 15-20 saniye — metalik sesler
        "chunk_time": "15-20 sn",
        "human_present": False,
        "expected": "İnsan YOK → alarm YOK",
        "location": "Secondary clarifier pool edge, Ceyhan WWTP",
        "operation": "Secondary clarifier sludge scraper bridge running normal cycle. Automatic operation. No personnel in restricted zone.",
    },
    {
        "scene_id": "S4",
        "title": "Menhol Galeri — Maskeli İşçi",
        "file": "S4_manhole_masked.wav",
        "chunk_idx": 5,       # 25-30 saniye — maskeli ses
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "İnsan VAR → alarm VER",
        "location": "Underground sewer gallery, manhole access point MH-07, Ceyhan WWTP",
        "operation": "Confined space entry permit issued for gallery inspection. Single worker with respirator. Entry logged at 09:45. Buddy system in place — surface attendant monitoring.",
    },
    {
        "scene_id": "S5",
        "title": "Durultma Havuzu — GERÇEK KAZA SAHNESİ",
        "file": "S5_pool_critical.wav",
        "chunk_idx": 5,       # 25-30 saniye — çığlık başlıyor
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "İnsan VAR → ALARM + ESTOP",
        "location": "Primary clarifier pool, Ceyhan WWTP",
        "operation": "Saturday construction work on new press building. Heavy machinery operating adjacent to clarifier pool. Worker observed climbing pool wall at approximately 09:52. Clarifier bridge scraper in automatic operation. No safety observer assigned to pool perimeter.",
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
# CONTEXT MODU PROMPT OLUŞTURUCU
# ═══════════════════════════════════════════════════════════════

def build_context_prompt(scene):
    """
    CONTEXT modu: Modele lokasyon ve operasyon bilgisi veriliyor.
    BARE moddan farkı tam olarak bu — model nerede olduğunu biliyor.
    """
    return (
        f"You are an AI acoustic safety monitoring system integrated into SCADA "
        f"at Ceyhan Wastewater Treatment Plant (WWTP), Adana, Turkey.\n"
        f"You monitor microphone feeds from critical facility locations in real time.\n\n"
        f"Current monitoring context:\n"
        f"  Location : {scene['location']}\n"
        f"  Operation: {scene['operation']}\n"
        f"  Time     : Saturday morning — weekend shift, reduced personnel\n\n"
        f"Listen to this 5-second audio clip carefully.\n"
        f"What do you hear? Is there any human voice or human distress?\n\n"
        f"Respond ONLY with a JSON object, no other text:\n"
        f'{{"human_detected": true/false, "confidence": 0.0-1.0, '
        f'"distress_type": "none/shouting_help/screaming/muffled_call/unknown", '
        f'"alarm": true/false, '
        f'"action": "CONTINUE_MONITORING/NOTIFY_OPERATOR/ESTOP_POOL_BRIDGE/INITIATE_CONFINED_SPACE_RESCUE/CALL_EMERGENCY", '
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
    """Modelin cevabını değerlendir: doğru mu yanlış mı?"""
    if not response:
        return "HATA", "Cevap alınamadı"

    r = response.lower()
    human_present = scene["human_present"]

    # human_detected alanını bul
    has_true = '"human_detected": true' in r or '"human_detected":true' in r
    has_false = '"human_detected": false' in r or '"human_detected":false' in r

    if human_present:
        # İnsan var — model tespit etmeli
        if has_true:
            return "✅ GEÇTİ", "İnsanı tespit etti"
        else:
            return "❌ KAÇIRDI", "False Negative — insanı duyamadı"
    else:
        # İnsan yok — model alarm vermemeli
        if has_false:
            return "✅ GEÇTİ", "Doğru: insan yok dedi"
        else:
            return "❌ YANLIŞ ALARM", "False Positive — yanlış alarm verdi"


# ═══════════════════════════════════════════════════════════════
# ANA TEST DÖNGÜSÜ
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 65}")
    print(f"  WWTP Acoustic Safety — CONTEXT MODU TESTİ")
    print(f"  Tüm 5 sahne, lokasyon ve operasyon bağlamı ile")
    print(f"{'═' * 65}")
    print(f"  BARE moddan farkı: Model artık NEREDE olduğunu")
    print(f"  ve NE OLDUĞUNU biliyor. Bu fark yeter mi?")
    print(f"{'═' * 65}\n")

    results = []

    for scene in SCENES:
        sid = scene["scene_id"]
        print(f"{'─' * 65}")
        print(f"  {sid} — {scene['title']}")
        print(f"  Chunk: {scene['chunk_time']} | İnsan: {'EVET' if scene['human_present'] else 'HAYIR'}")
        print(f"  Beklenen: {scene['expected']}")
        print(f"{'─' * 65}")

        # Ses dosyası kontrolü
        audio_path = os.path.join(AUDIO_DIR, scene["file"])
        if not os.path.exists(audio_path):
            print(f"  [HATA] Dosya bulunamadı: {audio_path}\n")
            results.append({"scene": sid, "result": "HATA", "detail": "Dosya yok"})
            continue

        # Chunk çıkar
        audio_b64 = extract_chunk_as_wav(audio_path, scene["chunk_idx"], CHUNK_SEC)

        # CONTEXT prompt oluştur ve gönder
        prompt = build_context_prompt(scene)
        print(f"  Gemma 4 E4B'ye gönderiliyor (CONTEXT mod)...")
        response, elapsed, status = call_gemma4(audio_b64, prompt)

        # Sonucu göster
        print(f"  Süre: {elapsed:.1f}s | Durum: {status}")
        if response:
            # Kısa gösterim — ilk 200 karakter
            display = response[:300].replace('\n', ' ')
            print(f"  Cevap: {display}")

        # Değerlendir
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
    print(f"  CONTEXT MODU — ÖZET SONUÇLAR")
    print(f"{'═' * 65}")
    print(f"  {'Sahne':<8} {'İnsan':<8} {'Sonuç':<20} {'Detay'}")
    print(f"  {'─' * 58}")

    for r in results:
        scene_data = next(s for s in SCENES if s["scene_id"] == r["scene"])
        human = "EVET" if scene_data["human_present"] else "HAYIR"
        print(f"  {r['scene']:<8} {human:<8} {r['result']:<20} {r['detail']}")

    # BARE ile karşılaştırma
    print(f"\n{'─' * 65}")
    print(f"  BARE → CONTEXT KARŞILAŞTIRMASI")
    print(f"{'─' * 65}")
    print(f"  BARE modda S2, S4, S5 kaçırılmıştı.")
    print(f"  CONTEXT mod bu sahneleri kurtardı mı?")

    passed_critical = sum(
        1 for r in results
        if r["scene"] in ["S2", "S4", "S5"] and "GEÇTİ" in r["result"]
    )
    print(f"  Kritik sahnelerde başarı: {passed_critical}/3")

    if passed_critical == 3:
        print(f"  🎉 CONTEXT mod TÜM kritik sahneleri kurtardı!")
    elif passed_critical > 0:
        print(f"  👍 CONTEXT mod bazı sahneleri kurtardı. PROTOCOL mod daha iyi olabilir.")
    else:
        print(f"  ⚠️  CONTEXT mod yetmedi. PROTOCOL mod ile deneyelim.")

    # S5 hayatta kalma verdikti
    s5_result = next((r for r in results if r["scene"] == "S5"), None)
    if s5_result:
        print(f"\n{'─' * 65}")
        print(f"  S5 HAYATTA KALMA VERDİKTİ (CONTEXT)")
        print(f"{'─' * 65}")
        if "GEÇTİ" in s5_result["result"]:
            print(f"  ★ PROBABLE SURVIVAL — Bağlam bilgisi ile tespit yapıldı!")
            print(f"  O gün bu sistem olsaydı, adam büyük ihtimalle HAYATTA KALIRDI.")
        else:
            print(f"  ★ WOULD NOT HAVE SURVIVED — Bağlam bilgisi yetmedi.")
            print(f"  PROTOCOL mod ile tekrar denenecek.")

    print(f"\n{'═' * 65}\n")


if __name__ == "__main__":
    main()
