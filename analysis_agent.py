def analyze(predictions):

    count = len(predictions)

    # ---------------------------
    # SEVERITY LOGIC
    # ---------------------------
    if count == 0:
        severity = "No Damage"

    elif count <= 2:
        severity = "Minor"

    elif count <= 5:
        severity = "Moderate"

    else:
        severity = "Severe"

    # ---------------------------
    # ADDITIONAL INSIGHT (bonus)
    # ---------------------------
    avg_confidence = 0

    if count > 0:
        avg_confidence = sum([p.get("confidence", 0) for p in predictions]) / count

    return {
        "damage_count": count,
        "severity": severity,
        "avg_confidence": round(avg_confidence, 2)
    }