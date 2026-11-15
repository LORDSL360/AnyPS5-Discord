
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
        headers={"User-Agent": "AnyPS5-Discord-Bot"}
    )

    with urllib.request.urlopen(request, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def get_metrics(data):
    libraries = data.get("libraries", {})
    shader_source = data.get("shader_source", {})
    instructions = shader_source.get("instructions", {})
    profiles = shader_source.get("profiles", {})
    gfx1013 = profiles.get("gfx1013", {})
    gfx_instructions = gfx1013.get("instructions", {})

    return {
        "libraries": (
            libraries.get("completed", 0)
            if isinstance(libraries, dict)
            else 0
        ),
        "rdna2": (
            instructions.get("decoded", 0)
            if isinstance(instructions, dict)
            else 0
        ),
        "gfx1013": (
            gfx_instructions.get("decoded", 0)
            if isinstance(gfx_instructions, dict)
            else 0
        ),
    }


def load_previous():
    if not STATE_FILE.exists():
        return None

    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_current(metrics):
    STATE_FILE.write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8"
    )


def format_delta(current, previous):
    difference = current - previous

    if difference > 0:
        return f"+{difference:,}"
    if difference < 0:
        return f"{difference:,}"
    return "0"


def make_embed(current, previous):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    fields = []

    names = {
        "libraries": "Libraries completed",
        "rdna2": "RDNA2 instructions decoded",
        "gfx1013": "GFX1013 instructions decoded",
    }

    for key, name in names.items():
        value = current.get(key, 0)

        if previous is None:
            change = "First report - baseline"
        else:
            old_value = previous.get(key, 0)
            change = format_delta(value, old_value)

        fields.append({
            "name": name,
            "value": f"**{value:,}**\nChange: `{change}`",
            "inline": True
        })

    if previous is None:
        description = "Initial progress report. The next update will show changes."
    else:
        changes = [
            current.get(key, 0) - previous.get(key, 0)
            for key in names
        ]

        if any(value > 0 for value in changes):
            description = "Progress has increased since the previous report."
        elif any(value < 0 for value in changes):
            description = "Some reported values have changed since the previous report."
        else:
            description = "No progress changes detected since the previous report."

    return {
        "title": "AnyPS5 - Progress Report",
        "description": description,
        "color": 5793266,
        "fields": fields,
        "footer": {
            "text": f"Automatic update • {now}"
        }
    }


def send_discord(embed):
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()

    if not webhook_url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is missing!")

    payload = {
        "embeds": [embed]
    }

    request = urllib.request.Request(
        webhook_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            print("Discord response:", response.status)
            print("Message sent successfully!")

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
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

    print("Current metrics:", current)

    embed = make_embed(current, previous)

    print("Sending Discord report...")
    send_discord(embed)

    save_current(current)
    print("Progress state saved.")
    print("Done!")


if __name__ == "__main__":
    main()
