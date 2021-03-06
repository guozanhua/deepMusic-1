import os
import time

import numpy as np
import tensorflow as tf
from tensorflow.contrib import rnn

from deferred import dataload
from deferred.loader import loaderTrain, loaderTest

# from tensorflow.examples.tutorials.mnist import input_data
# mnist = input_data.read_data_sets("/tmp/data/", one_hot=True)


NB_NOTES_READ = dataload.MIN_SIZE
NB_TRACKS_READ = 3

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
print('TensorFlow version: {0}'.format(tf.__version__))

t = time.time()


def extend_y(y):
    temp = y.tolist()
    for i in range(len(temp)):
        if temp[i] == 1:
            temp[i] = [0, 1]
        else:
            temp[i] = [1, 0]
    y = np.array(temp)
    return y


# dataset = jl.load(r'C:\Users\Theo\Desktop\ClassifierAlbert\datasetSeries.pkl')
# X_train, X_test, y_train, y_test = dataset

X_train, X_test, y_train, y_test = loaderTrain.songs[:], loaderTest.songs[:], loaderTrain.artists[
                                                                              :], loaderTest.artists[:]


def toArray(X, y):
    """Turns lists X and y into arrays, only using relevant informations and a certain number of tracks and notes.
    This function selects the track that starts the latest and put the temporal starting point of gathering the input
    there.
    Params:
        X: cf dataload
        y: cf dataload
    Return:
         X: array of shape (number of songs kept, NB_TRACKS_READ, NB_NOTES_READ, 3)
         y: array of shape (number of songs kept, 1)
    """
    X_train_tmp = []
    indsTrain = []
    for song in X:
        tmp = []
        cmpt = 0
        if len(song.tracks) > 2:
            song.sort_by_tick()
            start_tick = song.tracks[0].notes[0].duration
            for track in song.tracks:
                tmp_track = []
                if track > NB_NOTES_READ and cmpt < 3:
                    for note in track.notes:
                        if note.tick >= start_tick:  # TODO: make sure there are enough notes.
                            tmp_track.append([note.note, note.tick, note.duration])
                    cmpt += 1
                    tmp.append(tmp_track)
            if cmpt == NB_TRACKS_READ:
                X_train_tmp.append(tmp)
                indsTrain.append(X.index(song))
    return np.array([[[k for k in track[:NB_NOTES_READ]] for track in song] for song in X_train_tmp], dtype=np.float32), \
           np.array(y)[indsTrain]

def toArray16(X, y):
    """Turns lists X and y into arrays, using all tracks and NB_NOTES_READ notes.
    This function selects the track that starts the latest and put the temporal starting point of gathering the input
    there.
    Params:
        X: cf dataload
        y: cf dataload
    Return:
         X: array of shape (number of songs kept, 16, NB_NOTES_READ, 3)
         y: array of shape (number of songs kept, 1)
    """
    X_train_tmp = []
    indsTrain = []
    empty = [[-1,-1,-1] for k in range(NB_NOTES_READ)]
    for song in X:
        tmp = []
        if len(song.tracks) > NB_TRACKS_READ-1:
            song.sort_by_tick()
            start_tick = song.tracks[0].notes[0].duration
            for k in range(len(song.tracks)):
                try:
                    track = song.tracks[k]
                    tmp_track = []
                    if track > NB_NOTES_READ:
                        for note in track.notes:
                            if note.tick >= start_tick:  # TODO: make sure there are enough notes.
                                tmp_track.append([note.note, note.tick, note.duration])
                        tmp.append(tmp_track)
                except:
                    tmp.append(empty)
            X_train_tmp.append(tmp)
            indsTrain.append(X.index(song))
    return np.array([[[k for k in track[:NB_NOTES_READ]] for track in song] for song in X_train_tmp], dtype=np.float32), \
           np.array(y)[indsTrain]


