from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import csv
import json
import math
import os
from urllib import request as urllib_request
from urllib import error as urllib_error


DEFAULT_NIM_MODEL = "meta/llama-3.1-70b-instruct"


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """

    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """

    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def _to_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _to_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def _pick_value(row: Dict[str, Any], keys: List[str], fallback: Any = "") -> Any:
    for key in keys:
        if key in row and row[key] not in ("", None):
            return row[key]
    return fallback


def load_songs(csv_path: str) -> List[Dict[str, Any]]:
    """
    Load songs from either starter CSV schema or cleanedClassicHits schema.
    Returns a normalized dictionary for each song.
    """
    songs: List[Dict[str, Any]] = []
    with open(csv_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader, start=1):
            song = {
                "id": _to_int(_pick_value(row, ["id"]), idx),
                "title": _pick_value(row, ["title", "Track"], "Unknown Title"),
                "artist": _pick_value(row, ["artist", "Artist"], "Unknown Artist"),
                "genre": str(_pick_value(row, ["genre", "Genre"], "unknown")).strip(),
                "mood": str(_pick_value(row, ["mood"], "unknown")).strip(),
                "energy": _to_float(_pick_value(row, ["energy", "Energy"], 0.0)),
                "tempo_bpm": _to_float(_pick_value(row, ["tempo_bpm", "Tempo"], 0.0)),
                "valence": _to_float(_pick_value(row, ["valence", "Valence"], 0.0)),
                "danceability": _to_float(_pick_value(row, ["danceability", "Danceability"], 0.0)),
                "acousticness": _to_float(_pick_value(row, ["acousticness", "Acousticness"], 0.0)),
                "year": _to_int(_pick_value(row, ["year", "Year"], 0)),
                "popularity": _to_float(_pick_value(row, ["popularity", "Popularity"], 0.0)),
                "instrumentalness": _to_float(_pick_value(row, ["instrumentalness", "Instrumentalness"], 0.0)),
                "liveness": _to_float(_pick_value(row, ["liveness", "Liveness"], 0.0)),
            }
            songs.append(song)
    return songs


def score_song(user_prefs: Dict[str, Any], song: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Rule-based score for backward compatibility and baseline ranking."""
    score = 0.0
    reasons: List[str] = []

    requested_genre = str(user_prefs.get("genre", "")).strip().lower()
    requested_mood = str(user_prefs.get("mood", "")).strip().lower()
    song_genre = str(song.get("genre", "")).strip().lower()
    song_mood = str(song.get("mood", "")).strip().lower()

    if requested_genre and requested_genre in song_genre:
        score += 2.0
        reasons.append("genre match (+2.0)")

    if requested_mood and requested_mood == song_mood:
        score += 1.5
        reasons.append("mood match (+1.5)")

    if "energy" in user_prefs:
        energy_diff = abs(_to_float(song.get("energy")) - _to_float(user_prefs.get("energy")))
        energy_score = max(0.0, 1 - energy_diff)
        score += energy_score
        reasons.append(f"energy closeness ({energy_score:.2f})")

    return score, reasons


def recommend_songs(user_prefs: Dict[str, Any], songs: List[Dict[str, Any]], k: int = 5) -> List[Tuple[Dict[str, Any], float, str]]:
    """Return the top k songs ranked by rule-based score, highest to lowest."""
    scored_songs: List[Tuple[Dict[str, Any], float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "Because: " + ", ".join(reasons) if reasons else "No matching preferences"
        scored_songs.append((song, score, explanation))

    scored_songs.sort(key=lambda x: x[1], reverse=True)
    return scored_songs[:k]


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _song_score(self, user: UserProfile, song: Song) -> float:
        score = 0.0
        if user.favorite_genre.lower() == song.genre.lower():
            score += 2.0
        if user.favorite_mood.lower() == song.mood.lower():
            score += 1.5
        score += max(0.0, 1 - abs(song.energy - user.target_energy))
        if user.likes_acoustic:
            score += song.acousticness
        else:
            score += (1 - song.acousticness)
        return score

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        ranked = sorted(self.songs, key=lambda s: self._song_score(user, s), reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        reasons: List[str] = []
        if user.favorite_genre.lower() == song.genre.lower():
            reasons.append("genre matches your preference")
        if user.favorite_mood.lower() == song.mood.lower():
            reasons.append("mood matches what you asked for")
        reasons.append(f"energy is close to target ({song.energy:.2f} vs {user.target_energy:.2f})")
        if user.likes_acoustic:
            reasons.append("it is relatively acoustic")
        else:
            reasons.append("it leans less acoustic as requested")
        return "This song fits because " + ", ".join(reasons) + "."


def build_song_index(songs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build normalized vectors from songs for similarity retrieval.
    """
    numeric_features = [
        "energy",
        "tempo_bpm",
        "valence",
        "danceability",
        "acousticness",
        "instrumentalness",
        "liveness",
        "popularity",
        "year",
    ]
    genre_values = sorted({str(song.get("genre", "unknown")).strip().lower() for song in songs})
    stats: Dict[str, Tuple[float, float]] = {}
    for feature in numeric_features:
        values = [_to_float(song.get(feature, 0.0)) for song in songs]
        mean = sum(values) / len(values) if values else 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values) if values else 0.0
        std = math.sqrt(variance) if variance > 0 else 1.0
        stats[feature] = (mean, std)

    vectors: List[List[float]] = []
    for song in songs:
        vec: List[float] = []
        for feature in numeric_features:
            mean, std = stats[feature]
            normalized = (_to_float(song.get(feature, mean)) - mean) / std
            vec.append(normalized)
        song_genre = str(song.get("genre", "unknown")).strip().lower()
        vec.extend([1.0 if song_genre == g else 0.0 for g in genre_values])
        vectors.append(vec)

    return {
        "songs": songs,
        "vectors": vectors,
        "numeric_features": numeric_features,
        "genre_values": genre_values,
        "stats": stats,
    }


