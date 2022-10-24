from dataclasses import dataclass


@dataclass(frozen=True)
class SimpleTerminologyItem:
    codelist_code: str
    code: str
    nci_preferred_term: str
    cdisc_definition: str