def toArray2(X, y):  # collect more batches
    X_train_tmp = []
    indsTrain = []
    for song in X:
        tmp = []
        tmp2 = []
        cmpt = 0
        cmpt2 = 0
        if len(song.tracks) >= NB_TRACKS_READ:
            for track in song.tracks:
                tmp_track = []
                tmp_track2 = []
                if track > NB_NOTES_READ and cmpt < NB_TRACKS_READ:
                    for note in track.notes:
                        tmp_track.append([note.note, note.tick, note.duration])
                    cmpt += 1
                    tmp.append(tmp_track)
                    if track > 2 * NB_NOTES_READ and cmpt2 < NB_TRACKS_READ:
                        tmp_track2 += tmp_track[NB_NOTES_READ:2 * NB_NOTES_READ]
                        cmpt2 += 1
                        tmp2.append(tmp_track2)
            if cmpt == NB_TRACKS_READ:
                X_train_tmp.append(tmp)
                indsTrain.append(X.index(song))
                if cmpt2 == NB_TRACKS_READ:
                    X_train_tmp.append(tmp2)
                    indsTrain.append(X.index(song))
    return np.array([[[k for k in track[:NB_NOTES_READ]] for track in song] for song in X_train_tmp], dtype=np.float32), \
           np.array(y)[indsTrain]


X_train, y_train = toArray(X_train, y_train)
X_test, y_test = toArray(X_test, y_test)

print("X_train.shape : {0}\nX_test.shape : {1}".format(X_train.shape, X_test.shape))
print("y_train.shape : {0}\ny_test.shape : {1}".format(y_train.shape, y_test.shape))

""" useless for our data
indsTrain = np.where(np.isnan(X_train))
indsTest= np.where(np.isnan(X_test))
colMainTrain, colMainTest = np.nanmean(X_train, axis=0), np.nanmean(X_test, axis=0)
X_train[indsTrain] = np.take(colMainTrain, indsTrain[1])
X_test[indsTest] = np.take(colMainTest, indsTest[1])
"""
y_test = extend_y(y_test)
y_train = extend_y(y_train)
# y_train, y_test = np.array(y_train),np.array(y_test)

# learning parameters
learning_rate = 0.0001
epoches = 5000
batch_size = 50  # was 100. Maybe we should try to cut the files in smaller parts in order to get more samples
display_step = 10

# network parameters
n_input = 3  # was 1, changed it to get 3 information on each note
n_tracks = NB_TRACKS_READ  # for now, fixed value, but will have to be changed to "None" (any value)
n_steps = NB_NOTES_READ  # was 10
n_hidden = 1000
n_classes = 2

# Placeholders
X = tf.placeholder(shape=[None, n_tracks, n_steps, n_input], dtype=tf.float32, name="X")
y_true = tf.placeholder(shape=[None, n_classes], dtype=tf.float32, name="y_true")
y_true_cls = tf.argmax(y_true, dimension=1)


def new_weights(shape):
    return tf.Variable(tf.truncated_normal(shape, stddev=0.05))


def new_biases(length):
    return tf.Variable(tf.constant(0.05, shape=[length]))


