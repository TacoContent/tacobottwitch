from . import mongo
from . import loglevel


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
        stackTrace: str = None,
    ):
        if channel is None:
            channel = str(loglevel.EmptyChannel())
        print(f"[{level.name}] [{method}] [channel:{channel.strip().lower()}] {message}")
        if stackTrace:
            print(stackTrace)
        if level >= self.minimum_log_level:
            self.db.insert_log(
                channel=channel.strip().lower(),
                level=level,
                method=method,
                message=message,
                stackTrace=stackTrace,
            )

    def debug(self, channel: str, method: str, message: str, stackTrace: str = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.DEBUG,
            method=method,
            message=message,
            stackTrace=stackTrace,
        )

    def info(self, channel: str, method: str, message: str, stackTrace: str = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.INFO,
            method=method,
            message=message,
            stackTrace=stackTrace,
        )

    def warn(self, channel: str, method: str, message: str, stackTrace: str = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.WARNING,
            method=method,
            message=message,
            stackTrace=stackTrace,
        )

    def error(self, channel: str, method: str, message: str, stackTrace: str = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.ERROR,
            method=method,
            message=message,
            stackTrace=stackTrace,
        )

    def fatal(self, channel: str, method: str, message: str, stackTrace: str = None):
        self.__write(
            channel=channel.strip().lower(),
            level=loglevel.LogLevel.FATAL,
            method=method,
            message=message,
            stackTrace=stackTrace,
        )
