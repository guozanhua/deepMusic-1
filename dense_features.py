"""
This file is used to generate a model that classifies songs depending on the genre they belong to.
The model can use from two to four different genres.
"""

import os
import time
import xml.etree.ElementTree as ET
import keras
import matplotlib.pyplot as plt
from matplotlib import offsetbox
import matplotlib.patheffects as PathEffects
import seaborn as sns
import numpy as np
import tensorflow as tf
from keras.layers import Dense, Dropout
from keras.models import Sequential
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score, precision_score
from sklearn.preprocessing import StandardScaler
from sklearn.manifold import TSNE
from sklearn.model_selection import StratifiedKFold
from deferred import dataload_hex
from sklearn import datasets
from mpl_toolkits.mplot3d import Axes3D
#from XGBoost import run_XGBoost

# NB_NOTES_READ = dataload_hex.MIN_SIZE

# This prevents Tensorflow from throwing warning messages all the time
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
print('TensorFlow version: {0}'.format(tf.__version__))

# Global time counter
t = time.time()
# Number of different classes processed (1<x<5)
N_CLASSES = 2
CLASSES = ["jazz", "rap", "rock", "blues"]

# Extracts data from jSymbolic2 generated xml files. Cf ReadMe for more detailed information
X1 = ET.parse(
    r"jSymbolic2\features\extracted_feature_led_zep124.xml").getroot()
X2 = ET.parse(
    r"jSymbolic2\features\extracted_feature_random_feat.xml").getroot()
X3 = ET.parse(
    r"jSymbolic2\features\extracted_feature_values_jazz.xml").getroot()
X4 = ET.parse(
    r"jSymbolic2\features\extracted_feature_values_rap.xml").getroot()

print("XML files parsed")


def parse(X, y):
    """
    :param X: jSymbolic2 data
    :param y: id of the class
    :return: (features of each song of X, a vector that contains the id of the class)
    """
    out = []
    for song in X[1:]:  # remove the first
        features = []
        for feature in song[1:]:  # remove the first
            features.append(float(feature[1].text.replace(',', '.')))  # commas in XML files have to be turned into dot
        out.append(features)
    return out, [y for _ in range(len(X[1:]))]


def get_data(X1, X2, X3=None, X4=None):
    """
    :param X1 to X4: jSymbolic2 data
    :return: (feature vector of each songs, their id)
    """
    xt1, yt1 = parse(X1, 0)
    xt2, yt2 = parse(X2, 1)
    xt3, yt3, xt4, yt4 = None, None, None, None
    if X3 is not None:
        xt3, yt3 = parse(X3, 2)
    if X4 is not None:
        xt4, yt4 = parse(X4, 3)

    X_tot = np.concatenate(tuple((k for k in (xt1, xt2, xt3, xt4) if k is not None)))
    y_tot = np.concatenate(tuple((k for k in (yt1, yt2, yt3, yt4) if k is not None)))
    return X_tot, y_tot


# Standardization, cf implementation of StandardScaler
def standardize(X):
    scaler = StandardScaler().fit(X)
    rescaled = scaler.transform(X)
    return rescaled


def data_process(X1, X2, X3=None, X4=None):
    """
    Standardizes, randomizes the data, making it usable by keras
    :param X1 to X4: jSymbolic2 data
    :return: X_train, X_test, y_train, y_test
    """
    X_tot, y_tot = get_data(X1, X2, X3, X4)

    X_tot = standardize(X_tot)

    # Randomization
    inds = np.random.permutation(X_tot.shape[0])
    train_inds, test_inds = inds[:int(0.8 * len(inds))], inds[int(0.8 * len(inds)):]  # 80% training set, 20% testing set
    X_train = X_tot[train_inds]
    X_test = X_tot[test_inds]
    y_train = y_tot[train_inds]
    y_test = y_tot[test_inds]

    return X_train, X_test, y_train, y_test

# Not really clever switch, that calls data_process for the good number of inputs
if N_CLASSES == 2:
    X_train, X_test, y_train, y_test = data_process(X1, X2)
elif N_CLASSES == 3:
    X_train, X_test, y_train, y_test = data_process(X1, X2, X3)
else:
    X_train, X_test, y_train, y_test = data_process(X1, X2, X3, X4)

X_tot = np.concatenate((X_test, X_train))
y_tot = np.concatenate((y_test, y_train))


# GBM
def call_GMB():
    clf = GradientBoostingClassifier()
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("GBM accuracy = ", accuracy)

