# Dockerfile
FROM node:24-alpine

WORKDIR /app
COPY . .
RUN npm install
RUN npm run build

EXPOSE 5173
CMD ["npm", "run", "dev"]
