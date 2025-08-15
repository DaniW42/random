## Teslamate 

docker compose stack to be run behind nginx proxy manager

You need to add the following to your npm proxy host under Advanced:

```
location / {
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}```
