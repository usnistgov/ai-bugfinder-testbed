"""
"""
import csv
import sys
from multiprocessing import Pool
from os.path import isfile, join

from tools.settings import LOGGER

USAGE = "./tools/batch_training.py ${batch_csv_file} ${processes}"


def launch_training(input_list):
    LOGGER.info("Launching training rounds with parameters %s" % str(input_list))

    input_list.append(join(input_list[2], "training.log"))

    # FIXME update script to use newer functionalities
    # try:
    #     run_tensorflow(*input_list)
    # except Exception as exc:
    #     LOGGER.error(exc.message)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        LOGGER.error("Illegal number of arguments. Usage: %s." % USAGE)
        exit(1)

    # Parse process information
    nb_process = -1
    try:
        nb_process = int(sys.argv[2])

        if nb_process <= 0:
            LOGGER.error("Invalid number of processes. Usage. %s." % USAGE)
            exit(1)
    except ValueError:
        LOGGER.error("Invalid number of processes. Usage. %s." % USAGE)
        exit(1)

    # Parse CSV file
    if not isfile(sys.argv[1]):
        LOGGER.error("Invalid batch file. Usage. %s." % USAGE)
        exit(1)

    input_data_dict = list()
    input_data_headers = None

    with open(sys.argv[1], "rb") as input_data:
        input_data_table = list(csv.reader(input_data))

    LOGGER.info(
        "Launching %d training rounds on %d processes..."
        % (len(input_data_table) - 1, nb_process)
    )
    worker_pool = Pool(nb_process)
    worker_pool.map_async(launch_training, input_data_table[1:])
    worker_pool.close()
    worker_pool.join()
