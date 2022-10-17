import time

import matplotlib.pyplot as plt
from sklearn import datasets
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import StratifiedKFold, cross_validate

# import the measure package
from carbonai import PowerMeter

# In all this script we'll try to measure how much CO2 does the training
# of a toy algorithm on the mnist database emit
X, y = datasets.load_digits(return_X_y=True)

# display the data studied
plt.figure(figsize=(8, 6))
plt.style.use("fast")
plt.suptitle("The MNIST dataset")
for i in range(9):
    plt.subplot(3, 3, i + 1)
    plt.imshow(X[i].reshape((8, 8)), cmap="gray")
    plt.title(f"label:{y[i]}")
    plt.axis("off")
plt.show()


# Creates a power meter object that contains information relative to the
# current project
# You need to do this step no matter how you use the package
# You can either declare the variable by hand or use a config file
# power_meter = PowerMeter(
#   project_name="example",
#   program_name="CarbonAI",
#   client_name="IDE",
#   is_online=False,
#   location="FR"
# )
power_meter = PowerMeter.from_config(path="config.json")

# ========== FIRST USAGE OPTION ==========
# Add a decorator to the main function to measure power usage of this
# function each time it is called


@power_meter.measure_power(
    package="sklearn",
    algorithm="SGDClassifier",
    data_type="tabular/images",
    data_shape="(1797, 64)",
    algorithm_params="loss='log_loss', alpha=1e-5",
    comments="10 fold cross validated training of logistic regression \
        classifier trained on the MNIST dataset",
)
def cross_val_mnist(alpha, random_state=0):
    # load data
    mnist = datasets.load_digits(return_X_y=True)
    X = mnist[0]
    y = mnist[1]
    # Classifier
    clf = SGDClassifier(loss="log_loss", alpha=alpha, random_state=random_state)
    # Cross val
    cv = StratifiedKFold(10, random_state=random_state, shuffle=True)
    cv_results = cross_validate(clf, X, y, cv=cv)
    # print results
    print(cv_results["test_score"].mean(), cv_results["test_score"].std())
    time.sleep(5)
    return cv_results


train_results = cross_val_mnist(1e-5)


# ========== SECOND USAGE OPTION ==========
# Use a with statement to run your code

with power_meter(
    package="sklearn",
    algorithm="SGDClassifier",
    data_type="tabular/images",
    data_shape="(1797, 64)",
    algorithm_params="loss='log_loss', alpha=1e-5",
    comments="10 fold cross validated training of logistic regression \
        classifier trained on the MNIST dataset",
):
    mnist = datasets.load_digits(return_X_y=True)
    X = mnist[0]
    y = mnist[1]
    clf = SGDClassifier(loss="log_loss", alpha=1e-5, random_state=0)
    cv = StratifiedKFold(10, random_state=0, shuffle=True)
    cv_results = cross_validate(clf, X, y, cv=cv)
    print(cv_results["test_score"].mean(), cv_results["test_score"].std())
    time.sleep(5)
