"""Ingestion pipeline for loading congress data from unitedstates/congress JSON files.

Loads legislators, bills, votes, vote records, and bill text into the data_science_dev database.
Expects the parent directory to contain congress-tracker/ and congress-legislators/ as siblings.

Usage:
    ingest-congress /path/to/parent/
    ingest-congress /path/to/parent/ --congress 118
    ingest-congress /path/to/parent/ --congress 118 --only bills
"""

from __future__ import annotations

import logging
from pathlib import Path  # noqa: TC003 needed at runtime for typer CLI argument
from typing import TYPE_CHECKING, Annotated

import orjson
import typer
import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from python.common import configure_logger
from python.orm.common import get_postgres_engine
from python.orm.data_science_dev.congress import Bill, BillText, Legislator, LegislatorSocialMedia, Vote, VoteRecord

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

BATCH_SIZE = 10_000

app = typer.Typer(help="Ingest unitedstates/congress data into data_science_dev.")


@app.command()
def main(
    parent_dir: Annotated[
        Path,
        typer.Argument(help="Parent directory containing congress-tracker/ and congress-legislators/"),
    ],
    congress: Annotated[int | None, typer.Option(help="Only ingest a specific congress number")] = None,
    only: Annotated[
        str | None,
        typer.Option(help="Only run a specific step: legislators, social-media, bills, votes, bill-text"),
    ] = None,
) -> None:
    """Ingest congress data from unitedstates/congress JSON files."""
    configure_logger(level="INFO")

    data_dir = parent_dir / "congress-tracker/congress/data/"
    legislators_dir = parent_dir / "congress-legislators"

    if not data_dir.is_dir():
        typer.echo(f"Expected congress-tracker/ directory: {data_dir}", err=True)
        raise typer.Exit(code=1)

    if not legislators_dir.is_dir():
        typer.echo(f"Expected congress-legislators/ directory: {legislators_dir}", err=True)
        raise typer.Exit(code=1)

    engine = get_postgres_engine(name="DATA_SCIENCE_DEV")

    congress_dirs = _resolve_congress_dirs(data_dir, congress)
    if not congress_dirs:
        typer.echo("No congress directories found.", err=True)
        raise typer.Exit(code=1)

    logger.info("Found %d congress directories to process", len(congress_dirs))

    steps: dict[str, tuple] = {
        "legislators": (ingest_legislators, (engine, legislators_dir)),
        "legislators-social-media": (ingest_social_media, (engine, legislators_dir)),
        "bills": (ingest_bills, (engine, congress_dirs)),
        "votes": (ingest_votes, (engine, congress_dirs)),
        "bill-text": (ingest_bill_text, (engine, congress_dirs)),
    }

    if only:
        if only not in steps:
            typer.echo(f"Unknown step: {only}. Choose from: {', '.join(steps)}", err=True)
            raise typer.Exit(code=1)
        steps = {only: steps[only]}

    for step_name, (step_func, step_args) in steps.items():
        logger.info("=== Starting step: %s ===", step_name)
        step_func(*step_args)
        logger.info("=== Finished step: %s ===", step_name)

    logger.info("ingest-congress done")


def _resolve_congress_dirs(data_dir: Path, congress: int | None) -> list[Path]:
    """Find congress number directories under data_dir."""
    if congress is not None:
        target = data_dir / str(congress)
        return [target] if target.is_dir() else []
    return sorted(path for path in data_dir.iterdir() if path.is_dir() and path.name.isdigit())


def _flush_batch(session: Session, batch: list[object], label: str) -> int:
    """Add a batch of ORM objects to the session and commit. Returns count added."""
    if not batch:
        return 0
    session.add_all(batch)
    session.commit()
    count = len(batch)
    logger.info("Committed %d %s", count, label)
    batch.clear()
    return count


# ---------------------------------------------------------------------------
# Legislators — loaded from congress-legislators YAML files
# ---------------------------------------------------------------------------


