import asyncio
import random
from dataclasses import dataclass
from temporalio import activity


@dataclass
class ExpensiveActivityParam:
    input: int


@dataclass
class ExpensiveActivityResult:
    cost: int


@activity.defn
async def expensive_activity(param: ExpensiveActivityParam) -> ExpensiveActivityResult:
    s: int = random.randrange(param.input)
    await asyncio.sleep(50 / 1000 * s)
    return ExpensiveActivityResult(cost=s)


@dataclass
class UnreliableActivityParam:
    input: int


@activity.defn
async def unreliable_activity(param: UnreliableActivityParam):
    s: int = random.randrange(param.input)
    if s < (3 * param.input / 4):
        raise Exception("unexpected error executing expensive activity")
