FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 canarygraph
USER canarygraph

EXPOSE 8000
CMD ["uvicorn", "canarygraph.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

