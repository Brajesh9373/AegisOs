"""Standalone test: mem0 with CommandCode LLM (patched) + HuggingFace embedder."""
import sys, os, shutil
sys.path.insert(0, "src")
os.environ["OPENAI_API_KEY"] = "REDACTED_COMMAND_CODE_KEY"

# Patch mem0's OpenAILLM before importing Memory
from legacy_ecms.memory.mem0_llm_adapter import patch_mem0_llm
patch_mem0_llm()

# Clean slate + ensure paths exist
qdrant_path = os.path.abspath("./data/mem0_qdrant")
mem0_home = os.path.abspath("./data/mem0_home")
os.makedirs(qdrant_path, exist_ok=True)
os.makedirs(mem0_home, exist_ok=True)
for p in [qdrant_path, mem0_home]:
    try:
        shutil.rmtree(p, ignore_errors=True)
        os.makedirs(p, exist_ok=True)
    except:
        pass

from mem0 import Memory

config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "deepseek/deepseek-v4-flash",
            "temperature": 0.1,
            "api_key": os.environ["OPENAI_API_KEY"],
            "openai_base_url": "https://api.commandcode.ai/provider/v1",
        },
    },
    "embedder": {
        "provider": "huggingface",
        "config": {
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "embedding_dims": 384,
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "path": qdrant_path,
            "embedding_model_dims": 384,
            "on_disk": True,
        },
    },
    "history_db_path": os.path.join(mem0_home, "history.db"),
}

print("Creating Memory...")
m = Memory.from_config(config)

print("Adding...")
try:
    r = m.add("Alex is a software engineer who loves basketball.", user_id="alex")
    print(f"  OK: {r}")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {str(e)[:300]}")

print("Searching...")
try:
    r = m.search("basketball", filters={"user_id": "alex"})
    print(f"  OK: {r}")
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {str(e)[:300]}")

print("Done.")
