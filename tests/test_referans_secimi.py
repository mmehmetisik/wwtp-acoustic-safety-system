"""
Few-shot referans seçimi için davranış testleri.

Neden var: Nisan 2026 ölçümünde referanslar puanlanan sahnelerin içinden geliyordu.
S4'ün 25–30 sn chunk'ı hem "insan" referansıydı hem de S4'te puanlanıyordu; model
referans olarak gördüğü görüntüyü puanlanırken yeniden gördü. Bu testler kırılırsa
ölçüm yeniden sızıntılı olur ve skor şişer.

Çalıştırma (depo kökünden):
    python -m unittest discover -s tests -p "test_*.py" -v
"""

import json
import os
import sys
import unittest

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

import acoustic_engine as motor  # noqa: E402


def sahneleri_yukle():
    with open(os.path.join(KOK, "dataset", "scene_config.json"), encoding="utf-8") as f:
        return json.load(f)["scenes"]


def insan_sesi_araliklari(sahne):
    """Sahne tanımındaki insan sesi aralıkları (saniye): [(başlangıç, bitiş), ...]."""
    araliklar = []
    for aralik, bilesim in sahne.get("audio_composition", {}).items():
        if bilesim.get("human_voice", False):
            bas, son = (int(x) for x in aralik.split("_"))
            araliklar.append((bas, son))
    return araliklar


def pencere_insan_sesi_iceriyor(sahne, chunk_idx):
    bas = chunk_idx * motor.CHUNK_SIZE_SEC
    son = bas + motor.CHUNK_SIZE_SEC
    return any(bas < a_son and son > a_bas for a_bas, a_son in insan_sesi_araliklari(sahne))


class ReferansSecimiTest(unittest.TestCase):
    def setUp(self):
        self.sahneler = sahneleri_yukle()
        self.dosyaya_gore = {s["file"]: s for s in self.sahneler}

    def test_degerlendirilen_sahnenin_dosyasindan_referans_alinmaz(self):
        # Kırılırsa: model referans olarak gördüğü chunk'ı puanlanırken yeniden görür; skor şişer.
        for sahne in self.sahneler:
            with self.subTest(sahne=sahne["scene_id"]):
                secim = motor.referanslari_sec(haric_dosya=sahne["file"])
                kullanilan = {dosya for _, dosya, _, _ in secim}
                self.assertNotIn(sahne["file"], kullanilan)

    def test_her_sahnede_uc_temiz_bir_insan_referansi_secilir(self):
        # Kırılırsa: istem 3 temiz + 1 insan örneği beklediği için model eksik örnekle karar verir.
        for sahne in self.sahneler:
            with self.subTest(sahne=sahne["scene_id"]):
                roller = [rol for rol, _, _, _ in motor.referanslari_sec(haric_dosya=sahne["file"])]
                self.assertEqual(roller, ["temiz", "temiz", "temiz", "insan"])

    def test_insan_referansinda_insan_sesi_vardir(self):
        # Kırılırsa: "insan" diye gösterilen örnekte insan sesi yoktur; model yanlış deseni öğrenir.
        for sahne in self.sahneler:
            with self.subTest(sahne=sahne["scene_id"]):
                rol, dosya, chunk_idx, _ = motor.referanslari_sec(haric_dosya=sahne["file"])[3]
                self.assertEqual(rol, "insan")
                self.assertTrue(pencere_insan_sesi_iceriyor(self.dosyaya_gore[dosya], chunk_idx))

    def test_temiz_referanslarda_insan_sesi_yoktur(self):
        # Kırılırsa: "temiz" örnekte insan sesi olur; model insan sesini gürültü sanmayı öğrenir.
        for sahne in self.sahneler:
            for rol, dosya, chunk_idx, _ in motor.referanslari_sec(haric_dosya=sahne["file"])[:3]:
                with self.subTest(sahne=sahne["scene_id"], referans=f"{dosya}#{chunk_idx}"):
                    self.assertEqual(rol, "temiz")
                    self.assertFalse(pencere_insan_sesi_iceriyor(self.dosyaya_gore[dosya], chunk_idx))

    def test_haric_verilmezse_eski_set_aynen_doner(self):
        # Kırılırsa: Nisan 2026 ölçümü (91.0) yeniden üretilemez; eski ve yeni skor kıyaslanamaz.
        secim = [(dosya, chunk_idx) for _, dosya, chunk_idx, _ in motor.referanslari_sec()]
        self.assertEqual(secim, [
            ("S1_pump_room_normal.wav", 3),
            ("S2_construction_human.wav", 0),
            ("S3_pool_false_alarm.wav", 0),
            ("S4_manhole_masked.wav", 5),
        ])

    def test_eski_set_sizintiyi_gercekten_iceriyor(self):
        # Kırılırsa: eski set sızıntısızmış gibi görünür ve yukarıdaki testler bir şey ölçmez.
        eski = {dosya for _, dosya, _, _ in motor.referanslari_sec()}
        sizintili = [s["scene_id"] for s in self.sahneler if s["file"] in eski]
        self.assertEqual(sizintili, ["S1", "S2", "S3", "S4"])


if __name__ == "__main__":
    unittest.main()
