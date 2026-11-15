
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

    if difference < 0:
        return f"{difference:,}"

    return "0"


def make_embed(current, previous):
    now = datetime.now(timezone.utc).strftime(
        "%d %b %Y • %H:%M UTC"
    )

    def change(key):
        if previous is None:
            return "First update"

        return delta(
            current[key],
            previous.get(key, current[key])
        )

    if previous is None:
        description = "📊 First progress report."
    else:
        description = "📈 Changes compared with the previous update."

    lines = [
        "📚 **Libraries**",
        (
            f"{current['libraries_done']:,} / "
            f"{current['libraries_total']:,} implemented "
            f"({current['libraries_percent']:.2f}%)"
        ),
        "",
        "⚙️ **RDNA2**",
        (
            f"{current['rdna2_decoded']:,} / "
            f"{current['rdna2_total']:,} decoded"
        ),
        "",
        "🎮 **GFX1013**",
        (
            f"{current['gfx1013_decoded']:,} / "
            f"{current['gfx1013_total']:,} decoded"
        ),
        "",
        "🔧 **DPP**",
        (
            f"{current['dpp_decoded']:,} / "
            f"{current['dpp_total']:,} decoded"
        ),
        "",
        "📈 **Since last update**",
        f"Libraries: `{change('libraries_done')}`",
        f"RDNA2: `{change('rdna2_decoded')}`",
        f"GFX1013: `{change('gfx1013_decoded')}`",
        f"DPP: `{change('dpp_decoded')}`"
    ]

    return {
        "title": "🚀 AnyPS5 Progress",
        "description": description + "\n\n" + "\n".join(lines),
        "color": 5793266,
        "footer": {
            "text": f"Updated • {now}"
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
