FROM node:20-alpine

ENV PNPM_HOME=/root/.local/share/pnpm
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable

WORKDIR /app

COPY package.json tsconfig.json next.config.mjs tailwind.config.ts postcss.config.js eslint.config.mjs .prettierrc.json ./
COPY app ./app

RUN pnpm install

EXPOSE 3000
CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "3000"]
