# Versions are explicit; Node and Poetry are build-only tools.
FROM node:22.19.0-bookworm-slim@sha256:4a4884e8a44826194dff92ba316264f392056cbe243dcc9fd3551e71cea02b90 AS charts
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --omit=dev --no-audit --no-fund

FROM python:3.13.7-slim-bookworm@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d AS python-base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

FROM python-base AS dependencies
RUN pip install --no-cache-dir poetry==2.5.1
WORKDIR /app
ENV POETRY_VIRTUALENVS_IN_PROJECT=true POETRY_NO_INTERACTION=1
COPY pyproject.toml poetry.lock README.md ./
RUN poetry check --lock && poetry install --only main --no-root --no-directory --no-ansi

FROM python-base AS api
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH"
COPY --from=dependencies /app/.venv /app/.venv
COPY contracts/ contracts/
COPY persistence/ persistence/
COPY bootstrap/ bootstrap/
COPY bridge_node/ bridge_node/
COPY hub_client/ hub_client/
COPY orca_provision/ orca_provision/
COPY orchestration/ orchestration/
COPY topology/ topology/
COPY metabolism/ metabolism/
COPY mocks/ mocks/
COPY viz/*.py viz/
COPY demo/data/mock-run.json demo/data/mock-run.json
COPY --from=charts /build/node_modules/echarts/dist/echarts.min.js node_modules/echarts/dist/echarts.min.js
COPY LICENSE THIRD_PARTY_NOTICES.md /app/notices/
COPY --from=charts /build/node_modules/echarts/LICENSE /app/notices/LICENSE-echarts.txt
COPY deploy/healthcheck.py deploy/smoke.py /app/deploy/
USER 10001:10001
EXPOSE 7500
ENTRYPOINT ["python", "-m", "viz.server", "--host", "0.0.0.0", "--port", "7500"]
CMD ["--input", "demo/data/mock-run.json"]

FROM nginx:1.28.0-alpine@sha256:30f1c0d78e0ad60901648be663a710bdadf19e4c10ac6782c235200619158284 AS web
# Built UI comes from the reviewed integration commit. No UI build or rewrite.
COPY viz/static/ /srv/morphogenesis/
COPY --from=charts /build/node_modules/echarts/dist/echarts.min.js /srv/morphogenesis/vendor/echarts.min.js
COPY --from=charts /build/node_modules/echarts/LICENSE /srv/morphogenesis/licenses/LICENSE-echarts.txt
COPY deploy/nginx.conf /etc/nginx/nginx.conf
COPY deploy/proxy.conf /etc/nginx/morphogenesis-proxy.conf
USER 101:101
EXPOSE 8080
ENTRYPOINT ["nginx", "-g", "daemon off;"]
