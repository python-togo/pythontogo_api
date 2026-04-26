from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from app.core.security import get_current_user, require_permission
from app.database.connection import get_db_connection
from app.schemas.models import (
    AuthenticatedUser,
    TalkReviewCreate,
    TalkStatusUpdate,
)
from app.core.settings import logger
from app.utils.responses import success
from app.utils.send_email import build_talk_decision_email, send_email
from app.utils.pagination import paginate

api_router = APIRouter(prefix="/cfp", tags=["CFP Review"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _get_proposal_or_404(db, proposal_id: str) -> dict:
    async with db.cursor() as cur:
        await cur.execute(
            """
            SELECT p.id, p.title, p.status, p.speaker_full_name, p.speaker_email,
                   e.title AS event_title
            FROM proposals p
            JOIN events e ON e.id = p.event_id
            WHERE p.id = %s
            """,
            (proposal_id,),
        )
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    cols = ["id", "title", "status", "speaker_full_name", "speaker_email", "event_title"]
    return dict(zip(cols, row))


async def _has_reviewed(db, proposal_id: str, reviewer_id: str) -> bool:
    async with db.cursor() as cur:
        await cur.execute(
            "SELECT 1 FROM talk_reviews WHERE proposal_id = %s AND reviewer_id = %s",
            (proposal_id, reviewer_id),
        )
        return (await cur.fetchone()) is not None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@api_router.get("/talks")
async def list_talks_with_scores(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    _: AuthenticatedUser = Depends(require_permission("proposals:read")),
    db=Depends(get_db_connection),
):
    """List all proposals enriched with their average review score."""
    try:
        rows, total = await paginate(
            db,
            """
            SELECT
                p.id, p.title, p.status, p.session_type, p.language,
                p.speaker_full_name, p.speaker_email, p.created_at,
                e.code AS event_code, e.title AS event_title,
                COALESCE(s.avg_score, NULL)::float AS avg_score,
                COALESCE(s.review_count, 0)::int  AS review_count
            FROM proposals p
            JOIN events e ON e.id = p.event_id
            LEFT JOIN talk_avg_scores s ON s.proposal_id = p.id
            ORDER BY p.created_at DESC
            """,
            (),
            page, per_page,
        )
        cols = [
            "id", "title", "status", "session_type", "language",
            "speaker_full_name", "speaker_email", "created_at",
            "event_code", "event_title", "avg_score", "review_count",
        ]
        talks = [dict(zip(cols, row)) for row in rows]
        return success(talks, total=total, page=page, per_page=per_page)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error listing talks with scores: %s", e)
        raise HTTPException(status_code=500, detail="Error listing talks")


@api_router.get("/talks/{proposal_id}")
async def get_talk_detail(
    proposal_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("proposals:read")),
    db=Depends(get_db_connection),
):
    """Full proposal detail. Reviews are masked if the caller hasn't voted yet (unless admin)."""
    try:
        proposal = await _get_proposal_or_404(db, proposal_id)

        async with db.cursor() as cur:
            # Avg score
            await cur.execute(
                "SELECT avg_score, review_count FROM talk_avg_scores WHERE proposal_id = %s",
                (str(proposal["id"]),),
            )
            score_row = await cur.fetchone()
            proposal["avg_score"] = float(score_row[0]) if score_row else None
            proposal["review_count"] = int(score_row[1]) if score_row else 0

            # Reviews — masked unless admin or already reviewed
            already_reviewed = await _has_reviewed(db, str(proposal["id"]), str(current_user.id))
            can_see_all = current_user.is_admin or already_reviewed

            if can_see_all:
                await cur.execute(
                    """
                    SELECT tr.id, tr.reviewer_id, u.username AS reviewer_username,
                           tr.score, tr.comment, tr.created_at
                    FROM talk_reviews tr
                    JOIN users u ON u.id = tr.reviewer_id
                    WHERE tr.proposal_id = %s
                    ORDER BY tr.created_at
                    """,
                    (str(proposal["id"]),),
                )
                rev_rows = await cur.fetchall()
                rev_cols = ["id", "reviewer_id", "reviewer_username", "score", "comment", "created_at"]
                proposal["reviews"] = [dict(zip(rev_cols, r)) for r in rev_rows]
                proposal["reviews_masked"] = False
            else:
                await cur.execute(
                    "SELECT COUNT(*) FROM talk_reviews WHERE proposal_id = %s",
                    (str(proposal["id"]),),
                )
                count_row = await cur.fetchone()
                proposal["reviews"] = []
                proposal["reviews_masked"] = True
                proposal["total_reviews"] = int(count_row[0])

        return success(proposal)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving talk detail %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail="Error retrieving talk detail")


