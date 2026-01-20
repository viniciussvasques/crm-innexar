FROM node:20-alpine

WORKDIR /app

# Copiar package files
COPY package*.json ./

# Instalar dependências
RUN npm install

# Copiar código
COPY . .

# Build de produção
RUN npm run build

# Expor porta
EXPOSE 3000

# Comando para produção
CMD ["npm", "start"]

