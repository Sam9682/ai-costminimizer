FROM public.ecr.aws/docker/library/python:3.12

WORKDIR /app

RUN apt-get update && apt-get install -y curl unzip && \
    cmlog=/opt/costminimizer.log && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" >> "$cmlog" 2>&1 && \
    unzip -o awscliv2.zip >> "$cmlog" 2>&1 && \
    ./aws/install >> "$cmlog" 2>&1 && \
    rm -rf awscliv2.zip aws && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and setup files
COPY requirements.txt .
COPY setup.py .
COPY src/ ./src/

# Install dependencies including Flask
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir flask flask-cors
RUN pip install -e .

# Create necessary directories for AWS credentials
RUN mkdir -p /root/.aws
RUN mkdir -p /root/cow

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src/CostMinimizer/web/app.py

# Expose port for web interface
EXPOSE 8000

# Default command - run web interface
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=8000"]

# Alternative commands:
# CLI mode:
#   docker run -it -v $HOME/.aws:/root/.aws -v $HOME/cow:/root/cow -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN --entrypoint CostMinimizer costminimizer --ce
# Web mode (default):
#   docker run -p 8000:8000 -v $HOME/cow:/root/cow costminimizer
# Interactive shell:
#   docker run -it -v $HOME/.aws:/root/.aws -v $HOME/cow:/root/cow -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN --entrypoint /bin/bash costminimizer