def new_conv_layer(input,  # The previous layer.
                   num_input_channels,  # Num. channels in prev. layer.
                   filter_size,  # Width and height of filters.
                   num_filters,  # Number of filters.
                   use_pooling=True):  # Use 2x2 max-pooling.

    # Shape of the filter-weights for the convolution.
    # This format is determined by the TensorFlow API.
    shape = [filter_size, filter_size, num_input_channels, num_filters]

    # Create new weights aka. filters with the given shape.
    weights = new_weights(shape)

    # Create new biases, one for each filter.
    biases = new_biases(length=num_filters)

    # Create the TensorFlow operation for convolution.
    # Note the strides are set to 1 in all dimensions.
    # The first and last stride must always be 1,
    # because the first is for the image-number and
    # the last is for the input-channel.
    # But e.g. strides=[1, 2, 2, 1] would mean that the filter
    # is moved 2 pixels across the x- and y-axis of the image.
    # The padding is set to 'SAME' which means the input image
    # is padded with zeroes so the size of the output is the same.
    layer = tf.nn.conv2d(input=input,
                         filter=weights,
                         strides=[1, 1, 1, 1],
                         padding='SAME',
                         data_format='NCHW')

    # Add the biases to the results of the convolution.
    # A bias-value is added to each filter-channel.
    layer =tf.nn.bias_add(value=layer,
                          bias=biases,
                          data_format='NCHW')

    # Use pooling to down-sample the image resolution?
    if use_pooling:
        # This is 2x2 max-pooling, which means that we
        # consider 2x2 windows and select the largest value
        # in each window. Then we move 2 pixels to the next window.
        layer = tf.nn.max_pool(value=layer,
                               ksize=[1, 2, 2, 1],
                               strides=[1, 2, 2, 1],
                               padding='SAME',
                               data_format='NCHW')

    # Rectified Linear Unit (ReLU).
    # It calculates max(x, 0) for each input pixel x.
    # This adds some non-linearity to the formula and allows us
    # to learn more complicated functions.
    layer = tf.nn.relu(layer)

    # Note that ReLU is normally executed before the pooling,
    # but since relu(max_pool(x)) == max_pool(relu(x)) we can
    # save 75% of the relu-operations by max-pooling first.

    # We return both the resulting layer and the filter-weights
    # because we will plot the weights later.
    return layer, weights


def flatten_layer(layer):
    # Get the shape of the input layer.
    layer_shape = layer.get_shape()

    # The shape of the input layer is assumed to be:
    # layer_shape == [num_images, img_height, img_width, num_channels]

    # The number of features is: img_height * img_width * num_channels
    # We can use a function from TensorFlow to calculate this.
    num_features = layer_shape[1:4].num_elements()

    # Reshape the layer to [num_images, num_features].
    # Note that we just set the size of the second dimension
    # to num_features and the size of the first dimension to -1
    # which means the size in that dimension is calculated
    # so the total size of the tensor is unchanged from the reshaping.
    layer_flat = tf.reshape(layer, [-1, num_features])

    # The shape of the flattened layer is now:
    # [num_images, img_height * img_width * num_channels]

    # Return both the flattened layer and the number of features.
    return layer_flat, num_features


def new_fc_layer(input,  # The previous layer.
                 num_inputs,  # Num. inputs from prev. layer.
                 num_outputs,  # Num. outputs.
                 use_relu=True):  # Use Rectified Linear Unit (ReLU)?

    # Create new weights and biases.
    weights = new_weights(shape=[num_inputs, num_outputs])
    biases = new_biases(length=num_outputs)

    # Calculate the layer as the matrix multiplication of
    # the input and weights, and then add the bias-values.
    layer = tf.matmul(input, weights) + biases

    # Use ReLU?
    if use_relu:
        layer = tf.nn.relu(layer)

    return layer


weights = tf.Variable(tf.random_normal([n_hidden, n_classes]))
biases = tf.Variable(tf.random_normal([n_classes]))


def RNN(input, weights, biases):
    # unstack to get a list of 'n_steps' tensors of shape (batch_size, n_input)
    a, b, c, d = input.shape
    input = tf.unstack(input, b, 1)
    print(len(input))
    for k in range(len(input)):
        input[k] = tf.unstack(input[k], c, 1)

    lstm_cell = rnn.BasicLSTMCell(n_hidden)

    # lstm cell output
    outputs, states = rnn.static_rnn(lstm_cell, input[0], dtype=tf.float32)

    # activation_output = tf.reshape(tf.matmul(outputs[-1], weights) + biases, (batch_size, n_tracks, n_steps, n_input))
    outputs = tf.matmul(outputs[-1], weights) + biases
    return outputs, states, outputs.shape


# First convolutional layer.
layer_conv1, weights_conv1 = \
    new_conv_layer(input=X,
                   num_input_channels=n_input,
                   filter_size=50,
                   num_filters=32,
                   use_pooling=False)

