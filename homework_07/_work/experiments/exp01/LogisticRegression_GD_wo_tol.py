import logging
from abc import ABC

import numpy as np
from matplotlib import pyplot as plt


def sigmoid(z):
    return 1 / (1 + np.exp(-z))


def loss(h, y):
    return (-y * np.log(h) - (1 - y) * np.log(1 - h)).mean()


def add_intercept(X):
    intercept = np.ones((X.shape[0], 1))
    return np.concatenate((intercept, X), axis=1)


class BaseLG(ABC):
    init_method: str
    lr: int
    num_iter: int
    fit_interception: bool
    verbose: bool
    loss_by_iter_ = []


class LogisticRegression_GD_wo_tol(BaseLG):
    def __init__(self, init_method: str = 'zero',
                 lr=0,
                 num_iter: int = 10000,
                 fit_interception: bool = True,
                 verbose: bool = True):
        if init_method not in ['zero', 'random']:
            strError = "init_method must be one of ['zero','random']"
            print(strError)
            logging.error(strError)
            raise ValueError(strError)
        self.init_method = init_method
        self.lr = lr
        self.num_iter = num_iter
        self.fit_interception = fit_interception
        self.verbose = verbose

    def fit(self, X, y):
        if self.fit_interception:
            X = add_intercept(X)
        self.theta = np.zeros(X.shape[1])

        for i in range(self.num_iter):
            z = np.dot(X, self.theta)
            h = sigmoid(z)
            gradient = np.dot(X.T, (h - y)) / y.size
            self.theta -= self.lr * gradient
            if self.verbose:
                lo = loss(h, y)
                self.loss_by_iter_.append(loss)
                info_str = f'Iteration {i}, loss func {round(lo, 3)}, coeff {np.round(self.theta, 3)}'
                print(info_str)
                logging.info(info_str)

    def loss_visualize(self):
        plt.plot(range(len(self.loss_by_iter_)), self.loss_by_iter_)
        plt.xticks(np.arange(0, self.num_iter, step=self.num_iter / 5))
        plt.xlabel('Numder of iterations')
        plt.yticks('loss-function')
        plt.show()

    def predict_proba(self, X):
        if self.fit_interception:
            X = add_intercept(X)
        return sigmoid(np.dot(X, self.theta))

    def predict(self, X, threshold):
        return (self.predict_proba(X) >= threshold).astype(int)
