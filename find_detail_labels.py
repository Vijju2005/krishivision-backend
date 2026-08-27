with open(r"c:\Users\keert\Downloads\Krishi222-fixed\krishivision_ai\lib\features\analysis\screens\crop_detail_screen.dart", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for idx, line in enumerate(lines):
        if "Text(" in line:
            if any(k in line.lower() for k in ["area", "production", "yield", "health", "satellite"]):
                print(f"L{idx+1}: {line.strip()}")
