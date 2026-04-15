FROM python:3.10-slim

WORKDIR /app

# =========================
# SYSTEM DEPENDENCIES
# =========================
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# =========================
# PYTHON DEPENDENCIES (CACHE OPTIMIZED)
# =========================
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# =========================
# COPY PROJECT
# =========================
COPY . .

# =========================
# ENVIRONMENT
# =========================
ENV PYTHONUNBUFFERED=1

# =========================
# DEFAULT CMD (API ONLY)
# =========================
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
