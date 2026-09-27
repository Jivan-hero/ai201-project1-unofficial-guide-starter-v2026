#!/usr/bin/env python3
"""
AI201 environment check.

Run this before every class:

    python test.py

It checks the things that actually break: your Python version, your virtual
environment, your pinned packages, your API key, and one real call to the
model. It is the same file in every unit's starter repo — the checks adapt
to whatever that unit's requirements.txt pins.

Nothing here touches your project code, and nothing here is graded.
"""

import importlib
import importlib.metadata as md
import os
import platform
import re
import shutil
import sys
from pathlib import Path

# --- Course-wide pins -------------------------------------------------------
# The model lives here, in one place, so a provider change is one edit.
# Override locally by setting AI201_MODEL in your .env.
MODEL = os.getenv("AI201_MODEL", "gemini-3.5-flash-lite")

MIN_PYTHON = (3, 11)
MAX_PYTHON = (3, 14)  # exclusive — 3.14 breaks the pinned stack
# Was 5, which was sized for PyTorch. The pinned stack no longer installs it —
# see the note in requirements.txt — so the whole environment is now roughly
# 600 MB plus an 80 MB model. 2 GB leaves room for the vector store and slack.
MIN_DISK_GB = 2
MIN_RAM_GB = 4

# Distribution name on PyPI -> module name you actually import.
IMPORT_NAMES = {
    "python-dotenv": "dotenv",
    "google-genai": "google.genai",
    "rank-bm25": "rank_bm25",
    "rank_bm25": "rank_bm25",
    "pillow": "PIL",
    "beautifulsoup4": "bs4",
}

ROOT = Path(__file__).resolve().parent

passed, failed, warned, skipped = [], [], [], []


def report(status, name, detail=""):
    line = f"[{status:<4}] {name}"
    if detail:
        line += f"\n         {detail}"
    print(line)
    {"PASS": passed, "FAIL": failed, "WARN": warned, "SKIP": skipped}[status].append(name)


# --- 1. Python --------------------------------------------------------------

def check_python():
    v = sys.version_info
    actual = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) < MIN_PYTHON:
        return report("FAIL", "Python version", f"Found {actual}. This course needs 3.11 or newer.")
    if (v.major, v.minor) >= MAX_PYTHON:
        return report(
            "FAIL",
            "Python version",
            f"Found {actual}. The pinned packages do not support 3.14 yet — "
            f"install 3.13 and rebuild your virtual environment.",
        )
    report("PASS", "Python version", f"{actual} on {platform.system()}")


def check_venv():
    active = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    if not active:
        return report(
            "FAIL",
            "Virtual environment",
            "Not active. Run the activate command for your OS, then try again. "
            "Installing into your system Python is the most common cause of "
            "'it worked yesterday'.",
        )
    report("PASS", "Virtual environment", sys.prefix)


# --- 2. Packages ------------------------------------------------------------

def parse_requirements(path):
    """Yield (distribution_name, raw_specifier) for each real requirement line."""
    reqs = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[;]", line, maxsplit=1)[0].strip()
        if name:
            reqs.append((name, line))
    return reqs


def check_packages():
    req_file = ROOT / "requirements.txt"
    if not req_file.exists():
        return report(
            "FAIL",
            "requirements.txt",
            f"Not found next to test.py. Run this from inside the starter repo folder.",
        )

    missing, wrong = [], []
    for dist, spec in parse_requirements(req_file):
        module = IMPORT_NAMES.get(dist.lower(), dist.replace("-", "_"))
        try:
            importlib.import_module(module)
        except Exception as e:
            missing.append(f"{dist} ({type(e).__name__})")
            continue
        try:
            installed = md.version(dist)
        except md.PackageNotFoundError:
            continue
        if "==" in spec:
            want = spec.split("==")[1].split(",")[0].strip()
            if installed != want:
                wrong.append(f"{dist}: pinned {want}, installed {installed}")

    if missing:
        return report(
            "FAIL",
            "Pinned packages",
            "Could not import: " + ", ".join(missing)
            + "\n         Fix: pip install -r requirements.txt",
        )
    if wrong:
        return report("WARN", "Pinned packages", "; ".join(wrong))
    report("PASS", "Pinned packages", f"all {len(parse_requirements(req_file))} import cleanly")


# --- 3. Machine -------------------------------------------------------------

