"""Convert physical key positions, without translation or spelling correction."""

from collections.abc import Mapping


# Unshifted Windows Persian. The running app reads the complete mapping,
# including Shift and Standard Persian, from Windows instead.
EN_TO_FA = dict(zip(
    "qwertyuiop[]asdfghjkl;'zxcvbnm,./\\`",
    "ضصثقفغعهخحجچشسیبلاتنمکگظطزرذدئو./پ÷",
))


def reverse_mapping(mapping: Mapping[str, str]) -> dict[str, str]:
    reverse = {}
    for source, destination in mapping.items():
        # Prefer unshifted keys. Do not collapse an ordinary word like ریال
        # into a single key just because Windows also provides a ligature.
        if len(destination) == 1:
            reverse.setdefault(destination, source)
    for variant, canonical in (("ي", "ی"), ("ك", "ک")):
        if canonical in reverse:
            reverse[variant] = reverse[canonical]
    return reverse


FA_TO_EN = reverse_mapping(EN_TO_FA)


def convert_text(text: str, mapping: Mapping[str, str] | None = None) -> str:
    """Infer direction from letters; preserve whitespace and unknown characters.

    The dominant recognized script wins for mixed selections. Ties use the
    first recognized letter. Shared punctuation never determines direction.
    Uppercase keys in the complete mapping represent Shift, as on Windows.
    """
    forward = EN_TO_FA if mapping is None else mapping
    backward = reverse_mapping(forward)
    evidence = []
    for char in text:
        if char.isalpha():
            if char in forward and char not in backward:
                evidence.append(1)
            elif char in backward and char not in forward:
                evidence.append(-1)
    if not evidence:
        for char in text:
            if char in forward and char not in backward:
                evidence.append(1)
            elif char in backward and char not in forward:
                evidence.append(-1)
    if not evidence:
        return text
    score = sum(evidence)
    direction = score if score else evidence[0]
    table = forward if direction > 0 else backward
    return "".join(table.get(char, char) for char in text)
