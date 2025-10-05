FROM node:20-alpine

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@9.1.2 --activate

COPY apps/web/package.json apps/web/pnpm-lock.yaml* ./apps/web/
RUN cd apps/web && pnpm install

COPY . .

EXPOSE 5173
CMD ["pnpm", "--dir", "apps/web", "dev", "--host", "0.0.0.0", "--port", "5173"]
