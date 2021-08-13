ARG PYTHON_VERSION=3.9.1

FROM python:${PYTHON_VERSION}
ARG PYTHON_VERSION
RUN echo "Building with Python version $PYTHON_VERSION"

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir --disable-pip-version-check virtualenv && \
    virtualenv .venv && \
    . .venv/bin/activate && \
    pip install --no-cache-dir --disable-pip-version-check -r requirements.txt && \
    python -m unittest discover -p '*_test.py'

FROM python:${PYTHON_VERSION}-slim

RUN useradd -u 1000 user
COPY --chown=1000:1000 --from=0 /app /app
RUN pip install --no-cache-dir --disable-pip-version-check virtualenv

RUN chmod +x /app/container_start.sh

# Security context in k8s requires uid as user
USER 1000

WORKDIR /app

CMD ["/app/container_start.sh"]
