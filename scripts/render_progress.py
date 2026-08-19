#!/usr/bin/env python3
"""Render move-auditor progress.json to progress.md and dashboard.html."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


PHASES = [
    ("A", "Intake"),
    ("B", "Surface Map"),
    ("C", "Coverage Routing"),
    ("D", "Scope Audit"),
    ("E", "Cross-Scope Synthesis"),
    ("F", "Verification"),
    ("G", "Report"),
]


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def text(value: Any, default: str = "-") -> str:
    if value is None:
        return default
    rendered = str(value).strip()
    return rendered if rendered else default


def esc(value: Any, default: str = "-") -> str:
    return html.escape(text(value, default))


def number(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def percent(part: Any, whole: Any) -> int:
    denominator = number(whole)
    if denominator <= 0:
        return 0
    return max(0, min(100, round(number(part) * 100 / denominator)))


def slug(value: Any, default: str = "unknown") -> str:
    raw = text(value, default).lower()
    return "".join(char if char.isalnum() else "-" for char in raw).strip("-") or default


def phase_rows(progress: dict[str, Any]) -> list[dict[str, str]]:
    by_id = {
        str(item.get("id", "")): item
        for item in as_list(progress.get("phases"))
        if isinstance(item, dict)
    }
    rows: list[dict[str, str]] = []
    for phase_id, label in PHASES:
        item = as_dict(by_id.get(phase_id))
        rows.append(
            {
                "id": phase_id,
                "label": text(item.get("label"), label),
                "status": text(item.get("status"), "pending"),
                "summary": text(item.get("summary")),
            }
        )
    return rows


def phase_completion(rows: list[dict[str, str]]) -> int:
    if not rows:
        return 0
    done = sum(1 for row in rows if row["status"].lower() == "completed")
    return percent(done, len(rows))


def render_markdown(progress: dict[str, Any]) -> str:
    counts = as_dict(progress.get("counts"))
    active_scope = as_dict(progress.get("active_scope"))
    active_command = as_dict(progress.get("active_command"))
    blockers = [as_dict(item) for item in as_list(progress.get("blockers"))]
    events = [as_dict(item) for item in as_list(progress.get("latest_events"))]

    lines = [
        "# Move Auditor Progress",
        "",
        f"- Status: {text(progress.get('run_status'))}",
        f"- Phase: {text(progress.get('current_phase'))} - {text(progress.get('phase_label'))} ({text(progress.get('phase_status'))})",
        f"- Target: {text(progress.get('target'))}",
        f"- Updated: {text(progress.get('updated_at'))}",
        f"- Next: {text(progress.get('next_action'))}",
        "",
        "## Active Work",
        "",
        f"- Scope: {text(active_scope.get('id'))} {text(active_scope.get('module'))} {text(active_scope.get('region'))}",
        f"- Focus: {text(active_scope.get('summary'))}",
        f"- Command: {text(active_command.get('command'))} ({text(active_command.get('status'))})",
        f"- Command summary: {text(active_command.get('summary'))}",
        "",
        "## Counts",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]

    for key in [
        "scopes_total",
        "scopes_audited",
        "scopes_blocked",
        "scopes_pending",
        "candidates",
        "confirmed",
        "dismissed",
        "clean_checks",
        "resource_requests_open",
    ]:
        lines.append(f"| {key.replace('_', ' ')} | {text(counts.get(key), '0')} |")

    lines.extend(["", "## Phases", "", "| Phase | Status | Summary |", "| --- | --- | --- |"])
    for row in phase_rows(progress):
        lines.append(f"| {row['id']} - {row['label']} | {row['status']} | {row['summary']} |")

    lines.extend(["", "## Blockers", ""])
    if blockers:
        for item in blockers:
            lines.append(f"- {text(item.get('id'))}: {text(item.get('summary'))}")
    else:
        lines.append("- None")

    lines.extend(["", "## Latest Events", ""])
    if events:
        for item in events[-10:]:
            lines.append(
                f"- {text(item.get('time'))} [{text(item.get('level'))}] {text(item.get('message'))}"
            )
    else:
        lines.append("- No events yet")

    lines.append("")
    return "\n".join(lines)


def render_html(progress: dict[str, Any]) -> str:
    counts = as_dict(progress.get("counts"))
    active_scope = as_dict(progress.get("active_scope"))
    active_command = as_dict(progress.get("active_command"))
    blockers = [as_dict(item) for item in as_list(progress.get("blockers"))]
    events = [as_dict(item) for item in as_list(progress.get("latest_events"))]
    rows = phase_rows(progress)

    scope_total = number(counts.get("scopes_total"))
    scope_audited = number(counts.get("scopes_audited"))
    scope_pending = number(counts.get("scopes_pending"))
    scope_blocked = number(counts.get("scopes_blocked"))
    completed_phases = sum(1 for row in rows if row["status"].lower() == "completed")
    candidate_count = number(counts.get("candidates"))
    confirmed_count = number(counts.get("confirmed"))
    scope_progress = percent(counts.get("scopes_audited"), counts.get("scopes_total"))
    phase_progress = phase_completion(rows)
    signal_count = confirmed_count + candidate_count
    signal_strength = max(4, min(100, confirmed_count * 30 + candidate_count * 14))

    metric_specs = [
        ("Audited", "scopes_audited", f"{scope_progress}% scope coverage", "teal"),
        ("Pending", "scopes_pending", "remaining scopes", "blue"),
        ("Candidates", "candidates", "open leads", "amber"),
        ("Confirmed", "confirmed", "verified bugs", "red"),
        ("Dismissed", "dismissed", "FP/known/capped", "violet"),
        ("Clean Checks", "clean_checks", "evidence-backed clears", "green"),
        ("Blocked", "scopes_blocked", "deferred scopes", "gray"),
        ("Resources", "resource_requests_open", "open asks", "amber"),
        ("Total Scopes", "scopes_total", "mapped attack surface", "blue"),
    ]

    count_cards = "\n".join(
        "<div class=\"metric {tone}\">"
        "<span>{label}</span>"
        "<strong>{value}</strong>"
        "<em>{caption}</em>"
        "</div>".format(
            tone=tone,
            label=html.escape(label),
            value=esc(counts.get(key), "0"),
            caption=html.escape(caption),
        )
        for label, key, caption, tone in metric_specs
    )
    phases = "\n".join(
        "<li class=\"phase {status}\">"
        "<span class=\"phase-marker\">{id}</span>"
        "<div><strong>{label}</strong><p>{summary}</p></div>"
        "<em>{status_text}</em>"
        "</li>".format(
            status=slug(row["status"]),
            id=esc(row["id"]),
            label=esc(row["label"]),
            summary=esc(row["summary"]),
            status_text=esc(row["status"]),
        )
        for row in rows
    )
    blocker_items = "\n".join(
        "<li><strong>{id}</strong><p>{summary}</p></li>".format(
            id=esc(item.get("id")), summary=esc(item.get("summary"))
        )
        for item in blockers
    ) or "<li>None</li>"
    event_items = "\n".join(
        "<li class=\"event {level}\">"
        "<time>{time}</time>"
        "<span>{level_text}</span>"
        "<p>{message}</p>"
        "</li>".format(
            level=slug(item.get("level")),
            time=esc(item.get("time")),
            level_text=esc(item.get("level")),
            message=esc(item.get("message")),
        )
        for item in events[-10:]
    ) or "<li>No events yet</li>"
    command_status = slug(active_command.get("status"))
    run_status = slug(progress.get("run_status"))

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="5">
  <title>Move Auditor Progress</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #0b0d10;
      --panel: #12161c;
      --panel-2: #171c23;
      --panel-3: #1d232c;
      --text: #f4f7fb;
      --muted: #98a3b3;
      --line: #2b333f;
      --line-strong: #3b4655;
      --teal: #28d6b6;
      --blue: #5db7ff;
      --amber: #f7b955;
      --red: #ff6b6b;
      --violet: #aa8cff;
      --green: #67d391;
      --gray: #9aa4b2;
      --shadow: 0 18px 48px rgba(0, 0, 0, .32);
    }}
    @keyframes pulse {{
      0%, 100% {{ opacity: .55; transform: scale(.9); box-shadow: 0 0 0 0 rgba(40, 214, 182, .28); }}
      50% {{ opacity: 1; transform: scale(1); box-shadow: 0 0 0 8px rgba(40, 214, 182, 0); }}
    }}
    @keyframes sweep {{
      from {{ transform: translateX(-120%); }}
      to {{ transform: translateX(120%); }}
    }}
    @keyframes glow {{
      0%, 100% {{ filter: saturate(1); }}
      50% {{ filter: saturate(1.35) brightness(1.08); }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background:
        linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px),
        var(--bg);
      background-size: 28px 28px;
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    main {{
      max-width: 1240px;
      margin: 0 auto;
      padding: 28px;
    }}
    header {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 16px;
      margin-bottom: 18px;
    }}
    h1 {{ margin: 0 0 8px; font-size: 30px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 12px; font-size: 16px; letter-spacing: 0; }}
    p {{ margin: 0; }}
    .hero, .status, section {{
      border: 1px solid var(--line);
      background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.015)), var(--panel);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }}
    .hero {{
      padding: 18px;
      overflow: hidden;
      position: relative;
    }}
    .hero::before {{
      content: "";
      position: absolute;
      inset: 0;
      border-top: 2px solid var(--teal);
      pointer-events: none;
    }}
    .hero.running::after, .hero.initializing::after {{
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(100deg, transparent 0%, rgba(93,183,255,.08) 45%, rgba(40,214,182,.12) 50%, transparent 58%);
      animation: sweep 4.6s linear infinite;
      pointer-events: none;
    }}
    .hero.completed::before {{ border-top-color: var(--green); }}
    .hero.blocked::before {{ border-top-color: var(--red); }}
    .hero-top {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 18px;
    }}
    .target {{
      color: var(--muted);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      overflow-wrap: anywhere;
    }}
    .status {{
      padding: 16px;
      align-self: stretch;
    }}
    .status-meta {{
      display: grid;
      grid-template-columns: 1fr;
      gap: 6px;
      margin-top: 12px;
      color: var(--muted);
      font-size: 13px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      padding: 4px 9px;
      border-radius: 999px;
      border: 1px solid rgba(40, 214, 182, .38);
      background: rgba(40, 214, 182, .11);
      color: var(--teal);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .live-dot {{
      display: inline-block;
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
      animation: pulse 1.8s ease-in-out infinite;
    }}
    .completed .live-dot {{ animation: none; }}
    .status.running .badge, .status.initializing .badge {{ color: var(--blue); border-color: rgba(93,183,255,.38); background: rgba(93,183,255,.12); }}
    .status.blocked .badge {{ color: var(--red); border-color: rgba(255,107,107,.38); background: rgba(255,107,107,.12); }}
    .status.completed .badge {{ color: var(--green); border-color: rgba(103,211,145,.38); background: rgba(103,211,145,.12); }}
    .scan-strip {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
      margin-top: 16px;
    }}
    .scan-cell {{
      position: relative;
      overflow: hidden;
      border: 1px solid var(--line);
      background: var(--panel-2);
      border-radius: 8px;
      padding: 12px;
      min-height: 92px;
    }}
    .scan-cell::before {{
      content: "";
      position: absolute;
      left: 0;
      right: 0;
      top: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(40,214,182,.85), transparent);
    }}
    .cell-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 10px;
    }}
    .cell-head em {{
      color: var(--muted);
      font-size: 12px;
      font-style: normal;
      white-space: nowrap;
    }}
    .scan-cell span, .muted, .metric em {{ color: var(--muted); font-size: 13px; }}
    .scan-cell strong {{ display: block; font-size: 24px; margin-top: 8px; }}
    .bar {{
      height: 10px;
      border: 1px solid var(--line-strong);
      background: #080a0d;
      border-radius: 999px;
      overflow: hidden;
      margin-top: 10px;
    }}
    .bar i {{
      display: block;
      width: var(--value);
      height: 100%;
      background: linear-gradient(90deg, var(--teal), var(--blue), var(--violet));
      animation: glow 2.8s ease-in-out infinite;
    }}
    .signal-meter {{
      height: 7px;
      background: #080a0d;
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      overflow: hidden;
      margin-top: 12px;
    }}
    .signal-meter i {{
      display: block;
      width: var(--value);
      height: 100%;
      background: linear-gradient(90deg, var(--amber), var(--red));
    }}
    .grid {{
      display: grid;
      grid-template-columns: minmax(0, 1.05fr) minmax(0, .95fr);
      gap: 16px;
    }}
    section {{
      padding: 16px;
    }}
    .work-panel {{
      margin-bottom: 16px;
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(260px, .42fr);
      gap: 14px;
      align-items: stretch;
    }}
    .work-main {{
      min-width: 0;
    }}
    .scope-line {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      color: var(--teal);
      overflow-wrap: anywhere;
      margin-bottom: 8px;
    }}
    .command-box {{
      border: 1px solid var(--line);
      background: var(--panel-3);
      border-radius: 8px;
      padding: 12px;
    }}
    .command-box strong {{
      display: block;
      overflow-wrap: anywhere;
    }}
    .command-box .command-status {{
      display: inline-block;
      margin-bottom: 8px;
      padding: 2px 8px;
      border-radius: 999px;
      color: var(--blue);
      background: rgba(93,183,255,.12);
      border: 1px solid rgba(93,183,255,.3);
      font-size: 12px;
      text-transform: uppercase;
      font-weight: 700;
    }}
    .command-box .passed {{ color: var(--green); background: rgba(103,211,145,.12); border-color: rgba(103,211,145,.3); }}
    .command-box .failed, .command-box .blocked {{ color: var(--red); background: rgba(255,107,107,.12); border-color: rgba(255,107,107,.3); }}
    .command-box .running {{ color: var(--amber); background: rgba(247,185,85,.12); border-color: rgba(247,185,85,.3); }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .metric {{
      border: 1px solid var(--line);
      background: var(--panel-2);
      border-radius: 8px;
      padding: 12px;
      min-height: 96px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .metric strong {{ font-size: 28px; line-height: 1.05; }}
    .metric.teal strong {{ color: var(--teal); }}
    .metric.blue strong {{ color: var(--blue); }}
    .metric.amber strong {{ color: var(--amber); }}
    .metric.red strong {{ color: var(--red); }}
    .metric.violet strong {{ color: var(--violet); }}
    .metric.green strong {{ color: var(--green); }}
    .metric.gray strong {{ color: var(--gray); }}
    ul {{ margin: 0; padding: 0; list-style: none; }}
    .phase {{
      display: grid;
      grid-template-columns: 36px minmax(0, 1fr) auto;
      gap: 10px;
      padding: 11px 0;
      border-bottom: 1px solid var(--line);
    }}
    .phase.running {{
      margin: 0 -8px;
      padding-left: 8px;
      padding-right: 8px;
      border-radius: 8px;
      background: rgba(40,214,182,.055);
    }}
    .phase:last-child {{ border-bottom: 0; }}
    .phase-marker {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      display: inline-grid;
      place-items: center;
      border: 1px solid var(--line-strong);
      background: var(--panel-3);
      color: var(--muted);
      font-weight: 700;
    }}
    .phase em {{
      font-style: normal;
      font-size: 13px;
      color: var(--muted);
      text-transform: uppercase;
      white-space: nowrap;
    }}
    .phase p {{
      color: var(--muted);
      font-size: 13px;
      overflow-wrap: anywhere;
    }}
    .completed .phase-marker {{ background: rgba(103,211,145,.14); color: var(--green); border-color: rgba(103,211,145,.42); }}
    .running .phase-marker {{ background: rgba(40,214,182,.14); color: var(--teal); border-color: rgba(40,214,182,.42); }}
    .blocked .phase-marker {{ background: rgba(255,107,107,.14); color: var(--red); border-color: rgba(255,107,107,.42); }}
    .events li, .blockers li {{
      padding: 10px 0;
      border-bottom: 1px solid var(--line);
    }}
    .events li:last-child, .blockers li:last-child {{ border-bottom: 0; }}
    .event {{
      display: grid;
      grid-template-columns: 158px 76px minmax(0, 1fr);
      gap: 8px;
      align-items: start;
    }}
    time, .events span {{
      color: var(--muted);
      font-size: 12px;
    }}
    .events span {{
      text-transform: uppercase;
      font-weight: 700;
    }}
    .event.info span {{ color: var(--blue); }}
    .event.warn span, .event.warning span {{ color: var(--amber); }}
    .event.error span {{ color: var(--red); }}
    .event p {{ color: #d6dce6; overflow-wrap: anywhere; }}
    .next-action {{
      margin-top: 10px;
      padding-top: 10px;
      border-top: 1px solid var(--line);
      color: #d6dce6;
    }}
    @media (max-width: 860px) {{
      main {{ padding: 18px; }}
      header, .grid, .metrics, .work-panel, .scan-strip {{ grid-template-columns: 1fr; }}
      .event {{ grid-template-columns: 1fr; gap: 2px; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div class="hero {run_status}">
        <div class="hero-top">
          <div>
            <span class="badge"><i class="live-dot" aria-hidden="true"></i>Autonomous Move Audit</span>
            <h1>Move Auditor Scan Console</h1>
          </div>
          <span class="badge">{esc(progress.get('current_phase'))} - {esc(progress.get('phase_label'))}</span>
        </div>
        <p class="target">{esc(progress.get('target'))}</p>
        <div class="scan-strip">
          <div class="scan-cell">
            <div class="cell-head"><span>Scope Coverage</span><em>{scope_audited}/{scope_total}</em></div>
            <strong>{scope_progress}%</strong>
            <div class="bar" aria-hidden="true"><i style="--value:{scope_progress}%"></i></div>
          </div>
          <div class="scan-cell">
            <div class="cell-head"><span>Phase Completion</span><em>{completed_phases}/{len(rows)}</em></div>
            <strong>{phase_progress}%</strong>
            <div class="bar" aria-hidden="true"><i style="--value:{phase_progress}%"></i></div>
          </div>
          <div class="scan-cell">
            <div class="cell-head"><span>Live Finding Signal</span><em>{signal_count} total</em></div>
            <strong>{signal_count}</strong>
            <p class="muted">{candidate_count} candidates / {confirmed_count} confirmed</p>
            <div class="signal-meter" aria-hidden="true"><i style="--value:{signal_strength}%"></i></div>
          </div>
        </div>
      </div>
      <div class="status {run_status}">
        <span class="badge"><i class="live-dot" aria-hidden="true"></i>{esc(progress.get('run_status'))}</span>
        <p style="margin-top:12px"><strong>{esc(progress.get('current_phase'))} - {esc(progress.get('phase_label'))}</strong></p>
        <div class="status-meta">
          <span>{esc(progress.get('phase_status'))}</span>
          <span>Started: {esc(progress.get('started_at'))}</span>
          <span>Updated: {esc(progress.get('updated_at'))}</span>
          <span>Pending: {scope_pending} / Blocked: {scope_blocked}</span>
        </div>
        <p class="next-action"><strong>Next:</strong> {esc(progress.get('next_action'))}</p>
      </div>
    </header>

    <section class="work-panel">
      <div class="work-main">
      <h2>Active Work</h2>
      <p class="scope-line">{esc(active_scope.get('id'))} / {esc(active_scope.get('module'))} / {esc(active_scope.get('region'))}</p>
      <p><strong>Focus:</strong> {esc(active_scope.get('summary'))}</p>
      </div>
      <div class="command-box">
        <span class="command-status {command_status}">{esc(active_command.get('status'))}</span>
        <strong>{esc(active_command.get('command'))}</strong>
        <p class="muted">{esc(active_command.get('summary'))}</p>
      </div>
    </section>

    <div class="grid" style="margin-top:16px">
      <section>
        <h2>Counts</h2>
        <div class="metrics">{count_cards}</div>
      </section>
      <section>
        <h2>Phases</h2>
        <ul>{phases}</ul>
      </section>
      <section>
        <h2>Blockers</h2>
        <ul class="blockers">{blocker_items}</ul>
      </section>
      <section>
        <h2>Latest Events</h2>
        <ul class="events">{event_items}</ul>
      </section>
    </div>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("progress_json", type=Path)
    parser.add_argument("--out-dir", type=Path)
    args = parser.parse_args()

    progress_path = args.progress_json
    out_dir = args.out_dir or progress_path.parent
    progress = json.loads(progress_path.read_text(encoding="utf-8"))

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "progress.md").write_text(render_markdown(progress), encoding="utf-8")
    (out_dir / "dashboard.html").write_text(render_html(progress), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
