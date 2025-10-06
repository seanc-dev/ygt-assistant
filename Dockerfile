FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY core/ ./core/
COPY infra/ ./infra/
COPY utils/ ./utils/
COPY adapters/ ./adapters/
COPY config/ ./config/
COPY settings.py .
COPY calendar_agent_eventkit.py .
COPY openai_client.py .
COPY main.py .
COPY presentation/api/ ./presentation/api/

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "presentation.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
