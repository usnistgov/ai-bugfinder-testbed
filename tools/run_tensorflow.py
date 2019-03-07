"""
"""
from __future__ import division
import os

import sys
from os.path import join

import tensorflow as tf

from settings import LOGGER, ROOT_DIR
from utils.dataset import Dataset

USAGE = "./run_tensorflow.py ${DATA_DIR}"


def multilayer_perceptron(_x, _weights, _biases):
    assert len(_weights) == len(_biases), \
        "Weights and biases should have the same length."

    prev_layer = _x
    for i in xrange(len(_weights)):
        layer = tf.add(
            tf.matmul(prev_layer, _weights[i]), _biases[i]
        )
        layer = tf.nn.relu(layer)
        prev_layer = layer

    return prev_layer


def create_model(dataset, layers, input_vec, output_vec, learning_rate):

    # Store layers weight & bias
    weights = list()
    biases = list()
    weights_append = weights.append
    biases_append = biases.append
    weights_in = dataset.input

    for hidden_layer in layers:
        weights_append(
            tf.Variable(tf.random_normal(
                [weights_in, hidden_layer]
            ))
        )

        biases_append(
            tf.Variable(tf.random_normal(
                [hidden_layer]
            ))
        )

        weights_in = hidden_layer

    # Output weights
    weights_append(
        tf.Variable(tf.random_normal(
            [weights_in, dataset.output]
        ))
    )

    biases_append(
        tf.Variable(tf.random_normal(
            [dataset.output]
        ))
    )

    if len(biases) != len(weights):
        LOGGER.error(
            "Biases and weights do not have same length. Exiting"
        )
        exit(1)

    # Build model
    _logits = multilayer_perceptron(input_vec, weights, biases)

    _cost = tf.reduce_mean(
        tf.nn.softmax_cross_entropy_with_logits_v2(logits=_logits,
                                                   labels=output_vec)
    )
    _optimizer = tf.train.AdamOptimizer(
        learning_rate=learning_rate
    ).minimize(_cost)

    return _logits, _cost, _optimizer


def test_model(dataset, input_data, output_data, model):
    dataset.set_mode("testing")

    # Run testing
    y_, x_, t_ = dataset.get_whole_set()
    correct_prediction = tf.equal(
        tf.argmax(model, 1), tf.argmax(output_data, 1)
    )

    dataset.set_mode("training")

    # Calculate accuracy
    _accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
    return _accuracy.eval({input_data: x_, output_data: y_})


def run_tensorflow(training_set_path, test_set_path, neural_net_path,
                   hidden_layers, learning_rate, batch_size, epoch_nb):
    # Parsing input Parameters
    training_set_path = join(ROOT_DIR, training_set_path, "features")
    test_set_path = join(ROOT_DIR, test_set_path, "features")
    neural_net_path = join(ROOT_DIR, neural_net_path)

    hidden_layers = [int(h) for h in hidden_layers.split('|')]
    learning_rate = float(learning_rate)
    batch_size = int(batch_size)
    epoch_nb = int(epoch_nb)

    LOGGER.info("Loading training dataset...")
    # Load data
    training_data_set = Dataset(
        '%s/features.mtx' % training_set_path,
        '%s/labels.txt' % training_set_path,
        train_ratio=1,
        batch_size=batch_size
    )

    LOGGER.info(
        "Loaded training dataset in %dms. Loading test dataset..." % 1000
    )

    test_data_set = Dataset(
        '%s/features.mtx' % test_set_path,
        '%s/labels.txt' % test_set_path,
        train_ratio=0,
        batch_size=batch_size
    )

    LOGGER.info(
        "Loaded test dataset in %dms. Creating model..." % 1000
    )

    x_vector = tf.placeholder("float32", [None, training_data_set.input])
    y_vector = tf.placeholder("float32", [None, training_data_set.output])
    logits, cost, optimizer = create_model(training_data_set, hidden_layers,
                                           x_vector, y_vector, learning_rate)

    LOGGER.info("Model created. Starting training...")
    LOGGER.debug("%d batches" % training_data_set.get_batch_count())
    LOGGER.debug("%d epochs" % epoch_nb)
    LOGGER.debug("Learning rate: %.06f" % learning_rate)

    # Initializing the variables
    init = tf.global_variables_initializer()

    with tf.Session() as session:
        session.run(init)
        session.run(tf.local_variables_initializer())

        for epoch in range(epoch_nb):
            training_data_set.reset_index()
            avg_cost = 0.0
            # cum_cost = 0.0

            while True:
                try:
                    y, x, t = training_data_set.get_next_batch()

                    # Run optimization op (backprop) and cost op (to get loss
                    # value)
                    _, cum_cost = session.run([optimizer, cost],
                                              feed_dict={x_vector: x,
                                                         y_vector: y})

                    # Compute average loss
                    avg_cost += cum_cost
                except IndexError:
                    break

            disp_avg_cost = 999.99 if avg_cost > 999.99 else avg_cost

            accuracy = test_model(test_data_set, x_vector, y_vector, logits)

            LOGGER.info(
                "Epoch %03d/%03d [%06.2f%%]=(Loss: %06.2f; Test: %.05f)" %
                (epoch + 1, epoch_nb, (epoch + 1) * 100 / epoch_nb,
                 disp_avg_cost,
                 accuracy)
            )

            # Stop learning if the NN got it down nearly perfectly
            if avg_cost < 0.000001:
                break

        # Save the model
        LOGGER.info("Saving the neural net to disk...")

        if not os.path.exists(neural_net_path):
            os.mkdir(neural_net_path)

        tf.train.Saver().save(session, "%s/nn" % neural_net_path)

        LOGGER.info("Training finished. Starting testing...")

        accuracy = test_model(test_data_set, x_vector, y_vector, logits)
        LOGGER.info("Accuracy: %.05f", accuracy)


if __name__ == "__main__":
    if len(sys.argv) != 8:
        LOGGER.error(
            "Illegal number of parameters. Usage: %s." % USAGE
        )
        exit(1)

    run_tensorflow(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
                   sys.argv[5], sys.argv[6], sys.argv[7])
