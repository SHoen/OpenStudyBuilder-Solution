package org.openstudybuilder.model;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.annotation.JsonNaming;
import lombok.Getter;
import lombok.Setter;

@JsonNaming(PropertyNamingStrategies.SnakeCaseStrategy.class)
@Getter @Setter
public abstract class StudyMetadata {

    private IdentificationMetadata identificationMetadata;
    private VersionMetadata versionMetadata;
}