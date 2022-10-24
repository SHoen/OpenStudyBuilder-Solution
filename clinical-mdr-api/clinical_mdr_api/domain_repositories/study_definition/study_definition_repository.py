from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple

from neomodel import NodeMeta

from clinical_mdr_api.domain.study_definition_aggregate.root import (
    StudyDefinitionAR,
    StudyDefinitionSnapshot,
)
from clinical_mdr_api.domain.study_definition_aggregate.study_metadata import (
    StudyFieldAuditTrailEntryAR,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,  # type: ignore
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator


class StudyDefinitionRepository(ABC):
    """
    Abstract Study Repository. Abstract class meant to be a base for concrete study repository implementation.
    A class provides public repository methods for Study persistence and retrieval and implements all relevant
    Memento pattern interactions with the StudyDefinitionAR class for getting StudySnapshots for save and for
    StudyDefinitionAR creation from StudyDefinitionSnapshot retrieved from repository as well as tracking of
    StudyDefinitionAR instances declared as retrieved with intent of updating.

    Concrete repository implementation is expected to:
    * provide implementation for _retrieve_snapshot_by_uid, _save, _create and _retrieve_all_snapshots methods
    (see details in abstract method
        docstrings)
    * if necessary provide a constructor with some necessary initializations (possibly injecting some dependencies, e.g.
        some transaction manager object). It's assumed that every request served creates its own instance of this class.
        NOTE: if provided, subclass constructor is expected to call super().__init__(), to allow base class to init
        properly as well.
    * if necessary override a close lifecycle method to do some cleanup or finalization (and again if that's the case
        a super().close() also should be invoked).
    """

    @dataclass
    class _RepositoryAuditInfo:
        """
        A class to communicate additional information necessary for the repository, to retain proper audit info on
        modifications and creation of study instances.
        """

        user: Optional[str] = None

    __retrieved_for_update: Dict[str, StudyDefinitionAR]
    __audit_info: _RepositoryAuditInfo
    __closed: bool = False

    def __init__(self):
        self.__retrieved_for_update = {}
        self.__audit_info = self._RepositoryAuditInfo()

    def _check_not_closed(self) -> None:
        """
        Protected method used internally by the repository implementation to raise an error in case of
        attempt repository after it's been closed.
        """
        if self.__closed:
            raise ValueError("Cannot use repository after it's closed.")

    @property
    def audit_info(self) -> _RepositoryAuditInfo:
        """
        A property used to set and get information needed by the repository to retain proper audit trail on
        study updates and creation.

        :return: a reference to an object containing properties which should be set to retain a proper audit info
        """
        return self.__audit_info

    def find_by_uid(
        self, uid: str, for_update: bool = False
    ) -> Optional[StudyDefinitionAR]:
        """
        Public repository method for bringing an instance of study aggregate (StudyDefinitionAR class) restored from its
        state persisted in the underlying DB.

        :param uid: uid of the study to be retrieved
        :param for_update: True - informs the repository that an application intent is to change the state of this
            instance, which implies engaging means of assuring consistent update with regard to possible concurrency
            with other processing possibly changing the state of the same aggregate instance.
        :return: A restored instance of Study aggregate (StudyDefinitionAR class) or None (if instance given by uid does
         not exist in the underlying DB).
        """
        self._check_not_closed()

        # If we have it already in memory return the same one.
        # Note that means that (in above situation) we are going to return instance which already might have been
        # somehow processed
        # by the code outside repository and possibly modified. If that is the case the state of this instance
        # may be different that the state of underlying DB. This is done on purpose to avoid very difficult to debug
        # errors caused by the situation when actually in the service execution the same aggregate instance
        # (the same instance by mean of uid) is represented as two different in-memory instances and possibly updated
        # in different way and then saved. This may lead to some unpredictable result, so to avoid that we try to
        # guarantee that once some particular instance was retrieved for update (at least once) every subsequent
        # repository request to retrieve instance with the same uid returns exactly the same in-memory instance.
        result: Optional[StudyDefinitionAR] = self.__retrieved_for_update.get(uid)
        if result is not None:
            return result

        # now get the data from db
        snapshot: Optional[StudyDefinitionSnapshot]
        additional_closure: Any
        (snapshot, additional_closure) = self._retrieve_snapshot_by_uid(uid, for_update)

        # if no data, then no object
        if snapshot is None:
            return None
        # if exists then prepare our result
        result = StudyDefinitionAR.from_snapshot(snapshot)
        result.repository_closure_data = RepositoryClosureData(
            not_for_update=not for_update,
            additional_closure=additional_closure,
            repository=self,
        )

        # if retrieved for update then we should remember this instance
        if for_update:
            self.__retrieved_for_update[uid] = result

        # and that's it we are done
        return result

    @staticmethod
    def find_uid_by_study_number(study_number: int):
        all_study_values = StudyValue.nodes.filter(study_number=study_number)
        for study_value in all_study_values:
            sr = study_value.study_root.get_or_none()
            if sr is not None:
                return sr.uid
        return None

    @staticmethod
    def study_number_exists(study_number: str) -> bool:
        """
        Checks whether a specified study number already exists within the database.
        """
        study_value = StudyValue.nodes.get_or_none(study_number=study_number)
        if study_value:
            return bool(study_value.latest_value.get_or_none())
        return False

    def save(self, study: StudyDefinitionAR) -> None:
        """
        Public repository method for persisting a (possibly modified) state of the Study instance into the underlying
        DB. Provided instance can be brand new instance (never persisted before) or an instance which has been
        retrieved with find_by_uid(..., for_update=True). Attempt to persist an instance which was retrieved with
        for_update==False ends in error.

        :param study: an instance of Study aggregate (StudyDefinitionAR class) to persist
        """
        self._check_not_closed()
        repository_closure_data: RepositoryClosureData = study.repository_closure_data
        snapshot: StudyDefinitionSnapshot = study.get_snapshot()

        assert (
            snapshot.uid is not None
        )  # this should always hold (if not something must be wrong)

        if repository_closure_data is None:
            # this is the case of new instance (not persisted yet)
            self._create(snapshot)
        elif repository_closure_data.repository is not self:
            raise ValueError(
                "Aggregate instances can be save only by repository which has retrieved the instance."
            )
        elif repository_closure_data.not_for_update:
            raise ValueError(
                "Only aggregate instances retrieved for update can be saved."
            )
        else:
            # this is the case of saving an instance which was retrieved for update from this repository
            # if no one fiddled with repository closure data (which is strictly forbidden, only repository can do it)
            # following assertion should hold
            assert self.__retrieved_for_update[snapshot.uid] == study

            self._save(snapshot, repository_closure_data.additional_closure)
            self.__retrieved_for_update.pop(snapshot.uid)

        # we assume save is possible only once per instance
        # the following prevent future saves for this instance
        # i.e. the instance is now marked as if it was retrieved with for_update==False
        study.repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )

    def find_all(
        self,
        has_study_objective: Optional[bool] = None,
        has_study_endpoint: Optional[bool] = None,
        has_study_criteria: Optional[bool] = None,
        has_study_activity: Optional[bool] = None,
        has_study_activity_instruction: Optional[bool] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionAR]:
        """
        Public method which is to retrieve (a part of) whole Study repository content in the form of Study aggregate
        instances (StudyDefinitionAR class). The part of the content is given by pagination type parameters, accompanied
        with assumed sort of order of the repository given by identifying a sort key (currently only by uid supported)
        and possibility to request the order to be reverse. Instances are retrieved with for_update=False semantics (see
        description of find_by_uid method). Moreover it's forbidden to retrieve any Study instance for update before
        invoking this method (attempt to do that ends in Error).

        NOTE: Normally queried like this should not make use of domain model  since in most cases domain objects are
        too heavy to support reporting (meant as any queries that use data from numerous instances of aggregate).
        This has a chance to work fine only for very light aggregates and queries which do not need to use many
        instances. Currently this is a case for StudyDefinitionAR, so we do that (however we must be prepared for
        refactoring and reimplementation of those reporting methods as we progress).

        has_study_objective: boolean to specify if returned studies must be linked to study objectives or not
        has_study_endpoint: boolean to specify if returned studies must be linked to study endpoints or not
        has_study_criteria: boolean to specify if returned studies must be linked to study criteria or not
        has_study_activity: boolean to specify if returned studies must be linked to study activities or not
        has_study_activity_instruction: boolean to specify if returned studies must be linked to activity instruction or not
        sort_by: dictionary of Cypher aliases on which to apply sorting as keys, and boolean to define sort direction (true=ascending) as values
        page_number : int, number of the page to return. 1-based
        page_size : int, number of results per page
        filter_by : dict, keys are fieldNames for filter_variable and values are objects describing the filtering to execute
        total_count : boolean, indicates if total count of results should be returned
        :return: Dictionary of 'items' and 'total_count'. 'items' contains the results in the form of StudyDefinitionAR instances.
        Not more than page_size items. Can be less than than that in case of the last page.
        Empty sequence in case page_number and page_size parameters pass out of the whole repository content.
        """
        self._check_not_closed()
        # since query works in db so it cannot give proper result if we have some instances retrieved
        # for update
        assert len(self.__retrieved_for_update) == 0

        # delegating the real work to abstract method
        snapshots: GenericFilteringReturn[
            StudyDefinitionSnapshot
        ] = self._retrieve_all_snapshots(
            has_study_objective=has_study_objective,
            has_study_endpoint=has_study_endpoint,
            has_study_criteria=has_study_criteria,
            has_study_activity=has_study_activity,
            has_study_activity_instruction=has_study_activity_instruction,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
            filter_by=filter_by,
            filter_operator=filter_operator,
        )
        # projecting results to StudyDefinitionAR instances
        studies: Sequence[StudyDefinitionAR] = [
            StudyDefinitionAR.from_snapshot(s) for s in snapshots.items
        ]

        # attaching a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for study in studies:
            study.repository_closure_data = repository_closure_data

        # and we are done
        return GenericFilteringReturn.create(
            items=studies, total_count=snapshots.total_count
        )

    def find_all_by_library_item_uid(
        self,
        uid: str,
        library_item_type: NodeMeta,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 50,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
    ) -> GenericFilteringReturn[StudyDefinitionAR]:
        """
        Public method which is to retrieve the list of studies having selected the library item with provided uid
        in the form of Study aggregate instances (StudyDefinitionAR class).

        :param uid: The uid of the library item that the study must have selected
        """
        self._check_not_closed()
        # Since query works in db so it cannot give proper result if we have some instances retrieved for update
        assert len(self.__retrieved_for_update) == 0

        # Find all studies referencing given library item
        # Get snapshots through implementation
        snapshots: GenericFilteringReturn[
            StudyDefinitionSnapshot
        ] = self._retrieve_all_snapshots(
            page_number=page_number,
            page_size=page_size,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            study_selection_object_node_id=uid,
            study_selection_object_node_type=library_item_type,
        )
        # Project results to StudyDefinitionAR instances
        studies: Sequence[StudyDefinitionAR] = [
            StudyDefinitionAR.from_snapshot(s) for s in snapshots.items
        ]

        # Attach a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for study in studies:
            study.repository_closure_data = repository_closure_data

        # Return output
        return GenericFilteringReturn.create(items=studies, total_count=0)

    def close(self) -> None:
        """
        Marks this repository instance as closed. Closed repository cannot be used anymore.
        If concrete repository has some more cleanup to do it should override this method (but call super().close()).
        """
        self.__retrieved_for_update = {}
        self.__closed = True

    def __del__(self):
        if not self.__closed:
            self.close()

    @abstractmethod
    def _retrieve_snapshot_by_uid(
        self, uid: str, for_update: bool
    ) -> Tuple[Optional[StudyDefinitionSnapshot], Any]:
        """
        Abstract method of the study repository, which is supposed to:

        * retrieve a representation of study aggregate given by uid in a form of StudyDefinitionSnapshot object

        * if called with for_update == True the method should also either acquire relevant write locks (in case
            a repository implementation assumes pessimistic locking strategy) or provide information necessary to
            implement optimistic concurrency checks when this particular instance of aggregate is saved with _save
            method (a method can also do some combination of those or skip this for some part of aggregate state in case
            it's sure they are never updated).

        It's useful if the method makes as few as possible assumptions on aggregate behavior (i.e. what changes
        of aggregate state are possible/impossible) since it minimizes repository breakages in case of changes in
        business logic. However usually completely agnostic implementation will be very inefficient (or even
        impossible) hence it's expected there may be some assumptions.

        :param uid: uid of study representation to retrieve from db
        :param for_update: informs a method that the instance is retrieved to perform some update transaction
        :return: A two position tuple. First being state of the Study retrieved form db (or None if not exists), the
            second a reference to any additional object (or None) which will be passed on to the _save method at the
            time of saving the new state of aggregate back into repository as additional_closure parameter (this may
            contain whatever information are helpful for proper saving, e.g. above mentioned information needed for
            optimistic concurrency checks). NOTE: expected result in case a study with given uid does not exists in the
            underlying DB is (None, None) tuple.
        """
        raise NotImplementedError

    @abstractmethod
    def _save(self, snapshot: StudyDefinitionSnapshot, additional_closure: Any) -> None:
        """
        Abstract method of the study repository, which is supposed to update and instance of the study aggregate, which
        was earlier retrieved with _get_by_uid (with for_update == True). The method is expected to save a new state
        of aggregate into database, assuring proper concurrency control (especially in case when concrete repository
        implementation assumes optimistic concurrency control) and assuring retaining all required audit information in
        the underlying DB (a method should read data from self.audit_info property to get relevant information).
        In case of concurrency control failure a method is expected to throw an Error.

        :param snapshot: A StudyDefinitionSnapshot representing a new state of the study. WARNING!: when this method
        is called it's not known for sure whether the state of the aggregate actually has changed. If it's important
        for the concrete repository implementation to know that then it must provide some mean of detecting this by
        attaching relevant additional_closure while performing _get_by_uid(..., for_update=True) and use this
        information here to detect if/what parts of the aggregate state has changed.

        :param additional_closure: A reference to object which was returned on index 2 of the tuple returned by
            _get_by_id when the instance of the aggregate was retrieved from the DB.
        """
        raise NotImplementedError

    @abstractmethod
    def _create(self, snapshot: StudyDefinitionSnapshot) -> None:
        """
        Abstract method of the study repository, which is supposed to persist a new instance of Study aggregate (the
        brand new study, not retrieved from repo) including retaining a proper audit information (a method should read
        data from self.audit_info property to get relevant information).

        :param snapshot: A state of the new study to persist.
        """
        raise NotImplementedError

    @abstractmethod
    def _retrieve_all_snapshots(
        self,
        has_study_objective: Optional[bool] = None,
        has_study_endpoint: Optional[bool] = None,
        has_study_criteria: Optional[bool] = None,
        has_study_activity: Optional[bool] = None,
        has_study_activity_instruction: Optional[bool] = None,
        sort_by: Optional[dict] = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: Optional[dict] = None,
        filter_operator: Optional[FilterOperator] = FilterOperator.AND,
        total_count: bool = False,
        study_selection_object_node_id: Optional[int] = None,
        study_selection_object_node_type: Optional[NodeMeta] = None,
    ) -> GenericFilteringReturn[StudyDefinitionSnapshot]:
        """
        Abstract method which is expected to retrieve (a part of) whole Study
        repository content in the form of
        sequence of StudySnapshots. This method allows for filtering, sorting and
        pagination scenarios.

        sort_by: dictionary of Cypher aliases on which to apply sorting as keys, and
        boolean to define sort direction (true=ascending) as values

        page_number : int, number of the page to return. 1-based

        page_size : int, number of results per page

        filter_by : dict, keys are fieldNames for filter_variable and values are
        objects describing the filtering to execute

        total_count : boolean, indicates if total count of results should be returned

        :return: Dictionary of 'items' and 'total_count'. 'items' contains the
        results in the form of StudyDefinitionSnapshot instances. Not more than
        page_size items. Can
            be less than than that in case of the last page. Empty sequence in case
            page_number and page_size parameters
            pass out of the whole repository content.
        """
        raise NotImplementedError

    @abstractmethod
    def _retrieve_fields_audit_trail(
        self, uid: str
    ) -> Optional[Sequence[StudyFieldAuditTrailEntryAR]]:
        """
        Private method to retrieve an audit trail for a study by UID.
        :return: A sequence of Study field audit trail objects.
        """

    def get_audit_trail_by_uid(
        self, uid: str
    ) -> Optional[Sequence[StudyFieldAuditTrailEntryAR]]:
        """
        Public method which is to retrieve the audit trail for a given study identified by UID.
        :return: A sequence of retrieved data in a form StudyAuditTrailAR instances.
        """
        return self._retrieve_fields_audit_trail(uid)

    @abstractmethod
    def generate_uid(self) -> str:
        """
        A method is supposed to generate a new unique id
        for the StudyDefinition which is about to be created. It's meant to be used as a callback for some
        StudyDefinitionAR factories.
        :return: a string, an uid for the object about to be created
        """
