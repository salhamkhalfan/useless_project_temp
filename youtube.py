"""YouTube Data API v3 helper: find one long nature video from the leaf's
computed R value.

The R value seeds a random choice of a calm/nature search query, then the
YouTube Data API searches for videos longer than 20 minutes
(videoDuration=long). Results are cached per query to save API quota.

Needs the env var YOUTUBE_API_KEY. If it is missing, the app falls back to
a plain "open YouTube search" link so the site still works.
"""
import os
import random
import urllib.parse

import httpx

YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"


def load_dotenv():
    """Load YOUTUBE_API_KEY (and friends) from a .env file next to this file."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding="utf-8") as fh:
        for line in fh.read().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(),
                                  value.strip().strip('"').strip("'"))


load_dotenv()

# ---- Huge, broad query space ----
# Every leaf's R value deterministically builds a query from these pools,
# so different leaves tend to pull videos from completely different corners
# of YouTube (nature, history, food, space, music, sports, ...).
SUBJECTS = [
    "forest", "ocean", "rain", "birds", "space", "deep space", "galaxy",
    "stars", "planets", "mars", "moon", "saturn", "aurora borealis",
    "fireplace", "campfire", "storm", "thunder", "waterfall", "river",
    "mountain", "desert", "cave", "canyon", "geyser", "volcano", "glacier",
    "ice", "arctic", "penguins", "whales", "dolphins", "sharks", "jellyfish",
    "coral reef", "fishes", "tropical fish", "aquarium", "animals", "wildlife",
    "safari", "elephants", "lions", "tigers", "bears", "wolves", "foxes",
    "birds of prey", "eagles", "owls", "parrots", "cats", "dogs", "puppies",
    "kittens", "horses", "rabbits", "squirrels", "butterflies", "bees",
    "insects", "spiders", "snakes", "frogs", "turtles", "dinosaurs",
    "ancient history", "medieval history", "roman empire", "ancient egypt",
    "pyramids", "greek mythology", "norse mythology", "vikings", "samurai",
    "knights", "castles", "world war 2", "world war 1", "cold war",
    "industrial revolution", "history documentary", "archeology", "paleontology",
    "mummies", "titanic", "lost cities", "atlantis", "mythology", "legends",
    "folklore", "fairytales", "alchemy", "astronomy", "astrophysics",
    "quantum physics", "black holes", "time travel", "parallel universe",
    "physics", "chemistry", "biology", "genetics", "neuroscience", "psychology",
    "philosophy", "stoicism", "meditation", "yoga", "zen", "mindfulness",
    "relaxation", "sleep music", "lofi", "ambient music", "classical music",
    "jazz", "piano", "guitar", "violin", "flute", "drums", "synthesizer",
    "orchestra", "opera", "choir", "binaural beats", "white noise", "asmr",
    "cooking", "baking", "bread", "pizza", "pasta", "sushi", "chocolate",
    "coffee", "tea", "dessert", "cheesemaking", "grilling", "bbq", "street food",
    "food documentary", "restaurant", "spices", "baking bread",
    "painting", "drawing", "digital art", "watercolor", "pottery", "sculpture",
    "origami", "woodworking", "blacksmithing", "glassblowing", "calligraphy",
    "architecture", "skyscrapers", "bridges", "trains", "steam locomotive",
    "airplanes", "helicopters", "rockets", "spacex", "nasa", "drones",
    "submarines", "sailing", "yachts", "race cars", "f1", "motorcycles",
    "bicycles", "skateboarding", "surfing", "snowboarding", "skiing", "hiking",
    "camping", "fishing", "kayaking", "scuba diving", "paragliding",
    "base jumping", "rock climbing", "basketball", "football", "soccer",
    "tennis", "golf", "swimming", "boxing", "chess", "poker", "video games",
    "minecraft", "retro games", "arcade", "programming", "coding", "robotics",
    "amazing inventions", "builds", "restoration", "how its made", "factories",
    "machines", "turbines", "engines", "gemstones", "crystals", "meteorites",
    "fossils", "spacecraft", "telescopes", "microscope", "experiments",
    "magic tricks", "illusions", "street artists", "history of music",
    "film history", "behind the scenes", "movie breakdowns", "science fiction",
    "fantasy", "books", "poetry", "writing", "documentary", "travel vlog",
    "japan", "iceland", "norway", "switzerland", "new zealand", "morocco",
    "peru", "india", "china", "africa", "amazon rainforest", "sahara",
    "himalayas", "mount everest", "kilimanjaro", "grand canyon", "niagara falls",
]

FLAVOURS = [
    "", "long", "relaxing", "calm", "best of", "top 10", "full", "compilation",
    "4k", "hd", "amazing", "incredible", "educational", "documentary",
    "for beginners", "how to", "explained", "asmr", "ambience", "looping",
    "epic", "beautiful", "hidden gems", "underrated", "rare", "mega",
    "extended", "complete", "the ultimate", "midnight", "sunrise", "8 hours",
    "1 hour", "hours", "live", "classic", "nostalgic", "cozy", "satisfying",
]

TEMPLATES = [
    "{subject} {flavour}".strip(),
    "{flavour} {subject}".strip(),
    "{subject} {subject2} {flavour}".strip(),
    "{subject} - {flavour} {duration}".strip(),
    "best {subject} {flavour}".strip(),
    "{subject} documentary {flavour}".strip(),
    "{flavour} {subject} compilation".strip(),
]

DURATIONS = ["1 hour", "2 hours", "4 hours", "8 hours", "10 hours",
             "11 hours", "full length"]

# Persistent cache so that ONE leaf (its R value) always maps to ONE video.
CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "video_cache.json")


def _load_cache():
    try:
        import json
        with open(CACHE_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _save_cache(cache):
    import json
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as fh:
            json.dump(cache, fh, ensure_ascii=False, indent=1)
    except OSError:
        pass


def _make_query(R, rng=None):
    """Deterministically build a varied search query from the leaf's R."""
    rng = rng or random.Random(int(R))
    subject = rng.choice(SUBJECTS)
    subject2 = rng.choice(SUBJECTS)
    flavour = rng.choice(FLAVOURS)
    duration = rng.choice(DURATIONS)
    template = rng.choice(TEMPLATES)
    return template.format(subject=subject, subject2=subject2,
                           flavour=flavour, duration=duration).strip()


