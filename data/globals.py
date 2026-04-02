import asyncio
from collections import defaultdict

EVENT_BUFFERS = defaultdict(asyncio.Queue)