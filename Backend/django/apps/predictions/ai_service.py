import json
from django.conf import settings


def _client():
    from openai import OpenAI
    return OpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL,
    )


def generate_explanation(prediction) -> str:
    factors_str = "\n".join(
        f"  - {k}: {v:.1f}%"
        for k, v in (prediction.price_factors or {}).items()
    )
    features = [
        label
        for flag, label in [
            (prediction.has_parking,  "parking garage"),
            (prediction.has_pool,     "swimming pool"),
            (prediction.has_balcony,  "balcony/terrace"),
            (prediction.has_elevator, "elevator"),
        ]
        if flag
    ]
    features_str = ", ".join(features) if features else "none"

    prompt = (
        "You are a real estate expert. A machine learning model estimated the market value of a property. "
        "Based on the details and price factors below, write a clear 2–3 sentence explanation of why the "
        "property was estimated at this price. Be specific, mention the most impactful factors, and use "
        "a professional but accessible tone. Write only the explanation, no preamble.\n\n"
        f"Property Details:\n"
        f"  Type: {prediction.property_type}\n"
        f"  Location: {prediction.location}\n"
        f"  Floor area: {prediction.floor_area} m²\n"
        f"  Bedrooms: {prediction.bedrooms}, Bathrooms: {prediction.bathrooms}\n"
        f"  Year built: {prediction.year_built}\n"
        f"  Features: {features_str}\n\n"
        f"Estimated price: ${prediction.prediction_value:,}\n"
        f"Model confidence: {prediction.confidence * 100:.0f}%\n\n"
        f"Key price factors (contribution %):\n"
        f"{factors_str if factors_str else '  No detailed factors available'}"
    )

    response = _client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=250,
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()


def generate_tips(prediction) -> dict:
    if prediction.property_type == "Apartment":
        type_note = (
            "This is an APARTMENT. Only suggest interior renovations: "
            "Kitchen, Bathroom, Flooring, Smart Home, Lighting, Insulation. "
            "Do NOT suggest exterior structural changes, garden additions, attic conversions, or pool installations."
        )
    else:
        type_note = (
            "This is a HOUSE or VILLA. All renovation types are eligible: "
            "interior (Kitchen, Bathroom, Flooring, Smart Home, Lighting, Insulation) "
            "and exterior (Garden, Exterior, Parking, Pool)."
        )

    prompt = (
        "You are a real estate investment advisor. Generate 4–6 specific renovation tips that would "
        "meaningfully increase this property's market value.\n\n"
        f"{type_note}\n\n"
        f"Property:\n"
        f"  Type: {prediction.property_type}\n"
        f"  Location: {prediction.location}\n"
        f"  Floor area: {prediction.floor_area} m²\n"
        f"  Bedrooms: {prediction.bedrooms}, Year built: {prediction.year_built}\n"
        f"  Current estimated value: ${prediction.prediction_value:,}\n"
        f"  Has parking: {prediction.has_parking}, Has pool: {prediction.has_pool}, "
        f"Has balcony: {prediction.has_balcony}\n\n"
        "Return ONLY a valid JSON object — no markdown, no extra text:\n"
        "{\n"
        '  "total_investment_min": <integer: sum of all cost_min>,\n'
        '  "total_investment_max": <integer: sum of all cost_max>,\n'
        '  "potential_value_gain": <integer: sum of all value_added>,\n'
        '  "tips": [\n'
        "    {\n"
        '      "category": "<Kitchen|Bathroom|Flooring|Smart Home|Exterior|Garden|Lighting|Insulation|Parking>",\n'
        '      "action": "<specific actionable renovation in 1–2 sentences>",\n'
        '      "cost_min": <integer USD>,\n'
        '      "cost_max": <integer USD>,\n'
        '      "value_added": <integer USD>\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    response = _client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=900,
        temperature=0.3,
    )
    return json.loads(response.choices[0].message.content)
