FROM python:3.12-alpine
WORKDIR /app
COPY monitor.py dashboard.html ./
EXPOSE 8765
CMD ["python3", "monitor.py"]
