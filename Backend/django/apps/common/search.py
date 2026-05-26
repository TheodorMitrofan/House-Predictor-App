"""
Standardized list-search contract shared by every paginated list endpoint.

Request body (POST .../search/):
    {
      "filters":    [{ "field": str, "operator": "eq"|"contains", "value": any }],
      "sorters":    [{ "field": str, "direction": "asc"|"desc" }],
      "pagination": { "page": int >= 1, "pageSize": int 1..200 }
    }

Response body:
    {
      "results": [ ... ],
      "pagination": {
        "page": int, "pageSize": int,
        "totalElements": int, "totalPages": int
      }
    }

Filter semantics: combined with AND. Unknown/unauthorized fields are silently
dropped — each view supplies its own allowlist.
"""
from rest_framework import serializers
from rest_framework.response import Response


class FilterSerializer(serializers.Serializer):
    field = serializers.CharField()
    operator = serializers.ChoiceField(choices=["eq", "contains"], default="eq")
    value = serializers.JSONField(allow_null=True)


class SorterSerializer(serializers.Serializer):
    field = serializers.CharField()
    direction = serializers.ChoiceField(choices=["asc", "desc"], default="asc")


class PaginationSerializer(serializers.Serializer):
    page = serializers.IntegerField(min_value=1, default=1)
    pageSize = serializers.IntegerField(min_value=1, max_value=200, default=20)


class SearchSerializer(serializers.Serializer):
    filters = FilterSerializer(many=True, required=False, default=list)
    sorters = SorterSerializer(many=True, required=False, default=list)
    pagination = PaginationSerializer(required=False, default=dict)


def apply_search(qs, validated, *, allowed_eq, allowed_contains, allowed_sort):
    """Apply AND-ed filters then sorters. Unknown fields are ignored."""
    for f in validated.get("filters", []):
        field, op, val = f["field"], f["operator"], f["value"]
        if op == "eq" and field in allowed_eq:
            qs = qs.filter(**{field: val})
        elif op == "contains" and field in allowed_contains and val is not None:
            qs = qs.filter(**{f"{field}__icontains": val})

    order = []
    for s in validated.get("sorters", []):
        if s["field"] in allowed_sort:
            order.append(("-" if s["direction"] == "desc" else "") + s["field"])
    if order:
        qs = qs.order_by(*order)
    return qs


def paginated_response(qs, validated, serializer_class, context=None):
    pag = validated.get("pagination") or {}
    page = pag.get("page", 1)
    page_size = pag.get("pageSize", 20)

    total = qs.count()
    start = (page - 1) * page_size
    end = start + page_size

    results = serializer_class(qs[start:end], many=True, context=context or {}).data
    return Response({
        "results": results,
        "pagination": {
            "page": page,
            "pageSize": page_size,
            "totalElements": total,
            "totalPages": max((total + page_size - 1) // page_size, 1),
        },
    })