def total_ram_gb():
    try:
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names:
            return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1024**3
        if sys.platform == "win32":
            import ctypes

            class MemStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

            stat = MemStatus()
            stat.dwLength = ctypes.sizeof(MemStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            return stat.ullTotalPhys / 1024**3
    except Exception:
        pass
    return None


def check_machine():
    free_gb = shutil.disk_usage(ROOT).free / 1024**3
    if free_gb < MIN_DISK_GB:
        report("FAIL", "Free disk space",
               f"{free_gb:.1f} GB free, need about {MIN_DISK_GB} GB. "
               f"The packages and the embedding model are most of it.")
    else:
        report("PASS", "Free disk space", f"{free_gb:.1f} GB")

    ram = total_ram_gb()
    if ram is None:
        report("SKIP", "Memory", "Could not read total RAM on this OS — check manually.")
    elif ram < MIN_RAM_GB:
        report("WARN", "Memory",
               f"{ram:.1f} GB total, {MIN_RAM_GB} GB recommended. Things will run, "
               f"but close other apps while indexing.")
    else:
        report("PASS", "Memory", f"{ram:.1f} GB")


# --- 4. Secrets -------------------------------------------------------------

def check_key_hygiene():
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        return report("FAIL", "Key hygiene", "No .gitignore in this repo — your key can reach GitHub.")
    entries = {l.strip() for l in gitignore.read_text(encoding="utf-8").splitlines()}
    if ".env" not in entries:
        return report("FAIL", "Key hygiene",
                      ".env is not listed in .gitignore. Add a line containing exactly: .env")
    report("PASS", "Key hygiene", ".env is ignored by git")


def load_key():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    return os.getenv("GEMINI_API_KEY", "").strip()


def check_key_present(key):
    if not (ROOT / ".env").exists():
        return report("FAIL", "API key", "No .env file. Copy .env.example to .env and paste your key in.")
    if not key:
        return report("FAIL", "API key", "GEMINI_API_KEY is empty in .env.")
    if key.startswith(("your_", "<", "paste")) or key == "your_key_here":
        return report("FAIL", "API key", "GEMINI_API_KEY still holds the placeholder text.")
    if key != key.strip('"\'' ):
        return report("FAIL", "API key", "Remove the quotes around the key in .env.")
    report("PASS", "API key", f"loaded, {len(key)} characters")
    return True


# --- 5. The slow ones -------------------------------------------------------

def check_embeddings():
    # The embedding model ships inside chromadb — see the note in
    # requirements.txt — so there is no separate package to check for here.
    try:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
    except ImportError:
        return report("SKIP", "Embedding model", "chromadb not installed yet.")
    # Printed before the check runs, because on a first run this is where you
    # sit and wait. Name the check it belongs to — with no label it reads as a
    # detail line under whatever check printed last.
    print("[ .. ] Embedding model — first run downloads ~80 MB, this is the slow part")
    try:
        model = ONNXMiniLM_L6_V2()
        dim = len(model(["ready"])[0])
        report("PASS", "Embedding model", f"all-MiniLM-L6-v2 loaded, {dim}-dim vectors")
    except Exception as e:
        report("FAIL", "Embedding model", f"{type(e).__name__}: {e}")


def check_chroma():
    try:
        import chromadb
    except ImportError:
        return report("SKIP", "Vector store", "chromadb not installed yet.")
    try:
        client = chromadb.EphemeralClient()
        # Cosine is set explicitly here for the same reason the starter sets it:
        # Chroma defaults to squared L2, which would make the course's distance
        # threshold meaningless. Vectors are passed in directly, the way the
        # starter does it — Chroma stores and searches, it doesn't embed.
        col = client.create_collection("envcheck", metadata={"hnsw:space": "cosine"})
        col.add(ids=["a", "b"], documents=["the library closes at ten", "parking costs four dollars"],
                embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        hits = col.query(query_embeddings=[[0.9, 0.1, 0.0]], n_results=1)
        assert hits["ids"][0] == ["a"], "nearest neighbour came back wrong"
        report("PASS", "Vector store", "Chroma round trip on a cosine collection")
    except Exception as e:
        report("FAIL", "Vector store", f"{type(e).__name__}: {e}")


def check_api_call(key):
    try:
        from google import genai
    except ImportError:
        return report("SKIP", "Model call", "google-genai not installed yet.")
    try:
        client = genai.Client(api_key=key)
        resp = client.models.generate_content(model=MODEL, contents="Reply with one word: ready")
        text = (resp.text or "").strip()
        report("PASS", "Model call", f'{MODEL} replied "{text[:40]}"')
    except Exception as e:
        msg = str(e)
        hint = ""
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            hint = "\n         That's a rate limit, not a broken key. Wait a minute and re-run."
        elif "API key" in msg or "401" in msg or "403" in msg or "PERMISSION" in msg:
            hint = "\n         The key was rejected. Create a new one and paste it into .env again."
        elif "404" in msg or "NOT_FOUND" in msg:
            hint = f"\n         The model string '{MODEL}' did not resolve. Post in the help channel."
        report("FAIL", "Model call", f"{type(e).__name__}: {msg[:160]}{hint}")


# --- Run --------------------------------------------------------------------

def main():
    print("\nAI201 environment check\n" + "-" * 60)
    check_python()
    check_venv()
    check_packages()
    check_machine()
    check_key_hygiene()
    key = load_key()
    has_key = check_key_present(key)
    check_embeddings()
    check_chroma()
    if has_key:
        check_api_call(key)
    else:
        report("SKIP", "Model call", "no key to test with")

    print("-" * 60)
    print(f"{len(passed)} passed, {len(failed)} failed, "
          f"{len(warned)} to look at, {len(skipped)} skipped\n")
    if failed:
        print("Not ready yet. Fix the FAIL lines above, then run test.py again.")
        print("Still stuck after one honest attempt? Post the whole output in the")
        print("help channel — the day before class, not the morning of.\n")
        return 1
    if skipped:
        print("You're set for what's installed. The skipped checks are packages")
        print("this unit's requirements.txt doesn't pin yet — that's expected.\n")
        return 0
    print("You're set. See you in class.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
