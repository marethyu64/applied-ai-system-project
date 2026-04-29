"""
Command-line runner for converting modern taste into classic equivalents.
"""

import os
from .recommender import recommend_from_vibe


def _ask_optional_int(prompt: str, min_value: int, max_value: int) -> int | None:
    raw = input(prompt).strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        print("Invalid number; skipping this preference.")
        return None
    if value < min_value or value > max_value:
        print(f"Out of range ({min_value}-{max_value}); skipping this preference.")
        return None
    return value


def _collect_follow_up_preferences() -> tuple[str, int | None]:
    year_cutoff = _ask_optional_int(
        "Songs before what year? (press Enter to skip) > ",
        1900,
        2000,
    )
    mood = input(
        "Desired mood (e.g. chill, happy, dark, intense) (Enter to skip) > "
    ).strip()
    energy = _ask_optional_int(
        "Desired energy (1-10) (Enter to skip) > ",
        1,
        10,
    )
    preferences = input(
        "Any preferred genres or artists? Or anything you'd like to avoid? (Enter to skip) > "
    ).strip()

    details: list[str] = []
    if year_cutoff is not None:
        details.append(f"release year before {year_cutoff}")
    if mood:
        details.append(f"desired mood: {mood}")
    if energy is not None:
        details.append(f"desired energy: {energy}/10")
    if preferences:
        details.append(f"preferences and avoids: {preferences}")

    if not details:
        return "", year_cutoff
    return "Follow-up preferences: " + "; ".join(details), year_cutoff


def main() -> None:
    csv_path = "data/cleanedClassicHits.csv"
    nim_api_key = os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NIM_API_KEY")
    if not nim_api_key:
        raise ValueError("NIM API key is required. Set NVIDIA_NIM_API_KEY or NIM_API_KEY.")

    print("Old Time Music Recommender")
    print("Describe your current taste (artists/genres/vibe), and I'll convert it to what you'd like if you were born in the 1900s!")
    print("Example: 'I like Kanye West style hype tracks.'")
    print("After each vibe, I'll ask 3 quick follow-up questions for better matches.")
    print("Type 'quit' to exit.\n")

    while True:
        vibe = input("Current taste > ").strip()
        if not vibe:
            print("Please enter a vibe description.\n")
            continue
        if vibe.lower() in {"quit", "exit"}:
            print("Goodbye.")
            break

        follow_up_text, year_cutoff = _collect_follow_up_preferences()
        enriched_vibe = vibe if not follow_up_text else f"{vibe}\n{follow_up_text}"

        try:
            result = recommend_from_vibe(
                vibe_text=enriched_vibe,
                csv_path=csv_path,
                k=10,
                nim_api_key=nim_api_key,
                max_year=year_cutoff,
            )
        except (ValueError, RuntimeError) as exc:
            print(f"{exc}\n")
            continue

        best_song = result["best_song"]
        print("\nBest old-time equivalent:")
        print(f"- {best_song.get('title', 'Unknown')} | {best_song.get('artist', 'Unknown')}")
        print(f"- Genre: {best_song.get('genre', 'unknown')}")
        print(f"- Year: {best_song.get('year', 'unknown')}")
        print(f"- Conversion: {result.get('conversion_note', 'N/A')}")
        print(f"- Explanation: {result['explanation']}\n")

        print("Top retrieved matches:")
        for rank, (song, score) in enumerate(result["top_matches"][:5], start=1):
            print(
                f"{rank}. {song.get('title', 'Unknown')} | {song.get('artist', 'Unknown')} "
                f"| {song.get('genre', 'unknown')} | {song.get('year', 'unknown')} "
                f"| similarity={score:.3f}"
            )
        print()


if __name__ == "__main__":
    main()
