from subprocess import run 
from os import chdir
import logging
from pathlib import Path

def play_audio():
    script_dir = Path(__file__).resolve().parent
    chdir(script_dir)
    logging.basicConfig(level=logging.DEBUG, filename="anchor.log", format='%(asctime)s - %(levelname)s - %(message)s')
    logging.debug(f"Changing working directory to: {script_dir}")

    run(["paplay", "morning_intro.mp3"])
    run(["paplay", "morning_summary.wav"])

if __name__ == "__main__":
    play_audio()
