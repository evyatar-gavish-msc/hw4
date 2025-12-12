FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pet_store.py .
RUN mkdir -p images

ENV MONGO_URI=mongodb://localhost:27017/

EXPOSE 5001

CMD ["python", "pet_store.py"]
