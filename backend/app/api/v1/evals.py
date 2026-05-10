from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.core.auth import get_current_user
from app.services.dynamodb import get_eval_scores
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentEvalScore(BaseModel):
    agentName: str
    faithfulness: float
    answerRelevancy: float
    hallucinationScore: float
    contextPrecision: float
    contextRecall: float
    answerCorrectness: float
    timestamp: str
    scanId: str


class EvalTrend(BaseModel):
    date: str
    agentName: str
    averageScore: float


class EvalSummary(BaseModel):
    totalEvaluations: int
    flaggedResponses: int
    worstPerformingAgent: str
    scores: list[AgentEvalScore]
    trends: list[EvalTrend]


@router.get("/{repo_id}", response_model=EvalSummary)
async def get_eval_summary(
    repo_id: str,
    user: dict = Depends(get_current_user),
) -> EvalSummary:
    items = await get_eval_scores(user["user_id"], repo_id)

    scores: list[AgentEvalScore] = []
    flagged = 0

    for item in items:
        score = AgentEvalScore(
            agentName=item.get("agent_name", ""),
            faithfulness=float(item.get("faithfulness", 0.0)),
            answerRelevancy=float(item.get("answer_relevancy", 0.0)),
            hallucinationScore=float(item.get("hallucination_score", 0.0)),
            contextPrecision=float(item.get("context_precision", 0.0)),
            contextRecall=float(item.get("context_recall", 0.0)),
            answerCorrectness=float(item.get("answer_correctness", 0.0)),
            timestamp=item.get("timestamp", ""),
            scanId=item.get("scan_id", ""),
        )
        scores.append(score)
        avg = (
            score.faithfulness
            + score.answerRelevancy
            + score.contextPrecision
            + score.contextRecall
            + score.answerCorrectness
        ) / 5
        if avg < 0.6:
            flagged += 1

    worst = (
        min(scores, key=lambda s: (s.faithfulness + s.answerRelevancy) / 2).agentName
        if scores
        else ""
    )

    trends: list[EvalTrend] = [
        EvalTrend(
            date=s.timestamp[:10],
            agentName=s.agentName,
            averageScore=(s.faithfulness + s.answerRelevancy) / 2,
        )
        for s in scores
    ]

    return EvalSummary(
        totalEvaluations=len(items),
        flaggedResponses=flagged,
        worstPerformingAgent=worst,
        scores=scores,
        trends=trends,
    )
