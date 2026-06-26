FROM python:3.12-slim-bullseye

RUN apt update && apt install build-essential -y

# Clear unused files
RUN apt clean && \
    rm -rf \
	/tmp/* \
	/var/lib/apt/lists/* \
	/var/tmp/*

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./albion_assistant ./

ENV mysqlTableConfig=setting mysqlTableRegister=user mysqlTableBlacklist=blacklist mysqlTableGuild=guild mysqlTableAlliance=alliance mysqlTableRegion=regions

CMD [ "python", "main.py" ]