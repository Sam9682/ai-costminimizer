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

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -e .

# Create necessary directories for AWS credentials
RUN mkdir -p /root/.aws
RUN mkdir -p /root/cow

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
ENTRYPOINT ["CostMinimizer"]
CMD  ["--configure", "--auto-update-conf"]

# example of docker execution command
# CostExplorer :
#               docker run -it -v $HOME/.aws:/root/.aws -v $HOME/cow:/root/cow -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN costminimizer --ce
# ComputeOptimizer :
#               docker run -it -v $HOME/.aws:/root/.aws -v $HOME/cow:/root/cow -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN costminimizer --co
# docker run -it -v $HOME/.aws:/root/.aws -v $HOME/cow:/root/cow -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN --entrypoint /bin/bash costminimizer
