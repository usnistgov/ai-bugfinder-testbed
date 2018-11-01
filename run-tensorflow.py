#!/usr/bin/python
import os
import numpy as np
import sys
from random import shuffle
from scipy.io import mmread
import tensorflow as tf


class Dataset(object):

    def __init__(self, feature_filename, label_filename, ratio=0.8, batch_size=1):

        print 'Loading labels..... ',
        sys.stdout.flush()
        self.labels = np.genfromtxt(label_filename, delimiter=',', dtype=None)
        print "%d labels loaded" % self.labels.size

        print 'Loading features... ',
        sys.stdout.flush()
        self.features = mmread(feature_filename).tocsr()
        print "%d features of size %d loaded" % (self.features.shape[0], self.features.shape[1])

        # Check if we have as many labels as features
        if len(self.labels) != self.features.shape[0]:
            print 'Error: features and labels have different cardinalities'
            sys.exit(-1)

        self.INPUT = self.features.shape[1]
        self.OUTPUT = 2
        self.batch_size = batch_size

        # Prepare indexes to get random sets for training and testr
        # shufidx = range(self.INPUT)
        shufidx = range(self.features.shape[0])
        shuffle(shufidx)
        self.training_index = shufidx[:int(ratio * len(shufidx))]
        self.testing_index = shufidx[int(ratio * len(shufidx)):]
        self.last_index = 0

        # Assume training mode per default
        self.index = self.training_index

    def set_batch_size(self, batch_size):
        self.batch_size = batch_size

    def reset_index(self):
        self.last_index = 0
        shuffle(self.index)

    def set_mode(self, mode='training'):
        if mode == 'training':
            self.index = self.training_index
        else:
            self.index = self.testing_index
        self.last_index = 0

    def get_batch_count(self):
        return int(len(self.index) / self.batch_size)

    def get_next_batch(self):
        labels = np.zeros((self.batch_size, self.OUTPUT))
        features = np.zeros((self.batch_size, self.INPUT))
        testcases = [None] * self.batch_size

        for _offset in range(self.batch_size):
            if self.last_index >= len(self.index):
                raise IndexError("Dataset exhausted")

            label, testcase = self.labels[self.index[self.last_index]]
            features[_offset] = self.features[self.index[self.last_index]].todense()
            labels[_offset] = [label, 1 - label]  # Need to use this trick to use softmax in the NN
            testcases[_offset] = testcase

            self.last_index += 1

        return labels, features, testcases

    def get_whole_set(self):
        batch_size = self.batch_size
        last_index = self.last_index
        self.batch_size = len(self.index)
        self.last_index = 0
        labels, features, testcases = self.get_next_batch()
        self.batch_size = batch_size
        self.last_index = last_index

        return labels, features, testcases


# Parameters
learning_rate = 0.001
BATCH_SIZE = 200
NUM_EPOCH = 20

# Load data
ds = Dataset('data/features/features.mtx', 'data/features/labels.txt', batch_size=BATCH_SIZE)

print "__________________________________________"
print "%d batches / epoch" % ds.get_batch_count()
print "%d epochs" % NUM_EPOCH
print "Learning rate: %f" % learning_rate
print "------------------------------------------"

# Network Parameters
n_hidden_1 = 512  # 1st layer number of neurons
n_hidden_2 = 128  # 2nd layer number of neurons

# tf Graph input
X = tf.placeholder("float32", [None, ds.INPUT])
Y = tf.placeholder("float32", [None, ds.OUTPUT])

# Store layers weight & bias
weights = {
    'h1': tf.Variable(tf.random_normal([ds.INPUT, n_hidden_1])),
    'h2': tf.Variable(tf.random_normal([n_hidden_1, n_hidden_2])),
    'out': tf.Variable(tf.random_normal([n_hidden_2, ds.OUTPUT]))
}
biases = {
    'b1': tf.Variable(tf.random_normal([n_hidden_1])),
    'b2': tf.Variable(tf.random_normal([n_hidden_2])),
    'out': tf.Variable(tf.random_normal([ds.OUTPUT]))
}


# Create model
def multilayer_perceptron(_x):
    # Hidden fully connected layer with 4096 neurons
    layer_1 = tf.add(tf.matmul(_x, weights['h1']), biases['b1'])
    layer_1 = tf.nn.relu(layer_1)
    # Hidden fully connected layer with 1024 neurons
    layer_2 = tf.add(tf.matmul(layer_1, weights['h2']), biases['b2'])
    layer_2 = tf.nn.relu(layer_2)
    # Output fully connected layer with a neuron for each class
    out_layer = tf.matmul(layer_2, weights['out']) + biases['out']

    return out_layer


# Build model
logits = multilayer_perceptron(X)

cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits_v2(logits=logits, labels=Y))
optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)

# Initializing the variables
init = tf.global_variables_initializer()

with tf.Session() as session:
    session.run(init)
    session.run(tf.local_variables_initializer())

    for epoch in range(NUM_EPOCH):
        ds.reset_index()
        avg_cost = 0.0
        cum_cost = 0.0
        print "Starting Epoch %d..." % (epoch + 1)
        print "Cost:",
        while True:
            try:
                y, x, t = ds.get_next_batch()

                # Run optimization op (backprop) and cost op (to get loss value)
                _, cum_cost = session.run([optimizer, cost], feed_dict={X: x, Y: y})

                print cum_cost,
                sys.stdout.flush()

                # Compute average loss
                avg_cost += cum_cost

            except IndexError:
                print cum_cost
                break

        print "End of Epoch %d; Avg loss: %f" % (epoch + 1, avg_cost / ds.get_batch_count())

        # Stop learning if the NN got it down nearly perfectly
        if avg_cost < 0.000001:
            break

    # Save the model
    print "Saving the neural net to disk..."
    
    if not os.path.exists("./data/neuralnet"):
        os.mkdir("./data/neuralnet")
    tf.train.Saver().save(session, './data/neuralnet/nn')

    print "Training finished. Starting testing..."
    # Test model
    ds.set_mode('testing')
    y_, x_, t_ = ds.get_whole_set()
    correct_prediction = tf.equal(tf.argmax(logits, 1), tf.argmax(Y, 1))
    # Calculate accuracy
    accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))
    print "Accuracy:", accuracy.eval({X: x_, Y: y_})

    # Find out which test cases caused problems
    z_ = session.run(tf.argmax(logits, 1), feed_dict={X: x_})
    lab = {0: "bad", 1: "good"}
    print "Misprediction on test cases:"
    for offset in range(len(y_)):
        if z_[offset] != int(y_[offset][1]):
            print "%s: expected=%s predicted=%s" % (t_[offset], lab[y_[offset][1]], lab[z_[offset]])

