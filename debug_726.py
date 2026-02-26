from core.engine import VaxEngine

engine = VaxEngine()
records = engine.get_records("7/26")
with open("debug_utf8.txt", "w", encoding="utf-8") as f:
    for r in records:
        f.write(f"{r}\n")
