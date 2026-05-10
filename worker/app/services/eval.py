import asyncio
from typing import Any
from app.services.dynamodb import store_eval_scores
from app.services.s3 import upload_eval_log
import logging

logger = logging.getLogger(__name__)


async def run_ragas_evaluation(
    user_id: str,
    repo_id: str,
    scan_id: str,
    agent_outputs: dict[str, Any],
) -> None:
    try:
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
        )
        from ragas import evaluate
        from datasets import Dataset

        eval_scores: dict[str, dict] = {}

        for agent_name, agent_output in agent_outputs.items():
            if not agent_output:
                continue

            questions = _build_questions_for_agent(agent_name, agent_output)
            if not questions:
                continue

            dataset = Dataset.from_list(questions)

            try:
                result = evaluate(
                    dataset,
                    metrics=[
                        faithfulness,
                        answer_relevancy,
                        context_precision,
                        context_recall,
                        answer_correctness,
                    ],
                )

                scores_df = result.to_pandas()
                avg_scores = scores_df.mean(numeric_only=True).to_dict()

                eval_scores[agent_name] = {
                    "faithfulness": float(avg_scores.get("faithfulness", 0.0)),
                    "answer_relevancy": float(avg_scores.get("answer_relevancy", 0.0)),
                    "hallucination_score": float(1.0 - avg_scores.get("faithfulness", 1.0)),
                    "context_precision": float(avg_scores.get("context_precision", 0.0)),
                    "context_recall": float(avg_scores.get("context_recall", 0.0)),
                    "answer_correctness": float(avg_scores.get("answer_correctness", 0.0)),
                }
            except Exception as exc:
                logger.warning("Ragas evaluation failed for agent %s: %s", agent_name, exc)
                eval_scores[agent_name] = _default_scores()

        if eval_scores:
            await asyncio.gather(
                store_eval_scores(user_id, repo_id, scan_id, eval_scores),
                upload_eval_log(scan_id, {"scan_id": scan_id, "scores": eval_scores}),
            )
            logger.info("Ragas evaluation complete for scan %s", scan_id)

    except ImportError:
        logger.warning("Ragas not available, skipping evaluation")
    except Exception as exc:
        logger.error("Ragas evaluation error for scan %s: %s", scan_id, exc)


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