# Second convolutional layer.
layer_conv2, weights_conv2 = \
    new_conv_layer(input=layer_conv1,
                   num_input_channels=32,
                   filter_size=20,
                   num_filters=64,
                   use_pooling=False)

# Third convolutional layer.
layer_conv3, weights_conv3 = \
    new_conv_layer(input=layer_conv2,
                   num_input_channels=64,
                   filter_size=5,
                   num_filters=128,
                   use_pooling=False)

# 1st LSTM layer.
layer_lstm, states, shape = RNN(input=layer_conv3,
                                weights=weights,
                                biases=biases)

# Flatten layer.
layer_flat, num_features = flatten_layer(layer_lstm)

# First fully-connected layer.
layer_fc1 = new_fc_layer(input=layer_flat,
                         num_inputs=num_features,
                         num_outputs=256,
                         use_relu=True)

# Second fully-connected layer.
layer_fc2 = new_fc_layer(input=layer_fc1,
                         num_inputs=256,
                         num_outputs=n_classes,
                         use_relu=False)

# Predicted class-label.
y_pred = tf.nn.softmax(layer_fc2)
y_pred_cls = tf.argmax(y_pred, dimension=1)

# Cross-entropy for the classification of each image.
cross_entropy = \
    tf.nn.softmax_cross_entropy_with_logits(logits=layer_fc2,
                                            labels=y_true)

# Loss aka. cost-measure.
# This is the scalar value that must be minimized.
cost = tf.reduce_mean(cross_entropy)
optimizer = tf.train.AdamOptimizer(learning_rate=1e-4).minimize(cost)
correct_prediction = tf.equal(y_pred_cls, y_true_cls)
accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

session = tf.Session()
session.run(tf.global_variables_initializer())
train_batch_size = batch_size

# Counter for total number of iterations performed so far.
total_iterations = 0


def optimize(num_iterations):
    # Ensure we update the global variable rather than a local copy.
    global total_iterations

    # Start-time used for printing time-usage below.
    start_time = time.time()

    for i in range(total_iterations,
                   total_iterations + num_iterations):

        # Get a batch of training examples.
        # x_batch now holds a batch of images and
        # y_true_batch are the true labels for those images.
        rand_index = np.random.choice(len(X_train), size=batch_size)
        x_batch = X_train[rand_index]
        y_true_res = y_train[rand_index]
        x_batch = x_batch.reshape((batch_size, n_tracks, n_steps, n_input))
        y_true_res = y_true_res.reshape((batch_size, n_classes))
        y_true_res = y_true_res.astype(float)

        # Put the batch into a dict with the proper names
        # for placeholder variables in the TensorFlow graph.
        feed_dict_train = {X: x_batch,
                           y_true: y_true_res}

        # Run the optimizer using this batch of training data.
        # TensorFlow assigns the variables in feed_dict_train
        # to the placeholder variables and then runs the optimizer.
        session.run(optimizer, feed_dict=feed_dict_train)

        # Print status every 100 iterations.
        if i % 100 == 0:
            # Calculate the accuracy on the training-set.
            acc = session.run(accuracy, feed_dict=feed_dict_train)

            # Message for printing.
            msg = "Optimization Iteration: {0:>6}, Training Accuracy: {1:>6.1%}"

            # Print it.
            print(msg.format(i + 1, acc))

    # Update the total number of iterations performed.
    total_iterations += num_iterations

    # Ending time.
    end_time = time.time()

    # Difference between start and end-times.
    time_dif = end_time - start_time

    X_tes = X_test.reshape((len(X_test), n_tracks, n_steps, n_input))
    y_tes = y_test.reshape((len(y_test), n_classes))

    print("Testing Accuracy :", session.run(accuracy, feed_dict={X: X_tes, y_true: y_tes}))


optimize(num_iterations=2000)

print("Duration :", time.time() - t)