print("X_train.shape : {0}\nX_test.shape : {1}".format(X_train.shape, X_test.shape))
print("y_train.shape : {0}\ny_test.shape : {1}".format(y_train.shape, y_test.shape))


# Scatter plot, uses 3 most significant features.
def tSNE(X, y, labels, n_dim=3):
    model = TSNE(n_components=n_dim, random_state=42)
    np.set_printoptions(suppress=True)
    tX = model.fit_transform(X)
    # We choose a color palette with seaborn.
    palette = np.array(sns.color_palette("hls", len(labels)))

    # We create a scatter plot.
    f = plt.figure(figsize=(8, 8))
    ax = f.add_subplot(111, aspect='equal', projection='3d')
    sc = ax.scatter(tX[:, 0], tX[:, 1], zs=tX[:, 2], lw=0, s=40,
                    c=palette[y.astype(np.int)])
    plt.xlim(-25, 25)
    plt.ylim(-25, 25)
    # ax.axis('off')
    ax.axis('tight')

    # We add the labels for each digit.
    txts = []
    for label in labels:
        # Position of each label.
        g = tX[y == labels.index(label), :]
        xtext, ytext, ztext = np.median(tX[y == labels.index(label), :], axis=0)
        txt = ax.text(xtext, ytext, ztext, label, fontsize=24)
        txt.set_path_effects([
            PathEffects.Stroke(linewidth=5, foreground="w"),
            PathEffects.Normal()])
        txts.append(txt)
    plt.legend()
    plt.show()
    return f, ax, sc, txts

# tSNE(X_train, y_train, CLASSES)
# call_GMB()

# Learning parameters
learning_rate = 0.001  # Can be lower, avoid making it bigger
epoches = 5000  # Doesn't need to be too high (training accuracy can always improve, but then loss gets big)
batch_size = 100  # Has little impact on the results
dropout = 0.6  # Used to avoid overfitting, 0.6 seems to be a good value
dense_layers = 600  # 600 is empirically a good value


y_train_cat = keras.utils.to_categorical(y_train, num_classes= N_CLASSES)
y_test_cat = keras.utils.to_categorical(y_test, num_classes= N_CLASSES)


def create_model(n_classes=N_CLASSES):
    """
    Dense layers model : the number of layers could be changed, but it seems hard to significantly improve this model
    using this architecture. Should consider using other types of layers (convolutionnal, LSTM...)
    :param n_classes:
    :return: a Keras model
    """
    model = Sequential([
        Dense(dense_layers, activation="relu", input_shape=(len(X_tot[0]),)),
        Dropout(dropout),
        Dense(dense_layers, activation="relu"),
        Dropout(dropout),
        Dense(dense_layers, activation="relu"),
        Dropout(dropout),
        Dense(300, activation="relu"),
        Dropout(dropout),
        Dense(n_classes, activation="sigmoid")
    ])
    return model


def run_model(model, X_train, X_test, y_train, y_test, iter=0):
    """
    Main function. Evolves the given model using training data and tests it with testing data.
    Also plot and save the figure that shows accuracy through evolution. Saves the model.
    :param model: Keras model
    :param X_train:
    :param X_test:
    :param y_train:
    :param y_test:
    :param iter: optionnal, used when iterating
    :return: score for testing set using the evolved model
    """
    # Custom optimizer
    sgd = keras.optimizers.SGD(lr=learning_rate)

    # Choice of optimizer, loss and metrics
    model.compile(optimizer=sgd,
                  loss='categorical_crossentropy',
                  metrics=['accuracy'])

    hist_test = []
    hist1 = []
    # Training
    for k in range(int(epoches/100)):
        hist = model.fit(X_train, y_train, epochs=int(epoches/100), batch_size=batch_size, verbose=2)
        hist_test.append(model.evaluate(X_test,y_test))
        hist1.append(hist.history.get("acc")[-1])
    # model.optimizer.lr = tf.constant(learning_rate / 10)
    # hist2 = model.fit(X_train, y_train, epochs=int(epoches / 3), batch_size=batch_size, verbose=2)

    # Testing
    score = model.evaluate(X_test, y_test)

    print("\nScore :", score)
    print("\nDuration :", time.time() - t)

    # Saving the model
    model.save(r"models/dense_xml_ledzep_random_%.3f.h5" % score[1])

    '''plt.plot(hist1)  # + hist2.history.get("acc"))
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.axis([0, epoches, 0, 1])
    plt.savefig(r'plot/Training_JRR_Dense_4layers%s_%.1fdropout_%sbatch_%.3ftest.png' % (dense_layers, dropout, batch_size, score[1]))
    plt.clf()'''
    plt.plot(hist1)
    plt.plot(hist_test)
    plt.xlabel('Epoch/100')
    plt.ylabel('Accuracy')
    plt.axis([0, epoches/100, 0, 1])
    plt.legend()
    plt.savefig(r'plot/Testing_LedzepRandom_Dense_4layers%s_%.1fdropout_%sbatch_%.3ftest.png' % (dense_layers, dropout, batch_size, score[1]))
    return score[1]


