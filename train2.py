from __future__ import print_function
import tensorflow as tf
from keras.datasets import cifar10
from keras.preprocessing.image import ImageDataGenerator
from keras.models import Sequential
from keras.layers import Dropout, Activation, Convolution2D, GlobalAveragePooling2D, merge
from keras.utils import np_utils, plot_model
from keras.optimizers import SGD
from keras import backend as K
from keras.models import Model
from keras.layers.core import Lambda
from keras.callbacks import ModelCheckpoint
import provider
import pandas
import cv2
import numpy as np

K.set_image_dim_ordering('tf')

batch_size = 32
nb_classes = 10
nb_epoch = 350

rows, cols = 32, 32

channels = 3

train_dir = "data/quality_0"
test_dir = train_dir

def load_data(quality=True):
    if not (quality):
        (X_train, y_train), (X_test, y_test) = cifar10.load_data()
        print('X_train shape:', X_train.shape)
        print(X_train.shape[0], 'train samples')
        print(X_test.shape[0], 'test samples')

        print (X_train.shape[1:])

        Y_train = np_utils.to_categorical(y_train, nb_classes)
        Y_test = np_utils.to_categorical(y_test, nb_classes)

        X_train = X_train.astype('float32')
        X_test = X_test.astype('float32')
        X_train /= 255
        X_test /= 255

    else:
        print ("load quality")
        X_train, y_train = provider.load_data(train_dir, "train.h5")
        X_test, y_test = provider.load_data(test_dir, "test.h5")

    Y_train = np_utils.to_categorical(y_train, nb_classes)
    Y_test = np_utils.to_categorical(y_test, nb_classes)
    print (X_train.shape, Y_train.shape, X_test.shape, Y_test.shape)
    return (X_train, Y_train), (X_test, Y_test)

def build_model():
    model = Sequential()

    model.add(Convolution2D(32, (3, 3), padding = 'same', input_shape=(32, 32, 3)))
    model.add(Activation('relu'))
    model.add(Convolution2D(64, (3, 3), padding='same'))
    model.add(Activation('relu'))
    model.add(Convolution2D(128, (3, 3), padding='same', strides = (2,2)))
    model.add(Dropout(0.5))

    model.add(Convolution2D(128, (3, 3), padding = 'same'))
    model.add(Activation('relu'))
    model.add(Convolution2D(128, (3, 3), padding='same'))
    model.add(Activation('relu'))
    model.add(Convolution2D(128, (3, 3), padding='same', strides = (2,2)))
    model.add(Dropout(0.5))

    model.add(Convolution2D(128, (3, 3), padding = 'same'))
    model.add(Activation('relu'))
    model.add(Convolution2D(128, (1, 1), padding='valid'))
    model.add(Activation('relu'))
    model.add(Convolution2D(10, (1, 1), padding='valid'))

    model.add(GlobalAveragePooling2D())
    model.add(Activation('softmax'))
    sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

    return model

def save_summary(model, header, suffix):
    assert(suffix.split(".")[0] == "")
    with open(header + suffix, 'w') as fh:
        # Pass the file handle in as a lambda functions to make it callable
        model.summary(print_fn=lambda x: fh.write(x + '\n'))

def data_generator():
    data_gen = ImageDataGenerator(
            featurewise_center=False,  # set input mean to 0 over the dataset
            samplewise_center=False,  # set each sample mean to 0
            featurewise_std_normalization=False,  # divide inputs by std of the dataset
            samplewise_std_normalization=False,  # divide each input by its std
            zca_whitening=False,  # apply ZCA whitening
            rotation_range=0,  # randomly rotate images in the range (degrees, 0 to 180)
            width_shift_range=0.1,  # randomly shift images horizontally (fraction of total width)
            height_shift_range=0.1,  # randomly shift images vertically (fraction of total height)
            horizontal_flip=True,  # randomly flip images
            vertical_flip=False)
    return data_gen

def train():
    (X_train, Y_train), (X_test, Y_test) = load_data()
    model = build_model()
    # save_summary(model, "parameters/model", ".txt")
    # plot_model(model, to_file="parameters/model" + ".pdf", show_shapes=True)
    data_gen = data_generator()
    data_gen.fit(X_train)
    filepath="weights.hdf5"
    checkpoint = ModelCheckpoint(filepath, monitor='val_acc', verbose=1, save_best_only=True, save_weights_only=False, mode='max')

    callbacks_list = [checkpoint]
        # Fit the model on the batches generated by datagen.flow().
    history_callback = model.fit_generator(data_gen.flow(X_train, Y_train,
                                           batch_size=batch_size),
                                           samples_per_epoch=X_train.shape[0],
                                           nb_epoch=nb_epoch, validation_data=(X_test, Y_test),
                                           callbacks=callbacks_list, verbose=0)

    pandas.DataFrame(history_callback.history).to_csv("history.csv")
    model.save('keras_allconv.h5')


def predict(filename):
    im = cv2.resize(cv2.imread('image.jpg'), (224, 224)).astype(np.float32)
    out = model.predict(im)
    print (np.argmax(out))

if __name__ == "__main__":
    train()
