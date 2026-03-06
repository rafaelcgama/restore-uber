FROM python:3.13-slim

WORKDIR /usr/src/app

# Environment variables should be managed via .env and Docker Compose
# to avoid baking secrets into the image.

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD python ./main.py