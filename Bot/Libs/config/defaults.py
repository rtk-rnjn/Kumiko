from typing import Union

import msgspec


class LoggingGuildConfig(msgspec.Struct):
    channel_id: Union[int, None]
    mod_events: bool = True
    eco_events: bool = False
    redirects: bool = True


class GuildConfig(msgspec.Struct):
    id: int
    logging_config: Union[LoggingGuildConfig, None]
    logs: bool = True
    birthday: bool = False
    local_economy: bool = False
    redirects: bool = True
    pins: bool = True
    local_economy_name: str = "Server Economy"
