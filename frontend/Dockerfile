FROM node:20-alpine

# Work directory inside container
WORKDIR /app

# Install curl so healthcheck works
RUN apk add --no-cache curl

# Expose Next.js dev port
EXPOSE 3000

# Run Next dev server via npm script
CMD ["npm", "run", "dev"]
