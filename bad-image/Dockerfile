FROM python:3.8-slim

ADD . /app

RUN pip install --no-cache-dir pillow==8.2.0
RUN pip install --no-cache-dir cryptography==3.3.1
RUN pip install --no-cache-dir pyyaml==5.3.1
RUN pip install --no-cache-dir urllib3==1.25.8
RUN pip install --no-cache-dir werkzeug==0.16.1
RUN pip install --no-cache-dir django==2.2.28
RUN pip install --no-cache-dir boto3 pytest pandas numpy

ENV SECRET_KEY=mysupersecretkey123abc
ENV DATABASE_PASSWORD=Admin123!
ENV AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
ENV AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
ENV STRIPE_SECRET_KEY=sk_live_abcdefghijklmnop123
ENV GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
ENV DATABASE_URL=postgresql://admin:password123@prod-db.internal:5432/mydb
ENV REDIS_PASSWORD=redis_secret_456

EXPOSE 22
EXPOSE 3306
EXPOSE 5432
EXPOSE 80

CMD ["python", "/app/app.py"]
