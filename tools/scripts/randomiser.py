import random
import time

notes = ["c", "c+d", "d", "d+e", "e", "f", "f+g", "g", "g+a", "a", "a+b", "b"]
strings = ["E", "A", "D", "G"]
intervals = [
    "I",
    "II-",
    "II",
    "III-",
    "III",
    "IV",
    "V-",
    "V",
    "VI-",
    "VI",
    "VII+",
    "VII",
    "VIII",
    "IX-",
    "IX",
    "X-",
    "X",
]
directions = ["top down", "bottom up"]


def accident(note):
    note = note.upper()
    if len(note) == 1:
        return note
    if random.random() > 0.5:
        return f"{note[0]}#"
    return f"{note[2]}♭"


def pick():
    def r(lst):
        return random.sample(lst, k=1)[0]

    return f"""
   STRING: {r(strings)}
     NOTE: {accident(r(notes))}
 INTERVAL: {r(intervals)}
DIRECTION: {r(directions)}
    """


def print_instructions(interval, stop_event):
    time_signature = 4
    count = time_signature
    while not stop_event.is_set():
        if count == time_signature:
            print(". . . .")
        print(pick(), flush=True)
        time.sleep(interval)


def main():
    try:
        bpm = int(input("Enter BPM (beats per minute): "))
        bars = int(input("Enter number of bars: "))
        interval = 60 / bpm  # Calculate time interval in seconds

        print("\nPress Ctrl-C to stop.\n")

        period = 4 * bars
        i = 0
        randomised = ""
        while True:
            if i == 0:
                i = period
                randomised = pick()
                print("---------------------")
                continue
            start_time = time.time()
            time.sleep(interval)
            print(randomised)
            i -= 1
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")


if __name__ == "__main__":
    main()
