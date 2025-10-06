def coerce_amount(raw, round_to=0):
    if raw is None: 
        return None
    s = str(raw).strip().replace(",", "")
    for prefix in ("$", "NZD", "USD", "AUD", "EUR"):
        if s.upper().startswith(prefix): 
            s = s[len(prefix):].strip()
    try:
        val = float(s)
        if round_to is not None:
            q = 10 ** max(0, int(round_to))
            val = round(val * q) / q
        return val
    except Exception:
        return None
