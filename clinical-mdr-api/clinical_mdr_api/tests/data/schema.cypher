CREATE INDEX FOR (n:ObjectiveTemplateValue) ON (n.name);
CREATE INDEX FOR (n:ObjectiveValue) ON (n.name);
CREATE INDEX FOR (n:TemplateParameterValue) ON (n.name);

CREATE CONSTRAINT ON (n:Library) ASSERT n.name IS UNIQUE;
CREATE CONSTRAINT ON (n:ObjectiveTemplateRoot) ASSERT n.uid IS UNIQUE;
CREATE CONSTRAINT ON (n:ObjectiveRoot) ASSERT n.uid IS UNIQUE;
CREATE CONSTRAINT ON (n:TemplateParameter) ASSERT n.name IS UNIQUE;
CREATE CONSTRAINT ON (n:TemplateParameterValueRoot) ASSERT n.uid IS UNIQUE;
