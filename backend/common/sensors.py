import numpy as np
from typing import List, Dict, Optional, Tuple
from .models import GeoVideo

Reading = List[float]  # [x,y,z,t] or [v,t]
Series = List[Reading]
RawStreams = Dict[str, Series]


def _vector_magnitude(series_xyz: Series) -> List[float]:
    """Compute vector magnitudes from [x,y,z,t] arrays."""
    arr = np.array([r[:3] for r in series_xyz if len(r) >= 3], dtype=float)
    if arr.size == 0:
        return []
    return np.linalg.norm(arr, axis=1).tolist()


def _scalar_values(series_scalar: Series) -> List[float]:
    """Extract scalar values [v,t] -> v."""
    return [float(r[0]) for r in series_scalar if len(r) >= 1]


def _stats(
    values: List[float],
) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    """Return (min, max, mean) for a list of values."""
    if not values:
        return None, None, None
    arr = np.array(values, dtype=float)
    return float(np.min(arr)), float(np.max(arr)), float(np.mean(arr))


def process_and_store_sensors(
    geovideo: GeoVideo,
    raw_streams: RawStreams,
    duration_sec: Optional[float],
) -> None:
    """
    Store downsampled sensor streams (already ≤10Hz from frontend),
    compute summary stats, and save into GeoVideo.
    """
    geovideo.duration_sec = duration_sec

    # Save arrays (frontend already downsampled)
    geovideo.accelerometer = [
        list(map(float, r)) for r in raw_streams.get("accelerometer", [])
    ]
    geovideo.gyroscope = [list(map(float, r)) for r in raw_streams.get("gyroscope", [])]
    geovideo.magnetometer = [
        list(map(float, r)) for r in raw_streams.get("magnetometer", [])
    ]
    geovideo.barometer = [list(map(float, r)) for r in raw_streams.get("barometer", [])]
    geovideo.orientation_series = [
        list(map(float, r)) for r in raw_streams.get("orientation_series", [])
    ]

    # Compute stats
    geovideo.accel_min, geovideo.accel_max, geovideo.accel_mean = _stats(
        _vector_magnitude(geovideo.accelerometer)
    )
    geovideo.gyro_min, geovideo.gyro_max, geovideo.gyro_mean = _stats(
        _vector_magnitude(geovideo.gyroscope)
    )
    geovideo.mag_min, geovideo.mag_max, geovideo.mag_mean = _stats(
        _vector_magnitude(geovideo.magnetometer)
    )
    geovideo.baro_min, geovideo.baro_max, geovideo.baro_mean = _stats(
        _scalar_values(geovideo.barometer)
    )

    geovideo.save()
