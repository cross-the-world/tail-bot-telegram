# Tail Bot

## Install

```
# install Python >=3.7

pip3 install --upgrade setuptools

pip3 install numpy scipy matplotlib voila pandas sympy nose

pip3 install python-telegram-bot
```

## Configuration
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
# python bot.py
python3 tail.py

```

## Deploy
```
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
