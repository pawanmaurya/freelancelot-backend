FROM python:3.11-slim

WORKDIR /app

# Install Postgres client (for pg_isready)
RUN apt-get update && apt-get install -y postgresql-client

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make sure wait-for-it.sh is executable
RUN chmod +x wait-for-it.sh

EXPOSE 8000

# NOTE: CMD will be overridden by docker-compose.yml, so this is fine.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
