import msgspec


class LoggingGuildConfig(msgspec.Struct):
    mod: bool = True
    eco: bool = False
    redirects: bool = False


class GuildConfig(msgspec.Struct):
    logs: bool = True
    local_economy: bool = False
    redirects: bool = True
    pins: bool = True


class FullGuildConfig(msgspec.Struct):
    config: GuildConfig
    logging_config: LoggingGuildConfig
