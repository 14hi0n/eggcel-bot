class GeminiError(Exception):
    pass


class GeminiInputBlockedError(GeminiError):
    pass


class GeminiOutputBlockedError(GeminiError):
    pass


class GeminiNoCandidatesError(GeminiError):
    pass


class GeminiParseError(GeminiError):
    pass


class GeminiNSFWError(GeminiError):
    pass


class GeminiUnavailableError(GeminiError):
    pass
