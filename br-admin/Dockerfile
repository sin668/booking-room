FROM docker.m.daocloud.io/node:22
ENV TZ Asia/Shanghai
WORKDIR /home
COPY . /home
RUN npm install -g pnpm
RUN pnpm install
CMD ["pnpm", "dev"]
