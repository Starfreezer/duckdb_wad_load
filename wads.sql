WITH wall AS (
    SELECT
        round(
            (v1.x + (v2.x - v1.x) * t.i / 32.0) / 48
        ) AS col,

        round(
            (v1.y + (v2.y - v1.y) * t.i / 32.0) / 96
        ) AS row,

        l.left_sidedef < 0 AS solid

    FROM linedefs l

    JOIN vertices v1
      ON v1.map_id = l.map_id
     AND v1.id = l.v1_id

    JOIN vertices v2
      ON v2.map_id = l.map_id
     AND v2.id = l.v2_id

    CROSS JOIN generate_series(0, 32) AS t(i)

    WHERE l.map_id = 0
)

SELECT
    string_agg(
        CASE
            WHEN EXISTS (
                SELECT 1
                FROM wall w
                WHERE w.col = c.col
                  AND w.row = r.row
                  AND w.solid
            )
            THEN '#'

            WHEN EXISTS (
                SELECT 1
                FROM wall w
                WHERE w.col = c.col
                  AND w.row = r.row
            )
            THEN '.'

            ELSE ' '
        END,
        ''
        ORDER BY c.col
    )

FROM generate_series(-16, 79) AS c(col)
CROSS JOIN generate_series(-51, -21) AS r(row)

GROUP BY r.row
ORDER BY r.row DESC;