@api_router.post("/talks/{proposal_id}/reviews", status_code=status.HTTP_201_CREATED)
async def submit_review(
    proposal_id: str,
    payload: TalkReviewCreate,
    current_user: AuthenticatedUser = Depends(require_permission("proposals:review")),
    db=Depends(get_db_connection),
):
    """Submit a score + optional comment for a proposal. One review per reviewer."""
    try:
        await _get_proposal_or_404(db, proposal_id)

        async with db.cursor() as cur:
            try:
                await cur.execute(
                    """
                    INSERT INTO talk_reviews (proposal_id, reviewer_id, score, comment)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, proposal_id, reviewer_id, score, comment, created_at, updated_at
                    """,
                    (proposal_id, str(current_user.id), payload.score, payload.comment),
                )
            except Exception as db_exc:
                if "uq_tr_proposal_reviewer" in str(db_exc):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="You have already submitted a review for this proposal",
                    )
                raise
            row = await cur.fetchone()
        await db.commit()

        cols = ["id", "proposal_id", "reviewer_id", "score", "comment", "created_at", "updated_at"]
        return success(dict(zip(cols, row)), code=201)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error submitting review for %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail="Error submitting review")


@api_router.get("/talks/{proposal_id}/reviews")
async def get_reviews(
    proposal_id: str,
    current_user: AuthenticatedUser = Depends(require_permission("proposals:read")),
    db=Depends(get_db_connection),
):
    """
    Return reviews for a proposal.
    - Admin: always sees all reviews.
    - Reviewer: sees all reviews only after submitting their own; otherwise sees only aggregate count.
    """
    try:
        await _get_proposal_or_404(db, proposal_id)
        already_reviewed = await _has_reviewed(db, proposal_id, str(current_user.id))
        can_see_all = current_user.is_admin or already_reviewed

        async with db.cursor() as cur:
            if can_see_all:
                await cur.execute(
                    """
                    SELECT tr.id, tr.reviewer_id, u.username AS reviewer_username,
                           tr.score, tr.comment, tr.created_at, tr.updated_at
                    FROM talk_reviews tr
                    JOIN users u ON u.id = tr.reviewer_id
                    WHERE tr.proposal_id = %s
                    ORDER BY tr.created_at
                    """,
                    (proposal_id,),
                )
                rows = await cur.fetchall()
                cols = ["id", "reviewer_id", "reviewer_username", "score", "comment", "created_at", "updated_at"]
                return success({"reviews": [dict(zip(cols, r)) for r in rows], "masked": False})
            else:
                await cur.execute(
                    "SELECT COUNT(*) FROM talk_reviews WHERE proposal_id = %s",
                    (proposal_id,),
                )
                count_row = await cur.fetchone()
                return success({
                    "masked": True,
                    "has_reviewed": False,
                    "total_reviews": int(count_row[0]),
                    "message": "Submit your review to unlock all scores.",
                })
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching reviews for %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail="Error fetching reviews")


@api_router.patch("/talks/{proposal_id}/status")
async def update_talk_status(
    proposal_id: str,
    payload: TalkStatusUpdate,
    background_tasks: BackgroundTasks,
    _: AuthenticatedUser = Depends(require_permission("proposals:update")),
    db=Depends(get_db_connection),
):
    """Change proposal status and notify the speaker by email (background task)."""
    try:
        proposal = await _get_proposal_or_404(db, proposal_id)
        new_status = payload.status.value

        async with db.cursor() as cur:
            await cur.execute(
                """
                UPDATE proposals
                SET status = %s, updated_at = NOW()
                WHERE id = %s
                RETURNING id, title, status, updated_at
                """,
                (new_status, proposal_id),
            )
            row = await cur.fetchone()
        await db.commit()

        # Trigger email notification to speaker
        if new_status in ("accepted", "rejected", "waitlisted"):
            subject, text_body, html_body = build_talk_decision_email(
                speaker_name=proposal["speaker_full_name"],
                talk_title=proposal["title"],
                status=new_status,
                event_title=proposal["event_title"],
            )
            background_tasks.add_task(
                send_email,
                to=proposal["speaker_email"],
                subject=subject,
                body_html=html_body,
                body_text=text_body,
            )

        cols = ["id", "title", "status", "updated_at"]
        return success(dict(zip(cols, row)))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating status for proposal %s: %s", proposal_id, e)
        raise HTTPException(status_code=500, detail="Error updating talk status")
