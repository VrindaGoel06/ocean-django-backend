from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from hazards.models import UserReport
import json
from common.models import hazardSet, actionStatusSet, verificationStatusSet
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt


@swagger_auto_schema(
    method="get",
    operation_description="Get GeoVideos + UserReports as GeoJSON FeatureCollection",
    responses={
        200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "type": openapi.Schema(
                    type=openapi.TYPE_STRING, example="FeatureCollection"
                ),
                "features": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "type": openapi.Schema(
                                type=openapi.TYPE_STRING, example="Feature"
                            ),
                            "geometry": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                example={
                                    "type": "Point",
                                    "coordinates": [12.49, 41.89],
                                },
                            ),
                            "properties": openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                    "type": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="Hazard type enum",
                                        enum=[c.value for c in hazardSet],
                                        example=hazardSet.TSUNAMI,
                                    ),
                                    "severity": openapi.Schema(
                                        type=openapi.TYPE_INTEGER, example=70
                                    ),
                                    "confidence": openapi.Schema(
                                        type=openapi.TYPE_INTEGER, example=60
                                    ),
                                    "verification": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="Verification status enum",
                                        enum=[c.value for c in verificationStatusSet],
                                        example=verificationStatusSet.VERIFIED,
                                    ),
                                    "action_status": openapi.Schema(
                                        type=openapi.TYPE_INTEGER,
                                        description="Action status enum",
                                        enum=[c.value for c in actionStatusSet],
                                        example=actionStatusSet.IN_PROGRESS,
                                    ),
                                    "created_at": openapi.Schema(
                                        type=openapi.TYPE_STRING,
                                        format="date-time",
                                        example="2025-09-23T12:34:56Z",
                                    ),
                                },
                            ),
                        },
                    ),
                ),
            },
        )
    },
)
@api_view(["GET"])
def geovideos_geojson(request):
    features = []
    for report in UserReport.objects.select_related("geovideo").iterator():
        geojson = json.loads(report.geovideo.location.geojson)
        features.append(
            {
                "type": "Feature",
                "geometry": geojson,
                "properties": {
                    "id": report.pk,
                    "type": report.type or report.user_submit_type,  # hazardSet int
                    "severity": report.severity or 60,
                    "confidence": report.confidence or 60,
                    "verification": report.verification,  # verificationStatusSet int
                    "action_status": report.action_status,  # actionStatusSet int
                    "desc": report.user_text,
                    "created_at": report.created_at.isoformat(),
                },
            }
        )

    return Response({"type": "FeatureCollection", "features": features})


@xframe_options_exempt
def render_map(request):
    return render(request, "map.html")
