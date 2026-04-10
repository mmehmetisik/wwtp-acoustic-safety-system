"""
TEST — BARE MODE (All Scenes)
=================================
En düşük bağlam seviyesi. Modele sadece ses gönderiliyor.
Lokasyon yok, operasyon bilgisi yok, güvenlik protokolü yok.
"Take this and listen, what do you hear?"

This mode simulates the real-world situation:
Like the human ear — decide only by listening, with no context.

Kullanım:
  python tests/test_ALL_bare.py

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
# SAHNE TANIMLARI
# ═══════════════════════════════════════════════════════════════

SCENES = [
    {
        "scene_id": "S1",
        "title": "Pompa Dairesi — Normal Operasyon",
        "file": "S1_pump_room_normal.wav",
        "chunk_idx": 0,       # 0-5 saniye
        "chunk_time": "0-5 sn",
        "human_present": False,
        "expected": "No human → no alarm",
    },
    {
        "scene_id": "S2",
        "title": "Construction Zone — Human Shouting",
        "file": "S2_construction_human.wav",
        "chunk_idx": 5,       # 25-30 saniye — bağırma başlıyor
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "Human present → trigger alarm",
    },
    {
        "scene_id": "S3",
        "title": "Havuz Kenarı — Yanlış Alarm Testi",
        "file": "S3_pool_false_alarm.wav",
        "chunk_idx": 3,       # 15-20 saniye — metalik sesler
        "chunk_time": "15-20 sn",
        "human_present": False,
        "expected": "No human → no alarm",
    },
    {
        "scene_id": "S4",
        "title": "Menhol Galeri — Maskeli İşçi",
        "file": "S4_manhole_masked.wav",
        "chunk_idx": 5,       # 25-30 saniye — maskeli ses
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "Human present → trigger alarm",
    },
    {
        "scene_id": "S5",
        "title": "Durultma Havuzu — GERÇEK KAZA SAHNESİ",
        "file": "S5_pool_critical.wav",
        "chunk_idx": 5,       # 25-30 saniye — çığlık başlıyor
        "chunk_time": "25-30 sn",
        "human_present": True,
        "expected": "Human present → ALARM + ESTOP",
    },
]


# ═══════════════════════════════════════════════════════════════
# WAV OKUMA VE CHUNK ÇIKARMA
# ═══════════════════════════════════════════════════════════════

def read_wav(path):
    with open(path, 'rb') as f:
        riff = f.read(4)
        if riff != b'RIFF':
            raise ValueError("Not a WAV file")
        f.read(4)
        wave = f.read(4)
        if wave != b'WAVE':
            raise ValueError("Not WAVE format")
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
# BARE MODU PROMPT — No context, just listen and report
# ═══════════════════════════════════════════════════════════════

BARE_PROMPT = (
    "You are an industrial safety audio monitoring system. "
    "Listen to this audio clip carefully. "
    "What do you hear? Is there any human voice or human distress? "
    "Respond ONLY with a JSON object, no other text: "
    '{"human_detected": true/false, "confidence": 0.0-1.0, '
    '"distress_type": "none/shouting_help/screaming/muffled_call/unknown", '
    '"alarm": true/false, '
    '"action": "CONTINUE_MONITORING/NOTIFY_OPERATOR/ESTOP_POOL_BRIDGE/INITIATE_CONFINED_SPACE_RESCUE/CALL_EMERGENCY", '
    '"reasoning": "brief explanation max 2 sentences"}'
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
            return "✅ PASSED", "Human detected"
        else:
            return "❌ KAÇIRDI", "False Negative — insanı duyamadı"
    else:
        if has_false:
            return "✅ PASSED", "Doğru: insan yok dedi"
        else:
            return "❌ YANLIŞ ALARM", "False Positive — yanlış alarm verdi"


# ═══════════════════════════════════════════════════════════════
# ANA TEST DÖNGÜSÜ
# ═══════════════════════════════════════════════════════════════

def main():
    print(f"\n{'═' * 65}")
    print(f"  WWTP Acoustic Safety — BARE MODU TESTİ")
    print(f"  Tüm 5 sahne, hiçbir bağlam olmadan")
    print(f"{'═' * 65}")
    print(f"  Model hiçbir şey bilmiyor:")
    print(f"  Nerede olduğunu, ne yapıldığını, neye dikkat etmesi")
    print(f"  gerektiğini bilmeden sadece sesi dinliyor.")
    print(f"  Tıpkı o gün sahada kimsenin duyamadığı gibi.")
    print(f"{'═' * 65}\n")

    results = []

    for scene in SCENES:
        sid = scene["scene_id"]
        print(f"{'─' * 65}")
        print(f"  {sid} — {scene['title']}")
        print(f"  Chunk: {scene['chunk_time']} | Human: {'YES' if scene['human_present'] else 'NO'}")
        print(f"  Beklenen: {scene['expected']}")
        print(f"{'─' * 65}")

        audio_path = os.path.join(AUDIO_DIR, scene["file"])
        if not os.path.exists(audio_path):
            print(f"  [HATA] Dosya bulunamadı: {audio_path}\n")
            results.append({"scene": sid, "result": "HATA", "detail": "Dosya yok"})
            continue

        audio_b64 = extract_chunk_as_wav(audio_path, scene["chunk_idx"], CHUNK_SEC)

        print(f"  Gemma 4 E4B'ye gönderiliyor (BARE mod)...")
        response, elapsed, status = call_gemma4(audio_b64, BARE_PROMPT)

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
    print(f"  BARE MODU — ÖZET SONUÇLAR")
    print(f"{'═' * 65}")
    print(f"  {'Scene':<8} {'Human':<8} {'Result':<20} {'Detail'}")
    print(f"  {'─' * 58}")

    for r in results:
        scene_data = next(s for s in SCENES if s["scene_id"] == r["scene"])
        human = "YES" if scene_data["human_present"] else "NO"
        print(f"  {r['scene']:<8} {human:<8} {r['result']:<20} {r['detail']}")

    passed = sum(1 for r in results if "PASSED" in r["result"])
    critical = sum(
        1 for r in results
        if r["scene"] in ["S2", "S4", "S5"] and "PASSED" in r["result"]
    )
    print(f"\n  Toplam başarı      : {passed}/5")
    print(f"  Kritik sahne başarı: {critical}/3")

    # S5 verdikti
    s5 = next((r for r in results if r["scene"] == "S5"), None)
    if s5:
        print(f"\n{'─' * 65}")
        print(f"  S5 HAYATTA KALMA VERDİKTİ (BARE)")
        print(f"{'─' * 65}")
        if "PASSED" in s5["result"]:
            print(f"  ★ PROBABLE SURVIVAL — Bağlam olmadan bile tespit yaptı!")
        else:
            print(f"  ★ WOULD NOT HAVE SURVIVED — Bağlam olmadan duyamadı.")
            print(f"  CONTEXT ve PROTOCOL modlar sonucu değiştirebilir.")

    print(f"\n{'═' * 65}\n")


if __name__ == "__main__":
    main()
