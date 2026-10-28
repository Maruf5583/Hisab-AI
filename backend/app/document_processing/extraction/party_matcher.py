import uuid
from typing import Optional, Tuple, List
from rapidfuzz import fuzz, process
from sqlalchemy.orm import Session
from app.models.party import Party


def match_party_name(
    candidate_name: str,
    business_id: uuid.UUID,
    db: Session,
    threshold: float = 75.0,
) -> Tuple[Optional[uuid.UUID], Optional[str], float]:
    """Find the best matching Party in the database using fuzzy token similarity.
    
    Returns (matched_party_id, matched_party_name, match_score).
    If no match achieves the threshold, returns (None, None, highest_score).
    """
    if not candidate_name or len(candidate_name.strip()) < 2:
        return None, None, 0.0

    parties: List[Party] = db.query(Party).filter(
        Party.business_id == business_id,
        Party.is_active.is_(True),
    ).all()

    if not parties:
        return None, None, 0.0

    clean_candidate = candidate_name.strip().lower()
    best_party: Optional[Party] = None
    best_score: float = 0.0

    for party in parties:
        party_name_clean = party.name.strip().lower()
        score = fuzz.token_sort_ratio(clean_candidate, party_name_clean)
        if score > best_score:
            best_score = float(score)
            best_party = party

    if best_party and best_score >= threshold:
        return best_party.id, best_party.name, best_score

    return None, None, best_score
