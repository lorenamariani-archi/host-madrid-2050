MADRID_DISTRICT_NAMES = [
    "Centro",
    "Arganzuela",
    "Retiro",
    "Salamanca",
    "Chamartin",
    "Tetuan",
    "Chamberi",
    "Fuencarral-El Pardo",
    "Moncloa-Aravaca",
    "Latina",
    "Carabanchel",
    "Usera",
    "Puente de Vallecas",
    "Moratalaz",
    "Ciudad Lineal",
    "Hortaleza",
    "Villaverde",
    "Villa de Vallecas",
    "Vicalvaro",
    "San Blas-Canillejas",
    "Barajas",
]

DISTRICT_DATA = {
    "Centro": {
        "name": "Centro",
        "population": 135000,
        "density": 27000,
        "children_share": 0.11,
        "young_adults_share": 0.22,
        "adults_share": 0.42,
        "seniors_share": 0.25,
        "main_profiles": [
            "businessman",
            "international student",
            "retired couple",
            "teenager",
        ],
        "existing_facilities": {
            "green": 2,
            "sport": 2,
            "cultural": 4,
            "learning": 3,
            "community": 2,
            "care": 2,
        },
    },
    "Arganzuela": {
        "name": "Arganzuela",
        "population": 155000,
        "density": 15500,
        "children_share": 0.16,
        "young_adults_share": 0.18,
        "adults_share": 0.44,
        "seniors_share": 0.22,
        "main_profiles": [
            "mom_with_kids",
            "businessman",
            "retired couple",
        ],
        "existing_facilities": {
            "green": 3,
            "sport": 3,
            "cultural": 2,
            "learning": 2,
            "community": 2,
            "care": 2,
        },
    },
    "Chamberi": {
        "name": "Chamberi",
        "population": 140000,
        "density": 29500,
        "children_share": 0.10,
        "young_adults_share": 0.20,
        "adults_share": 0.40,
        "seniors_share": 0.30,
        "main_profiles": [
            "businessman",
            "retired couple",
            "international student",
        ],
        "existing_facilities": {
            "green": 2,
            "sport": 2,
            "cultural": 3,
            "learning": 3,
            "community": 2,
            "care": 3,
        },
    },
}

BUILDING_DATA = {
    "FactoryA": {
        "name": "FactoryA",
        "total_area": 12000,
        "plot_area": 9000,
        "floors": 3,
        "average_height": 6,
        "structure_flexibility": 5,
        "outdoor_space": 1,
        "roof_usable": 1,
        "heritage_constraint": 3,
        "condition": 4,
    },
    "WarehouseB": {
        "name": "WarehouseB",
        "total_area": 8000,
        "plot_area": 7000,
        "floors": 2,
        "average_height": 8,
        "structure_flexibility": 5,
        "outdoor_space": 0,
        "roof_usable": 1,
        "heritage_constraint": 1,
        "condition": 4,
    },
    "IndustrialBlockC": {
        "name": "IndustrialBlockC",
        "total_area": 6000,
        "plot_area": 5000,
        "floors": 4,
        "average_height": 4,
        "structure_flexibility": 3,
        "outdoor_space": 1,
        "roof_usable": 0,
        "heritage_constraint": 5,
        "condition": 3,
    },
}

PROFILE_NEEDS = {
    "mom_with_kids": {
        "label": "Young parent with children",
        "activity_text": "Daily routines center on childcare, safe outdoor play, after-school support, family wellbeing, and nearby community help.",
        "priority_categories": ["green", "sport", "learning", "community", "care"],
        "category_spaces": {
            "green": ["Urban park", "Playground"],
            "sport": ["Indoor sports facilities"],
            "learning": ["After-school learning spaces"],
            "community": ["Community center"],
            "care": ["Family support rooms"],
        },
    },
    "businessman": {
        "label": "Business man",
        "activity_text": "Main activities include co-working, meetings, networking, short learning sessions, and flexible spaces for professional exchange.",
        "priority_categories": ["learning", "community", "cultural"],
        "category_spaces": {
            "learning": ["Co-working spaces", "Seminar rooms", "Business support hub"],
            "community": ["Cafés and informal gathering spaces"],
            "cultural": ["Lecture halls"],
        },
    },
    "teenager": {
        "label": "Teenager",
        "activity_text": "Main activities focus on study support, sport, digital and creative workshops, social gathering, and safe free time after school.",
        "priority_categories": ["sport", "learning", "community", "cultural", "green"],
        "category_spaces": {
            "sport": ["Indoor sports facilities"],
            "learning": ["After-school study lounges", "Creative media lab"],
            "community": ["Youth social hub"],
            "cultural": ["Music and rehearsal rooms"],
            "green": ["Outdoor recreation terrace"],
        },
    },
    "international student": {
        "label": "International student",
        "activity_text": "Typical use includes study, shared work, affordable social life, language exchange, making, and cultural participation.",
        "priority_categories": ["learning", "community", "cultural", "sport"],
        "category_spaces": {
            "learning": ["Library / media library", "Co-working spaces", "Workshops / fabrication labs"],
            "community": ["Affordable social spaces"],
            "cultural": ["Performance spaces"],
            "sport": ["Wellness spaces"],
        },
    },
    "retired couple": {
        "label": "Retired / old people",
        "activity_text": "Main activities include quiet social time, preventive wellbeing, reading, cultural visits, and restorative outdoor use.",
        "priority_categories": ["green", "community", "care", "cultural"],
        "category_spaces": {
            "green": ["Therapeutic garden"],
            "community": ["Social spaces for elderly", "Community center"],
            "care": ["Preventive wellbeing support"],
            "cultural": ["Quiet reading rooms", "Art exhibition spaces"],
        },
    },
}

PROFILE_DISPLAY_ORDER = [
    "retired couple",
    "businessman",
    "teenager",
    "international student",
    "mom_with_kids",
]

CATEGORY_LABELS = {
    "green": "Green Infrastructures",
    "sport": "Sport",
    "cultural": "Cultural",
    "learning": "Learning and Innovation",
    "community": "Community",
    "care": "Care and Social Support",
}

CATEGORY_KEYS = {
    "Green Infrastructures": "green",
    "Sport": "sport",
    "Cultural": "cultural",
    "Learning and Innovation": "learning",
    "Community": "community",
    "Care and Social Support": "care",
}

CLIMATE_STRATEGIES = {
    "heat": [
        "Shading systems in facades and open spaces",
        "Tree canopy and intensive planting",
        "Cool and permeable pavements",
        "Cross ventilation strategies",
        "Thermal buffering spaces",
        "Roof retrofitting for heat protection",
    ],
    "energy": [
        "Solar panels",
        "Electricity-producing pavement in selected public areas",
        "Energy storage systems",
        "Low-consumption lighting",
        "Smart building management",
    ],
    "water": [
        "Rainwater collection",
        "Greywater reuse",
        "Drought-resistant landscape",
        "Water-sensitive urban design",
    ],
    "future_adaptation": [
        "Flexible and reversible partitions",
        "Multi-season public spaces",
        "Phased retrofit strategy",
        "Climate refuge rooms",
        "Long-life low-carbon materials",
    ],
}

CLIMATE_CATEGORY_BONUS = {
    "Green Infrastructures": 1.0,
    "Sport": 0.4,
    "Cultural": 0.3,
    "Learning and Innovation": 0.5,
    "Community": 0.6,
    "Care and Social Support": 0.8,
}
