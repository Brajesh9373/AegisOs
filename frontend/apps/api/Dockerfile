FROM node:20-alpine AS alpine
RUN apk update && apk add --no-cache libc6-compat

FROM alpine AS pruner
WORKDIR /app
RUN npm install -g turbo
COPY . .
RUN turbo prune @aegisos/api --docker

FROM alpine AS installer
WORKDIR /app
RUN npm install -g pnpm
COPY --from=pruner /app/out/json/ .
COPY --from=pruner /app/out/pnpm-lock.yaml ./pnpm-lock.yaml
RUN pnpm install --frozen-lockfile
COPY --from=pruner /app/out/full/ .
COPY tsconfig.base.json tsconfig.base.json
COPY turbo.json turbo.json
RUN pnpm build --filter=@aegisos/api...
RUN pnpm deploy --filter=@aegisos/api --prod /prod/api

FROM alpine AS runner
WORKDIR /app
COPY --from=installer /prod/api ./
EXPOSE 3001
CMD ["node", "dist/index.js"]
