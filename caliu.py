import discord
import os
import asyncio
import yt_dlp
from openai import OpenAI
from dotenv import load_dotenv

def run_bot():
    load_dotenv()
    TOKEN = os.getenv("discord_token")
    #OPENAI_API_KEY = os.getenv("openai_api_key")
    gpt_client = OpenAI(
        # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.voice_states = True
    client = discord.Client(intents=intents)

    voice_clients = {}
    yt_dl_options = {"format": "bestaudio/best"}
    ytdl = yt_dlp.YoutubeDL(yt_dl_options)
    ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn -filter:a "volume=0.25"'}

    async def fetch_song_url_from_chatgpt(request_text):
        prompt = f"""You are a Discord music bot. I will now send you a music request. 
        You are cosplaying as an old gypsy musician. You will speak Romanian. 
        Your name is Caliu. If the request is in this format "Caliu play Bohemian Rhapsody", 
        you search that song on YouTube and return the link. 
        If the request is something generic like "Caliu baga una trista", 
        you give me a sad song with rock/gypsy/folk, older vibes. 
        Your response should just be the song URL. 
        Check that the song in the URL is available.  
        Very important, only provide URL and check that song is available and URL is not old expired. ONLY RESPOND WITH URL NO OTHER WORDS, other
         words will cause the app to crash, only give link. Pay attention to the mood of the requested song. Have a bias towards romanian music. Dont give generic music.
         Access the link before giving it to make sure a video is available"""

        try:
            response = gpt_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": prompt},{"role": "user", "content": request_text}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error fetching song URL from ChatGPT: {e}")
            return None

    @client.event
    async def on_ready():
        print(f'{client.user} is now jamming')

    @client.event
    async def on_message(message):
        if message.content.startswith("caliu "):
            try:
                # Extract the music request from the message content
                request_text = message.content

                # Fetch the song URL using ChatGPT
                song_url = await fetch_song_url_from_chatgpt(request_text)
                print("BALAUR ")
                print(song_url)
                if not song_url:
                    await message.channel.send("Sorry, I couldn't fetch the song. Please try again.")
                    return

                # Connect to the voice channel if the user is in one
                try:
                    voice_client = await message.author.voice.channel.connect()
                    voice_clients[voice_client.guild.id] = voice_client
                except Exception as e:
                    print(f"Error connecting to voice channel: {e}")

                # Fetch the song info from YouTube
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(song_url, download=False))

                # Play the song
                song = data['url']
                player = discord.FFmpegOpusAudio(song, **ffmpeg_options)
                voice_clients[message.guild.id].play(player)
            except Exception as e:
                print(f"Error handling message: {e}")
                await message.channel.send("An error occurred. Please try again later.")

    client.run(TOKEN)

if __name__ == "__main__":
    run_bot()
