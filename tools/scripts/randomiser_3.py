import random
from textwrap import dedent
import time
import threading
import curses
from typing import NamedTuple

notes = [
    "C",
    "C#",
    "Db",
    "D",
    "Eb",
    "E",
    "F",
    "F#",
    "Gb",
    "G",
    "Ab",
    "A",
    "Bb",
    "B",
]
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


class ShufflingIterator:
    def __init__(self, items):
        self.items = items
        random.shuffle(self.items)
        self.index = 0
        self.lock = threading.Lock()

    def __iter__(self):
        return self

    def __next__(self):
        with self.lock:
            if self.index == len(self.items):
                # Shuffle the list when reaching the end
                random.shuffle(self.items)
                print("List shuffled:", self.items)
                self.index = 0  # Reset the index after shuffling

            if self.index >= len(self.items):
                random.shuffle(self.items)
                self.index = 0
            current_number = self.items[self.index]
            self.index += 1
            return current_number


class NotesGenerator:
    def __init__(self):
        self.strings = ShufflingIterator(strings)
        self.notes = ShufflingIterator(notes)
        self.intervals = ShufflingIterator(intervals)
        self.directions = ShufflingIterator(directions)

    def generate(self):
        return dedent(
            f"""
                  NOTE: {next(self.notes)}
              INTERVAL: {next(self.intervals)}
             DIRECTION: {next(self.directions)}
                STRING: {next(self.strings)}
            """
        ).strip("\n")


def listen_for_key(win: curses.window, notes_generator, stop_event, interval):
    win.nodelay(True)  # Make getch non-blocking
    win.clear()
    win.addstr(0, 0, notes_generator.generate())
    win.refresh()
    while not stop_event.is_set():
        time.sleep(interval)
        key = win.getch()
        if key != -1:
            win.clear()
            win.addstr(0, 0, notes_generator.generate())
            win.refresh()


def print_beat(win: curses.window, stop_event, interval):
    win.clear()
    time_signature = 4
    BEAT = ".  "
    count = 0
    while not stop_event.is_set():
        if count == time_signature:
            win.clear()
            count = 0
        win.addstr(0, count * len(BEAT), BEAT)
        win.refresh()
        count += 1
        time.sleep(interval)
    win.addstr("DONE")
    win.refresh()


def timer(stop_event, timer_duration):
    time.sleep(timer_duration)
    stop_event.set()


class Params(NamedTuple):
    duration: int
    interval: float


def create_params(params_dict: dict) -> Params:
    return Params(**params_dict)


def get_params(stdscr: curses.window) -> Params:
    params_dict: dict[str, int | float] = {}
    stdscr.clear()
    curses.echo()

    msg = "Enter timer duration in seconds: "
    stdscr.addstr(msg)
    params_dict["duration"] = int(stdscr.getstr(0, len(msg) + 1))

    msg = "BPM: "
    stdscr.addstr(msg)
    params_dict["interval"] = 60 / int(stdscr.getstr(1, len(msg) + 1))

    stdscr.clear()

    # Params: NamedTuple = namedtuple("params", params_dict.keys())
    return create_params(params_dict)


def main(stdscr: curses.window) -> None:
    stop_event = None
    try:
        curses.curs_set(0)  # Hide cursor

        params = get_params(stdscr)

        stdscr.clear()
        stdscr.refresh()

        refresh_event = threading.Event()
        stop_event = threading.Event()

        # # Create a window for the printing thread
        metronome_win = curses.newwin(1, 15, 0, 0)

        # Start the metronome
        metronome_thread = threading.Thread(
            target=print_beat,
            args=(metronome_win, stop_event, params.interval),
        )
        metronome_thread.start()

        # cap the whole program length
        main_thread = threading.Thread(target=timer, args=(stop_event, params.duration))
        main_thread.start()

        # # Create a window for the printing thread
        message_win = curses.newwin(50, 50, 2, 0)

        # Start the key listening thread
        key_thread = threading.Thread(
            target=listen_for_key,
            args=(message_win, NotesGenerator(), stop_event, params.interval),
        )
        key_thread.start()

        # # Wait for the key listening thread to finish (user presses a key)

        # Wait for all events to stop
        main_thread.join()
        # metronome_thread.join()
    except KeyboardInterrupt:
        curses.endwin()
        print("\nProgram terminated by user.")

    finally:
        if stop_event:
            # Signal the printing thread to stop
            stop_event.set()
            # Wait for both threads to finish
            metronome_thread.join()
            # key_thread.join()
            main_thread.join()
            key_thread.join()


if __name__ == "__main__":
    curses.wrapper(main)