def one_vs_all(y_train, y_test, num_class=0):
    """
    Used when the number of class is bigger than 2.
    :param y_train:
    :param y_test:
    :param num_class:
    :return:
    """
    ytr, yte = [], []
    for k in range(len(y_train)):
        ytr.append(int(y_train[k] == num_class))
    for k in range(len(y_test)):
        yte.append(int(y_test[k] == num_class))
    return ytr, yte


def run_model_one_vs_all():
    """
    Same as run_model with more classes. Less efficient.
    :return:
    """
    # Custom optimizer
    sgd = keras.optimizers.SGD(lr=learning_rate)

    hist_test_tot = []
    hist_train_tot = []
    a = {}

    for k in range(N_CLASSES):  # Create as many models as there are classes

        ytr, yte = one_vs_all(y_train, y_test, num_class=k)

        model = create_model(n_classes=1)  # In binary classification, we only need one output
        # Choice of optimizer, loss and metrics
        model.compile(optimizer=sgd,
                  loss='binary_crossentropy',
                  metrics=['binary_accuracy'])

        hist_test = []
        hist1 = []

        # Training
        for j in range(int(epoches/100)):
            hist = model.fit(X_train, ytr, epochs=int(epoches/100), batch_size=batch_size, verbose=0)
            print("%s/%s" % (j, int(epoches/100)))
            # hist_test.append(model.evaluate(X_test, y_test))
            hist1.append(hist.history.get("binary_accuracy")[-1])

        hist_train_tot.append(hist1)

        # Testing
        score = model.evaluate(X_test, yte)

        # Saving the model in the dict
        a[k] = model

        print("\nScore %s vs all : %s" % (CLASSES[k], score))
        print("\nDuration :", time.time() - t)

    # Saving the model
    # model.save(r"models/dense_xml_jazz_rap_rock_blues_%.3f.h5" % score[1])

    # Testing the model. We use "one vs all" strategy, and compare which one gives the best result in each case.
    score = 0
    for j in range(len(y_test)):
        pred = []
        for k in range(N_CLASSES):
            pred.append(a[k].predict(X_test[j:j+1]))
        prediction = pred.index(max(pred))
        score += int(prediction == y_test[j])  # Adds 1 to the score if the prediction is correct

    print('\n Final Score :', score/len(y_test))

    # Plot accuracy for training set
    '''plt.plot(hist1)  # + hist2.history.get("acc"))
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.axis([0, epoches, 0, 1])
    plt.savefig(r'plot/Training_JRR_Dense_4layers%s_%.1fdropout_%sbatch_%.3ftest.png' % (dense_layers, dropout, batch_size, score[1]))
    plt.clf()'''
    plt.plot(hist_train_tot[0])
    #plt.plot(hist_test)
    plt.xlabel('Epoch/100')
    plt.ylabel('Accuracy')
    plt.axis([0, epoches/100, 0, 1])
    plt.legend()
    plt.savefig(r'plot/Testing_JRRB_Dense_4layers%s_%.1fdropout_%sbatch_%.3ftest.png' % (dense_layers, dropout, batch_size, score/len(y_test)))
    return score

# Dirty switch to run the evolution.
if N_CLASSES == 2:
    model = create_model()
    out = run_model(model, X_train, X_test, y_train_cat, y_test_cat)
else:
    out = run_model_one_vs_all()

# StratifiedKFold method (cf google to see how it works), used to get better insight on the results.

'''if __name__ == "__main__":
    n_folds = 5
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True)
    i = 0
    output = []
    for (train, test) in skf.split(X_tot, y_tot):
        i += 1
        print("\nRunning Fold", i, "/", n_folds)
        model = None
        model = create_model()
        out = run_model(model, X_tot[train], X_tot[test], y_tot[train], y_tot[test], iter=i)
        output.append(out)
    print("\nMean : ", np.mean(output))
    print("\nStd : ", np.std(output))'''
