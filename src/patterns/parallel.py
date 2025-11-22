import asyncio
from typing import Any, Coroutine, List


async def fan_out_fan_in(coroutines: List[Coroutine]) -> List[Any]:
    """Execute multiple coroutines in parallel and return all results."""
    return await asyncio.gather(*coroutines, return_exceptions=True)