def ingest_legislators(engine: Engine, legislators_dir: Path) -> None:
    """Load legislators from congress-legislators YAML files."""
    legislators_data = _load_legislators_yaml(legislators_dir)
    logger.info("Loaded %d legislators from YAML files", len(legislators_data))

    with Session(engine) as session:
        existing_legislators = {
            legislator.bioguide_id: legislator for legislator in session.scalars(select(Legislator)).all()
        }
        logger.info("Found %d existing legislators in DB", len(existing_legislators))

        total_inserted = 0
        total_updated = 0
        for entry in legislators_data:
            bioguide_id = entry.get("id", {}).get("bioguide")
            if not bioguide_id:
                continue

            fields = _parse_legislator(entry)
            if existing := existing_legislators.get(bioguide_id):
                changed = False
                for field, value in fields.items():
                    if value is not None and getattr(existing, field) != value:
                        setattr(existing, field, value)
                        changed = True
                if changed:
                    total_updated += 1
            else:
                session.add(Legislator(bioguide_id=bioguide_id, **fields))
                total_inserted += 1

        session.commit()
    logger.info("Inserted %d new legislators, updated %d existing", total_inserted, total_updated)


def _load_legislators_yaml(legislators_dir: Path) -> list[dict]:
    """Load and combine legislators-current.yaml and legislators-historical.yaml."""
    legislators: list[dict] = []
    for filename in ("legislators-current.yaml", "legislators-historical.yaml"):
        path = legislators_dir / filename
        if not path.exists():
            logger.warning("Legislators file not found: %s", path)
            continue
        with path.open() as file:
            data = yaml.safe_load(file)
            if isinstance(data, list):
                legislators.extend(data)
    return legislators


def _parse_legislator(entry: dict) -> dict:
    """Extract Legislator fields from a congress-legislators YAML entry."""
    ids = entry.get("id", {})
    name = entry.get("name", {})
    bio = entry.get("bio", {})
    terms = entry.get("terms", [])
    latest_term = terms[-1] if terms else {}

    fec_ids = ids.get("fec")
    fec_ids_joined = ",".join(fec_ids) if isinstance(fec_ids, list) else fec_ids

    chamber = latest_term.get("type")
    chamber_normalized = {"rep": "House", "sen": "Senate"}.get(chamber, chamber)

    return {
        "thomas_id": ids.get("thomas"),
        "lis_id": ids.get("lis"),
        "govtrack_id": ids.get("govtrack"),
        "opensecrets_id": ids.get("opensecrets"),
        "fec_ids": fec_ids_joined,
        "first_name": name.get("first"),
        "last_name": name.get("last"),
        "official_full_name": name.get("official_full"),
        "nickname": name.get("nickname"),
        "birthday": bio.get("birthday"),
        "gender": bio.get("gender"),
        "current_party": latest_term.get("party"),
        "current_state": latest_term.get("state"),
        "current_district": latest_term.get("district"),
        "current_chamber": chamber_normalized,
    }


# ---------------------------------------------------------------------------
# Social Media — loaded from legislators-social-media.yaml
# ---------------------------------------------------------------------------

SOCIAL_MEDIA_PLATFORMS = {
    "twitter": "https://twitter.com/{account}",
    "facebook": "https://facebook.com/{account}",
    "youtube": "https://youtube.com/{account}",
    "instagram": "https://instagram.com/{account}",
    "mastodon": None,
}


