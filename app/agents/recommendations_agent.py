from typing import List, Optional

from strands import Agent as StrandsAgent
from strands.types.exceptions import StructuredOutputException

from app.agents.providers import LLMProvider
from app.models.domain import RecommendationItem, RecommendationsOutput, UserPreferences

_RECOMMENDATIONS_SYSTEM_PROMPT = """
You are a travel recommendations specialist at Wanderlust Travel Agency.
You have expert knowledge of the agency's curated travel packages and portfolio.

Our agency offers the following destinations and packages:

BEACH & TROPICAL:
- Bali, Indonesia: 7-night packages from $1,200/person.
  Highlights: rice terraces, Hindu temples, surf lessons, cooking classes, jungle trekking, vibrant nightlife.
- Maldives: 5-night overwater bungalow packages from $2,800/person.
  Highlights: private beaches, coral reef snorkelling, water sports, world-class spa retreats.
- Phuket, Thailand: 8-night packages from $900/person.
  Highlights: white-sand beaches, island hopping, Thai massage, street food tours, Phi Phi Islands.
- Santorini, Greece: 6-night packages from $1,600/person.
  Highlights: caldera sunsets, wine tasting, volcanic beaches, private sailing tours.

ADVENTURE:
- Patagonia, Argentina/Chile: 10-night trekking packages from $2,200/person.
  Highlights: Torres del Paine, glacier hikes, wildlife (condors, pumas), W-Trek.
- Nepal: 14-night Himalaya packages from $1,800/person.
  Highlights: Everest Base Camp trek, Annapurna Circuit, Kathmandu temples, white-water rafting, paragliding.
- New Zealand: 12-night adventure packages from $2,500/person.
  Highlights: bungee jumping, skydiving, Milford Sound, Queenstown thrills, Tongariro Alpine Crossing.
- Costa Rica: 9-night eco-adventure from $1,400/person.
  Highlights: rainforest zip-lining, volcano hiking, wildlife, Pacuare River rafting, Pacific surf.

CULTURAL:
- Kyoto, Japan: 8-night cultural immersion from $2,100/person.
  Highlights: geisha districts, tea ceremony, Buddhist temples, bamboo grove, traditional ryokan, kaiseki dining.
- Rome, Italy: 7-night history & culture from $1,500/person.
  Highlights: Colosseum, Vatican Museums, Roman Forum, cooking classes, wine tours, day trips to Florence and Pompeii.
- Morocco: 9-night cultural journey from $1,200/person.
  Highlights: Marrakech medina, Sahara desert camping, Fes el-Bali, Atlas Mountains, traditional hammam.
- Peru: 10-night heritage package from $1,800/person.
  Highlights: Machu Picchu, Cusco, Sacred Valley, Inca Trail, Lima food scene, Lake Titicaca.

CITY BREAK:
- Paris, France: 5-night city break from $1,100/person.
  Highlights: Eiffel Tower, Louvre, Montmartre, Seine river cruise, bistro dining, Versailles day trip.
- Tokyo, Japan: 7-night city break from $1,700/person.
  Highlights: Shibuya crossing, Tsukiji market, teamLab digital art, Akihabara, Mount Fuji day trip.
- New York City, USA: 6-night city break from $1,400/person.
  Highlights: Central Park, MoMA, Broadway shows, Brooklyn food tours, Statue of Liberty, diverse dining.
- Barcelona, Spain: 6-night city break from $1,100/person.
  Highlights: Sagrada Familia, Park Güell, Gothic Quarter, tapas tours, flamenco show, Costa Brava day trip.

SKI & WINTER:
- Swiss Alps, Switzerland: 7-night ski package from $2,800/person.
  Highlights: Verbier and Zermatt resorts, Matterhorn views, après-ski, mountain restaurants, fondue evenings.
- Hokkaido, Japan: 8-night powder ski package from $2,200/person.
  Highlights: Niseko resort, world-famous powder snow, Japanese onsens, fresh seafood, ice fishing.

LUXURY:
- Seychelles: 7-night luxury retreat from $3,500/person.
  Highlights: private beach villas, granite boulder landscapes, whale shark encounters, Creole gastronomy.
- Dubai, UAE: 6-night luxury package from $2,000/person.
  Highlights: Burj Khalifa, desert safari, luxury shopping, yacht cruises, Michelin-starred dining.

Given the traveller's profile below, recommend exactly 2-3 destinations from the portfolio above
that best match their travel style, budget, interests, and preferred destinations.
For each pick a compelling 1-2 sentence description that explains why it suits them.
Return ONLY destinations listed above.
""".strip()


def _build_preferences_context(preferences: UserPreferences) -> str:
    """Format user preferences as a concise context string for the recommendations prompt."""
    lines = ["[Traveller profile]"]

    lines.append(f"- Travel style: {preferences.travel_style or 'not specified'}")
    lines.append(f"- Budget: {preferences.budget or 'not specified'}")

    if preferences.preferred_destinations:
        lines.append(f"- Preferred destinations: {', '.join(str(d) for d in preferences.preferred_destinations)}")
    else:
        lines.append("- Preferred destinations: no preference")

    if preferences.dietary_restrictions:
        lines.append(f"- Dietary restrictions: {', '.join(str(r) for r in preferences.dietary_restrictions)}")

    if preferences.interests:
        lines.append(f"- Interests: {', '.join(str(i) for i in preferences.interests)}")
    else:
        lines.append("- Interests: not specified")

    return "\n".join(lines)


class RecommendationsAgent:
    """LLM-backed agent that recommends destinations from the agency's portfolio."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        if llm_provider is None:
            from app.agents.providers import create_provider

            llm_provider = create_provider("recommendations_agent")
        self._model = llm_provider.get_model()

    def get_recommendations(self, preferences: UserPreferences) -> RecommendationsOutput:
        """Return 2-3 destination recommendations matching *preferences*."""
        context = _build_preferences_context(preferences)
        agent = StrandsAgent(model=self._model, system_prompt=_RECOMMENDATIONS_SYSTEM_PROMPT)
        try:
            return agent(context, structured_output_model=RecommendationsOutput)
        except StructuredOutputException:
            return RecommendationsOutput(recommendations=[])
