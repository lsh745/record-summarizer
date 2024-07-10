import enum

class GPTModelEnum(enum.Enum):
    GPT35 = "gpt-3.5-turbo"
    GPT4o = "gpt-4o"

class LanguageEnum(enum.Enum):
    KO = "ko"
    EN = "en"
    AUTO = None

class StatusEnum(enum.Enum):
    PENDING = "PENDING"
    INITIALIZING = "INITIALIZING"
    IN_PROGRESS_WHISPER = "WHISPER"
    IN_PROGRESS_CHATGPT = "CHATGPT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
