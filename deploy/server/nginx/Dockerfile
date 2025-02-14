# Use the official Nginx image
FROM nginx:latest

# Copy Nginx configuration files into the container
COPY ./nginx/* /etc/nginx/

# Set the correct permissions
RUN chmod -R 644 /etc/nginx/*.conf && \
    chmod 755 /etc/nginx && \
    chown -R root:root /etc/nginx
