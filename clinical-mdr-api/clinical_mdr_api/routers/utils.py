"""Common utility constants / functions used by router functions."""

from fastapi import Path

# Useful type declarations

studyUID = Path(None, description="The unique id of the study.")

studySelectionUid = Path(None, description="The unique id of the study selection.")

studyDesignCellUid = Path(None, description="The unique id of the study design cell.")

studyActivityScheduleUid = Path(
    None, description="The unique id of the study activity schedule."
)

studyActivityInstructionUid = Path(
    None, description="The unique id of the study activity instruction."
)

studyCompoundDosingUid = Path(
    None, description="The unique id of the study compound dosing."
)
