import redis.asyncio as aioredis
from src.config import settings

JTI_EXP = 864000


# client = aioredis.from_url(url=settings.REDIS_URI, decode_responses=True)

client = aioredis.Redis(
    host=settings.REDIS_URI,
    port=6379,
    password=settings.REDIS_TOKEN,
    ssl=True,
)


async def add_token_to_blacklist(jti: str):
    await client.set(name=jti, value=jti, ex=JTI_EXP)


async def token_in_blacklist(jti: str):
    jti_info = await client.get(jti)
    print("RETURNED JTI INFO: ", jti_info)
    return jti_info is not None
