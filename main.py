import bot.tacobot as bot
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


def main() -> None:
    bot.TacoBot()
    # tacobot = bot.TacoBot()
    # tacobot.loop.run_until_complete(tacobot.__ainit__())
    # tacobot.run()


if __name__ == "__main__":
    main()
