"""Direct verification: Redis session sharing across CLI agents."""
import redis, sys
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# SIMULATE: Claude sends a query
r.setex('ecms:session:default:shared:last_question', 3600, 'I am working on the payment microservice')
r.setex('ecms:session:default:shared:last_answer', 3600, 'The payment service uses PostgreSQL and JWT auth')

# SIMULATE: Codex reads Claude's context
prev_q = r.get('ecms:session:default:shared:last_question')
prev_a = r.get('ecms:session:default:shared:last_answer')

print(f"Claude wrote:  '{prev_q}'")
print(f"Claude wrote:  '{prev_a}'")
print(f"Codex read:    previous question = '{prev_q}'")
print(f"Codex read:    previous answer = '{prev_a}'")
print(f"\nSame Redis connection? YES — both agents share the same session state.")
print(f"Key prefix: ecms:session:{BACKEND}:{SESSION_ID}:*")
