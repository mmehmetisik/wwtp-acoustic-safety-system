"""WWTP Acoustic Safety Benchmark v1.0 — Can AI Hear What Human Ears Miss?"""
import kaggle_benchmarks as kbench
import sys
import glob
import time
import os

# ── Find dataset and import engine ──
_cfg = glob.glob("/kaggle/input/**/scene_config.json", recursive=True)
DATA_DIR  = os.path.dirname(_cfg[0]) if _cfg else "/kaggle/input/wwtp-acoustic-safety-benchmark"
AUDIO_DIR = os.path.join(DATA_DIR, "audio")
sys.path.insert(0, DATA_DIR)

from acoustic_engine import (
    load_all_data, find_data_dir,
    run_scene, print_scene_result, print_final_summary,
    LINE1, LINE2,
)


@kbench.task(name='WWTP Acoustic Safety: Can AI Hear What Human Ears Miss?')
def wwtp_acoustic_v1(llm) -> float:
    """
    Industrial acoustic distress detection on a real WWTP.
    5 scenes × 3 modes = 15 evaluations.
    A worker fell into a clarifier pool during noisy construction.
    No one heard his calls. Would an LLM have saved him?
    Asymmetric scoring: FN=-40pts | FP=-10pts | S5 weight=40%.
    """

    _start = time.time()

    # ── Load data ──
    data_dir  = find_data_dir()
    audio_dir = os.path.join(data_dir, "audio")
    scene_config, answer_key, scoring_rubric, acoustic_profiles, site_map = load_all_data(data_dir)

    # ── Header ──
    print(f"\n{'═' * 65}")
    print(f"  WWTP ACOUSTIC SAFETY BENCHMARK v1.0")
    print(f"  Can AI Hear What Human Ears Miss?")
    print(f"{'═' * 65}")
    print(f"  Plant   : Ceyhan WWTP, Adana, Turkey (34,896 m3/day)")
    print(f"  Scenes  : 5 | Modes: 3 | Chunks/scene: 12 × 5s")
    print(f"  Scoring : Asymmetric — FN: -40pts | FP: -10pts")
    print(f"  S5 Weight: 40% of total (real incident scene)")
    print(f"  Survival: ≤15s=Certain | ≤30s=Probable | >30s=Unlikely")
    print(f"{'═' * 65}")
    print(f"\n  THE QUESTION:")
    print(f"  A worker fell into a clarifier pool on a Saturday morning.")
    print(f"  Construction noise masked his calls for help.")
    print(f"  Would he have survived if an LLM had been monitoring?")
    print(f"\n{'═' * 65}")

    # ── Initialize LLM ──
    llm.prompt("WWTP Acoustic Safety Benchmark v1.0 starting. Respond OK.")

    # ── Definitions ──
    scenes  = scene_config["scenes"]
    modes   = ["BARE", "CONTEXT", "PROTOCOL"]
    weights = {"S1": 0.10, "S2": 0.20, "S3": 0.10, "S4": 0.20, "S5": 0.40}

    all_scores = []
    run_count  = 0
    total_runs = len(scenes) * len(modes)

    # ── Main loop ──
    for mode in modes:
        print(f"\n{'█' * 65}")
        print(f"  MODE: {mode}")
        if mode == "BARE":
            print(f"  Audio only. No context. Hardest mode.")
        elif mode == "CONTEXT":
            print(f"  Audio + location and operational context.")
        elif mode == "PROTOCOL":
            print(f"  Audio + context + full safety protocol document.")
        print(f"{'█' * 65}")

        for scene in scenes:
            scene_id   = scene["scene_id"]
            run_count += 1

            print(f"\n{'═' * 65}")
            print(f"  RUN {run_count}/{total_runs}: {mode} | {scene_id} | {scene['title']}")
            print(f"{'═' * 65}")

            _run_start   = time.time()
            ak_scene     = answer_key["scenes"].get(scene_id, {})

            scores, chunk_results = run_scene(
                llm              = llm,
                scene_cfg        = scene,
                answer_key_scene = ak_scene,
                audio_dir        = audio_dir,
                mode             = mode,
            )

            _run_time = time.time() - _run_start
            print_scene_result(scene_id, mode, scores)
            print(f"\n  Run time: {_run_time:.1f}s ({_run_time / 60:.1f} min)")

            entry = {
                "scene_id":            scene_id,
                "mode":                mode,
                "title":               scene["title"],
                "human_present":       scene.get("human_present", False),
                "total_raw":           scores["total_raw"],
                "detection_accuracy":  scores["detection_accuracy"],
                "time_to_detection":   scores["time_to_detection"],
                "false_alarm_control": scores["false_alarm_control"],
                "action_quality":      scores["action_quality"],
                "first_alarm_sec":     scores.get("first_alarm_sec"),
                "first_alarm_chunk":   scores.get("first_alarm_chunk"),
                "false_alarms":        scores.get("false_alarms", 0),
            }
            if "survival_verdict" in scores:
                entry["survival_verdict"] = scores["survival_verdict"]
                entry["survival_color"]   = scores["survival_color"]
                entry["survival_reason"]  = scores["survival_reason"]

            all_scores.append(entry)

    # ══════════════════════════════════════════════════════════════
    # FINAL RESULTS
    # ══════════════════════════════════════════════════════════════

    _total_time = time.time() - _start
    grand_avg   = print_final_summary(all_scores)

    # ── Mode progression ──
    print(f"\n  BARE → CONTEXT → PROTOCOL PROGRESSION:")
    print(f"  {'─' * 45}")
    mode_avgs = {}
    for mode in modes:
        m_entries = [e for e in all_scores if e["mode"] == mode]
        if m_entries:
            weighted = sum(e["total_raw"] * weights.get(e["scene_id"], 0) for e in m_entries)
            mode_avgs[mode] = weighted
            print(f"  {mode:<12}: {weighted:6.1f}/100")

    if "BARE" in mode_avgs and "PROTOCOL" in mode_avgs:
        gap = mode_avgs["PROTOCOL"] - mode_avgs["BARE"]
        print(f"\n  Context lift (BARE → PROTOCOL): {gap:+.1f} pts")
        if gap > 20:
            print(f"  → Safety protocols dramatically improve AI detection")
        elif gap > 10:
            print(f"  → Safety protocols provide meaningful improvement")
        elif gap > 0:
            print(f"  → Safety protocols help marginally")
        else:
            print(f"  → Safety protocols did not improve detection")

    # ── Scene difficulty ──
    print(f"\n  SCENE DIFFICULTY (lower = harder for AI):")
    print(f"  {'─' * 45}")
    scene_avgs = {}
    for sid in ["S1", "S2", "S3", "S4", "S5"]:
        s_entries = [e for e in all_scores if e["scene_id"] == sid]
        if s_entries:
            scene_avgs[sid] = sum(e["total_raw"] for e in s_entries) / len(s_entries)

    for sid, avg in sorted(scene_avgs.items(), key=lambda x: x[1]):
        bar   = "█" * int(avg / 5)
        grade = ("FAIL" if avg < 25 else "WEAK" if avg < 50 else
                 "PASS" if avg < 70 else "GOOD" if avg < 85 else "EXCEL")
        print(f"  {sid}: {avg:5.1f}/100  {bar}  [{grade}]")

    # ── Aggregate metrics ──
    total_fa  = sum(e.get("false_alarms", 0) for e in all_scores)
    detections = [e for e in all_scores
                  if e.get("first_alarm_sec") is not None and e.get("human_present", False)]
    avg_det   = (sum(e["first_alarm_sec"] for e in detections) / len(detections)
                 if detections else None)

    print(f"\n  AGGREGATE METRICS:")
    print(f"  Total runs         : {run_count}")
    print(f"  Total false alarms : {total_fa}")
    if avg_det:
        print(f"  Avg detection time : {avg_det:.1f}s (distress scenes only)")

    # ── THE ANSWER ──
    print(f"\n{'═' * 65}")
    print(f"  THE ANSWER: Would he have survived?")
    print(f"{'═' * 65}")
    for entry in all_scores:
        if entry["scene_id"] == "S5":
            det     = entry.get("first_alarm_sec")
            verdict = entry.get("survival_verdict", "N/A")
            det_str = f"{det}s" if det is not None else "NO DETECTION"
            print(f"  {entry['mode']:<12} → {det_str:>12}  →  {verdict}")

    print(f"\n  Clarifier pool: low buoyancy (flocculation chemistry).")
    print(f"  Strong swimmer: 30s. Weak swimmer: 15s.")

    # ── Grand average ──
    print(f"\n{'═' * 65}")
    print(f"  GRAND WEIGHTED AVERAGE : {grand_avg:.1f}/100")
    print(f"  Runs completed         : {run_count}/{total_runs}")
    print(f"  Total time             : {_total_time:.0f}s ({_total_time / 60:.1f} min)")
    print(f"{'═' * 65}\n")

    return round(grand_avg, 1)


# ── Execute ──
wwtp_acoustic_v1.run(llm=kbench.llm)
