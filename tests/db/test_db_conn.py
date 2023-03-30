import sys
from pathlib import Path

import pytest

path = Path(__file__).parents[2].joinpath("Bot")
sys.path.append(str(path))


from Libs.utils.postgresql import PrismaClientSession
from prisma.models import User


@pytest.mark.asyncio
async def test_prisma_client_session():
    async with PrismaClientSession():
        res = await User.prisma().find_first(where={"id": 454357482102587393})
        assert (res is None) or (isinstance(res, User))  # nosec
