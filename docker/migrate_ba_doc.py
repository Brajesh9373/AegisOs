#!/usr/bin/env python3
"""Migrate existing BA Discovery sessions to Knowledge Base documents."""
import psycopg2

PROJECT_ID = "79fc1d88-afac-4029-9a26-666a2d9f832f"
SESSION_ID = f"ba-{PROJECT_ID}"
DOC_ID = f"doc-{PROJECT_ID}-discovery"

conn = psycopg2.connect("postgresql://ecms:ecms@localhost:5432/ecms")
cur = conn.cursor()

# Get messages
cur.execute(
    "SELECT role, content FROM session_messages WHERE session_id = %s ORDER BY created_at",
    (SESSION_ID,),
)
rows = cur.fetchall()
if not rows:
    print("No messages found for session", SESSION_ID)
    exit()

lines = ["# BA Discovery Transcript", ""]
for role, content in rows:
    if not content:
        continue
    label = "**You**" if role == "user" else "**Business Analyst**"
    lines.append(label)
    lines.append("")
    lines.append(content)
    lines.append("")
    lines.append("---")
    lines.append("")

md_content = "\n".join(lines)
uri = f"knowledge/{PROJECT_ID}/ba-discovery-transcript.md"

# Check if document already exists
cur.execute("SELECT 1 FROM artifacts WHERE id = %s", (DOC_ID,))
if cur.fetchone():
    print("Document already exists, skipping insert")
else:
    cur.execute(
        """INSERT INTO artifacts (id, projectid, name, type, content, uri, storagepath, agentid, createdat, versionhistory)
           VALUES (%s, %s, %s, %s, %s, %s, %s, NULL, now(), '{}')
           ON CONFLICT (id) DO NOTHING""",
        (DOC_ID, PROJECT_ID, "ba-discovery-transcript.md", "Discovery",
         md_content, uri, uri),
    )
    print("Created Discovery document:", DOC_ID)

# Delete old BA session (messages cascade via FK)
cur.execute("DELETE FROM sessions WHERE id = %s", (SESSION_ID,))
print(f"Deleted old BA session: {cur.rowcount} row(s)")

conn.commit()
cur.close()
conn.close()
print("Done!")
