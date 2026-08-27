with open(r"c:\Users\keert\Downloads\Krishi222-fixed\krishivision_ai\lib\features\map\screens\map_screen.dart", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for idx, line in enumerate(lines):
        if "void" in line or "Future<" in line:
            if "district" in line.lower() or "select" in line.lower() or "load" in line.lower():
                print(f"L{idx+1}: {line.strip()}")
