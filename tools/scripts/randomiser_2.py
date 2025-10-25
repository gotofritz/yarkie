import random
import time
import threading
import curses

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


def generate_random_number():
    def r(lst):
        return random.sample(lst, k=1)[0]

    return f"""
   STRING: {r(strings)}
     NOTE: {accident(r(notes))}
 INTERVAL: {r(intervals)}
DIRECTION: {r(directions)}
    """


# def print_same_number(instructions, interval, refresh_event):
#     time_signature = 4
#     count = time_signature
#     while not refresh_event.is_set():
#         if count == 0:
#             print(". . . .")
#             count = time_signature
#         print(instructions, flush=True)
#         time.sleep(interval)
#         count -= 1


def print_same_number(win, refresh_event, stop_event):
    time_signature = 4
    count = time_signature
    message = generate_random_number()
    while not stop_event.is_set():
        if refresh_event.is_set():
            message = generate_random_number()
            refresh_event.clear()
        if count == time_signature:
            win.addstr(". . . .\n")
            count = 0
        win.addstr(f"{message}\n")
        count += 1
        win.refresh()
        time.sleep(1)


def listen_for_key(stdscr, refresh_event, stop_event):
    stdscr.nodelay(1)  # Make getch non-blocking
    while not stop_event.is_set():
        key = stdscr.getch()
        if key != -1:
            refresh_event.set()


def main(stdscr):
    try:
        curses.curs_set(0)  # Hide cursor
        stdscr.clear()

        refresh_event = threading.Event()
        stop_event = threading.Event()

        # Create a window for the printing thread
        print_thread_win = curses.newwin(curses.LINES - 1, curses.COLS)
        print_thread_win.scrollok(True)  # Enable scrolling

        # Start the printing thread
        print_thread = threading.Thread(
            target=print_same_number,
            args=(
                print_thread_win,
                refresh_event,
                stop_event,
            ),
        )
        print_thread.start()

        # Start the key listening thread
        key_thread = threading.Thread(
            target=listen_for_key,
            args=(
                stdscr,
                refresh_event,
                stop_event,
            ),
        )
        key_thread.start()

        # Wait for the key listening thread to finish (user presses a key)
        key_thread.join()

        # Signal the printing thread to stop
        # refresh_event.set()
        # Wait for the printing thread to finish
        print_thread.join()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    finally:
        # Signal the printing thread to stop
        stop_event.set()
        # Wait for both threads to finish
        print_thread.join()
        key_thread.join()


if __name__ == "__main__":
    curses.wrapper(main)
