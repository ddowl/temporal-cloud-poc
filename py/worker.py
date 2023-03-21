import asyncio
from datetime import datetime, timedelta
import logging
import sys
from temporalio.worker import Worker
from temporalio import workflow
from temporalio import activity

from activity import expensive_activity, unreliable_activity
from client import create_temporal_client
from constants import TASK_QUEUE_NAME
from workflow import DummyWorkflow

namespace, cert_path, key_path, codec_key = sys.argv[1:]


@workflow.defn(sandboxed=False)
class ReturnFortyTwo:
    """Test workflow"""

    @workflow.run
    async def run(self) -> int:
        return 42


@workflow.defn(sandboxed=False)
class PrintCurrentDate:
    """Test workflow"""

    @workflow.run
    async def run(self) -> datetime:
        return await workflow.execute_activity(
            print_current_date, schedule_to_close_timeout=timedelta(seconds=5)
        )


@activity.defn
async def print_current_date() -> datetime:
    now = workflow.now()
    logging.getLogger().info("current time: %s", now)
    return now


async def main():
    print("Creating client to Temporal Cloud...")
    client = await create_temporal_client(namespace, cert_path, key_path, codec_key)

    print("Running worker...")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[DummyWorkflow, ReturnFortyTwo, PrintCurrentDate],
        activities=[expensive_activity, unreliable_activity, print_current_date],
    )
    await worker.run()


# Run async main w/ graceful keyboard interrupt shutdown

if __name__ == "__main__":
    asyncio.run(main())

