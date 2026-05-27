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
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def generate_tips(prediction) -> dict:
    age = 2026 - prediction.year_built

    if prediction.property_type == "Apartment":
        type_note = (
            "This is an APARTMENT — suggest only interior renovations: "
            "Kitchen, Bathroom, Flooring, Smart Home, Lighting, Insulation. "
            "Do NOT suggest structural changes, garden, attic, or pool."
        )
    else:
        type_note = (
            "This is a HOUSE or VILLA — all renovation types are eligible: "
            "interior (Kitchen, Bathroom, Flooring, Smart Home, Lighting, Insulation) "
            "and exterior (Garden, Exterior, Parking, Pool)."
        )

    prompt = (
        "You are a senior real estate investment advisor with deep knowledge of renovation costs and ROI. "
        "Generate 4–6 renovation recommendations that would realistically and meaningfully increase this "
        "property's market value. Base cost estimates on real 2024–2025 US market prices.\n\n"
        f"{type_note}\n\n"
        f"Property context:\n"
        f"  Type: {prediction.property_type}\n"
        f"  Location: {prediction.location}\n"
        f"  Floor area: {prediction.floor_area} m²\n"
        f"  Bedrooms: {prediction.bedrooms}, Year built: {prediction.year_built} (~{age} years old)\n"
        f"  Current estimated value: ${prediction.prediction_value:,}\n"
        f"  Has parking: {prediction.has_parking}, Has pool: {prediction.has_pool}, "
        f"Has balcony: {prediction.has_balcony}\n\n"
        "For each tip you MUST provide:\n"
        "- A specific, actionable description (not generic — say exactly what to replace/install/upgrade)\n"
        "- A concrete product or brand example (e.g. 'IKEA SEKTION cabinets', 'Nest Learning Thermostat', "
        "'LVP flooring from Home Depot')\n"
        "- A realistic cost range in USD based on the property size\n"
        "- The estimated value added to the property\n"
        "- ROI as a percentage: (value_added / cost_max * 100), rounded to nearest 5\n"
        "- A practical resource hint — either a well-known platform (Houzz, Angi, HomeAdvisor, IKEA, "
        "Home Depot, Wayfair) or a search tip (e.g. 'Search \"LVP flooring installer near me\" on Angi')\n\n"
        "Return ONLY a valid JSON object — no markdown, no extra text:\n"
        "{\n"
        '  "total_investment_min": <integer: sum of all cost_min>,\n'
        '  "total_investment_max": <integer: sum of all cost_max>,\n'
        '  "potential_value_gain": <integer: sum of all value_added>,\n'
        '  "tips": [\n'
        "    {\n"
        '      "category": "<Kitchen|Bathroom|Flooring|Smart Home|Exterior|Garden|Lighting|Insulation|Parking>",\n'
        '      "action": "<specific renovation description — what exactly to do>",\n'
        '      "example": "<concrete product/brand/service example>",\n'
        '      "resource": "<platform name or search tip, e.g. Houzz.com · Search kitchen remodel contractors>",\n'
        '      "cost_min": <integer USD>,\n'
        '      "cost_max": <integer USD>,\n'
        '      "value_added": <integer USD>,\n'
        '      "roi_percent": <integer: value_added / cost_max * 100, rounded to nearest 5>\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    response = _client().chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=1400,
        temperature=0.2,
    )
    return json.loads(response.choices[0].message.content)
