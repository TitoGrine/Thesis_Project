import time
import math


def print_elapsed_time(start_time, message):
    elapsed_time = time.time() - start_time

    print(f"\033[95m\033[96m {message}: {math.floor(elapsed_time / 60):02d}:{round(elapsed_time % 60):02d}. \033[0m")
