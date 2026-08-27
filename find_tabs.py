with open(r"c:\Users\keert\Downloads\Krishi222-fixed\krishivision_ai\lib\features\analysis\screens\crop_detail_screen.dart", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for idx, line in enumerate(lines):
        if "TabBar(" in line or "Tab(" in line or "_tabController" in line:
            print(f"L{idx+1}: {line.strip()}")
