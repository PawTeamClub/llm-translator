from mcdreforged.api.all import *
from .proxy_other_server import *
from .sign_and_book import *
from .config import Config
from .llm import *


config = None


def on_load(server: PluginServerInterface, prev_module):
    global config
    config = server.load_config_simple(target_class=Config)
    send_config()
    prefix_1 = "t [translate-message]"
    prefix_2 = "!!tr <x> <y> <z> [xyz is sign or book location]"
    help_message = f"使用大模型进行{config.first_language}和{config.secondary_language}互译。玩家对话，游戏内木牌和放在讲台上的书均可翻译"
    server.register_help_message(prefix_1, help_message)
    server.register_help_message(prefix_2, help_message)

    builder = SimpleCommandBuilder()
    builder.command("!!tr <x> <y> <z>", send_nbt)

    builder.arg("x", QuotableText)
    builder.arg("y", QuotableText)
    builder.arg("z", QuotableText)

    builder.register(server)


def send_config():
    from . import llm

    llm.config = config
    from . import proxy_other_server

    proxy_other_server.config = config
    from . import sign_and_book

    sign_and_book.config = config


@new_thread
def send_nbt(source: InfoCommandSource, dic: dict):
    import minecraft_data_api as api

    server = source.get_server()
    try:
        re_dim_convert = {
            0: "minecraft:overworld",
            -1: "minecraft:the_nether",
            1: "minecraft:the_end",
        }
        player = source.get_info().player
        dim = api.get_player_dimension(player)
        coordinate = api.get_player_coordinate(player)

        for key in "xyz":
            if dic[key] == "~":
                cord = getattr(coordinate, key)
                dic[key] = int(cord) if cord >= 0 else int(cord - 1)

        server.execute(
            f"execute in {re_dim_convert[dim]} run data get block {dic['x']} {dic['y']} {dic['z']}"
        )
    except Exception as e:
        server.logger.error(f"[LLM Translator] Error getting NBT data: {e}")
        server.logger.debug(f"[LLM Translator] Coordinates: {dic}")


def on_user_info(server: ServerInterface, info: Info):
    import re
    
    player = None
    content = None
    
    try:
        if "[lobby]" in info.content and not "[global:" in info.content:
            return
            
        if info.player:
            player = info.player
            content = info.content
        else:
            # 匹配 [global:lobby]<Player> message 格式
            match = re.fullmatch(r'(?:\[global:[^\]]+\])?<([^>]+)>\s*(.*)', info.content)
            if match:
                player = match.group(1)
                content = match.group(2)
            else:
                # 备用匹配 <Player> message
                match = re.fullmatch(r'<([^>]+)>\s*(.*)', info.content)
                if match:
                    player = match.group(1)
                    content = match.group(2)
        
        if content and not content.startswith('!!'):
            translator_messages = LLM.use(content)
            if player:
                server.say(f"§7[T]<{player}> " + f"§f{translator_messages}")
            else:
                server.say(f"§7[T]" + f"§f{translator_messages}")
            if config.is_proxy_to_other_servers:
                proxy_message(player or "Unknown", translator_messages)
    except Exception as e:
        server.logger.error(f"[LLM Translator] Error processing user info: {e}")
        server.logger.debug(f"[LLM Translator] Info content: {info.content}")


def on_info(server: PluginServerInterface, info: Info):
    try:
        if "has the following block data:" in info.content and len(info.content) > 80:
            if not info.is_player:
                nbt = info.content
                get_messages_and_translate(nbt)
    except Exception as e:
        server.logger.error(f"[LLM Translator] Error processing block info: {e}")
        server.logger.debug(f"[LLM Translator] Info content: {info.content}")
