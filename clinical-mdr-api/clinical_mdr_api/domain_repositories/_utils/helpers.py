"""Database related helper functions."""

from neomodel import db


def db_result_to_list(result) -> list[dict]:
    """
    Converts a Cypher query result to a list of dictionaries.

    Args:
        result: The result of a Cypher query.

    Returns:
        list[dict]: A list of dictionaries representing the result.
    """
    data = []
    for row in result[0]:
        new_item = {}
        for index, header in enumerate(result[1], start=0):
            new_item[header] = row[index]
        data.append(new_item)
    return data


def acquire_write_lock_study_value(uid: str) -> None:
    db.cypher_query(
        """
        MATCH (sr:StudyRoot {uid: $uid})
        REMOVE sr.__WRITE_LOCK__
        RETURN true
        """,
        {"uid": uid},
    )
