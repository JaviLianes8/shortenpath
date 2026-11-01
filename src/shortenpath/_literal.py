"""Linear matching of nonoverlapping literal separator runs."""

from __future__ import annotations

from collections.abc import Iterator


def literal_runs(text: str, sep: str) -> Iterator[tuple[int, int]]:
    # Prefix links avoid retrying a long almost-matching separator at every position.
    links = [0] * len(sep)
    matched = 0
    for index in range(1, len(sep)):
        while matched and sep[index] != sep[matched]:
            matched = links[matched - 1]
        if sep[index] == sep[matched]:
            matched += 1
        links[index] = matched

    matched = 0
    start = end = -1
    for index, char in enumerate(text):
        while matched and char != sep[matched]:
            matched = links[matched - 1]
        if char == sep[matched]:
            matched += 1
        if matched == len(sep):
            begin = index + 1 - len(sep)
            if begin != end:
                if end != -1:
                    yield start, end
                start = begin
            end = index + 1
            # Separator occurrences cannot overlap, even when the literal repeats itself.
            matched = 0
    if end != -1:
        yield start, end
