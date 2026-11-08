"""Editable time-of-day assumptions for the eight HKU canteens.

These curves are empirical planning defaults, not measured calibration or live
queue observations. The historical application's baseline of eight people is
retained at each canteen. Replace the profile values after collecting timed
headcounts; synthetic tests verify behavior, not real-world accuracy.
"""

from datetime import date, datetime, time, timedelta, timezone
import math


# HK has no seasonal clock changes. A fixed offset also works on Windows without
# an external tzdata installation and never depends on the server's timezone.
HK_TIMEZONE = timezone(timedelta(hours=8), "Asia/Hong_Kong")

STALL_RATES = {
    "CYM Canteen (Chong Yuet Ming Cultural Centre)": {"rate_min_per_person": 0.8},
    "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": {"rate_min_per_person": 0.6},
    "Union Restaurant (Haking Wong Building)": {"rate_min_per_person": 0.8},
    "alfafa bistro (Jockey Club Tower, Centennial Campus)": {"rate_min_per_person": 1.2},
    "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": {"rate_min_per_person": 1.0},
    "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": {"rate_min_per_person": 1.5},
    "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": {"rate_min_per_person": 1.5},
    "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": {"rate_min_per_person": 2.0},
}

CAMPUS_LOCATIONS = [
    "Main Building",
    "Chong Yuet Ming Cultural Centre",
    "Run Run Shaw Building",
    "Centennial Campus (Grand Hall)",
    "Haking Wong Building",
    "Knowles Building",
    "KKL Building",
]

# The ordering matches STALL_RATES. Each entry is (lunch peak, dinner peak).
# These provisional factors express different demand patterns, not observations.
_PEAK_WEIGHTS = (
    (2.0, 1.5), (1.8, 1.4), (2.2, 1.6), (1.7, 1.5),
    (2.0, 1.8), (1.8, 2.0), (1.9, 1.7), (1.6, 1.9),
)
TEMPORAL_PROFILES = {
    name: {
        "baseline_people": 8.0,
        "off_peak_weight": 0.4,
        "lunch_peak_weight": weights[0],
        "dinner_peak_weight": weights[1],
    }
    for name, weights in zip(STALL_RATES, _PEAK_WEIGHTS)
}

# Minutes since midnight and normalized lunch/dinner intensity. Linear
# interpolation avoids abrupt jumps at the proposal's observation windows.
# Lunch ramps from 11:30, peaks at 12:00-12:30 and tails off after 13:30.
# Dinner ramps from 17:30, peaks at 18:00 and tails off by 19:30.
TIME_CURVE_KNOTS = (
    (0, 0.0, 0.0),
    (660, 0.0, 0.0),   # 11:00
    (690, 0.2, 0.0),   # 11:30
    (710, 0.7, 0.0),   # 11:50
    (720, 1.0, 0.0),   # 12:00
    (750, 1.0, 0.0),   # 12:30
    (770, 0.7, 0.0),   # 12:50
    (810, 0.2, 0.0),   # 13:30
    (870, 0.0, 0.0),   # 14:30
    (1020, 0.0, 0.0),  # 17:00
    (1050, 0.0, 0.4),  # 17:30
    (1080, 0.0, 1.0),  # 18:00
    (1110, 0.0, 0.8),  # 18:30
    (1140, 0.0, 0.4),  # 19:00
    (1170, 0.0, 0.0),  # 19:30
    (1440, 0.0, 0.0),
)


def hong_kong_time(dining_time=None):
    """Return HK wall-clock time; naive time/datetime values already mean HK."""
    if dining_time is None:
        return datetime.now(HK_TIMEZONE).time()
    if isinstance(dining_time, datetime):
        if dining_time.tzinfo is not None:
            dining_time = dining_time.astimezone(HK_TIMEZONE)
        return dining_time.time()
    if isinstance(dining_time, time):
        if dining_time.tzinfo is not None:
            return datetime.combine(date(2000, 1, 1), dining_time).astimezone(HK_TIMEZONE).time()
        return dining_time
    raise TypeError("dining_time must be a datetime.time or datetime.datetime")


def _intensities(dining_time=None):
    local_time = hong_kong_time(dining_time)
    minute = local_time.hour * 60 + local_time.minute + local_time.second / 60 + local_time.microsecond / 60_000_000
    for left, right in zip(TIME_CURVE_KNOTS, TIME_CURVE_KNOTS[1:]):
        if left[0] <= minute <= right[0]:
            ratio = (minute - left[0]) / (right[0] - left[0])
            return tuple(left[i] + ratio * (right[i] - left[i]) for i in (1, 2))
    raise ValueError("Time is outside the daily calibration curve")


def queue_multiplier(canteen, dining_time=None):
    """Return the assumed demand weight at the selected HK dining time."""
    if canteen not in TEMPORAL_PROFILES:
        raise ValueError(f"Unknown canteen: {canteen}")
    profile = TEMPORAL_PROFILES[canteen]
    lunch, dinner = _intensities(dining_time)
    off_peak = profile["off_peak_weight"]
    return (
        off_peak
        + lunch * (profile["lunch_peak_weight"] - off_peak)
        + dinner * (profile["dinner_peak_weight"] - off_peak)
    )


def estimated_queue_count(canteen, dining_time=None):
    """Return a fractional planning headcount, never a live count."""
    weight = queue_multiplier(canteen, dining_time)
    return TEMPORAL_PROFILES[canteen]["baseline_people"] * weight


def estimate_wait_minutes(canteen, people_count=None, dining_time=None, rate_min_per_person=None):
    """Use an observed count when supplied, otherwise the temporal assumption.

    Observed/manual counts are not multiplied by demand again. The service rate
    remains an empirical minutes-per-person estimate, not a measured guarantee.
    """
    if canteen not in STALL_RATES:
        raise ValueError(f"Unknown canteen: {canteen}")
    count = estimated_queue_count(canteen, dining_time) if people_count is None else people_count
    rate = STALL_RATES[canteen]["rate_min_per_person"] if rate_min_per_person is None else rate_min_per_person
    for label, value in (("people_count", count), ("rate_min_per_person", rate)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError(f"{label} must be a finite non-negative number")
    if rate == 0:
        raise ValueError("rate_min_per_person must be greater than zero")
    return count * rate