def ingest_social_media(engine: Engine, legislators_dir: Path) -> None:
    """Load social media accounts from legislators-social-media.yaml."""
    social_media_path = legislators_dir / "legislators-social-media.yaml"
    if not social_media_path.exists():
        logger.warning("Social media file not found: %s", social_media_path)
        return

    with social_media_path.open() as file:
        social_media_data = yaml.safe_load(file)

    if not isinstance(social_media_data, list):
        logger.warning("Unexpected format in %s", social_media_path)
        return

    logger.info("Loaded %d entries from legislators-social-media.yaml", len(social_media_data))

    with Session(engine) as session:
        legislator_map = _build_legislator_map(session)
        existing_accounts = {
            (account.legislator_id, account.platform)
            for account in session.scalars(select(LegislatorSocialMedia)).all()
        }
        logger.info("Found %d existing social media accounts in DB", len(existing_accounts))

        total_inserted = 0
        total_updated = 0
        for entry in social_media_data:
            bioguide_id = entry.get("id", {}).get("bioguide")
            if not bioguide_id:
                continue

            legislator_id = legislator_map.get(bioguide_id)
            if legislator_id is None:
                continue

            social = entry.get("social", {})
            for platform, url_template in SOCIAL_MEDIA_PLATFORMS.items():
                account_name = social.get(platform)
                if not account_name:
                    continue

                url = url_template.format(account=account_name) if url_template else None

                if (legislator_id, platform) in existing_accounts:
                    total_updated += 1
                else:
                    session.add(
                        LegislatorSocialMedia(
                            legislator_id=legislator_id,
                            platform=platform,
                            account_name=str(account_name),
                            url=url,
                            source="https://github.com/unitedstates/congress-legislators",
                        )
                    )
                    existing_accounts.add((legislator_id, platform))
                    total_inserted += 1

        session.commit()
    logger.info("Inserted %d new social media accounts, updated %d existing", total_inserted, total_updated)


def _iter_voters(position_group: object) -> Iterator[dict]:
    """Yield voter dicts from a vote position group (handles list, single dict, or string)."""
    if isinstance(position_group, dict):
        yield position_group
    elif isinstance(position_group, list):
        for voter in position_group:
            if isinstance(voter, dict):
                yield voter


# ---------------------------------------------------------------------------
# Bills
# ---------------------------------------------------------------------------


def ingest_bills(engine: Engine, congress_dirs: list[Path]) -> None:
    """Load bill data.json files."""
    with Session(engine) as session:
        existing_bills = {(bill.congress, bill.bill_type, bill.number) for bill in session.scalars(select(Bill)).all()}
        logger.info("Found %d existing bills in DB", len(existing_bills))

        total_inserted = 0
        batch: list[Bill] = []
        for congress_dir in congress_dirs:
            bills_dir = congress_dir / "bills"
            if not bills_dir.is_dir():
                continue
            logger.info("Scanning bills from %s", congress_dir.name)
            for bill_file in bills_dir.rglob("data.json"):
                data = _read_json(bill_file)
                if data is None:
                    continue
                bill = _parse_bill(data, existing_bills)
                if bill is not None:
                    batch.append(bill)
                    if len(batch) >= BATCH_SIZE:
                        total_inserted += _flush_batch(session, batch, "bills")

        total_inserted += _flush_batch(session, batch, "bills")
    logger.info("Inserted %d new bills total", total_inserted)


def _parse_bill(data: dict, existing_bills: set[tuple[int, str, int]]) -> Bill | None:
    """Parse a bill data.json dict into a Bill ORM object, skipping existing."""
    raw_congress = data.get("congress")
    bill_type = data.get("bill_type")
    raw_number = data.get("number")
    if raw_congress is None or bill_type is None or raw_number is None:
        return None
    congress = int(raw_congress)
    number = int(raw_number)
    if (congress, bill_type, number) in existing_bills:
        return None

    sponsor_bioguide = None
    sponsor = data.get("sponsor")
    if sponsor:
        sponsor_bioguide = sponsor.get("bioguide_id")

    return Bill(
        congress=congress,
        bill_type=bill_type,
        number=number,
        title=data.get("short_title") or data.get("official_title"),
        title_short=data.get("short_title"),
        official_title=data.get("official_title"),
        status=data.get("status"),
        status_at=data.get("status_at"),
        sponsor_bioguide_id=sponsor_bioguide,
        subjects_top_term=data.get("subjects_top_term"),
    )


# ---------------------------------------------------------------------------
# Votes (and vote records)
# ---------------------------------------------------------------------------


