#!/usr/bin/env python3
"""
Claude Monitor Dashboard — terminal Matrix style.
"""

import re
import sys
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


GREEN  = "\033[92m"
DGREEN = "\033[32m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
RESET  = "\033[0m"
CLEAR  = "\033[2J\033[H"
YEL    = "\033[93m"
RED    = "\033[91m"
CYA    = "\033[96m"


def g(t):   return f"{GREEN}{t}{RESET}"
def dg(t):  return f"{DGREEN}{t}{RESET}"
def dim(t): return f"{DIM}{t}{RESET}"
def plain(t): return re.sub(r'\033\[[0-9;]*m', '', t)


def animate_startup():
    """8-bit boot sequence. Very important. Do not skip."""

    BOOT_STEPS = [
        ("LOADING TOKEN HARVESTER 3000",          True),
        ("INITIALIZING REGRET DATABASE",          True),
        ("CALIBRATING VIBE DETECTOR",             True),
        ("CHECKING IF AI TOOK YOUR JOB",          False),
        ("SUPPRESSING EXISTENTIAL DREAD",         True),
        ("COUNTING BUGS YOU WROTE TODAY",         True),
        ("CONVINCING SELF: I AM PRODUCTIVE",      True),
        ("UPLOADING BRAIN TO THE CLOUD",          True),
    ]

    print(CLEAR, end="")

    bios = [
        f"  {YEL}╔══════════════════════════════════════════════╗",
        f"  ║   ▄█████╗  CLAUDEOS v1.0 · BIOS v69.420    ║",
        f"  ║   █◉  ◉█   640K RAM DETECTED (it's enough™) ║",
        f"  ║   ██▄▄██   CPU: VERY BIG BRAIN  FAN: LOUD   ║",
        f"  ║   ◥████◤   PRESS F1 TO REGRET THIS PROJECT  ║",
        f"  ╚══════════════════════════════════════════════╝{RESET}",
    ]
    for line in bios:
        print(line)
        time.sleep(0.07)

    print()
    time.sleep(0.2)

    BAR_W = 14
    spin  = r"|/-\\"
    for label, ok in BOOT_STEPS:
        for j in range(BAR_W + 1):
            filled = "█" * j + "░" * (BAR_W - j)
            s = spin[j % 4]
            sys.stdout.write(f"\r  {s} [{filled}] {label:<44}")
            sys.stdout.flush()
            time.sleep(0.018)
        if ok:
            sys.stdout.write(
                f"\r  {GREEN}✓{RESET} [{GREEN}{'█'*BAR_W}{RESET}] {label:<44} {GREEN}OK{RESET}\n"
            )
        else:
            sys.stdout.write(
                f"\r  {RED}✗{RESET} [{RED}{'█'*BAR_W}{RESET}] {label:<44} {RED}FAIL{RESET}\n"
            )
        sys.stdout.flush()
        time.sleep(0.04)

    print()

    # pac-man eating tokens
    DOTS = 30
    for i in range(DOTS + 1):
        pm   = "ᗧ" if i % 2 == 0 else "ᗤ"
        line = " " * i + pm + "·" * (DOTS - i) + "🍒"
        sys.stdout.write(f"\r  {CYA}{line}{RESET}   ")
        sys.stdout.flush()
        time.sleep(0.035)

    print(f"\n\n  {YEL}*CHOMP*  {DOTS} TOKENS CONSUMED.{RESET}")
    print(f"  {DIM}productivity level: statistically indistinguishable from zero{RESET}")
    print()
    time.sleep(0.8)


def get_conn():
    return psycopg2.connect(dbname="claude_monitor")


