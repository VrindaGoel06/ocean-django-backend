from rest_framework import views, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from common.models import GeoVideo
from .models import UserReport
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import json

from common.sensors import process_and_store_sensors

geovideo_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "device_model": openapi.Schema(
            type=openapi.TYPE_STRING, description="Device model, if available"
        ),
        "software_info": openapi.Schema(
            type=openapi.TYPE_STRING, description="Software/app info, if available"
        ),
        "location": openapi.Schema(
            type=openapi.TYPE_STRING,
            description="WKT format string, e.g. 'POINT(-73.985 40.748)'",
        ),
        "altitude": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "gps_accuracy": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "speed": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            format="float",
            nullable=True,
            description="Device speed in m/s (from geolocation). May be null if not provided by browser.",
        ),
        "direction": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            format="float",
            nullable=True,
            description="Heading/bearing in degrees. May be null if not provided by browser.",
        ),
        "gps_fix_type": openapi.Schema(
            type=openapi.TYPE_STRING,
            nullable=True,
            description="GPS fix type (2D, 3D, DGPS, RTK). Not available in browser, always null.",
        ),
        "num_satellites": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            nullable=True,
            description="Number of satellites. Not available in browser, always null.",
        ),
        "timestamp_utc": openapi.Schema(type=openapi.TYPE_STRING, format="date-time"),
        # Orientation snapshot
        "orientation_roll": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "orientation_pitch": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "orientation_yaw": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        # Camera metadata
        "resolution": openapi.Schema(
            type=openapi.TYPE_STRING,
            nullable=True,
            description="Video resolution (e.g., 1920x1080). May be null if browser cannot determine.",
        ),
        "frame_rate": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            format="float",
            nullable=True,
            description="Video frame rate (fps). May be null if browser cannot determine.",
        ),
        "aperture": openapi.Schema(
            type=openapi.TYPE_NUMBER,
            format="float",
            nullable=True,
            description="Camera aperture (f-stop). Not exposed by browsers.",
        ),
        "iso": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            nullable=True,
            description="ISO sensitivity. Not exposed by browsers.",
        ),
        "lens": openapi.Schema(
            type=openapi.TYPE_STRING,
            nullable=True,
            description="Lens info. Not exposed by browsers.",
        ),
        # Sensor arrays
        "accelerometer": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="Array of [x,y,z,t]. t = seconds since start.",
            items=openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_NUMBER)
            ),
        ),
        "gyroscope": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="Array of [alpha,beta,gamma,t]. May be empty if not supported.",
            items=openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_NUMBER)
            ),
        ),
        "magnetometer": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="Array of [x,y,z,t]. May be empty if device/browser doesn’t expose Magnetometer API.",
            items=openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_NUMBER)
            ),
        ),
        "barometer": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="Array of [pressure_hPa,t]. May be empty if device/browser doesn’t expose Barometer API.",
            items=openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_NUMBER)
            ),
        ),
        "orientation_series": openapi.Schema(
            type=openapi.TYPE_ARRAY,
            description="Array of [roll,pitch,yaw,t].",
            items=openapi.Schema(
                type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_NUMBER)
            ),
        ),
        # Pre-computed stats
        "accel_min": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "accel_max": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "accel_mean": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "gyro_min": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "gyro_max": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "gyro_mean": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "mag_min": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "mag_max": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "mag_mean": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "baro_min": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "baro_max": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "baro_mean": openapi.Schema(
            type=openapi.TYPE_NUMBER, format="float", nullable=True
        ),
        "duration_sec": openapi.Schema(type=openapi.TYPE_NUMBER, format="float"),
    },
    required=["timestamp_utc"],
)

client_info_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "userAgent": openapi.Schema(type=openapi.TYPE_STRING),
        "platform": openapi.Schema(type=openapi.TYPE_STRING),
        "language": openapi.Schema(type=openapi.TYPE_STRING),
    },
)


class UserReportCreateView(views.APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @swagger_auto_schema(
        operation_description="Submit a hazard report with video + GeoVideo sensor data",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "user_submit_type": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Hazard type"
                ),
                "user_text": openapi.Schema(
                    type=openapi.TYPE_STRING, description="User text"
                ),
                "user_video": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format=openapi.FORMAT_BINARY,
                    description="Video file",
                ),
                "geovideo": geovideo_schema,
                "client_info": client_info_schema,
            },
            required=["user_submit_type", "user_text", "user_video", "geovideo"],
        ),
        responses={201: openapi.Response("Created")},
    )
    def post(self, request, *args, **kwargs):
        # validate only the simple fields, not nested geovideo
        basic_fields = {
            "user_submit_type": request.data.get("user_submit_type"),
            "user_text": request.data.get("user_text"),
            "user_video": request.data.get("user_video"),
        }
        if not all(basic_fields.values()):
            return Response(
                {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
            )

        geovideo_data = request.data.get("geovideo")
        client_info = request.data.get("client_info")

        if isinstance(geovideo_data, str):
            geovideo_data = json.loads(geovideo_data)
        if isinstance(client_info, str):
            client_info = json.loads(client_info)

        user_video = request.data.get("user_video")

        geovideo = GeoVideo.objects.create(
            video_file=user_video,
            device_model=geovideo_data.get("device_model", ""),
            software_info=geovideo_data.get("software_info", ""),
            location=geovideo_data.get("location"),
            altitude=geovideo_data.get("altitude"),
            gps_accuracy=geovideo_data.get("gps_accuracy"),
            speed=geovideo_data.get("speed"),
            direction=geovideo_data.get("direction"),
            gps_fix_type=geovideo_data.get("gps_fix_type"),
            num_satellites=geovideo_data.get("num_satellites"),
            timestamp_utc=geovideo_data.get("timestamp_utc"),
            orientation_roll=geovideo_data.get("orientation_roll"),
            orientation_pitch=geovideo_data.get("orientation_pitch"),
            orientation_yaw=geovideo_data.get("orientation_yaw"),
            resolution=geovideo_data.get("resolution"),
            frame_rate=geovideo_data.get("frame_rate"),
            aperture=geovideo_data.get("aperture"),
            iso=geovideo_data.get("iso"),
            lens=geovideo_data.get("lens"),
            duration_sec=geovideo_data.get("duration_sec"),
        )

        # Process and save sensors
        process_and_store_sensors(
            geovideo,
            raw_streams=geovideo_data,
            duration_sec=geovideo_data.get("duration_sec"),
        )

        report = UserReport.objects.create(
            geovideo=geovideo,
            user_submit_type=basic_fields["user_submit_type"],
            user_text=basic_fields["user_text"],
            user_ip=request.META.get(
                "HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR")
            ),
            user_userAgent=client_info.get("userAgent", ""),
            user_platform=client_info.get("platform", ""),
            user_device_language=client_info.get("language", ""),
            user=request.user if request.user.is_authenticated else None,
        )

        return Response(
            {"id": report.pk, "status": "created"}, status=status.HTTP_201_CREATED
        )
