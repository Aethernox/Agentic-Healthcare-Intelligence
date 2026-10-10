"""
MLflow 3 configuration for MedMap agent tracing.
Sets up experiment tracking and agent step logging.
"""
import mlflow
import functools
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)

EXPERIMENT_NAME = "/medmap/agent-runs"
MODEL_NAME = "medmap-healthcare-agent"


def setup_mlflow(tracking_uri: str = "databricks"):
    """Initialize MLflow with Databricks backend."""
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    logger.info(f"MLflow initialized: {tracking_uri} / {EXPERIMENT_NAME}")


def trace_agent_step(step_name: str):
    """
    Decorator to trace individual agent steps with MLflow.
    Logs inputs, outputs, duration, and any errors.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with mlflow.start_run(nested=True, run_name=step_name):
                mlflow.log_param("step", step_name)
                try:
                    result = await func(*args, **kwargs)
                    mlflow.log_param("status", "success")
                    return result
                except Exception as e:
                    mlflow.log_param("status", "failed")
                    mlflow.log_param("error", str(e)[:500])
                    raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with mlflow.start_run(nested=True, run_name=step_name):
                mlflow.log_param("step", step_name)
                try:
                    result = func(*args, **kwargs)
                    mlflow.log_param("status", "success")
                    return result
                except Exception as e:
                    mlflow.log_param("status", "failed")
                    mlflow.log_param("error", str(e)[:500])
                    raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def log_search_run(
    query: str,
    results_count: int,
    trust_distribution: dict,
    tavily_triggered: int,
    run_id: str = None,
) -> str:
    """Log a complete search agent run to MLflow."""
    with mlflow.start_run(run_name=f"search: {query[:30]}") as run:
        mlflow.log_param("query", query)
        mlflow.log_metric("results_count", results_count)
        mlflow.log_metric("tavily_triggered", tavily_triggered)
        mlflow.log_metrics({
            "trust_high": trust_distribution.get("high", 0),
            "trust_medium": trust_distribution.get("medium", 0),
            "trust_low": trust_distribution.get("low", 0),
        })
        return run.info.run_id
