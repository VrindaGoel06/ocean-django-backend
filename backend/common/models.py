from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.postgres.indexes import GistIndex
from django.contrib.postgres.fields import ArrayField


class TimeStampedModel(models.Model):
    """Abstract base class that adds created_at and updated_at fields to models."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class hazardSet(models.IntegerChoices):
    UNKNOWN = 0
    TIDE = 1
    COASTAL_DAMAGE = 2
    FLOODING = 3
    WAVES = 4
    SWELL = 5
    SURGE = 6
    STORM = 7
    TSUNAMI = 8
    OTHER = 9


class actionStatusSet(models.IntegerChoices):
    TO_BE_STARTED = 0
    IN_PROGRESS = 1
    NEXT_STAGE = 2
    FINISH = 3


class verificationStatusSet(models.IntegerChoices):
    DISCARDED = -2
    NOT_SEVERE = -1
    NOT_SYSTEM_PROCESSED = 0
    NOT_ACKNOWLEDGED = 1
    IN_PROGRESS = 2
    PERSONNEL_UNCONFIRMED = 3
    VERIFIED = 4


class GeoVideo(TimeStampedModel):
    device_model = models.CharField(max_length=255, blank=True)  # e.g., "iPhone 14 Pro"
    software_info = models.CharField(
        max_length=255, blank=True
    )  # e.g., "iOS Camera v17.2"

    # Geospatial data
    location = gis_models.PointField(geography=True)  # WGS84 lat/lon
    altitude = models.FloatField(null=True, blank=True)  # meters
    gps_accuracy = models.FloatField(null=True, blank=True)  # meters (1σ or 95%)
    speed = models.FloatField(null=True, blank=True)  # m/s
    direction = models.FloatField(null=True, blank=True)  # degrees (0–360)
    gps_fix_type = models.CharField(
        max_length=50, blank=True, null=True
    )  # "2D", "3D", "DGPS", "RTK"
    num_satellites = models.IntegerField(null=True, blank=True)
    timestamp_utc = models.DateTimeField()  # GPS-synced UTC

    # Orientation snapshot (optional quick-look)
    orientation_roll = models.FloatField(null=True, blank=True)  # deg
    orientation_pitch = models.FloatField(null=True, blank=True)  # deg
    orientation_yaw = models.FloatField(null=True, blank=True)  # deg

    # Camera metadata
    resolution = models.CharField(max_length=50, blank=True, null=True)  # "3840x2160"
    frame_rate = models.FloatField(null=True, blank=True)  # fps
    aperture = models.FloatField(null=True, blank=True)  # f-stop
    iso = models.IntegerField(null=True, blank=True)
    lens = models.CharField(max_length=100, blank=True, null=True)

    # ---- Batch sensor data (Downsampled & Synchronized to ≤10Hz) ----
    # Each reading is [x, y, z, t] with t = seconds since video start
    accelerometer = ArrayField(
        ArrayField(models.FloatField(), size=4), default=list, blank=True, null=True
    )
    gyroscope = ArrayField(
        ArrayField(models.FloatField(), size=4), default=list, blank=True, null=True
    )
    magnetometer = ArrayField(
        ArrayField(models.FloatField(), size=4), default=list, blank=True, null=True
    )
    # [pressure_hPa, t]
    barometer = ArrayField(
        ArrayField(models.FloatField(), size=2), default=list, blank=True, null=True
    )
    # [roll, pitch, yaw, t]
    orientation_series = ArrayField(
        ArrayField(models.FloatField(), size=4), default=list, blank=True, null=True
    )

    # Summary stats for fast filtering (computed from downsampled arrays)
    accel_min = models.FloatField(null=True, blank=True)
    accel_max = models.FloatField(null=True, blank=True)
    accel_mean = models.FloatField(null=True, blank=True)

    gyro_min = models.FloatField(null=True, blank=True)
    gyro_max = models.FloatField(null=True, blank=True)
    gyro_mean = models.FloatField(null=True, blank=True)

    mag_min = models.FloatField(null=True, blank=True)
    mag_max = models.FloatField(null=True, blank=True)
    mag_mean = models.FloatField(null=True, blank=True)

    baro_min = models.FloatField(null=True, blank=True)
    baro_max = models.FloatField(null=True, blank=True)
    baro_mean = models.FloatField(null=True, blank=True)

    duration_sec = models.FloatField(null=True, blank=True)  # video duration in seconds
    video_file = models.FileField(upload_to="report_videos/")
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta(TimeStampedModel.Meta):
        indexes = [
            models.Index(fields=["timestamp_utc"], name="geovideo_ts_idx"),
            models.Index(fields=["recorded_at"], name="geovideo_recorded_idx"),
            GistIndex(fields=["location"], name="geovideo_location_gix"),
        ]

    def __str__(self):
        return f"GPS data @ {self.timestamp_utc.isoformat()}"
