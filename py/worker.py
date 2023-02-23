import asyncio
import sys
from temporalio.worker import Worker

from activity import expensive_activity, unreliable_activity
from client import create_temporal_client
from constants import TASK_QUEUE_NAME
from workflow import DummyWorkflow

namespace, cert_path, key_path = sys.argv[1:]

interrupt_event = asyncio.Event()


async def main():
    print("Creating client to Temporal Cloud...")
    client = await create_temporal_client(namespace, cert_path, key_path)

    print("Running worker...")
    worker = Worker(
        client,
        task_queue=TASK_QUEUE_NAME,
        workflows=[DummyWorkflow],
        activities=[expensive_activity, unreliable_activity],
    )
    async with worker:
        print("Worker started, ctrl+c to exit")
        await interrupt_event.wait()
        print("Shutting down worker")


# Run async main w/ graceful keyboard interrupt shutdown

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        interrupt_event.set()
        loop.run_until_complete(loop.shutdown_asyncgens())
