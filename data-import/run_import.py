from importers.metrics import Metrics

from run_import_dictionaries import Dictionaries
from run_import_config import Configuration
from run_import_standardcodelistterms1 import StandardCodelistTerms1
from run_import_standardcodelistterms2 import StandardCodelistTerms2
from run_import_activities import Activities
from run_import_unitdefinitions import Units
from run_import_standardcodelistfinish import StandardCodelistFinish
from run_import_compounds import Compounds
from run_import_crfs import Crfs
from run_import_mockdata import Mockdata
from run_import_mockdatajson import MockdataJson


def main():
    metr = Metrics()

    # Migrate the libraries (SNOMED etc)
    dictmigrator = Dictionaries(metrics_inst=metr)
    dictmigrator.run()

    # General configuration
    config = Configuration(metrics_inst=metr)
    config.run()

    # Import standard codelist terms, part 1
    standardterms1 = StandardCodelistTerms1(metrics_inst=metr)
    standardterms1.run()
    # cache will be populated now, lets get it
    cache = standardterms1.get_cache()

    # Import standard codelist terms, part 2
    standardterms2 = StandardCodelistTerms2(metrics_inst=metr, cache=cache)
    standardterms2.run()

    # Import unit definitions
    units = Units(metrics_inst=metr, cache=cache)
    units.run()

    activities = Activities(metrics_inst=metr, cache=cache)
    activities.run()

    # Finish up sponsor library
    finishing = StandardCodelistFinish(metrics_inst=metr, cache=cache)
    finishing.run()

    # Import compounds
    compounds = Compounds(metrics_inst=metr, cache=cache)
    compounds.run()

    # Import crfs
    crfs = Crfs(metrics_inst=metr, cache=cache)
    crfs.run()

    # Import mock data
    mockdata = Mockdata(metrics_inst=metr, cache=cache)
    mockdata.run()

    # Import mock data from json
    mockdatajson = MockdataJson(metrics_inst=metr, cache=cache)
    mockdatajson.run()

    # Display metrics
    metr.print_sorted_by_key()
    metr.print_sorted_by_value()


if __name__ == "__main__":
    main()
