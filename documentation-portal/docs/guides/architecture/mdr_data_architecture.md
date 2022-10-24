# Clinical MDR Database Architecture

This document holds the design documentation for the StudyBuilder database architecture - named as the Clinical MDR database component.

The database is implemented as a linked graph database in Neo4j, and the solution design utilise a number of capabilities uniquely supported by the label property graph model.

# Modelling guidelines
## General guidelines
### Nodes
Entities are the **nouns** in the business questions :
* What **ingredients** are used in a **recipe** ?
* What **term** is used by an **objective template** ?

These entities will be represented by nodes, and :

* The generic nouns often become labels in the model
* Use domain knowledge deciding how to further group or differentiate entities

### Node properties
Property lookups have a cost, and parsing complex properties adds even more cost.
Therefore, properties used as filters / anchors for traversal (starting points in a path) should be as simple as possible : strings, numbers, boolean, dates.

Also, properties used as filters in common queries should have an **index** on them to increase performance.

Finally, if a property is unique throughout the graph for a given label (e.g. the unique identifier of a study), then a **uniqueness constraint** should be created on that property. Note that this automatically creates an index on that property.

_Note_ : In the Neo4j database, existence constraints also exist, preventing a node being created without a given property, but these are not enforced in this project.

### Node label vs property
Sometimes, the questions arises of : should this value be a **property** or a **node label** ? For example, a _Concept_ node in the MDR domain model can have a second type, like "Activity" or "CompoundDosing". This could be both a property "type=Activity", or an additional label on the node ":Concept:Activity".

The general guidance is :
* If all the nodes with the main label (Concept) have a value for this _property_
* And if the set of possible values is identified
* And if the set of possible values is small and the cardinality is high
  
=> You can use a label.

Otherwise, use a property.

### Relationships
Relationships are the **verbs** in the business questions :
* What ingredients are **used** in a recipe ?
* What term is **used** by an objective template ?

It is recommended to use _verbs_ and not nouns for the relationship types ; and to avoid _symmetric_ relationships (e.g. USES and USED_BY). Except if the relationship is inherently non-symmetric (e.g. Mikkel FOLLOWS Anja is not the same as Anja FOLLOWS Mikkel).
The _direction_ of the relationships is based on the expected business questions.

Follow the same rules for relationship properties as for node properties. _Note_ : This project does not have many properties on relationships because in past versions of Neo4j, relationship properties could not be indexed ; but this is now possible since version 4.3.

### Intermediate nodes
Sometimes, a relationship - and its properties - between two nodes is not enough to store all the information and the context needed.

For example, in the MDR domain model, a Study has Endpoints, which can be shared between multiple Studies. But in the context of a given Study, an Endpoint has a Unit, which can be different in the other Studies that also have this Endpoint.
So here, connecting the Endpoint to the Unit is not enough, because it would be connected to multiple Unit nodes, and how can we know for which Study each of these relationships are for ?

This is where we introduce intermediate nodes : in our case, the complete path is like this : (:Study)-->(:StudyEndpoint)-->(:Endpoint) ; and the (:StudyEndpoint) node has a relationship to its (:Unit).

## Versioning
### Node versioning
On a basic level, versioned nodes are split into two types of nodes :
* A root node (e.g. StudyRoot) ; this node contains all the immutable properties (e.g. its uid)
* A value node (e.g. StudyValue) ; this node contains all the mutable properties (e.g. its name)

Between each pair of nodes (the Root and one of its Value nodes), there is a HAS_VERSION relationship, containing the versioning information :
- start_date
- end_date (not present when open)
- version (metadata version)
- status (Draft, Final, Retired)
- change_description
- user_initials

Additional relationships also exist as "shortcuts" for
- LATEST_FINAL (most recent version with status Final)
- LATEST_DRAFT (most recent version when in Draft status)
- LATEST_RETIRED (most recent when in Retired status)
- LATEST (most recent independent of status)

