# Estimated walking times in minutes.
WALK_TIMES = {
    "Main Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 6,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 6,
        "Union Restaurant (Haking Wong Building)": 7,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 11,
        "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": 8,
        "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": 10,
        "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": 11,
        "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": 8,
    },
    "Chong Yuet Ming Cultural Centre": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 1,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 6,
        "Union Restaurant (Haking Wong Building)": 9,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 13,
        "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": 10,
        "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": 11,
        "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": 12,
        "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": 10,
    },
    "Run Run Shaw Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 3,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 7,
        "Union Restaurant (Haking Wong Building)": 4,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 7,
        "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": 6,
        "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": 7,
        "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": 8,
        "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": 6,
    },
    "Centennial Campus (Grand Hall)": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 11,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 11,
        "Union Restaurant (Haking Wong Building)": 5,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 1,
        "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": 3,
        "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": 3,
        "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": 3,
        "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": 3,
    },
    "Haking Wong Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": ,7
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 8,
        "Union Restaurant (Haking Wong Building)": 1,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 5,
        "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": 3,
        "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": 5,
        "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": 6,
        "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": 3,
    },
    "Knowles Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 5,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 4,
        "Union Restaurant (Haking Wong Building)": 5,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 7,
        "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": 6,
        "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": 8,
        "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": 9,
        "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": 6,
    },
    "KKL Building": {
        "CYM Canteen (Chong Yuet Ming Cultural Centre)": 3,
        "JuYing Tai (Fong Shu Chuen Amenities Centre, Swire Building)": 3,
        "Union Restaurant (Haking Wong Building)": 5,
        "alfafa bistro (Jockey Club Tower, Centennial Campus)": 7,
        "TAI TAI FOODTOPIA (Shop G. 02, G/F, Composite Building, Main Campus)": 6,
        "TamJai SamGor (G/F The Jockey Club Tower, Centennial Campus)": 8,
        "Asian Gourmet (G/F, Run Run Shaw Tower, Centennial Campus)": 9,
        "OORI HANSIK (Shop G. 01, G/F, Composite Building, Main Campus)": 6,
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
