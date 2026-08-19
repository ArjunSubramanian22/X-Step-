FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt pyproject.toml ./
COPY xstep_ml ./xstep_ml
COPY api ./api
COPY artifacts ./artifacts
COPY scripts ./scripts
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080
CMD ["python", "-m", "api.main"]