def ingest_votes(engine: Engine, congress_dirs: list[Path]) -> None:
    """Load vote data.json files with their vote records."""
    with Session(engine) as session:
        legislator_map = _build_legislator_map(session)
        logger.info("Loaded %d legislators into lookup map", len(legislator_map))
        bill_map = _build_bill_map(session)
        logger.info("Loaded %d bills into lookup map", len(bill_map))
        existing_votes = {
            (vote.congress, vote.chamber, vote.session, vote.number) for vote in session.scalars(select(Vote)).all()
        }
        logger.info("Found %d existing votes in DB", len(existing_votes))

        total_inserted = 0
        batch: list[Vote] = []
        for congress_dir in congress_dirs:
            votes_dir = congress_dir / "votes"
            if not votes_dir.is_dir():
                continue
            logger.info("Scanning votes from %s", congress_dir.name)
            for vote_file in votes_dir.rglob("data.json"):
                data = _read_json(vote_file)
                if data is None:
                    continue
                vote = _parse_vote(data, legislator_map, bill_map, existing_votes)
                if vote is not None:
                    batch.append(vote)
                    if len(batch) >= BATCH_SIZE:
                        total_inserted += _flush_batch(session, batch, "votes")

        total_inserted += _flush_batch(session, batch, "votes")
    logger.info("Inserted %d new votes total", total_inserted)


def _build_legislator_map(session: Session) -> dict[str, int]:
    """Build a mapping of bioguide_id -> legislator.id."""
    return {legislator.bioguide_id: legislator.id for legislator in session.scalars(select(Legislator)).all()}


def _build_bill_map(session: Session) -> dict[tuple[int, str, int], int]:
    """Build a mapping of (congress, bill_type, number) -> bill.id."""
    return {(bill.congress, bill.bill_type, bill.number): bill.id for bill in session.scalars(select(Bill)).all()}


def _parse_vote(
    data: dict,
    legislator_map: dict[str, int],
    bill_map: dict[tuple[int, str, int], int],
    existing_votes: set[tuple[int, str, int, int]],
) -> Vote | None:
    """Parse a vote data.json dict into a Vote ORM object with records."""
    raw_congress = data.get("congress")
    chamber = data.get("chamber")
    raw_number = data.get("number")
    vote_date = data.get("date")
    if raw_congress is None or chamber is None or raw_number is None or vote_date is None:
        return None

    raw_session = data.get("session")
    if raw_session is None:
        return None

    congress = int(raw_congress)
    number = int(raw_number)
    session_number = int(raw_session)

    # Normalize chamber from "h"/"s" to "House"/"Senate"
    chamber_normalized = {"h": "House", "s": "Senate"}.get(chamber, chamber)

    if (congress, chamber_normalized, session_number, number) in existing_votes:
        return None

    # Resolve linked bill
    bill_id = None
    bill_ref = data.get("bill")
    if bill_ref:
        bill_key = (
            int(bill_ref.get("congress", congress)),
            bill_ref.get("type"),
            int(bill_ref.get("number", 0)),
        )
        bill_id = bill_map.get(bill_key)

    raw_votes = data.get("votes", {})
    vote_counts = _count_votes(raw_votes)
    vote_records = _build_vote_records(raw_votes, legislator_map)

    return Vote(
        congress=congress,
        chamber=chamber_normalized,
        session=session_number,
        number=number,
        vote_type=data.get("type"),
        question=data.get("question"),
        result=data.get("result"),
        result_text=data.get("result_text"),
        vote_date=vote_date[:10] if isinstance(vote_date, str) else vote_date,
        bill_id=bill_id,
        vote_records=vote_records,
        **vote_counts,
    )


def _count_votes(raw_votes: dict) -> dict[str, int]:
    """Count voters per position category, correctly handling dict and list formats."""
    yea_count = 0
    nay_count = 0
    not_voting_count = 0
    present_count = 0

    for position, position_group in raw_votes.items():
        voter_count = sum(1 for _ in _iter_voters(position_group))
        if position in ("Yea", "Aye"):
            yea_count += voter_count
        elif position in ("Nay", "No"):
            nay_count += voter_count
        elif position == "Not Voting":
            not_voting_count += voter_count
        elif position == "Present":
            present_count += voter_count

    return {
        "yea_count": yea_count,
        "nay_count": nay_count,
        "not_voting_count": not_voting_count,
        "present_count": present_count,
    }


