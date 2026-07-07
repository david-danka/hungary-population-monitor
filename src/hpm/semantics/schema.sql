-- Create semantic views used by the analysis layer
DROP VIEW IF EXISTS population_settlements;
CREATE VIEW IF NOT EXISTS population_settlements AS
SELECT
    fp.year,
    s.settlement_name,
    fp.settlement_type,
    c.county_name,
    s.latitude,
    s.longitude,
    fp.male_population,
    fp.female_population,
    fp.population
FROM fact_population fp
JOIN dim_settlement s 
    ON fp.settlement_code = s.settlement_code
LEFT JOIN dim_county c
    ON fp.county_code = c.county_code
WHERE fp.settlement_type NOT IN (
    'capital_district',
    'no_address'
)

UNION ALL

-- Budapest is synthesized by aggregating all capital districts into a
-- single settlement-level entity. Because this entity does not belong to
-- any county, county_name is intentionally NULL.
SELECT
    fp.year,
    'Budapest' AS settlement_name,
    'capital' AS settlement_type,
    NULL AS county_name,
    s.latitude,
    s.longitude,
    SUM(fp.male_population),
    SUM(fp.female_population),
    SUM(fp.population)
FROM fact_population fp
JOIN dim_settlement s
    ON s.settlement_code = 1357  -- BUDAPEST_SETTLEMENT_CODE, see star_schema.py
WHERE fp.settlement_type = 'capital_district'
GROUP BY
    fp.year,
    s.settlement_code,
    s.latitude,
    s.longitude;