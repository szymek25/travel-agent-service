from typing import List, Optional
from app.models.schemas import TripRecommendation, TripRecommendationRequest, TripRecommendationResponse


MOCK_RECOMMENDATIONS: List[TripRecommendation] = [
    TripRecommendation(
        destination="Bali, Indonesia",
        description="A tropical paradise with stunning temples, rice terraces, and vibrant nightlife.",
        estimated_cost="$1,500 – $3,000",
        travel_style="beach",
        highlights=["Ubud Monkey Forest", "Tanah Lot Temple", "Seminyak Beach", "Mount Batur sunrise trek"],
    ),
    TripRecommendation(
        destination="Kyoto, Japan",
        description="Japan's ancient capital, famous for its classical Buddhist temples and traditional wooden machiya.",
        estimated_cost="$2,000 – $4,000",
        travel_style="cultural",
        highlights=["Fushimi Inari Shrine", "Arashiyama Bamboo Grove", "Gion district", "Nijo Castle"],
    ),
    TripRecommendation(
        destination="Patagonia, Argentina",
        description="A remote wilderness at the southern tip of South America with dramatic peaks and glaciers.",
        estimated_cost="$2,500 – $5,000",
        travel_style="adventure",
        highlights=["Torres del Paine", "Perito Moreno Glacier", "Los Glaciares National Park", "Fitz Roy Trek"],
    ),
    TripRecommendation(
        destination="Maldives",
        description="An archipelago of over 1,000 coral islands offering world-class snorkelling and luxury resorts.",
        estimated_cost="$3,000 – $8,000",
        travel_style="beach",
        highlights=["Overwater bungalows", "Snorkelling with manta rays", "Male Fish Market", "Sunset cruises"],
    ),
    TripRecommendation(
        destination="Rome, Italy",
        description="The Eternal City, packed with millennia of history, art, and some of the world's best cuisine.",
        estimated_cost="$1,500 – $3,500",
        travel_style="cultural",
        highlights=["Colosseum", "Vatican Museums", "Trevi Fountain", "Trastevere neighbourhood"],
    ),
]


class RecommendationService:
    def get_recommendations(
        self,
        request: Optional[TripRecommendationRequest] = None,
    ) -> TripRecommendationResponse:
        results = MOCK_RECOMMENDATIONS

        if request:
            if request.travel_style:
                results = [r for r in results if r.travel_style == request.travel_style.lower()]
            if request.destination:
                dest_lower = request.destination.lower()
                results = [r for r in results if dest_lower in r.destination.lower()]

        return TripRecommendationResponse(recommendations=results)
