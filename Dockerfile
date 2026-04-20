# Dashboard SC - Frontend
# Version: 1.2.3
# Build: 20260420

FROM nginx:alpine

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy frontend files
COPY index.html /usr/share/nginx/html/
COPY variant_retail_finance_logo.jpg /usr/share/nginx/html/

# Create directories for reports and docs
RUN mkdir -p /usr/share/nginx/html/reports /usr/share/nginx/html/docs

# Note: reports/ and *.pdf not copied (optional during build)

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/index.html || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
