# 1. Python ka chota version use karo
FROM python:3.10-slim

# 2. System update karo aur FFmpeg install karo (Video banane ke liye zaroori)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# 3. Folder set karo
WORKDIR /app

# 4. Libraries install karo
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Sara code copy karo
COPY . .

# 6. Default Command (Railway isay override kar sakta hai)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]