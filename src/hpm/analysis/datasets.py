from hpm.db import query


def population_settlements():
    return query("SELECT * FROM population_settlements")


def county_population():
    return query("""
        SELECT county_name, SUM(population) AS population
        FROM population_settlements
        GROUP BY county_name
    """)