from os import getenv, chdir
from dotenv import load_dotenv
import trafilatura
import feedparser
from curl_cffi import requests
import json
from google import genai
from google.genai.errors import APIError
from datetime import datetime
import logging
import wave
import base64
from pathlib import Path
from time import sleep
from weather_predict import get_weather, get_max_temp, get_min_temp, get_clouds


def get_candidates():
    rss_links = [
        "https://www.irozhlas.cz/rss/irozhlas/section/veda-technologie",
        "https://www.irozhlas.cz/rss/irozhlas/section/zpravy-domov",
        "https://www.irozhlas.cz/rss/irozhlas/section/zpravy-svet",
        "https://www.irozhlas.cz/rss/irozhlas/tag/167727"]

    candidates = []

    logging.debug("Fetching RSS feeds...")
    for rss in rss_links:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:6]:  # Limit to the first 6 entries
            title = entry.title
            link = entry.link
            description = entry.description
            candidates.append({"title": title, "link": link, "description": description})
    return candidates


def filter_candidates(client):
    candidates = get_candidates()
    day = datetime.now().strftime("%A")
    prompt_selection = f"""
    Z následujícího seznamu zpráv vyber 5 nejvýznamnějších.
    Pokud je dnes mezi sobota až středa, nevybírej zpravy s násilnou tématikou, bez válek, zločinů a podobně.
    V tyto dny upřednostni více technických a pozitivních nebo alespoň neutrálních zpráv. Zprávy typu "Válka čipů" a podobně jsou v pořádku,
    ale v tyto dny se vyhni ozbrojeným konfliktům a násilným činnům.
    Čtvrtek a pátek mohou být zprávy bez omezení. Dnes je {day}.
    Vráť POUZE platný JSON pole objektů obsahující pouze jejich název ('title') a URL adresy ('link')

    Seznam článků:
    {json.dumps(candidates, ensure_ascii=False)}
    """

    logging.debug(f"Prompt for selection:\n{prompt_selection}\n")

    selected_links = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_selection,
        config={"response_mime_type": "application/json"}
    )

    logging.debug("Selected links:")
    logging.debug(selected_links.text)
    
    with open("selected_links.json", "w", encoding="utf-8") as f:
        f.write(selected_links.text)

    selected_links_json = json.loads(selected_links.text)
    news = ""

    for link in selected_links_json:
        response = requests.get(link['link'], impersonate="chrome")
        if response.status_code == 200:
            html_content = response.text
            text = trafilatura.extract(html_content)
            news += f"Title: {link['title']}\nText: {text}\n---\n"

    datum = datetime.now().strftime("%A %d.%B.%Y")

    weather_forecast = get_weather()
    max_temp = get_max_temp(weather_forecast)
    min_temp = get_min_temp(weather_forecast)

    prompt_summary = f"""
    Vytvoř stručný souhrn následujících zpráv, který bude vhodný pro hlasové čtení.
    Souhrn by měl být vhodný pro čtení přirozeným hlasem, aby posluchač získal jasnou představu o obsahu zpráv.
    Začni pozdravem dobrého rána a dnešním datumem {datum} v češtině.
    Na základě dat {weather_forecast} vytvoř předpověď počasí pro dnešní den. Uveď maximální {max_temp[0]} a minimální {min_temp[0]}, oblačnost a jestli bude během dne pršet.
    Přidej doporučení, jak se obléknout (teplé obleční, oblečení do deště)
    Jednen článek by neměl přesahovat 1 minutu čtení, ale zároveň by měl obsahovat všechny klíčové informace.
    Jednotlivé články jsou odděleny '---'.

    Zprávy:
    {news}

    Hlášení ukonči s poděkováním za poslech a přáním hezkého dne.
    """
    logging.debug(f"Prompt for summary:\n{prompt_summary}\n")
    return prompt_summary

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def generate_summary(client):

    max_tries = 5
    for i in range(max_tries):
        try:
            prompt_summary = filter_candidates(client)
            morning_summary = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_summary,
                config={"response_mime_type": "text/plain"}
            )

            logging.debug("Saving summary to file...")
            with open("morning_summary.txt", "w", encoding="utf-8") as f:
                f.write(morning_summary.text)
            return True

        except APIError as e:
            if e.code in (503, 429) or "503" in str(e):
                logging.error("Error")
                sleep(600)
            else:
                logging.error("Too many attempts to generate summary")

    return False

def generate_audio(client):
    with open("morning_summary.txt", "r", encoding="utf-8") as f:
        morning_summary = f.read()

    logging.debug("Generating audio from summary...")
    logging.debug(f"Summary text:\n{morning_summary}\n")

    max_tries = 5
    for i in range(max_tries):
        try:

            interaction = client.interactions.create(
                model="gemini-3.8-flash-tts",
                input=f"Přečti následující text přirozeným mluveným hlasem v češtině:\n\n{morning_summary}",
                response_format={"type": "audio"},
                    generation_config={
                        "speech_config": [
                            {"voice": "Aoede"}
                    ]
                }
            )

            audio_data = base64.b64decode(interaction.output_audio.data)
            wave_file("morning_summary.wav", audio_data)
            return True
        except APIError as e:
            if e.code in (503, 429) or "503" in str(e):
                logging.error(f"Error {e.code}. Try: {i}")
                sleep(600)
            else:
                logging.error("Some other error happened. (Check your fw rules, idiot!)")

    return False

def main():

    script_dir = Path(__file__).resolve().parent
    chdir(script_dir)
    logging.basicConfig(level=logging.DEBUG, filename="anchor.log", format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug(f"Changing working directory to: {script_dir}")

    load_dotenv()
    google_api_key = getenv("GOOGLE_API_KEY")
    client = genai.Client(api_key=google_api_key)
    generate_summary(client)
    generate_audio(client)
    client.close()

if __name__ == "__main__":
    main()