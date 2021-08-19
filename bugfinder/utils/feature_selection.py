"""
"""


def retrieve_original_columns_name(feature_selection_model, original_cols):
    selected_cols = feature_selection_model.get_support(indices=True)
    return [original_cols[idx] for idx in selected_cols]
