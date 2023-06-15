from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
import bot.tacobot as bot


def main() -> None:
    tacobot = bot.TacoBot()
    # tacobot.loop.run_until_complete(tacobot.__ainit__())
    # tacobot.run()


if __name__ == "__main__":
    main()
