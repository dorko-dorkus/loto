"""Project-wide constants."""

DOC_CATEGORY = "Permit/LOTO"
DOC_CATEGORY_DIR = DOC_CATEGORY.replace("/", "_")

# Checklist item verifying the permit has been closed and uploaded.
CHECKLIST_HAND_BACK = "Permit Closed & Hand-back uploaded"

# Work order status domain descriptions
WOSTATUS_DESCRIPTIONS = {
    "SCHED": "Scheduled",
    "INPRG": "In Progress",
    "HOLD": "On Hold",
    "COMP": "Completed",
}