def fetch_stats() -> dict:
    conn = get_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            COUNT(*) as total_sessions,
            COALESCE(SUM(total_tokens), 0) as total_tokens,
            COALESCE(AVG(total_tokens), 0) as avg_tokens,
            COUNT(*) FILTER (WHERE model LIKE '%opus%') as opus_sessions,
            COUNT(*) FILTER (WHERE model LIKE '%sonnet%') as sonnet_sessions,
            COUNT(*) FILTER (WHERE model LIKE '%haiku%') as haiku_sessions
        FROM sessions
    """)
    stats = dict(cur.fetchone())

    cur.execute("""
        SELECT COALESCE(COUNT(*), 0) as sessions, COALESCE(SUM(total_tokens), 0) as tokens
        FROM sessions WHERE timestamp > DATE_TRUNC('day', NOW())
    """)
    stats["today"] = dict(cur.fetchone())

    cur.execute("""
        SELECT project, COUNT(*) as cnt, COALESCE(SUM(total_tokens), 0) as tokens
        FROM sessions GROUP BY project ORDER BY tokens DESC LIMIT 5
    """)
    stats["projects"] = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT session_id, project, timestamp, model,
               total_tokens, first_user_message, outcome
        FROM sessions ORDER BY timestamp DESC LIMIT 7
    """)
    stats["recent"] = [dict(r) for r in cur.fetchall()]

    cur.close()
    conn.close()
    return stats


def bar(value, total, width=26) -> str:
    if not total:
        return dg("░" * width)
    filled = int((value / total) * width)
    return g("█" * filled) + dg("░" * (width - filled))


def fmt(n) -> str:
    n = int(n or 0)
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000:     return f"{n/1_000:.1f}K"
    return str(n)


def fmt_model(model: str) -> str:
    if not model: return "???"
    if "opus"   in model: return "OPUS  "
    if "sonnet" in model: return "SONNET"
    if "haiku"  in model: return "HAIKU "
    return model[:6].upper()


def row(content: str, W: int) -> str:
    pad = W - len(plain(content))
    return g("║") + content + " " * max(0, pad) + g("║")


def render(stats: dict):
    W = 62
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total = int(stats["total_sessions"])
    opus   = int(stats["opus_sessions"])
    sonnet = int(stats["sonnet_sessions"])
    today  = stats["today"]

    print(CLEAR, end="")
    print(g(f"╔{'═'*W}╗"))
    print(row(BOLD + GREEN + "  CLAUDE CODE USAGE MONITOR".center(W) + RESET, W))
    print(row(dim(f"  {now}"), W))
    print(g(f"╠{'═'*W}╣"))

    print(row(g("  ▸ OVERALL"), W))
    print(row(f"  Total sessions : {g(str(total))}", W))
    print(row(f"  Total tokens   : {g(fmt(stats['total_tokens']))}", W))
    print(row(f"  Avg per session: {g(fmt(stats['avg_tokens']))}", W))
    print(row(dg("  " + "─"*58), W))

    print(row(g("  ▸ TODAY"), W))
    print(row(f"  Sessions: {g(str(today['sessions']))}   Tokens: {g(fmt(today['tokens']))}", W))
    print(row(dg("  " + "─"*58), W))

    print(row(g("  ▸ MODELS"), W))
    print(row(f"  OPUS   [{bar(opus, total)}] {g(str(opus))}", W))
    print(row(f"  SONNET [{bar(sonnet, total)}] {dg(str(sonnet))}", W))
    print(row(dg("  " + "─"*58), W))

    print(row(g("  ▸ TOP PROJECTS"), W))
    for p in stats["projects"][:4]:
        name = (p["project"] or "unknown")[:22]
        line = f"  {name:<22} {str(p['cnt']):>3} sess  {fmt(p['tokens']):>6}"
        print(row(g(line), W))
    print(row(dg("  " + "─"*58), W))

    print(row(g("  ▸ RECENT SESSIONS"), W))
    for s in stats["recent"]:
        ts   = str(s["timestamp"])[:16] if s["timestamp"] else "???"
        mdl  = fmt_model(s["model"])
        tkns = fmt(s["total_tokens"])
        task = (s["first_user_message"] or "")[:18].replace("\n", " ")
        mark = g("✓") if s["outcome"] else dg("·")
        line = f"  {mark} {ts} {mdl} {tkns:>5}  {task}"
        print(row(line, W))

    print(g(f"╚{'═'*W}╝"))
    print(dim("  ✓ = outcome logged   · = no outcome"))
    print()


def main():
    try:
        animate_startup()
        render(fetch_stats())
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    main()