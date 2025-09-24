FROM python:3.11-slim

RUN groupadd --system labs && useradd --system --gid labs --create-home labs

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R labs:labs /app

USER labs

CMD ["pytest", "-q"]