def _build_vote_records(raw_votes: dict, legislator_map: dict[str, int]) -> list[VoteRecord]:
    """Build VoteRecord objects from raw vote data."""
    records: list[VoteRecord] = []
    for position, position_group in raw_votes.items():
        for voter in _iter_voters(position_group):
            bioguide_id = voter.get("id")
            if not bioguide_id:
                continue
            legislator_id = legislator_map.get(bioguide_id)
            if legislator_id is None:
                continue
            records.append(
                VoteRecord(
                    legislator_id=legislator_id,
                    position=position,
                )
            )
    return records


# ---------------------------------------------------------------------------
# Bill Text
# ---------------------------------------------------------------------------


def ingest_bill_text(engine: Engine, congress_dirs: list[Path]) -> None:
    """Load bill text from text-versions directories."""
    with Session(engine) as session:
        bill_map = _build_bill_map(session)
        logger.info("Loaded %d bills into lookup map", len(bill_map))
        existing_bill_texts = {
            (bill_text.bill_id, bill_text.version_code) for bill_text in session.scalars(select(BillText)).all()
        }
        logger.info("Found %d existing bill text versions in DB", len(existing_bill_texts))

        total_inserted = 0
        batch: list[BillText] = []
        for congress_dir in congress_dirs:
            logger.info("Scanning bill texts from %s", congress_dir.name)
            for bill_text in _iter_bill_texts(congress_dir, bill_map, existing_bill_texts):
                batch.append(bill_text)
                if len(batch) >= BATCH_SIZE:
                    total_inserted += _flush_batch(session, batch, "bill texts")

        total_inserted += _flush_batch(session, batch, "bill texts")
    logger.info("Inserted %d new bill text versions total", total_inserted)


def _iter_bill_texts(
    congress_dir: Path,
    bill_map: dict[tuple[int, str, int], int],
    existing_bill_texts: set[tuple[int, str]],
) -> Iterator[BillText]:
    """Yield BillText objects for a single congress directory, skipping existing."""
    bills_dir = congress_dir / "bills"
    if not bills_dir.is_dir():
        return

    for bill_dir in bills_dir.rglob("text-versions"):
        if not bill_dir.is_dir():
            continue
        bill_key = _bill_key_from_dir(bill_dir.parent, congress_dir)
        if bill_key is None:
            continue
        bill_id = bill_map.get(bill_key)
        if bill_id is None:
            continue

        for version_dir in sorted(bill_dir.iterdir()):
            if not version_dir.is_dir():
                continue
            if (bill_id, version_dir.name) in existing_bill_texts:
                continue
            text_content = _read_bill_text(version_dir)
            version_data = _read_json(version_dir / "data.json")
            yield BillText(
                bill_id=bill_id,
                version_code=version_dir.name,
                version_name=version_data.get("version_name") if version_data else None,
                date=version_data.get("issued_on") if version_data else None,
                text_content=text_content,
            )


def _bill_key_from_dir(bill_dir: Path, congress_dir: Path) -> tuple[int, str, int] | None:
    """Extract (congress, bill_type, number) from directory structure."""
    congress = int(congress_dir.name)
    bill_type = bill_dir.parent.name
    name = bill_dir.name
    # Directory name is like "hr3590" — strip the type prefix to get the number
    number_str = name[len(bill_type) :]
    if not number_str.isdigit():
        return None
    return (congress, bill_type, int(number_str))


def _read_bill_text(version_dir: Path) -> str | None:
    """Read bill text from a version directory, preferring .txt over .xml."""
    for extension in ("txt", "htm", "html", "xml"):
        candidates = list(version_dir.glob(f"document.{extension}"))
        if not candidates:
            candidates = list(version_dir.glob(f"*.{extension}"))
        if candidates:
            try:
                return candidates[0].read_text(encoding="utf-8")
            except Exception:
                logger.exception("Failed to read %s", candidates[0])
    return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict | None:
    """Read and parse a JSON file, returning None on failure."""
    try:
        return orjson.loads(path.read_bytes())
    except FileNotFoundError:
        return None
    except Exception:
        logger.exception("Failed to parse %s", path)
        return None


if __name__ == "__main__":
    app()
