These are the original formant-synthesized audio files (deprecated).

The model hallucinated heavily with these files — formant synthesis did not match
the model's ASR training data. Replaced with TTS-based audio (Google TTS) in the
dataset/audio/ directory. The new TTS audio files produce significantly better results.

See findings/04_tts_prompt_optimization.md for details on the transition.
