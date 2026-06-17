from __future__ import annotations

import json
import re
from typing import Any

try:
    from json_repair import repair_json  # type: ignore
except Exception:  # pragma: no cover - optional import for runtime fallback
    repair_json = None


_FENCED_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S | re.I)


def _try_json_loads(text: str) -> Any:
    return json.loads(text)


def loads_loose(text: str) -> Any:
    """Best-effort JSON parsing for LLM output.

    Strategy:
    1. Direct json.loads
    2. Strip fenced code block and retry
    3. Use json_repair when available
    4. Extract first balanced top-level array/object and retry/repair
    """
    if text is None:
        raise ValueError("text is None")

    candidate = text.strip()
    if not candidate:
        raise ValueError("empty json candidate")

    try:
        return _try_json_loads(candidate)
    except Exception:
        pass

    fenced = _FENCED_RE.search(candidate)
    if fenced:
        inner = fenced.group(1).strip()
        try:
            return _try_json_loads(inner)
        except Exception:
            candidate = inner

    if repair_json is not None:
        try:
            repaired = repair_json(candidate, return_objects=True)
            if repaired is not None:
                return repaired
        except TypeError:
            repaired_text = repair_json(candidate)
            return _try_json_loads(repaired_text)
        except Exception:
            pass

    extracted = extract_balanced_json(candidate)
    if extracted and extracted != candidate:
        try:
            return _try_json_loads(extracted)
        except Exception:
            if repair_json is not None:
                try:
                    repaired = repair_json(extracted, return_objects=True)
                    if repaired is not None:
                        return repaired
                except TypeError:
                    repaired_text = repair_json(extracted)
                    return _try_json_loads(repaired_text)
                except Exception:
                    pass

    raise ValueError(f"unable to parse model json: {text}")


def extract_balanced_json(text: str) -> str | None:
    for opener, closer in (("[", "]"), ("{", "}")):
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escaped = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == opener:
                    depth += 1
                elif ch == closer:
                    depth -= 1
                    if depth == 0:
                        return text[start : i + 1]
    return None
