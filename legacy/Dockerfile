FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
COPY scripts ./scripts

RUN pip install --no-cache-dir uv && uv pip install --system -e .

CMD ["uvicorn", "ecms.main:app", "--host", "0.0.0.0", "--port", "8000"]
