import math
import time

from src import pipeline


# TODO:


def main():
    start_time = time.time()

    # pipeline()

    end_time = time.time()

    print("Total run time: {:02d}:{:02d}".format(math.floor((end_time - start_time) / 60),
                                                 round((end_time - start_time) % 60)))


if __name__ == '__main__':
    main()
    # test()
