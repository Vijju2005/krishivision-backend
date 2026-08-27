with open(r"c:\Users\keert\Downloads\Krishi222-fixed\krishivision_ai\backend\app\routers\dashboard_map.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
    for idx, line in enumerate(lines):
        if "@router.get(" in line:
            print(f"L{idx+1}: {line.strip()}")
