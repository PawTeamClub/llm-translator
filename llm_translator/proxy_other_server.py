from mcdreforged.api.all import *

config = None


def proxy_message(player, message):
    if config is None:
        server = ServerInterface.get_instance()
        server.logger.error("[LLM Translator] Config not initialized")
        return
    
    for proxy_server in config.proxy_servers:
        try:
            proxy(
                proxy_server["address"],
                proxy_server["port"],
                proxy_server["password"],
                player,
                message,
            )
        except Exception as e:
            ServerInterface.get_instance().logger.error(
                f"[llm-translator] Error proxying message to {proxy_server['address']}:{proxy_server['port']}: {e}"
            )


def proxy(address, port, password, player, message):
    command = f'/tellraw @a [{{"text":"[i18n] <{player}> ","color":"gray"}},{{"text":"{message}","color":"white"}}]'
    rcon = RconConnection(address, port, password)
    try:
        if rcon.connect():
            rcon.send_command(command)
            rcon.disconnect()
    except Exception as e:
        ServerInterface.get_instance().logger.error(
            f"[llm-translator] Failed to connect to the port: {port}: {e}"
        )
