"""Parse Hermes orchestrator stdout into per-speaker utterances.

The marszalek-sejmu skill produces a single stdout blob with sectioned markdown:

    [MARSZAŁEK REASONING] ...
    ## Ministry Analysis
    ### Ministry of Finance — Expert Analysis ...
    ## Party Debate — First Reading
    **CR (157 seats):** "..." [node:abc-123]
    **NC (194 seats):** "..."
    ## Party Debate — Second Reading
    ## Vote
    ## Draft Bill

This module decomposes that blob into a flat list of utterances suitable for SSE streaming.
Each utterance is `{speaker, phase, content, node_ids}` and is intended to be inserted one at
a time so the frontend can render incremental progress.
"""
from __future__ import annotations

import re
from typing import Iterable

PARTIES = ["CR", "NC", "AC", "LF", "SD"]

_NODE_ID_RE = re.compile(r"\[node:([^\]]+)\]")

def _extract_node_ids(text: str) -> list[str]:
    return [m.group(1).strip() for m in _NODE_ID_RE.finditer(text)]

def _split_party_speeches(section_text: str, phase: str) -> list[dict]:
    """Split a 'First/Second Reading' section into per-party utterances.

    Speeches start with patterns like `**CR (157 seats):**` or `**SD rebuttal:**`.
    """
    out: list[dict] = []
    pattern = re.compile(
        r"\*\*\s*(CR|NC|AC|LF|SD)\b[^*]*\*\*",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(section_text))
    if not matches:
        return [{
            "speaker": "Debate",
            "phase": phase,
            "content": section_text.strip(),
            "node_ids": _extract_node_ids(section_text),
        }]
    for i, m in enumerate(matches):
        speaker_raw = m.group(1)
        speaker = next((p for p in PARTIES if p.lower() == speaker_raw.lower()), speaker_raw)
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
        body = section_text[start:end].strip()
        if not body:
            continue
        out.append({
            "speaker": speaker,
            "phase": phase,
            "content": body,
            "node_ids": _extract_node_ids(body),
        })
    return out

def _split_ministry_section(section_text: str) -> list[dict]:
    """Split 'Ministry Analysis' into per-ministry utterances.

    Subsections look like `### Ministry of Finance — Expert Analysis` or
    `### Ministerstwo Finansów`.
    """
    out: list[dict] = []
    pattern = re.compile(r"^### +(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(section_text))
    if not matches:
        return [{
            "speaker": "Ministerstwa",
            "phase": "ministry_analysis",
            "content": section_text.strip(),
            "node_ids": _extract_node_ids(section_text),
        }]
    for i, m in enumerate(matches):
        speaker = m.group(1).strip().rstrip("—-").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(section_text)
        body = section_text[start:end].strip()
        if not body:
            continue
        out.append({
            "speaker": speaker,
            "phase": "ministry_analysis",
            "content": body,
            "node_ids": _extract_node_ids(body),
        })
    return out

def parse_transcript(stdout: str) -> list[dict]:
    """Parse the orchestrator stdout into a flat list of per-speaker utterances.

    Returns a list of dicts: {speaker, phase, content, node_ids}, in narrative order.
    """
    out: list[dict] = []

    section_specs = [
        ("[MARSZAŁEK REASONING]", "marszalek_reasoning", "Marszałek Sejmu"),
        ("## Ministry Analysis", "ministry_analysis", None),
        ("## Party Debate — First Reading", "first_reading", None),
        ("## Party Debate — Second Reading", "second_reading", None),
        ("## Vote", "vote", "Komisja głosowania"),
        ("## Draft Bill", "bill_draft", "Marszałek Sejmu"),
    ]

    offsets: list[tuple[int, str, str, str | None]] = []
    for marker, phase, default_speaker in section_specs:
        idx = 0
        while (idx := stdout.find(marker, idx)) != -1:
            offsets.append((idx, marker, phase, default_speaker))
            idx += len(marker)
    offsets.sort(key=lambda x: x[0])

    for i, (off, marker, phase, default_speaker) in enumerate(offsets):
        body_start = off + len(marker)
        body_end = offsets[i + 1][0] if i + 1 < len(offsets) else len(stdout)
        body = stdout[body_start:body_end].strip()
        if not body:
            continue

        if phase == "ministry_analysis":
            out.extend(_split_ministry_section(body))
        elif phase in ("first_reading", "second_reading"):
            out.extend(_split_party_speeches(body, phase))
        else:
            disclaimer_idx = body.find("⚠️ EDUCATIONAL")
            if disclaimer_idx >= 0:
                body = body[:disclaimer_idx].strip()
            if not body:
                continue
            out.append({
                "speaker": default_speaker or "Marszałek Sejmu",
                "phase": phase,
                "content": body,
                "node_ids": _extract_node_ids(body),
            })

    return out
