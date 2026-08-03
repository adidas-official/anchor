from subprocess import run 

def play_audio():
    run(["paplay", "morning_intro.mp3"])
    run(["paplay", "morning_summary.wav"])

if __name__ == "__main__":
    play_audio()