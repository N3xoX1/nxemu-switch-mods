#!/usr/bin/env python3
"""Checks the mods: folder names, mod.json, licenses, and that every file is a plain-text patch, cheat, note (README.md)
or license."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_DIRS = {".git", ".github", "tools"}
GAME_DIR = re.compile(r"^(?P<name>.+) \[(?P<title_id>[0-9A-F]{16})\]$")
BUILD_ID = re.compile(r"^[0-9A-Fa-f]{1,64}$")
INVALID_CHARS = set('<>:"/\\|?*')
MAX_FILE_SIZE = 64 * 1024
# Where each kind of file may be in a mod folder
ALLOWED = {
    "": {"", ".json", ".md", ".txt"},
    "exefs": {".nxpatch", ".pchtxt", ".ips"},
    "cheats": {".txt"},
}
TEXT_PATCHES = {".nxpatch", ".pchtxt"}
FEATURES = {"frame_step"}
LICENSE_FILE = re.compile(r"^LICENSE(\.(md|txt))?$")

errors = []


def error(path, message):
    errors.append(f"{path.relative_to(ROOT).as_posix()}: {message}")


def check_name(path):
    name = path.name
    if any(c in INVALID_CHARS or ord(c) < 32 for c in name):
        error(path, "the name has a character Windows does not allow")
    if name != name.strip() or name.endswith("."):
        error(path, "the name starts or ends with a space, or ends with a dot")


def is_text(value):
    return isinstance(value, str) and bool(value.strip())


def check_mod_json(mod):
    path = mod / "mod.json"
    if not path.is_file():
        error(mod, "has no mod.json")
        return
    try:
        info = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError) as e:
        error(path, f"is not valid JSON: {e}")
        return
    if not isinstance(info, dict):
        error(path, "is not a JSON object")
        return
    for key in ("name", "description"):
        if not isinstance(info.get(key), str) or not info[key].strip():
            error(path, f'needs "{key}" (text)')
    # The license is the mod author's to give: null when they gave none, and the mod is here by their permission
    if "license" not in info or not (info["license"] is None or is_text(info["license"])):
        error(path, 'needs "license" (the license its authors gave, or null for none)')
    elif info["license"] is None:
        if not is_text(info.get("permission")):
            error(path, 'has no license, so needs "permission" (who allowed it to be here, and when)')
    elif not any(LICENSE_FILE.match(f.name) for f in mod.iterdir() if f.is_file()):
        error(mod, "has a license, so needs its text, with the copyright lines, in LICENSE")
    versions = info.get("game_versions")
    if not isinstance(versions, list) or not versions or not all(isinstance(v, str) and v for v in versions):
        error(path, 'needs "game_versions" (a list of game versions)')
    if not isinstance(info.get("enabled_by_default"), bool):
        error(path, 'needs "enabled_by_default" (true or false)')
    requires = info.get("requires", [])
    if not isinstance(requires, list) or any(r not in FEATURES for r in requires):
        error(path, f'"requires" may only list {sorted(FEATURES)}')
    credits = info.get("credits")
    if not isinstance(credits, list) or not credits:
        error(path, 'needs "credits" (who made the mod and whose work it uses)')
    else:
        for credit in credits:
            if not isinstance(credit, dict) or not is_text(credit.get("name")):
                error(path, 'every credit needs a "name"')
            elif not is_text(credit.get("license")) and not is_text(credit.get("permission")):
                error(path, f'the credit for {credit["name"]} needs the "license" of their work or the "permission" they gave')


def check_file(mod, path):
    folder = path.parent.relative_to(mod).as_posix()
    folder = "" if folder == "." else folder
    allowed = ALLOWED.get(folder)
    if allowed is None:
        error(path, f"is in a folder a mod may not have (only {sorted(k for k in ALLOWED if k)})")
        return
    if path.suffix.lower() not in allowed:
        error(path, f"is not a file type allowed here ({sorted(allowed)})")
        return
    if folder == "" and path.suffix.lower() != ".json" and path.stem.upper() != "README" and not LICENSE_FILE.match(path.name):
        error(path, "only mod.json, a README and a LICENSE may be at the top of a mod")
    if folder == "" and path.suffix.lower() == ".json" and path.name != "mod.json":
        error(path, "the only JSON file is mod.json")
    if path.stat().st_size > MAX_FILE_SIZE:
        error(path, f"is over {MAX_FILE_SIZE // 1024} KiB")
    if path.suffix.lower() in TEXT_PATCHES:
        text = path.read_text(encoding="utf-8", errors="replace")
        if not re.search(r"^@nsobid-[0-9A-Fa-f]+", text, re.MULTILINE):
            error(path, "names no build id (@nsobid-)")
    if folder in ("exefs", "cheats") and path.suffix.lower() in (".ips", ".txt"):
        if not BUILD_ID.match(path.stem):
            error(path, "is not named by the build id it applies to")


def main():
    title_ids = {}
    for entry in sorted(ROOT.iterdir()):
        if entry.name in REPO_DIRS or entry.is_file():
            continue
        check_name(entry)
        match = GAME_DIR.match(entry.name)
        if not match:
            error(entry, "a game folder is named '<Game name> [<16-digit hex title id, upper case>]'")
            continue
        title_id = match.group("title_id")
        if title_id in title_ids:
            error(entry, f"has the same title id as {title_ids[title_id]}")
        title_ids[title_id] = entry.name
        for mod in sorted(entry.iterdir()):
            if mod.is_file():
                error(mod, "a game folder holds only mod folders")
                continue
            check_name(mod)
            check_mod_json(mod)
            for path in sorted(mod.rglob("*")):
                check_name(path)
                if path.is_file():
                    check_file(mod, path)

    for message in errors:
        print(message)
    print(f"{len(title_ids)} games checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
