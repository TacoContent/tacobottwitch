import sys
import typing

from bot.cogs.lib import loglevel, mongo
from bot.cogs.lib.colors import Colors


class Log:
    def __init__(self, minimumLogLevel: loglevel.LogLevel = loglevel.LogLevel.DEBUG):
        self.db = mongo.MongoDatabase()
        self.minimum_log_level = minimumLogLevel
        pass

    def __write(
        self,
        channel: str,
        level: loglevel.LogLevel,
        method: str,
        message: str,
        stackTrace: typing.Optional[str] = None,
        file: typing.IO = sys.stdout,
    ):
        if channel is None:
            channel = str(loglevel.EmptyChannel())

        color = Colors.get_color(level)
        m_level = Colors.colorize(color, f"[{level.name}]", bold=True)
        m_method = Colors.colorize(Colors.HEADER, f"[{method}]", bold=True)
        m_channel = Colors.colorize(Colors.OKGREEN, f"[{channel}]", bold=True)
        m_message = f"{Colors.colorize(color, message)}"

        str_out = f"{m_level} {m_method} {m_channel} {m_message}"
        print(str_out, file=file)
        if stackTrace:
            print(Colors.colorize(color, stackTrace), file=file)
        if level >= self.minimum_log_level:
            self.db.insert_log(
                channel=channel.strip().lower(),
                level=level,
                method=method,
                message=message,
                stackTrace=stackTrace or "",
            )

    def debug(self, channel: str, method: str, message: str, stackTrace: typing.Optional[str] = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.DEBUG,
            method=method,
            message=message,
            stackTrace=stackTrace,
            file=sys.stdout,
        )

    def info(self, channel: str, method: str, message: str, stackTrace: typing.Optional[str] = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.INFO,
            method=method,
            message=message,
            stackTrace=stackTrace,
            file=sys.stdout,
        )

    def warn(self, channel: str, method: str, message: str, stackTrace: typing.Optional[str] = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.WARNING,
            method=method,
            message=message,
            stackTrace=stackTrace,
            file=sys.stdout,
        )

    def error(self, channel: str, method: str, message: str, stackTrace: typing.Optional[str] = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.ERROR,
            method=method,
            message=message,
            stackTrace=stackTrace,
            file=sys.stderr,
        )

    def fatal(self, channel: str, method: str, message: str, stackTrace: typing.Optional[str] = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.FATAL,
            method=method,
            message=message,
            stackTrace=stackTrace,
            file=sys.stderr,
        )
