# Albion Online Assistant Bot

## Setting up with Docker

### Docker Compose

```docker
version: '3.3'
services:
    AlbionAssistant:
        container_name: AoAssistant
        environment:
            - mysqlUser=aoassisnant
            - mysqlPass=MY_SUPER_SECRET_MYSQL_PASSWORD
            - mysqlHost=mysql
            - mysqlPort=3306
            - mysqldb=albionAssistant
            - TOKEN=MY_SUPER_SECRET_TOKEN
        restart: always
        image: 'aoassistant:latest'
```

## Invite link

Those will be the permissions that the bot will have

![Permissions](./images/permissions_link.png)

### Link

```
https://discord.com/oauth2/authorize?client_id=INSERT_CLIENT_ID_HERE&scope=bot&permissions=2617338880
```
