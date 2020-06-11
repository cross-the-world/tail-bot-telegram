# Tail Bot

## Install
```
# install Python >=3.8
pip3 install --upgrade setuptools
pip3 install numpy scipy matplotlib voila pandas sympy nose
pip3 install python-telegram-bot

# or with requirements
pip3 -r ./requirements.txt
```

## Configuration
such the configuration should be save in secrets "CONFIG_JSON", when runner is inuse

[User info in Telegram](https://bigone.zendesk.com/hc/en-us/articles/360008014894-How-to-get-the-Telegram-user-ID-)
```
{
  "telegram": {
    "token": "xxx",
    "path": "path_file_1,path_file_2,...",
    "n": 5,
    "offset": 0, # minus m last lines of n last lines
    "interval": "10s" # unit: s, m (minute), h, d, w, M (month)
  },
  "valid_users": [
    "username"
  ],
  "valid_ids": [
    userid
  ]

}
```

## Test
```
python3 src/tail.py
```

## Deploy

### Without Docker
[Python packages](#Install)

```
# Copy source to server "/opt/bots/tail-bot-telegram/"
# Copy file config.json to "/opt/bots/tail-bot-telegram/config/"

# link service
ln -s /opt/bots/tail-bot-telegram/service/taillogs_bot.service /lib/systemd/system/

# reset daemon
sudo systemctl daemon-reload

# enable service
sudo systemctl enable taillogs_bot.service

# start/stop/restart/status
# status ACTIVE is OK
sudo systemctl [start|stop|restart|status] taillogs_bot.service

```

### With Docker
```
# re-build images, base on docker-compose.yml and Dockerfile
docker-compose build .

# force remove old containers
docker-compose rm -fs

# up in background
docker-compose up -d
```

### Autodeploy

#### Runner
[Runner deploy](https://github.com/cross-the-world/github-runner)

#### Secrets

##### DC_HOST
```
server_ip
```

##### DC_PORT
```
ssh_port, e.g. 25000
```

##### DC_USER
```
user, e.g. github
```

##### DC_KEY
e.g.
```
private_key, e.g. $server> cat ~/.ssh/id_rsa
```

##### DC_PASS
in case DC_PASS is not inuse 
```
xxx
```
  
##### CONFIG_JSON
[Configuartion](#Configuration)

#### Workflow
* Checkout
* Create config.json
* Copy to server
* Clear config.json
* Deploy on server
