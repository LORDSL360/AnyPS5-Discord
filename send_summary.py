
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

DATA_URL = "https://boykopovar.github.io/AnyPS5/progress.json"
STATE_FILE = Path("last_progress.json")


def fetch_progress():
    request = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "AnyPS5ProgressBot/1.0"}
    )

    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def get_metrics(data):
    libraries = data.get("libraries", {})
    shader = data.get("shader_source", {})
    gfx = shader.get("profiles", {}).get("gfx1013", {})

    return {
        "libraries_done": int(libraries.get("done", 0)),
        "libraries_total": int(libraries.get("total", 0)),
        "libraries_percent": float(libraries.get("percent", 0)),
        "rdna2_decoded": int(
            shader.get("instructions", {}).get("decoded", 0)
        ),
        "rdna2_total": int(
            shader.get("instructions", {}).get("total", 0)
        ),
        "gfx1013_decoded": int(
            gfx.get("instructions", {}).get("decoded", 0)
        ),
        "gfx1013_total": int(
            gfx.get("instructions", {}).get("total", 0)
        ),
        "dpp_decoded": int(
            shader.get("dpp", {}).get("decoded", 0)
        ),
        "dpp_total": int(
            shader.get("dpp", {}).get("total", 0)
        )
    }


def load_previous():
    if not STATE_FILE.exists():
        return None

    try:
        previous = json.loads(
            STATE_FILE.read_text(encoding="utf-8")
        )

        required = [
            "libraries_done",
            "libraries_total",
            "rdna2_decoded",
            "gfx1013_decoded",
            "dpp_decoded"
        ]

        if not all(key in previous for key in required):
            return None

        return previous

    except (json.JSONDecodeError, OSError):
        return None


def save_current(metrics):
    STATE_FILE.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8"
    )


def delta(current, previous):
    difference = current - previous

    if difference > 0:
        return f"+{difference:,}"
    elif difference < 0:
        return f"{difference:,}"

    return "0"


def progress_bar(percent):
    filled = round(percent / 5)
    filled = max(0, min(20, filled))
    return "[" + ("█" * filled) + ("░" * (20 - filled)) + "]"


def make_embed(current, previous):
    now = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    if previous is None:
        description = (
            "📊 **Initial progress baseline**\n"
            "The next report will show changes."
        )
        first = True
    else:
        description = "📈 **Progress since the previous update**"
        first = False

    fields = []

    # Libraries
    lib_done = current["libraries_done"]
    lib_total = current["libraries_total"]
    lib_percent = current["libraries_percent"]

    if first:
        lib_change = "First report"
    else:
        lib_change = delta(
            lib_done,
            previous["libraries_done"]
        )

    fields.append({
        "name": "📚 LIBRARIES IMPLEMENTED",
        "value": (
            f"**{lib_done:,} / {lib_total:,}** implemented\n"
            f"**Completion:** {lib_percent:.2f}%\n"
            f"`{progress_bar(lib_percent)}`\n"
            f"**Change:** `{lib_change}`"
        ),
        "inline": False
    })

    # RDNA2
    rdna2 = current["rdna2_decoded"]

    if first:
        rdna2_change = "First report"
    else:
        rdna2_change = delta(
            rdna2,
            previous["rdna2_decoded"]
        )

    fields.append({
        "name": "⚙️ RDNA2 INSTRUCTIONS",
        "value": (
            f"**{rdna2:,} / "
            f"{current['rdna2_total']:,}** decoded\n"
            f"**Change:** `{rdna2_change}`"
        ),
        "inline": False
    })

    # GFX1013
    gfx = current["gfx1013_decoded"]

    if first:
        gfx_change = "First report"
    else:
        gfx_change = delta(
            gfx,
            previous["gfx1013_decoded"]
        )

    fields.append({
        "name": "🎮 GFX1013 REFERENCE",
        "value": (
            f"**{gfx:,} / "
            f"{current['gfx1013_total']:,}** decoded\n"
            f"**Change:** `{gfx_change}`"
        ),
        "inline": False
    })

    # DPP
    dpp = current["dpp_decoded"]

    if first:
        dpp_change = "First report"
    else:
        dpp_change = delta(
            dpp,
            previous["dpp_decoded"]
        )

    fields.append({
        "name": "🔧 DPP INSTRUCTIONS",
        "value": (
            f"**{dpp:,} / "
            f"{current['dpp_total']:,}** decoded\n"
            f"**Change:** `{dpp_change}`"
        ),
        "inline": False
    })

    return {
        "title": "🚀 AnyPS5 - Progress Report",
        "description": description,
        "color": 5793266,
        "fields": fields,
        "footer": {
            "text": f"Automatic update • {now}"
        }
    }


def send_discord(embed):
    webhook_url = os.environ.get(
        "DISCORD_WEBHOOK_URL", ""
    ).strip()

    if not webhook_url:
        raise RuntimeError(
            "DISCORD_WEBHOOK_URL is missing!"
        )

    payload = {
        "username": "AnyPS5 Progress",
        "embeds": [embed]
    }

    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "AnyPS5ProgressBot/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(
            request, timeout=45
        ) as response:
            print("Discord response:", response.status)
            print("Message sent successfully!")

    except urllib.error.HTTPError as error:
        details = error.read().decode(
            "utf-8", errors="replace"
        )
        print("Discord HTTP status:", error.code)
        print("Discord error details:", details)
        raise

    except urllib.error.URLError as error:
        print("Discord connection error:", error)
        raise


def main():
    print("Fetching AnyPS5 progress...")

    data = fetch_progress()
    current = get_metrics(data)
    previous = load_previous()

    print("Current metrics:")
    print(json.dumps(current, indent=2))

    embed = make_embed(current, previous)

    print("Sending Discord report...")
    send_discord(embed)

    save_current(current)

    print("Progress history saved.")
    print("Done!")


if __name__ == "__main__":
    main()
