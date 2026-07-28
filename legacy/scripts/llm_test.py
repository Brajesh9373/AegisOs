"""Test: exactly how does the LLM call work vs fail?"""
import openai, asyncio, os
os.environ["OPENAI_API_KEY"] = "REDACTED_COMMAND_CODE_KEY"

async def test():
    client = openai.AsyncOpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url="https://api.commandcode.ai/provider/v1/",
        timeout=15,
    )
    try:
        r = await client.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": "say ok"}],
            max_tokens=5,
        )
        print(f"OK: {r.choices[0].message.content}")
    except Exception as e:
        print(f"FAIL: {type(e).__name__}: {e}")

asyncio.run(test())
