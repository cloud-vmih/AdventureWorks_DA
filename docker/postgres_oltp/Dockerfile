FROM postgres:16

RUN apt-get update \
    && apt-get -y install --no-install-recommends unzip ruby dos2unix \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir /data
COPY install.sql /data/
COPY update_csvs.rb /data/
COPY data.zip /data/
RUN cd /data && \
    mkdir raw && \
    unzip data.zip -d raw && \
    find raw -type f -name '*.csv' -exec cp {} . \; && \
    rm -rf raw && \
    rm data.zip && \
    ruby update_csvs.rb && \
    rm update_csvs.rb

COPY install.sh /docker-entrypoint-initdb.d/
WORKDIR /data/
RUN dos2unix /docker-entrypoint-initdb.d/*.sh
