package org.openstudybuilder.engine;

import org.CDISC.DDF.model.Study;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.openstudybuilder.model.*;

import java.util.List;

class StudyObjectMapperTest {

    private final OpenStudyObjectFactory objectFactory = OpenStudyObjectFactory.withStaticBuilderAdaptor();
    private final String STUDY_UID = "Study_000002";
    @Test
    void testEncounterMap() throws Exception {
        StudyObjectMapper studyObjectMapper = new StudyObjectMapper();
        List<Visit> visits = objectFactory.getVisits(STUDY_UID);
        org.CDISC.DDF.model.Encounter encounter = studyObjectMapper.map(visits.get(0));
        Assertions.assertNotNull(encounter);
        Assertions.assertEquals("Visit 1", encounter.getEncounterName());
    }

    @Test
    void testPopulationMap() throws Exception {
        // TODO create an ad-hoc model class for Populations from listings API request
        StudyObjectMapper studyObjectMapper = new StudyObjectMapper();
        Population population = objectFactory.getPopulation("0");
        org.CDISC.DDF.model.StudyDesignPopulation CDISCPopulation = studyObjectMapper.map(population);
        Assertions.assertNotNull(CDISCPopulation);
        Assertions.assertTrue(CDISCPopulation.getPopulationDescription().contains("Type 2 diabetes mellitus"));
    }

    @Test
    // Disabling due to structural differences between file and rest api
    void testObjectiveMap() throws Exception {
        StudyObjectMapper studyObjectMapper = new StudyObjectMapper();
        List<StudySelectionEndpoint> studySelectionEndpoints = objectFactory.getStudyEndpointSections(STUDY_UID);

        for (StudySelectionEndpoint studySelectionEndpoint : studySelectionEndpoints) {
            org.CDISC.DDF.model.Objective CDISCObjective = studyObjectMapper.map(studySelectionEndpoint);
            if (studySelectionEndpoint.getStudyObjective() != null) {
                Assertions.assertNotNull(CDISCObjective);
            }
        }
    }

    @Test
    void testStudyElement() throws Exception {
        StudyObjectMapper studyObjectMapper = new StudyObjectMapper();
        List<Element> elements = objectFactory.getElements(STUDY_UID);

        for (Element element : elements) {

            org.CDISC.DDF.model.StudyElement studyElement = studyObjectMapper.map(element);
            Assertions.assertNotNull(studyElement);
        }


    }

    @Test
    void testEpoch() throws Exception {
        StudyObjectMapper studyObjectMapper = new StudyObjectMapper();
        List<Epoch> epochs = objectFactory.getEpochs(STUDY_UID);

        for (Epoch epoch : epochs) {

            org.CDISC.DDF.model.StudyEpoch studyEpoch = studyObjectMapper.map(epoch);
            Assertions.assertNotNull(studyEpoch);
        }


    }

    @Test
    void testArm() throws Exception {
        StudyObjectMapper studyObjectMapper = new StudyObjectMapper();
        List<Arm> arms = objectFactory.getArms("001");

        for (Arm arm : arms) {

            org.CDISC.DDF.model.StudyArm studyArm = studyObjectMapper.map(arm);
            Assertions.assertNotNull(studyArm);
        }

    }

    @Test
    void testStudyMapping() throws Exception {
        OpenStudy openStudy = objectFactory.getStudy(STUDY_UID);
        StudyObjectMapper studyObjectMapper = new StudyObjectMapper();
        Study study = studyObjectMapper.map(openStudy, objectFactory);
        Assertions.assertNotNull(openStudy);
        Assertions.assertNotNull(study);
    }
}