from dotenv import find_dotenv, load_dotenv
import bot.tacobot as bot


load_dotenv(find_dotenv())

def main() -> None:
    tacobot = bot.TacoBot()
    # tacobot.loop.run_until_complete(tacobot.__ainit__())
    # tacobot.run()


if __name__ == "__main__":
    main()
