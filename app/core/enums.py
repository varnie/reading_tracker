from enum import StrEnum


class BookStatus(StrEnum):
    WANT_TO_READ = "want_to_read"
    READING = "reading"
    FINISHED = "finished"
    ABANDONED = "abandoned"
