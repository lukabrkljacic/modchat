# model_registry.py
"""Model Registry contains the dictionary of available vendors and models as defined in mod/enums/model_vendors.py"""
from src.enums.model_vendors import MODEL_VENDORS
# Add cards from imported enums to available vendors list

AVAILABLE_VENDORS = [
    vendor.Card.value for vendor in MODEL_VENDORS
]
