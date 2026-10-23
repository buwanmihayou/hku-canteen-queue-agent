# Estimated walking times in minutes.
WALK_TIMES = {
    "Main Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 6,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 4,
        "Union Restaurant (Haking Wong Building)": 7,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 11,
        "TAI TAI FOODTOPIA (Composite Building)": 8,
    },
    "Chong Yuet Ming Cultural Centre": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 1,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 4,
        "Union Restaurant (Haking Wong Building)": 9,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 13,
        "TAI TAI FOODTOPIA (Composite Building)": 10,
    },
    "Run Run Shaw Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 6,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 4,
        "Union Restaurant (Haking Wong Building)": 4,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 8,
        "TAI TAI FOODTOPIA (Composite Building)": 5,
    },
    "Centennial Campus (Grand Hall)": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 14,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 11,
        "Union Restaurant (Haking Wong Building)": 7,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 4,
        "TAI TAI FOODTOPIA (Composite Building)": 6,
    },
    "Haking Wong Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 10,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 7,
        "Union Restaurant (Haking Wong Building)": 1,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 6,
        "TAI TAI FOODTOPIA (Composite Building)": 3,
    },
    "Knowles Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 8,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 5,
        "Union Restaurant (Haking Wong Building)": 5,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 8,
        "TAI TAI FOODTOPIA (Composite Building)": 5,
    },
}


def rank_canteens(stall_rates, user_location, prioritize_short_walk=False):
    if user_location not in WALK_TIMES:
        raise ValueError(f"Unknown campus location: {user_location}")

    location_walk_times = WALK_TIMES[user_location]
    missing_canteens = set(stall_rates) - set(location_walk_times)
    if missing_canteens:
        missing = ", ".join(sorted(missing_canteens))
        raise ValueError(f"Missing walking-time estimates for: {missing}")

    ranked = []
    for canteen, info in stall_rates.items():
        walk = location_walk_times[canteen]
        wait = 8 * info["rate_min_per_person"]
        total = walk + wait
        score = walk * 1.5 + wait if prioritize_short_walk else total
        ranked.append((canteen, walk, wait, total, score))

    return sorted(ranked, key=lambda item: item[4])
