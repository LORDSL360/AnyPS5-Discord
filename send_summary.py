
import json
import os
import urllib.request
from datetime import datetime, timezone

PROGRESS_URL = "https://boykopovar.github.io/AnyPS5/progress.json"
STATE_FILE = "last_progress.json"
WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AnyPS5-Discord-Tracker"}
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def signed(number):
    return f"+{number:,}" if number > 0 else f"{number:,}"


def percentage(done, total):
    return done / total * 100 if total else 0


def metric(name, done, total, old=None):
    result = (
        f"`{done:,} / {total:,}`"
        f" • **{percentage(done, total):.2f}%**"
    )

    if old is None:
        result += "\nأول قراءة - تبدأ المقارنة من التقرير القادم"
    else:
        result += f"\nالتغير: **{signed(done - old)}**"

    return f"**{name}**\n{result}"


def send_discord(embed):
    payload = {
        "embeds": [embed],
        "allowed_mentions": {"parse": []}
    }

    request = urllib.request.Request(
        WEBHOOK,
        data=json.dumps(
            payload, ensure_ascii=False
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(request, timeout=45) as response:
        if response.status not in (200, 204):
            raise RuntimeError("Discord sending failed")


def main():
    data = fetch_json(PROGRESS_URL)

    libs = data["libraries"]
    shader = data["shader_source"]
    rdna = shader["instructions"]
    gfx = shader["profiles"]["gfx1013"]["instructions"]
    dpp = shader.get("dpp", {})

    current = {
        "libraries": {
            "done": libs["done"],
            "total": libs["total"]
        },
        "rdna2": {
            "decoded": rdna["decoded"],
            "total": rdna["total"],
            "translated": rdna.get("translated", rdna["decoded"])
        },
        "gfx1013": {
            "decoded": gfx["decoded"],
            "total": gfx["total"],
            "translated": gfx.get("translated", gfx["decoded"])
        },
        "dpp": {
            "decoded": dpp.get("decoded", 0),
            "total": dpp.get("total", 0)
        }
    }

    previous = None

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as file:
                previous = json.load(file)
        except (OSError, json.JSONDecodeError):
            pass

    old_libs = previous.get("libraries", {}) if previous else {}
    old_rdna = previous.get("rdna2", {}) if previous else {}
    old_gfx = previous.get("gfx1013", {}) if previous else {}
    old_dpp = previous.get("dpp", {}) if previous else {}

    lib_delta = (
        libs["done"] - old_libs["done"]
        if "done" in old_libs else None
    )

    rdna_delta = (
        rdna["decoded"] - old_rdna["decoded"]
        if "decoded" in old_rdna else None
    )

    gfx_delta = (
        gfx["decoded"] - old_gfx["decoded"]
        if "decoded" in old_gfx else None
    )

    if previous is None:
        status = "🆕 أول تقرير - تم حفظ خط الأساس"
        color = 3447003
        summary = "ستبدأ مقارنة التقدم من التقرير القادم."

    else:
        total_delta = sum(
            x for x in [lib_delta, rdna_delta, gfx_delta]
            if x is not None
        )

        if total_delta > 0:
            status = "📈 تقدم جديد منذ آخر تقرير"
            color = 3066993
        elif total_delta < 0:
            status = "🔄 تغير في بيانات المشروع"
            color = 15105570
        else:
            status = "⏸️ لا يوجد تغير منذ آخر تقرير"
            color = 9807270

        summary = (
            f"System Libraries: **{signed(lib_delta or 0)}** دالة\n"
            f"RDNA 2: **{signed(rdna_delta or 0)}** تعليمة\n"
            f"gfx1013: **{signed(gfx_delta or 0)}** تعليمة"
        )

    fields = [
        {
            "name": "📚 System Libraries",
            "value": metric(
                "Implemented Functions",
                libs["done"],
                libs["total"],
                old_libs.get("done")
            ),
            "inline": False
        },
        {
            "name": "🧩 RDNA 2 Shader Instructions",
            "value": (
                metric(
                    "Decoded",
                    rdna["decoded"],
                    rdna["total"],
                    old_rdna.get("decoded")
                )
                + f"\nTranslated: **{current['rdna2']['translated']:,}**"
            ),
            "inline": True
        },
        {
            "name": "🎮 gfx1013 Reference",
            "value": (
                metric(
                    "Decoded",
                    gfx["decoded"],
                    gfx["total"],
                    old_gfx.get("decoded")
                )
                + f"\nTranslated: **{current['gfx1013']['translated']:,}**"
            ),
            "inline": True
        }
    ]

    if dpp.get("total"):
        fields.append({
            "name": "🔀 DPP Instructions",
            "value": metric(
                "Decoded",
                dpp["decoded"],
                dpp["total"],
                old_dpp.get("decoded")
            ),
            "inline": True
        })

    now = datetime.now(timezone.utc).strftime(
        "%Y-%m-%d %H:%M UTC"
    )

    generated = data.get(
        "open_pr_progress", {}
    ).get("generated_at", "غير متاح")

    embed = {
        "title": "🚀 AnyPS5 - Project Progress",
        "url": "https://boykopovar.github.io/AnyPS5/",
        "description": f"**{status}**\n\n{summary}",
        "color": color,
        "fields": fields,
        "footer": {
            "text": f"Report: {now} | Source: {generated}"
        }
    }

    send_discord(embed)

    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(current, file, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
