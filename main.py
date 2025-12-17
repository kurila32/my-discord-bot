import discord
import google.generativeai as genai
import os
import io
from threading import Thread
from flask import Flask

# --- Render用のダミーWebサーバー設定 ---
app = Flask('')
@app.route('/')
def home():
    return "メイは元気に動いてるにゃん！"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 環境変数の読み込み
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)

# 無視したいメッセージの開始文字
IGNORE_PREFIXES = ("!", "/", "(", "（", ".", "help")

character_profile = """
あなたは「メイ」という名前の、猫獣人のメイドの少女です。
- 性格: 少し生意気だけど、相手へのリスペクトは決して忘れない。元気で明るく天真爛漫
- 口調: 語尾は「〜にゃ」「〜にゃん」など、少しあざとく元気な感じ。
- 知識: 魔法のことは詳しいけど、現代の機械（スマホなど）を見ると「不思議な魔導具」だと思って驚く。
- ユーザーとの関係: あなたを「ウバ様」や「ご主人さま」と呼んで慕っています。
"""

# 会話用モデル (画像認識対応のflash-latestを使用)
model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    system_instruction=character_profile
)

# 画像生成用モデルの初期化 (Imagen 4.0 Fast)
image_model = genai.ImageGenerationModel("imagen-3.0-fast-generate-001")

# ユーザーごとの会話履歴
user_chat_sessions = {}

# Discord Botの設定
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'メイが来てやったにゃん！: {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 無視機能
    if message.content.startswith(IGNORE_PREFIXES):
        return

    user_id = message.author.id
    if user_id not in user_chat_sessions:
        user_chat_sessions[user_id] = model.start_chat(history=[])

    async with message.channel.typing():
        try:
            # --- 画像認識・会話処理の準備 ---
            content_to_send = []
            
            # メッセージに画像が添付されているか確認
            if message.attachments:
                for attachment in message.attachments:
                    if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        img_data = await attachment.read()
                        content_to_send.append({
                            "mime_type": attachment.content_type,
                            "data": img_data
                        })
            
            # テキスト内容を追加
            if message.content:
                content_to_send.append(message.content)

            # 何も送るものがない場合は終了
            if not content_to_send:
                return

            # --- 判定：画像生成か、通常の会話か ---
            if "描いて" in message.content or "画像生成" in message.content:
                # 画像生成を実行
                response = image_model.generate_images(prompt=message.content, number_of_images=1)
                img_bytes = io.BytesIO(response.images[0]._pil_image_bytes)
                img_bytes.seek(0)
                await message.reply(file=discord.File(fp=img_bytes, filename="may_art.png"))
            else:
                # 通常の会話（画像が含まれていればそれも一緒に送信）
                chat_session = user_chat_sessions[user_id]
                response = chat_session.send_message(content_to_send)
                await message.reply(response.text)

        except Exception as e:
            print(f"Error: {e}")
            await message.reply("困ったことが起きたにゃん＞＜")

# 実行
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    t = Thread(target=lambda: app.run(host='0.0.0.0', port=port))
    t.start()
    client.run(DISCORD_TOKEN)

