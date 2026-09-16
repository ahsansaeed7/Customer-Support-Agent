"""
Seed script — populates the local database with fake tours and itineraries
so search_tours() and the agent have real data to query.

Run with:
    python -m app.db.seed
(from the project root, with your venv activated)
"""

from app.db.session import SessionLocal
from app.db.models import Tour, Itinerary


TOURS = [
    {
        "title": "Bali Beach & Culture Escape",
        "slug": "bali-beach-culture-escape",
        "destination": "Bali, Indonesia",
        "duration_days": 5,
        "base_price": 899.00,
        "currency": "USD",
        "capacity": 20,
        "available_seats": 20,
        "tags": ["beach", "budget", "culture"],
        "itineraries": [
            {
                "day_number": 1,
                "title": "Arrival & Ubud Welcome",
                "description": "Arrive in Bali, transfer to Ubud, evening welcome dinner with traditional dance show.",
                "activities": ["Airport pickup", "Hotel check-in", "Welcome dinner"],
                "meal_plan": "Dinner",
                "accommodation": "Ubud Boutique Resort",
            },
            {
                "day_number": 2,
                "title": "Rice Terraces & Temples",
                "description": "Visit Tegallalang rice terraces and Tirta Empul water temple.",
                "activities": ["Tegallalang rice terraces", "Tirta Empul temple", "Local lunch"],
                "meal_plan": "Breakfast & Lunch",
                "accommodation": "Ubud Boutique Resort",
            },
        ],
    },
    {
        "title": "Swiss Alps Adventure",
        "slug": "swiss-alps-adventure",
        "destination": "Interlaken, Switzerland",
        "duration_days": 7,
        "base_price": 2199.00,
        "currency": "USD",
        "capacity": 15,
        "available_seats": 15,
        "tags": ["adventure", "mountains", "luxury"],
        "itineraries": [],
    },
    {
        "title": "Istanbul Heritage Tour",
        "slug": "istanbul-heritage-tour",
        "destination": "Istanbul, Turkey",
        "duration_days": 4,
        "base_price": 649.00,
        "currency": "USD",
        "capacity": 25,
        "available_seats": 25,
        "tags": ["culture", "history", "budget"],
        "itineraries": [],
    },
    {
        "title": "Maldives Honeymoon Retreat",
        "slug": "maldives-honeymoon-retreat",
        "destination": "Maldives",
        "duration_days": 6,
        "base_price": 3299.00,
        "currency": "USD",
        "capacity": 10,
        "available_seats": 10,
        "tags": ["honeymoon", "beach", "luxury"],
        "itineraries": [],
    },
    {
        "title": "Northern Pakistan Explorer",
        "slug": "northern-pakistan-explorer",
        "destination": "Hunza & Skardu, Pakistan",
        "duration_days": 8,
        "base_price": 799.00,
        "currency": "USD",
        "capacity": 18,
        "available_seats": 18,
        "tags": ["adventure", "mountains", "budget"],
        "itineraries": [],
    },
]


def seed():
    db = SessionLocal()
    try:
        for tour_data in TOURS:
            itineraries_data = tour_data.pop("itineraries")

            existing = db.query(Tour).filter_by(slug=tour_data["slug"]).first()
            if existing:
                print(f"Skipping (already exists): {tour_data['title']}")
                continue

            tour = Tour(**tour_data)
            db.add(tour)
            db.flush()  # get tour.id before creating itineraries

            for day in itineraries_data:
                db.add(Itinerary(tour_id=tour.id, **day))

            print(f"Added: {tour.title}")

        db.commit()
        print("Seeding complete.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
