from enum import Enum
class StreamAvatarTypes(Enum):
    REQUESTED = 0,
    ACCEPTED = 1,
    DECLINED = 2,
    COMPLETE = 3,

    UNKNOWN = 99,

    def __str__(self):
        return str(self.name)
