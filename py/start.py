import asyncio
import sys

from client import create_temporal_client
from constants import TASK_QUEUE_NAME
from workflow import DummyWorkflow, WorkflowParams

namespace, cert_path, key_path = sys.argv[1:]


async def main():
    client = await create_temporal_client(namespace, cert_path, key_path)

    params = WorkflowParams(A=7, B=10)
    print("Executing dummy workflow with params: ", params)

    workflow_res = await client.execute_workflow(
        DummyWorkflow.run, params, id="dummy-task-py-101", task_queue=TASK_QUEUE_NAME,
    )

    print("Result of dummy workflow: ", workflow_res)

    """
    Alternatively, can get intantiate a workflow via `client.start_workflow` for a WorkflowHandle (https://python.temporal.io/temporalio.client.WorkflowHandle.html)
    which allows you to query its metadata, send it signals, and wait for its result
    """


asyncio.run(main())
