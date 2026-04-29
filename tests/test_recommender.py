from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    build_song_index,
    parse_user_vibe,
    retrieve_top_k,
)
import pytest

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_parse_user_vibe_requires_nim_api_key():
    with pytest.raises(ValueError):
        parse_user_vibe("chill acoustic 70s soul", nim_api_key=None)


def test_parse_user_vibe_requires_nim_api_key_for_modern_style():
    with pytest.raises(ValueError):
        parse_user_vibe("I like hip hop trap with high energy", nim_api_key=None)


def test_retrieve_top_k_returns_sorted_similarity():
    songs = [
        {
            "id": 1,
            "title": "Energetic Rock Song",
            "artist": "A",
            "genre": "Rock",
            "mood": "unknown",
            "energy": 0.9,
            "tempo_bpm": 145.0,
            "valence": 0.6,
            "danceability": 0.7,
            "acousticness": 0.1,
            "instrumentalness": 0.0,
            "liveness": 0.2,
            "popularity": 50,
            "year": 1986,
        },
        {
            "id": 2,
            "title": "Soft Acoustic Ballad",
            "artist": "B",
            "genre": "Soul",
            "mood": "unknown",
            "energy": 0.3,
            "tempo_bpm": 85.0,
            "valence": 0.4,
            "danceability": 0.4,
            "acousticness": 0.85,
            "instrumentalness": 0.0,
            "liveness": 0.1,
            "popularity": 45,
            "year": 1974,
        },
    ]
    index = build_song_index(songs)
    user_profile = {
        "genre": "rock",
        "energy": 0.88,
        "tempo_bpm": 140.0,
        "valence": 0.6,
        "danceability": 0.68,
        "acousticness": 0.15,
        "instrumentalness": 0.0,
        "liveness": 0.2,
        "popularity": 40,
        "year": 1985,
    }
    results = retrieve_top_k(user_profile, index, k=2)
    assert len(results) == 2
    assert results[0][0]["title"] == "Energetic Rock Song"
    assert results[0][1] >= results[1][1]
