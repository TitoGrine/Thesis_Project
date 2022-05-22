import math
import time

from src import pipeline


# TODO:


def main():
    start_time = time.time()

    # pipeline()

    elapsed_time = time.time()

    print(f"Total run time: {math.floor(elapsed_time / 60):02d}:{round(elapsed_time % 60):02d}")


if __name__ == '__main__':
    main()
    # test()
