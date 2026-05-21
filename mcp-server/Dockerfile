FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose MCP server port
EXPOSE 8000

# Entrypoint sources shared env vars from terraform-setup
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["python", "mcp_server.py"]
