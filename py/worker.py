import asyncio
import sys
from temporalio.worker import Worker

from activity import expensive_activity, unreliable_activity
from client import create_temporal_client
from constants import TASK_QUEUE_NAME
from workflow import DummyWorkflow

namespace, cert_path, key_path = sys.argv[1:]


async def run_worker():
    print("Creating client to Temporal Cloud...")
    client = await create_temporal_client(namespace, cert_path, key_path)

    print("Running worker...")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[DummyWorkflow],
        activities=[expensive_activity, unreliable_activity],
    )
    await worker.run()


asyncio.run(run_worker())
