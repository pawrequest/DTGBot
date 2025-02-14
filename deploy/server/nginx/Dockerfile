# Use the official Nginx image
FROM nginx:latest

# Copy configuration files into the container
COPY ./conf.d /etc/nginx/conf.d

# Set the correct permissions for the config files
RUN chmod -R 644 /etc/nginx/conf.d/*.conf && \
    chmod 755 /etc/nginx && \
    chown -R root:root /etc/nginx