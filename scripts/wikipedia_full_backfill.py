"""Vollständiger Wikipedia-Backfill für ALLE Falken-Saisons + Liga-Saisons.

Holt für jede Saison sowohl den DEL2/Oberliga-Saison-Artikel als auch
spezifische Falken-Artikel + Trainer-Artikel.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql
from falken_kb.genai.dgx_client import DGXClient
from falken_kb.ingestion.scrapers.wikipedia_loader import load_wikipedia_season
from falken_kb.ingestion.scrapers.wikipedia import WikipediaScraper, label_variants


# Zusätzliche Wikipedia-Artikel-Titel die nicht über fetch_season_context kommen
ADDITIONAL_TITLES = [
    "Heilbronner Falken",          # Hauptartikel
    "Heilbronner EC",              # Vorgänger-Verein
    "Eishalle Heilbronn",          # Heimstätte
    "Kolbenschmidt Arena",         # Alternativname
    "DEL2",                        # Liga
    "Oberliga (Eishockey)",        # Liga
    "2. Eishockey-Bundesliga",     # historische Liga
]


async def fetch_additional(scraper: WikipediaScraper, dgx: DGXClient) -> dict:
    """Holt + speichert die zusätzlichen Allgemein-Artikel."""
    from falken_kb.db import supabase
    results = {}
    for title in ADDITIONAL_TITLES:
        try:
            page = await scraper.get_page(title)
            if page["missing"] or not page["extract"]:
                continue
            from falken_kb.ingestion.scrapers.wikipedia_loader import chunk_text
            chunks = chunk_text(page["extract"], max_chars=1500)
            for i, chunk in enumerate(chunks):
                url = f"https://de.wikipedia.org/wiki/{title.replace(' ', '_')}#chunk-{i}"
                emb = dgx.embed_one(chunk)
                supabase().table("falken_articles").upsert({
                    "source": "wikipedia",
                    "url": url,
                    "title": title,
                    "body": chunk,
                    "embedding": emb,
                }, on_conflict="url").execute()
            results[title] = len(chunks)
            print(f"  ✓ {title}: {len(chunks)} chunks")
        except Exception as e:
            print(f"  ✗ {title}: {str(e)[:80]}")
    return results


async def main():
    print("=== Wikipedia FULL Backfill ===\n")
    dgx = DGXClient()

    # 1. Zusätzliche Allgemeinartikel
    print("## A) Allgemein-Artikel")
    async with WikipediaScraper() as s:
        await fetch_additional(s, dgx)

    # 2. Saison-Artikel für ALLE Falken-Saisons
    print("\n## B) Saison-Artikel (alle Falken-Saisons)")
    seasons = exec_sql("""
        SELECT DISTINCT s.label
        FROM falken.seasons s
        JOIN falken.team_seasons ts ON ts.season_id = s.id
        JOIN falken.teams t ON t.id = ts.team_id
        WHERE t.name = 'Heilbronner Falken' AND s.label >= '2010/11'
        ORDER BY s.label DESC
    """)
    for s in seasons:
        try:
            res = await load_wikipedia_season(s["label"], dgx)
            print(f"  ✓ {s['label']}: {res['articles']} Artikel, {res['chunks']} chunks")
        except Exception as e:
            print(f"  ✗ {s['label']}: {str(e)[:80]}")

    print("\n=== DONE ===")


if __name__ == "__main__":
    asyncio.run(main())
