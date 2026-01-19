# NATAL CHART REPORT

**Generated**: {{ generated_date }}

## Birth Data

- **Date**: {{ birth_date }}
- **Time**: {{ birth_time }}
- **Location**: {{ location_name }}
- **Coordinates**: {{ latitude }}, {{ longitude }}
- **Timezone**: {{ timezone }}

## Time Conversion

| Time Scale | Value |
|------------|-------|
| Local Time | {{ local_time }} |
| UTC | {{ utc_time }} |
| Julian Day (UT) | {{ jd_ut }} |
| Julian Day (TT) | {{ jd_tt }} |
| Delta-T | {{ delta_t }} seconds |

## Planetary Positions

| Planet | Position | Sign | Degree | Speed | House |
|--------|----------|------|--------|-------|-------|
{% for planet in planets %}
| {{ planet.symbol }} {{ planet.name }} | {{ planet.longitude_zodiacal }} | {{ planet.sign }} | {{ planet.degree }}° | {{ planet.speed }} | {{ planet.house }} |
{% endfor %}

## House Cusps ({{ house_system }})

| House | Cusp | Sign |
|-------|------|------|
{% for house in houses %}
| {{ house.number }} | {{ house.cusp }}° | {{ house.sign }} |
{% endfor %}

## Key Angles

- **Ascendant**: {{ ascendant }}
- **Midheaven (MC)**: {{ midheaven }}
- **Vertex**: {{ vertex }}

## Aspects

{% for aspect in aspects %}
- {{ aspect.planet1 }} {{ aspect.symbol }} {{ aspect.planet2 }} ({{ aspect.name }}, orb: {{ aspect.orb }}°)
{% endfor %}

---

*Calculated using {{ calculation_method }}*
*Precision estimate: {{ precision }}*
