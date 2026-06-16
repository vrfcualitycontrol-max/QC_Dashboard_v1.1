# Dashboard SC - Frontend
# Version: 1.2.4
# Build: 20260511

FROM nginx:alpine

# Copy nginx server-block configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy frontend files (multi-page)
COPY *.html /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/
COPY logo/ /usr/share/nginx/html/logo/

# Optional: Create directories for reports and docs if they are mounted later
RUN mkdir -p /usr/share/nginx/html/reports /usr/share/nginx/html/docs

# Note: reports/ and *.pdf not copied (optional during build)

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/index.html || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
