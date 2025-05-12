FROM python:3.13-slim

# Ensure pip is up to date (optional, but recommended)
RUN pip install --upgrade pip

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of application code
COPY . .

# Expose the port for documentation; actual binding is in docker‑compose
EXPOSE 8000

# launch FastAPI via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
