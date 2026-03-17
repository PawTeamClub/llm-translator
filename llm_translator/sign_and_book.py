from mcdreforged import *
from nbtlib import *
from .llm import *

config = None


@new_thread
def get_messages_and_translate(nbt: str):
    server = ServerInterface.get_instance()
    try:
        nbt_part = nbt[nbt.find("{") :]
        nbt_part = remove_all_newlines(nbt_part)
        decode_nbt = parse_nbt(nbt_part)
        if (
            decode_nbt["id"] == "minecraft:sign"
            or decode_nbt["id"] == "minecraft:hanging_sign"
        ):
            server.say("§7[sign: front || back ] Translating...")
            front_sign_message = ""
            back_sign_message = ""
            for row in decode_nbt["front_text"]["messages"]:
                front_sign_message += row
            for row in decode_nbt["back_text"]["messages"]:
                back_sign_message += row
            sign_message = front_sign_message + "   ||   " + back_sign_message
            server.say(LLM.use(sign_message))
        elif decode_nbt["Book"] != None:
            writable_or_written = decode_nbt["Book"]["id"] + "_content"
            page_num = 1
            server.say("§7[book] Translating...")
            for page in decode_nbt["Book"]["components"][writable_or_written]["pages"]:
                if page["raw"] != "":
                    server.say(f"§7-------------- Page {page_num} --------------")
                    server.say(LLM.use(page["raw"]))
                page_num += 1
        else:
            server.say("§7Unsupported block. Please choose a sign or book.")
    except Exception as e:
        server.logger.error(f"[LLM Translator] Error parsing NBT data: {e}")
        server.logger.debug(f"[LLM Translator] NBT content: {nbt}")


def remove_all_newlines(text: str):
    if not text:
        return text

    text = text.replace("\n", "")
    text = text.replace("\\n", "")
    text = text.replace("\r", "")
    text = text.replace("\\r", "")
    text = text.replace("\t", " ")
    text = text.replace("\\t", " ")

    return text
