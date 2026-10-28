##
# File:  catalog.py
# Date:  28-Oct-2026
#
# Action ids and Level 2 module choices for the annotator batch console.
##
"""Catalog of console actions. Keep in sync with htdocs/console/js/console.js labels."""

ACTION_ADD_TO_MY_TODO = "add_to_my_todo"
ACTION_REMOVE_FROM_MY_TODO = "remove_from_my_todo"
ACTION_RUN_OR_RESTART_LEVEL2_MODULE = "run_or_restart_level2_module"

IMPLEMENTED_ACTION_IDS = frozenset(
    (
        ACTION_ADD_TO_MY_TODO,
        ACTION_REMOVE_FROM_MY_TODO,
        ACTION_RUN_OR_RESTART_LEVEL2_MODULE,
    )
)

ACTION_LABELS = {
    ACTION_ADD_TO_MY_TODO: "Add to my TO DO",
    ACTION_REMOVE_FROM_MY_TODO: "Remove from my TO DO",
    ACTION_RUN_OR_RESTART_LEVEL2_MODULE: "Run or Restart a module",
}

# id -> workflow class_id used in status.communication / wf_class_dict
LEVEL2_MODULES = (
    {"id": "reportmod", "class_id": "ReportMod", "label": "ReportMod", "has_run_ui": False},
    {"id": "transmod", "class_id": "TransMod", "label": "TransMod", "has_run_ui": True},
    {"id": "ligmod", "class_id": "LigMod", "label": "LigMod", "has_run_ui": True},
    {"id": "seqmod", "class_id": "SeqMod", "label": "SeqMod", "has_run_ui": True},
    {"id": "annmod", "class_id": "AnnMod", "label": "AnnMod", "has_run_ui": True},
    {"id": "valmod", "class_id": "ValMod", "label": "ValMod", "has_run_ui": False},
    {"id": "reportmod2", "class_id": "ReportMod2", "label": "ReportMod2", "has_run_ui": False},
    {"id": "statmod", "class_id": "StatMod", "label": "StatMod", "has_run_ui": False},
)

LEVEL2_OPERATIONS = (
    {"id": "run", "label": "Run"},
    {"id": "run_ui", "label": "Run+UI"},
    {"id": "restart", "label": "Restart"},
)


def action_label(action_id):
    return ACTION_LABELS.get(action_id, action_id)


def level2_module_by_id(module_id):
    wanted = str(module_id or "").strip().lower()
    for row in LEVEL2_MODULES:
        if row["id"] == wanted:
            return row
    return None


def validate_level2_choice(module_id, operation):
    row = level2_module_by_id(module_id)
    op = str(operation or "").strip().lower()
    if not row:
        raise ValueError("Choose a Level 2 module.")
    if op not in ("run", "run_ui", "restart"):
        raise ValueError("Choose Run, Run+UI, or Restart.")
    if op == "run_ui" and not row.get("has_run_ui"):
        raise ValueError("Run+UI is not available for that module. Choose Run or Restart.")
    return row, op
