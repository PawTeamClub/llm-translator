from mcdreforged import *
from nbtlib import *
from .llm import *

config = None


@new_thread
def get_messages_and_translate(nbt: str):
    server = ServerInterface.get_instance()
    try:
        if config is None:
            server.logger.error("[LLM Translator] Config not initialized")
            server.say("[Translation Error] Config not initialized")
            return
            
        # 提取NBT部分
        nbt_start = nbt.find("{")
        if nbt_start == -1:
            server.logger.error("[LLM Translator] No NBT data found in input")
            server.say("§7Error: No NBT data found")
            return
            
        nbt_part = nbt[nbt_start:]
        nbt_part = remove_all_newlines(nbt_part)
        
        # 解析NBT数据
        try:
            decode_nbt = parse_nbt(nbt_part)
        except Exception as parse_error:
            server.logger.error(f"[LLM Translator] Failed to parse NBT data: {parse_error}")
            server.logger.debug(f"[LLM Translator] NBT content: {nbt_part}")
            server.say("§7Error: Failed to parse NBT data")
            return
        
        # 检查是否为木牌
        if decode_nbt.get("id") in ["minecraft:sign", "minecraft:hanging_sign"]:
            if not config.enable_sign_translation:
                server.say("§7Sign translation is disabled")
                return
                
            server.say("§7[sign: front || back ] Translating...")
            front_sign_message = ""
            back_sign_message = ""
            
            try:
                # 安全获取木牌文本
                front_text = decode_nbt.get("front_text", {})
                back_text = decode_nbt.get("back_text", {})
                
                for row in front_text.get("messages", []):
                    front_sign_message += row
                for row in back_text.get("messages", []):
                    back_sign_message += row
                
                sign_message = front_sign_message + "   ||   " + back_sign_message
                if sign_message.strip():
                    server.say(LLM.use(sign_message))
                else:
                    server.say("§7Sign is empty")
            except Exception as sign_error:
                server.logger.error(f"[LLM Translator] Error processing sign data: {sign_error}")
                server.say("§7Error: Failed to process sign data")
        
        # 检查是否为书籍
        elif decode_nbt.get("Book") is not None:
            if not config.enable_book_translation:
                server.say("§7Book translation is disabled")
                return
                
            try:
                book = decode_nbt.get("Book", {})
                book_id = book.get("id", "")
                writable_or_written = book_id + "_content"
                
                components = book.get("components", {})
                book_content = components.get(writable_or_written, {})
                pages = book_content.get("pages", [])
                
                if not pages:
                    server.say("§7Book is empty")
                    return
                    
                page_num = 1
                server.say("§7[book] Translating...")
                for page in pages:
                    if page.get("raw") != "":
                        server.say(f"§7-------------- Page {page_num} --------------")
                        server.say(LLM.use(page["raw"]))
                    page_num += 1
            except Exception as book_error:
                server.logger.error(f"[LLM Translator] Error processing book data: {book_error}")
                server.say("§7Error: Failed to process book data")
        
        # 不支持的方块类型
        else:
            server.say("§7Unsupported block. Please choose a sign or book.")
    except Exception as e:
        server.logger.error(f"[LLM Translator] Unexpected error: {e}")
        server.logger.debug(f"[LLM Translator] Full NBT content: {nbt}")
        server.say("§7Error: An unexpected error occurred")


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