def _require_nim_api_key(nim_api_key: Optional[str] = None) -> str:
    resolved = nim_api_key or os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NIM_API_KEY")
    if not resolved:
        raise ValueError(
            "NIM API key is required. Set NVIDIA_NIM_API_KEY or NIM_API_KEY before requesting recommendations."
        )
    return resolved


def _call_nim_chat(messages: List[Dict[str, str]], api_key: str, model: str = DEFAULT_NIM_MODEL, temperature: float = 0.2) -> str:
    endpoint = "https://integrate.api.nvidia.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 400,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
        parsed = json.loads(raw)
        return parsed["choices"][0]["message"]["content"]
    except (urllib_error.URLError, urllib_error.HTTPError, KeyError, IndexError, json.JSONDecodeError):
        return ""


def parse_user_vibe(vibe_text: str, nim_api_key: Optional[str] = None, model: str = DEFAULT_NIM_MODEL) -> Dict[str, Any]:
    """
    Parse a natural-language vibe into structured preferences using NIM.
    """
    resolved_key = _require_nim_api_key(nim_api_key)
    schema_hint = {
        "genre": "string",
        "mood": "string",
        "energy": 0.0,
        "valence": 0.0,
        "danceability": 0.0,
        "acousticness": 0.0,
        "tempo_bpm": 0.0,
        "year": 0,
        "era_note": "string",
        "conversion_note": "string",
    }
    messages = [
        {
            "role": "system",
            "content": (
                "You convert present-day music taste into classic-era equivalents "
                "(1970s-1990s), then extract structured fields. Return strict JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User vibe: {vibe_text}\n"
                "Interpret modern artists/genres as old-time equivalents when needed.\n"
                f"Return JSON in this shape (floats from 0 to 1 where relevant): {json.dumps(schema_hint)}"
            ),
        },
    ]
    content = _call_nim_chat(messages=messages, api_key=resolved_key, model=model)
    if not content:
        raise RuntimeError("NIM parse request failed or returned empty output.")
    try:
        parsed = json.loads(content.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError("NIM parse request returned invalid JSON.") from exc
    return {
        "genre": str(parsed.get("genre", "unknown")),
        "mood": str(parsed.get("mood", "unknown")),
        "energy": _to_float(parsed.get("energy", 0.55), 0.55),
        "valence": _to_float(parsed.get("valence", 0.55), 0.55),
        "danceability": _to_float(parsed.get("danceability", 0.55), 0.55),
        "acousticness": _to_float(parsed.get("acousticness", 0.35), 0.35),
        "tempo_bpm": _to_float(parsed.get("tempo_bpm", 115.0), 115.0),
        "year": _to_int(parsed.get("year", 1985), 1985),
        "era_note": str(parsed.get("era_note", "classic era")),
        "conversion_note": str(
            parsed.get(
                "conversion_note",
                "Converted modern taste cues into a classic-era profile.",
            )
        ),
    }


def _vector_norm(vector: List[float]) -> float:
    return math.sqrt(sum(v * v for v in vector))


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if len(a) != len(b):
        return 0.0
    denom = _vector_norm(a) * _vector_norm(b)
    if denom == 0:
        return 0.0
    return sum(x * y for x, y in zip(a, b)) / denom


def vectorize_user_profile(user_profile: Dict[str, Any], index: Dict[str, Any]) -> List[float]:
    numeric_features: List[str] = index["numeric_features"]
    stats: Dict[str, Tuple[float, float]] = index["stats"]
    genre_values: List[str] = index["genre_values"]

    vec: List[float] = []
    for feature in numeric_features:
        mean, std = stats[feature]
        value = _to_float(user_profile.get(feature, mean), mean)
        vec.append((value - mean) / std)

    requested_genre = str(user_profile.get("genre", "unknown")).strip().lower()
    vec.extend([1.0 if requested_genre == g else 0.0 for g in genre_values])
    return vec


def retrieve_top_k(user_profile: Dict[str, Any], index: Dict[str, Any], k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
    query_vector = vectorize_user_profile(user_profile, index)
    scored: List[Tuple[Dict[str, Any], float]] = []
    for song, song_vector in zip(index["songs"], index["vectors"]):
        sim = _cosine_similarity(query_vector, song_vector)
        scored.append((song, sim))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:k]


def rerank_with_llm(
    vibe_text: str,
    user_profile: Dict[str, Any],
    candidates: List[Tuple[Dict[str, Any], float]],
    nim_api_key: Optional[str] = None,
    model: str = DEFAULT_NIM_MODEL,
) -> Tuple[Dict[str, Any], str]:
    if not candidates:
        return {}, "No candidates found."

    resolved_key = _require_nim_api_key(nim_api_key)
    compact_candidates = [
        {
            "title": song["title"],
            "artist": song["artist"],
            "genre": song["genre"],
            "year": song.get("year", 0),
            "energy": song.get("energy", 0.0),
            "valence": song.get("valence", 0.0),
            "danceability": song.get("danceability", 0.0),
            "retrieval_score": round(score, 4),
        }
        for song, score in candidates
    ]
    messages = [
        {
            "role": "system",
            "content": (
                "Pick the best old-time equivalent of the user's current taste. "
                "Explain in 2-3 sentences with era context. Use only provided candidates."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User vibe: {vibe_text}\n"
                f"Parsed profile: {json.dumps(user_profile)}\n"
                f"Candidates: {json.dumps(compact_candidates)}\n"
                "Return strict JSON: {\"selected_index\": int, \"explanation\": string}"
            ),
        },
    ]
    llm_output = _call_nim_chat(messages=messages, api_key=resolved_key, model=model, temperature=0.3)
    if not llm_output:
        raise RuntimeError("NIM rerank request failed or returned empty output.")
    try:
        parsed = json.loads(llm_output.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError("NIM rerank request returned invalid JSON.") from exc
    idx = _to_int(parsed.get("selected_index", 0), 0)
    if not (0 <= idx < len(candidates)):
        raise RuntimeError("NIM rerank output selected an invalid candidate index.")
    return candidates[idx][0], str(parsed.get("explanation", ""))


def recommend_from_vibe(
    vibe_text: str,
    csv_path: str = "data/cleanedClassicHits.csv",
    k: int = 10,
    nim_api_key: Optional[str] = None,
    model: str = DEFAULT_NIM_MODEL,
    max_year: Optional[int] = None,
) -> Dict[str, Any]:
    songs = load_songs(csv_path)
    if max_year is not None:
        songs = [song for song in songs if _to_int(song.get("year", 0), 0) <= max_year]
        if not songs:
            raise ValueError(f"No songs found at or before year {max_year}.")
    index = build_song_index(songs)
    user_profile = parse_user_vibe(vibe_text=vibe_text, nim_api_key=nim_api_key, model=model)
    candidates = retrieve_top_k(user_profile=user_profile, index=index, k=k)
    best_song, explanation = rerank_with_llm(
        vibe_text=vibe_text,
        user_profile=user_profile,
        candidates=candidates,
        nim_api_key=nim_api_key,
        model=model,
    )
    return {
        "user_profile": user_profile,
        "best_song": best_song,
        "explanation": explanation,
        "top_matches": candidates,
        "conversion_note": user_profile.get(
            "conversion_note",
            "Converted your current taste into an old-time equivalent.",
        ),
    }
