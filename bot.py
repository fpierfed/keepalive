import atexit
import json
import os
import aiocron
import dotenv
from pincer import Client
import pincer
from pincer.commands import command
from pincer.objects import Guild, MessageContext


dotenv.load_dotenv()


STATE_FILE = 'state.json'
CRONTAB = os.environ.get('KEEPALIVE_CRONTAB', None) or '35 15 * * *'
TOKEN = os.environ['KEEPALIVE_BOT_SECRET']


class Bot(Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #
        # Note: it looks like types in Pincer are not very consistent. For
        # this reason we establish the following standard:
        #   * Thread IDs are stiored as str but are used as ints. The reason
        #     being that Discord does not allow us to pass Thread IDs as ints.
        #   * Whenever we pass a Thread ID to Pincer, we pass an int.
        #
        #   * Guild/Server IDs are stored as ints since they are never passed
        #     to us from a user via Discord.
        #   * Guild/Server IDs are always passed as ints to Pincer.
        #
        self.thread_ids: set[str] = set()
        self.connected_guilds: dict[int, Guild] = {}

        if os.path.isfile(STATE_FILE):
            with open(STATE_FILE) as f:
                self.thread_ids = {str(_id) for _id in json.load(f)}

    def checkpoint(self):
        with open(STATE_FILE, 'w') as f:
            json.dump([str(_id) for _id in self.thread_ids], f)

    @Client.event
    async def on_ready(self):
        print(f'Started client on {self.bot}')
        print(f'Registered commands: {self.chat_commands}')

        self.connected_guilds = {}
        for guild_id in self.guilds:
            self.connected_guilds[int(guild_id)] = \
                await self.get_guild(guild_id)
        print(f'Connected Guild IDs: {[gid for gid in self.connected_guilds]}')

    @command(description='Keep the given thread ID alive (all: all threads)')
    async def addthread(self, ctx: MessageContext, thread_id: str):
        if thread_id.lower() == 'all':
            guild_id = int(ctx.guild_id)
            if guild_id not in self.connected_guilds:
                return 'Looks like you are not connected to this guild: ' + \
                    str(guild_id)

            connected_guild = self.connected_guilds[guild_id]
            threads, _ = await connected_guild.list_active_threads()
            added_threads = {str(thread.id) for thread in threads}
            self.thread_ids |= added_threads
            return f'Threads {added_threads} are being kept alive.'

        thread_id = str(thread_id)
        if thread_id in self.thread_ids:
            return f'{thread_id} is already being kept alive'

        self.thread_ids.add(thread_id)
        return f'Thread {thread_id} is being kept alive now'

    @command(description='Do not keep the given thread ID alive anymore')
    async def rmthread(self, thread_id: str):
        thread_id = str(thread_id)
        if thread_id not in self.thread_ids:
            return f'{thread_id} was not being kept alive anyway'

        self.thread_ids.remove(thread_id)
        return f'Thread {thread_id} not being kept alive anymore'

    @command(description='List all monitored threads')
    async def lsthread(self):
        return f'Keeping these thread IDs alive: {self.thread_ids}'

    @command(description='Manually execute keepalive')
    async def keepalive(self):
        await self.keep_them_all_alive()
        return f'Kept these thread IDs alive: {self.thread_ids}'

    async def keep_them_all_alive(self):
        for thread_id in self.thread_ids:
            await self.keep_alive(thread_id)

    async def keep_alive(self, thread_id):
        print(f'Keeping thread {thread_id} alive')

        try:
            channel = await self.get_channel(int(thread_id))
            msg = await channel.send('ping')
            await msg.delete()
        except pincer.exceptions.NotFoundError:
            print(f'{thread_id} was not found. Consider removing it from the list')


if __name__ == "__main__":
    bot = Bot(TOKEN)
    atexit.register(bot.checkpoint)

    @aiocron.crontab(CRONTAB)
    async def keep_alive():
        await bot.keep_them_all_alive()

    try:
        bot.run()
    except KeyboardInterrupt:
        pass
