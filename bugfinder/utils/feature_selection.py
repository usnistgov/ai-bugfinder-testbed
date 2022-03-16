""" Utilities for feature selection.
"""


def retrieve_original_columns_name(feature_selection_model, original_cols):
    """Retrieve column name from given indexes"""
    selected_cols = feature_selection_model.get_support(indices=True)
    return [original_cols[idx] for idx in selected_cols]


def selection_estimators():
    """Available estimators for feature selection."""
    return {
        "LogisticRegression": {
            "package": "sklearn.linear_model",
            "class": "LogisticRegression",
            "kwargs": {},
        },
        "LogisticRegressionCV": {
            "package": "sklearn.linear_model",
            "class": "LogisticRegressionCV",
            "kwargs": {},
        },
        "PassiveAggressive": {
            "package": "sklearn.linear_model",
            "class": "PassiveAggressiveClassifier",
            "kwargs": {},
        },
        "Perceptron": {
            "package": "sklearn.linear_model",
            "class": "Perceptron",
            "kwargs": {},
        },
        "Ridge": {
            "package": "sklearn.linear_model",
            "class": "RidgeClassifier",
            "kwargs": {},
        },
        "RidgeCV": {
            "package": "sklearn.linear_model",
            "class": "RidgeClassifierCV",
            "kwargs": {},
        },
        "SGD": {
            "package": "sklearn.linear_model",
            "class": "SGDClassifier",
            "kwargs": {},
        },
        "DecisionTree": {
            "package": "sklearn.tree",
            "class": "DecisionTreeClassifier",
            "kwargs": {},
        },
        "ExtraTree": {
            "package": "sklearn.tree",
            "class": "ExtraTreeClassifier",
            "kwargs": {},
        },
        "AdaBoost": {
            "package": "sklearn.ensemble",
            "class": "AdaBoostClassifier",
            "kwargs": {},
        },
        "ExtraTrees": {
            "package": "sklearn.ensemble",
            "class": "ExtraTreesClassifier",
            "kwargs": {},
        },
        "GradientBoosting": {
            "package": "sklearn.ensemble",
            "class": "GradientBoostingClassifier",
            "kwargs": {},
        },
        "RandomForest": {
            "package": "sklearn.ensemble",
            "class": "RandomForestClassifier",
            "kwargs": {},
        },
        "SVC": {
            "package": "sklearn.svm",
            "class": "SVC",
            "kwargs": {"kernel": "linear"},
        },
        "SVR": {
            "package": "sklearn.svm",
            "class": "SVR",
            "kwargs": {"kernel": "linear"},
        },
        "NuSVC": {
            "package": "sklearn.svm",
            "class": "NuSVC",
            "kwargs": {"kernel": "linear"},
        },
        "NuSVR": {
            "package": "sklearn.svm",
            "class": "NuSVR",
            "kwargs": {"kernel": "linear"},
        },
        "OneClassSVM": {
            "package": "sklearn.svm",
            "class": "OneClassSVM",
            "kwargs": {"kernel": "linear"},
        },
    }
