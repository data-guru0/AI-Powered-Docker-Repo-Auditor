import asyncio
import math
from typing import Any
from app.services.dynamodb import store_eval_scores
from app.services.s3 import upload_eval_log
import logging

logger = logging.getLogger(__name__)


def _safe(v: float) -> float:
    return 0.0 if (math.isnan(v) or math.isinf(v)) else v


def _run_ragas_for_agent(agent_name: str, questions: list[dict]) -> dict:
    """Synchronous ragas evaluation — runs in a thread pool to avoid blocking the event loop."""
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
        answer_correctness,
    )
    from ragas import evaluate
    from datasets import Dataset

    dataset = Dataset.from_list(questions)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness],
    )
    scores_df = result.to_pandas()
    avg = scores_df.mean(numeric_only=True).to_dict()

    fs = _safe(float(avg.get("faithfulness", 0.0)))
    return {
        "faithfulness": fs,
        "answer_relevancy": _safe(float(avg.get("answer_relevancy", 0.0))),
        "hallucination_score": _safe(1.0 - fs),
        "context_precision": _safe(float(avg.get("context_precision", 0.0))),
        "context_recall": _safe(float(avg.get("context_recall", 0.0))),
        "answer_correctness": _safe(float(avg.get("answer_correctness", 0.0))),
    }


async def run_ragas_evaluation(
    user_id: str,
    repo_id: str,
    scan_id: str,
    agent_outputs: dict[str, Any],
) -> None:
    try:
        import importlib
        if importlib.util.find_spec("ragas") is None:
            logger.warning("Ragas package not installed, skipping evaluation")
            return

        eval_scores: dict[str, dict] = {}
        loop = asyncio.get_event_loop()

        for agent_name, agent_output in agent_outputs.items():
            if not agent_output:
                continue

            questions = _build_questions_for_agent(agent_name, agent_output)
            if not questions:
                continue

            try:
                scores = await asyncio.wait_for(
                    loop.run_in_executor(None, _run_ragas_for_agent, agent_name, questions),
                    timeout=90,
                )
                eval_scores[agent_name] = scores
                logger.info("Ragas eval done for agent %s: faithfulness=%.2f", agent_name, scores["faithfulness"])
            except asyncio.TimeoutError:
                logger.warning("Ragas timed out for agent %s, using default scores", agent_name)
                eval_scores[agent_name] = _default_scores()
            except Exception as exc:
                logger.warning("Ragas failed for agent %s: %s", agent_name, exc, exc_info=True)
                eval_scores[agent_name] = _default_scores()

        if eval_scores:
            await asyncio.gather(
                store_eval_scores(scan_id, repo_id, eval_scores),
                upload_eval_log(scan_id, {"scan_id": scan_id, "scores": eval_scores}),
            )
            logger.info("Ragas evaluation complete for scan %s — %d agents scored", scan_id, len(eval_scores))

    except Exception as exc:
        logger.error("Ragas evaluation error for scan %s: %s", scan_id, exc, exc_info=True)


def _build_questions_for_agent(agent_name: str, output: Any) -> list[dict]:
    if not output:
        return []

    context = str(output)[:2000] if not isinstance(output, str) else output[:2000]

    questions_map: dict[str, list[str]] = {
        "cve": [
            "What are the most critical CVEs in this image?",
            "Which CVEs have known exploits?",
        ],
        "bloat": [
            "What are the main sources of bloat in this image?",
            "Which layers contain the most unnecessary files?",
        ],
        "base_image": [
            "Is the current base image up to date?",
            "What base image migration is recommended?",
        ],
        "risk": [
            "What is the overall security posture of this image?",
            "What are the top 3 actions to improve the image?",
        ],
        "dockerfile": [
            "What optimizations were made to the Dockerfile?",
            "How much size reduction was achieved?",
        ],
    }

    questions = questions_map.get(agent_name, ["What did this agent find?"])
    return [
        {
            "question": q,
            "answer": context,
            "contexts": [context],
            "ground_truth": context,
        }
        for q in questions
    ]


def _default_scores() -> dict:
    return {
        "faithfulness": 0.0,
        "answer_relevancy": 0.0,
        "hallucination_score": 1.0,
        "context_precision": 0.0,
        "context_recall": 0.0,
        "answer_correctness": 0.0,
    }
