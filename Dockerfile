FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY a7a0_bot/ a7a0_bot/
COPY play.py online_loop.py player_index.json ./

CMD ["python", "play.py", "-g", "0", "-t", "3", "--focus", "achievements"]
