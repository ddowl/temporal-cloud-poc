from dataclasses import dataclass
from datetime import timedelta
from temporalio import workflow, common

from activity import (
    ExpensiveActivityParam,
    UnreliableActivityParam,
    expensive_activity,
    unreliable_activity,
)


@dataclass
class WorkflowParams:
    A: int
    B: int


@dataclass
class WorkflowResult:
    Status: str
    Res: int


@workflow.defn
class DummyWorkflow:
    @workflow.run
    async def run(self, params: WorkflowParams) -> WorkflowResult:
        retry_policy = common.RetryPolicy(
            initial_interval=timedelta(milliseconds=100),
            backoff_coefficient=1.2,
            maximum_interval=timedelta(seconds=100),
            maximum_attempts=10,  # use `0` for unlimited retry attempts
        )

        activity_options = workflow.ActivityConfig(
            start_to_close_timeout=timedelta(minutes=1), retry_policy=retry_policy
        )

        await workflow.execute_activity(
            unreliable_activity, UnreliableActivityParam(params.A), **activity_options
        )

        expensive_result = await workflow.execute_activity(
            expensive_activity, ExpensiveActivityParam(params.B), **activity_options
        )

        return WorkflowResult(Status="COMPLETE", Res=expensive_result.cost)
