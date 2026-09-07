import math


NEG_INF = float("-inf")


def _logadd(*values):
    values = [v for v in values if v != NEG_INF]
    if not values:
        return NEG_INF
    top = max(values)
    return top + math.log(sum(math.exp(v - top) for v in values))


def greedy_decode(charsets, rows):
    text = []
    confidences = []
    last_index = None
    last_char = ""
    run_best = 0.0
    for row in rows:
        if not row:
            continue
        index = max(range(len(row)), key=lambda i: row[i])
        char = charsets[index]
        value = max(float(row[index]), 0.0)
        if index == last_index:
            run_best = max(run_best, value)
            continue
        if last_index is not None and last_char:
            text.append(last_char)
            confidences.append(run_best)
        last_index = index
        last_char = char
        run_best = value
    if last_index is not None and last_char:
        text.append(last_char)
        confidences.append(run_best)
    score = 0.0
    if confidences:
        score = math.exp(sum(math.log(max(v, 1e-12)) for v in confidences) / len(confidences))
    return "".join(text), score, confidences


def exact_prefix_beam_decode(charsets, rows, expected_length=4, beam_width=12, top_chars=10):
    """Small CTC prefix beam constrained to the known captcha length."""
    if not rows:
        return "", 0.0, []
    blank_indices = [i for i, char in enumerate(charsets) if char == ""]
    blank = blank_indices[-1] if blank_indices else 0
    beams = {"": (0.0, NEG_INF)}
    used_steps = 0
    for row in rows:
        if not row:
            continue
        used_steps += 1
        ranked = sorted(range(len(row)), key=lambda i: row[i], reverse=True)[:max(2, int(top_chars))]
        if blank not in ranked:
            ranked.append(blank)
        next_beams = {}
        for prefix, (prob_blank, prob_nonblank) in beams.items():
            total = _logadd(prob_blank, prob_nonblank)
            for index in ranked:
                value = math.log(max(float(row[index]), 1e-12))
                char = charsets[index]
                old_blank, old_nonblank = next_beams.get(prefix, (NEG_INF, NEG_INF))
                if index == blank or char == "":
                    next_beams[prefix] = (_logadd(old_blank, total + value), old_nonblank)
                    continue
                if prefix and char == prefix[-1]:
                    next_beams[prefix] = (old_blank, _logadd(old_nonblank, prob_nonblank + value))
                    if len(prefix) < expected_length:
                        extended = prefix + char
                        eb, en = next_beams.get(extended, (NEG_INF, NEG_INF))
                        next_beams[extended] = (eb, _logadd(en, prob_blank + value))
                elif len(prefix) < expected_length:
                    extended = prefix + char
                    eb, en = next_beams.get(extended, (NEG_INF, NEG_INF))
                    next_beams[extended] = (eb, _logadd(en, total + value))
        beams = dict(
            sorted(
                next_beams.items(),
                key=lambda item: _logadd(item[1][0], item[1][1]),
                reverse=True,
            )[:max(2, int(beam_width))]
        )
    exact = [(p, v) for p, v in beams.items() if len(p) == expected_length]
    choices = exact or list(beams.items())
    if not choices:
        return "", 0.0, []
    prefix, pair = max(choices, key=lambda item: _logadd(item[1][0], item[1][1]))
    log_score = _logadd(pair[0], pair[1])
    score = math.exp(log_score / max(used_steps, 1)) if log_score != NEG_INF else 0.0
    return prefix, min(max(score, 0.0), 1.0), []


def decode_probability(result, expected_length=4, decoder="exact_beam", beam_width=12):
    charsets = result.get("charsets") or []
    rows = result.get("probability") or []
    if rows and isinstance(rows[0], (int, float)):
        rows = [rows]
    if decoder == "greedy":
        return greedy_decode(charsets, rows)
    return exact_prefix_beam_decode(
        charsets,
        rows,
        expected_length=max(1, int(expected_length)),
        beam_width=max(2, int(beam_width)),
    )
