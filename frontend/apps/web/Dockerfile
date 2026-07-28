FROM node:20-alpine AS alpine
RUN apk update && apk add --no-cache libc6-compat

FROM alpine AS pruner
WORKDIR /app
RUN npm install -g turbo
COPY . .
RUN turbo prune @aegisos/web --docker

FROM alpine AS installer
WORKDIR /app
RUN npm install -g pnpm
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/pnpm-lock.yaml ./pnpm-lock.yaml
RUN pnpm install --frozen-lockfile
COPY --from=pruner /app/out/full/ .
COPY tsconfig.base.json tsconfig.base.json
COPY turbo.json turbo.json
RUN pnpm --filter @aegisos/web build

FROM alpine AS runner
WORKDIR /app
RUN npm install -g serve
COPY --from=installer /app/apps/web/dist ./dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
