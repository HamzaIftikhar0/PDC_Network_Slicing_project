# Simple production Dockerfile for Next.js
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the app
COPY . .

# Build Next.js app
RUN npm run build

# Next.js default production port
EXPOSE 3000

# Start Next.js in production mode
CMD ["npm", "start"]
