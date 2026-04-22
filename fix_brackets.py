import glob
import os

for fp in glob.glob("*.html"):
    try:
        content = open(fp, "r", encoding="utf-8").read()
        if "{{" in content or "}}" in content:
            content = content.replace("{{", "{").replace("}}", "}")
            open(fp, "w", encoding="utf-8").write(content)
            print(f"Fixed {fp}")
    except Exception as e:
        print(f"Error {fp}: {e}")
