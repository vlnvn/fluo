# Data lineage and engineering assumptions

The initial study case is steam-based indirect heating in textile yarn sizing. All training and test time series are programmatically generated; none are factory measurements.

## Sources and roles

1. Forbes Marshall, [Textile plant in western Indonesia](https://www.forbesmarshall.com/country-highlights-indonesia/optimising-energy-and-efficiency-at-a-textile-plant-in-western-indonesia/): historical account of condensate discarded from sizing, leaking steam traps and boiler blowdown. Reported vendor savings are not calibration targets, evidence of current plant problems, or Fluo results.
2. Spirax Sarco, [What is steam?](https://www.spiraxsarco.com/learn-about-steam/steam-engineering-principles-and-heat-transfer/what-is-steam): saturated steam properties in the generator's small lookup table.
3. Spirax Sarco, [Flash steam](https://www.spiraxsarco.com/learn-about-steam/condensate-recovery/flash-steam): flash fraction and enthalpy balance. The simulator assumes an atmospheric receiver venting flash steam.
4. U.S. DOE/NREL, [Improving Steam System Performance](https://www.osti.gov/biblio/15000711): distribution, recovery and mass/energy accounting principles.
5. UNIDO, [Energy Conservation in Textile Mills](https://downloads.unido.org/ot/47/89/4789812/10001-15000_10251.pdf): historical ATIRA steam consumption ratios per kilogram of **liquid evaporated** in two- and multi-cylinder sizing. Not a recorded Indonesian site.

## Explicitly synthetic parameters

Rated steam flow at the invented sites, operating schedule, thermal-hydraulic delay, meter noise, event probabilities, failure severity and incident duration are test assumptions. Sites CFG_A–CFG_E are artificial configurations, **not real factories or verified boiler models**. The one-episode-per-simulated-day rate is a stress-testing choice and is not an industrial failure frequency. Site instrumentation, condensate contamination status and recovery permission are unknown.

`fluo_parameter_provenance.csv` inside the v1 dataset package holds a field-level source/assumption register. Treat all generator-based labels as simulator oracle data, never field ground truth.
