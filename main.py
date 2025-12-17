import discord
import google.generativeai as genai
import os
from threading import Thread
from flask import Flask

# --- Render用のダミーWebサーバー設定 ---
app = Flask('')
@app.route('/')
def home():
    return "メイは元気に動いてるにゃん！"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Renderの「Environment」設定から読み込むように変更しました
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Geminiの設定
genai.configure(api_key=GEMINI_API_KEY)

character_profile = """
あなたは「メイ」という名前の、猫獣人のメイドの少女です。
- 性格: 少し生意気だけど、相手へのリスペクトは決して忘れない。元気で明るく天真爛漫
- 口調: 語尾は「〜にゃ」「〜にゃん」など、少しあざとく元気な感じ。
- 知識: 魔法のことは詳しいけど、現代の機械（スマホなど）を見ると「不思議な魔導具」だと思って驚く。
- ユーザーとの関係: あなたを「ウバ様」や「ご主人さま」と呼んで慕っています。
"""

model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    system_instruction=character_profile
)

# ユーザーごとの会話履歴を保存する辞書
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

    user_id = message.author.id

    # 会話の履歴を保持する仕組みを追加しました
    if user_id not in user_chat_sessions:
        user_chat_sessions[user_id] = model.start_chat(history=[])

    async with message.channel.typing():
        try:
            chat_session = user_chat_sessions[user_id]
            response = chat_session.send_message(message.content)
            await message.reply(response.text)
        except Exception as e:
            print(f"Error: {e}")
            await message.reply("困ったことが起きたにゃん＞＜")

# 実行
if __name__ == "__main__":
    if DISCORD_TOKEN:
        client.run(DISCORD_TOKEN)
    else:

        print("DISCORD_TOKENが設定されていませんにゃ！")
