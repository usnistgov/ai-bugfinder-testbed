"""
Temporary utils file for the LSTM model
"""
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split

from bugfinder.settings import LOGGER


def process_csv(input_file, test_data_size=0.33, seed=42):
    LOGGER.info("Processing feature file...")

    dataframe = pd.read_csv(input_file)

    LOGGER.info("Shape of the dataframe: %s" % (str(dataframe.shape)))

    y = (dataframe["result"].astype(int)).to_numpy()

    dataframe = dataframe.drop(["name", "result"], axis=1)

    x = dataframe.to_numpy()
    X = np.reshape(x, (x.shape[0], x.shape[1], 1))

    x_train, y_train, x_test, y_test = train_test_split(
        X, y, test_size=test_data_size, random_state=seed
    )

    LOGGER.info("Training and validation sets created.")
    LOGGER.info(
        "%d instances will be used for training and %d instances for validation"
        % (x_train.shape[0], x_test.shape[0])
    )

    return x_train, x_test, y_train, y_test
