# keepalive
Discord Bot to keep threads from expiring


## Installation

Create a new Discord Bot in the Discord developer console. Remember to select
"Bot" and "applications.commands" in OAuth2->URL Generator else your Bot will 
not work.


## Usage

The bot exports three (slash) commands:

 * `/addthread <thread ID>|all` to either keep the given thread ID alive or all threads alive.
 * `/rmthread <thread ID>` to stop keeping the given thread ID alive
 * `/lsthread` to list all thread IDs being kept alive
 
 The way any given thread is kept alive is by sending a message to it and then deleting it.


## Configuration

Create a .env file in the bot directory with two variables:

```
KEEPALIVE_BOT_SECRET="your bot token"
KEEPALIVE_CRONTAB="your bot crontab for keeping threads alive"
```

One good schedule to keep threads alive, IMHO is

```
KEEPALIVE_CRONTAB="0 1 * * *"
```

Meaning send a keep-alive message to all monitored threads every day at 1 AM.
