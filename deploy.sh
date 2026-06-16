#!/bin/bash
set -e

echo "🔄 Pulling latest changes..."
cd /opt/qc-dashboard
git pull origin main

echo "🏗️ Rebuilding containers..."
docker-compose -f docker-compose.prod.yml up -d --build

echo "🧹 Cleaning old images..."
docker image prune -f

echo "✅ Deploy complete!"
echo "📊 Status:"
docker-compose -f docker-compose.prod.yml ps
