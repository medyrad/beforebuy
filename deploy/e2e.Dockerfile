FROM node:24.11.0-alpine3.22@sha256:f36fed0b2129a8492535e2853c64fbdbd2d29dc1219ee3217023ca48aebd3787 AS dependencies
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

FROM mcr.microsoft.com/playwright:v1.65.1-noble@sha256:1507cbfc550a63a6b7396791ca4f00df17beb56342d2447b3f106c306f525579
WORKDIR /app/frontend
COPY --from=dependencies /build/node_modules /app/node_modules
RUN ln -s /app/node_modules /app/frontend/node_modules
COPY frontend/ ./
COPY tests/ /app/tests/
CMD ["npx", "playwright", "test", "--config=playwright.config.ts"]