def search_long_video(R):
    """Return dict describing a video chosen from the leaf's R value.

    The R value seeds a query drawn from a very broad space (billions of
    combinations), then the YouTube Data API searches for videos longer than
    20 minutes (videoDuration=long). Results are cached per query to save
    quota. Needs YOUTUBE_API_KEY; otherwise falls back to a search link.
    """
    rng = random.Random(int(R))
    query = _make_query(R, rng)

    api_key = (os.environ.get("YOUTUBE_API_KEY") or "").strip()
    search_url = (f"https://www.youtube.com/results?search_query="
                  f"{urllib.parse.quote(query)}")

    if not api_key:
        return {
            "mode": "link",
            "query": query,
            "search_url": search_url,
            "error": ("YOUTUBE_API_KEY is not set. Set it to embed the "
                      "top result automatically."),
        }

    # Same leaf (same R) -> same video, across restarts.
    cache = _load_cache()
    key = str(int(R))
    if key in cache:
        return cache[key]

    params = {
        "part": "snippet",
        "type": "video",
        "videoDuration": "long",
        "maxResults": 5,
        "order": "relevance",
        "q": query,
        "key": api_key,
    }

    try:
        with httpx.Client(timeout=20) as client:
            resp = client.get(YOUTUBE_API_URL, params=params)
    except httpx.HTTPError as exc:
        return {
            "mode": "link",
            "query": query,
            "search_url": search_url,
            "error": f"YouTube request failed: {exc}",
        }

    if resp.status_code != 200:
        return {
            "mode": "link",
            "query": query,
            "search_url": search_url,
            "error": f"YouTube API returned {resp.status_code}: {resp.text[:200]}",
        }

    items = resp.json().get("items", [])
    if not items:
        return {
            "mode": "link",
            "query": query,
            "search_url": search_url,
            "error": "No matching long videos found.",
        }

    item = items[0]
    snippet = item.get("snippet", {})
    video_id = item.get("id", {}).get("videoId")

    result = {
        "mode": "embed",
        "query": query,
        "id": video_id,
        "title": snippet.get("title", video_id),
        "channel": snippet.get("channelTitle", ""),
        "thumb": (
            snippet.get("thumbnails", {})
            .get("high", {})
            .get("url")
            or snippet.get("thumbnails", {}).get("medium", {}).get("url")
        ),
        "embed": f"https://www.youtube.com/embed/{video_id}",
        "watch": f"https://www.youtube.com/watch?v={video_id}",
    }
    cache[key] = result
    _save_cache(cache)
    return result