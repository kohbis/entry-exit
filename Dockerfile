FROM python:3.7

ENV LANG "C.UTF-8"
ENV APP_ROOT /app

WORKDIR $APP_ROOT
COPY . $APP_ROOT

RUN apt update -y \
    && apt install -y --no-install-recommends \
        vim git less zip \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p ${APP_ROOT}/package

RUN pip install \
        requests \
        pytz \
        boto3 \
        --target ${APP_ROOT}/package

EXPOSE 5000
