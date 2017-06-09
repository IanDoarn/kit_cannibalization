-- Function: kit_breakout(character varying)

-- DROP FUNCTION kit_breakout(character varying);

CREATE OR REPLACE FUNCTION kit_breakout(IN kit_id CHARACTER VARYING)
  RETURNS TABLE(
    kit_product_number        CHARACTER VARYING,
    kit_edi                   CHARACTER VARYING,
    kit_description           CHARACTER VARYING,
    serial_number             BIGINT,
    kit_bin                   TEXT,
    component_product_number  CHARACTER VARYING,
    component_prod_id         CHARACTER VARYING,
    component_description     CHARACTER VARYING,
    component_quantity_in_kit BIGINT,
    qty_in_kit                NUMERIC,
    qty_avail_sh              NUMERIC,
    component_bin             TEXT,
    qty_avail_e01             BIGINT,
    percent_invalid           NUMERIC,
    pieces_missing            NUMERIC
  ) AS
$BODY$
BEGIN

  /* Kit Breakout

	Acts similarly to ''Explode'' on SMS
	Returns contents of given KIT_ID showing
	its component count, missing pieces,
	component availability in SH and EO1 for
	every serial associated with that kit.
	This works successfully for legacy Biomet
	and legacy Zimmer kits

	Query written by: Patrick K. Schenkel
	Function written by: Ian Doarn
	Maintainers: Patrick K. Schenkel,
			   Ian Doarn
  */

  RETURN QUERY

  WITH s0 AS (
      SELECT DISTINCT
        s.product_id,
        pc.component_product_id,
        pc.quantity
      FROM
        sms.stock s
        LEFT JOIN sms.product_component pc ON s.product_id = pc.product_id
      WHERE
        stock_type IN (3, 4)
        AND inventory_type = 3),

      s1 AS (  --7292 lines no issues
        SELECT
          p.product_number  AS kit_product_number,
          p.edi_number      AS kit_edi,
          p.description     AS kit_description,
          p2.product_number AS component_product_number,
          p2.edi_number     AS component_prod_id,
          p2.description    AS component_description,
          s0.quantity       AS component_quantity_in_kit
        FROM
          s0
          LEFT JOIN sms.product p ON s0.product_id = p.id
          LEFT JOIN sms.product p2 ON s0.component_product_id = p2.id
        WHERE
          p.product_number NOT LIKE ''ZPB % ''
    ),

      s2 AS (
        SELECT
          p.product_number,
          p.edi_number,
          b.zone || '' - '' || b.position || '' - '' || b.shelf AS component_bin,
          sum(s.quantity_available)                             AS Qty_avail_SH
        FROM
          sms.stock s
          LEFT JOIN sms.product p ON p.id = s.product_id
          LEFT JOIN sms.bin b ON b.id = s.container_id AND s.container_type = 1
        WHERE
          s.stock_type = 1
          AND s.inventory_type = 3
          AND s.location_type = 1
          AND s.location_id = 370
          AND s.container_type = 1
          AND s.quantity_available > 0
          AND b.zone LIKE ''R%''
                             GROUP BY
                             p.product_number,
                             p.edi_number,
                               b.zone || ''-'' || b.position || ''-'' || b.shelf),

      s3 AS (
        SELECT
          p.product_number,
          p.edi_number,
          p.description,
          CASE WHEN stock_type = 3
            THEN sum(s.quantity_on_hand) END AS Valid,
          CASE WHEN stock_type = 4
            THEN sum(s.quantity_on_hand) END AS Invalid
        FROM
          sms.stock s
          LEFT JOIN sms.product p ON s.product_id = p.id
          LEFT JOIN sms.bin b ON b.id = s.container_id AND s.container_type = 1
        WHERE
          s.inventory_type = 3
          AND stock_type IN (3, 4)
          AND s.location_id = 370
          AND s.location_type = 1
          AND b.zone LIKE ''G%''
                             --and product_id = 688800
                             GROUP BY
                             p.product_number, p.edi_number, p.description,
        S.stock_type),

      s4 AS (
        SELECT
          s3.product_number                                            AS kit_prod_number,
          s3.edi_number                                                AS kit_edi,
          s3.description                                               AS kit_description,
          coalesce(sum(s3.valid), 0)                                   AS valid,
          coalesce(sum(s3.invalid), 0)                                 AS invalid,
          CASE
          WHEN sum(s3.valid) IS NULL
            THEN 1.0
          WHEN sum(s3.invalid) IS NULL
            THEN 0.0
          ELSE sum(s3.invalid) / (sum(s3.valid) + sum(s3.invalid)) END AS Percent_invalid
        FROM
          s3
        GROUP BY
          product_number, edi_number, description),

      s5 AS (
        SELECT
          p2.product_number                                     AS kit_prod_number,
          p2.edi_number                                         AS kit_edi,
          p2.description                                        AS kit_description,
          ps.serial_number,
          b.zone || '' - '' || b.position || '' - '' || b.shelf AS kit_bin,
          p.product_number                                      AS Component_product_number,
          p.edi_number                                          AS component_edi,
          p.description                                         AS component_description,
          sum(s.quantity_available)                             AS quantity_available
        FROM
          sms.stock s
          LEFT JOIN sms.product p ON s.product_id = p.id
          LEFT JOIN sms.stock s2 ON s.container_id = s2.id AND s.container_type = 2
          LEFT JOIN sms.product p2 ON s2.product_id = p2.id
          LEFT JOIN sms.product_serial ps ON s2.serial_id = ps.id
          LEFT JOIN sms.bin b ON s2.container_id = b.id AND s2.container_type = 1
        WHERE
          s.location_type = 1
          AND s.location_id = 370
          AND s.stock_type = 2
          AND s.container_type = 2
          AND p2.product_number IS NOT NULL
        GROUP BY
          p2.product_number,
          p2.edi_number,
          p2.description,
          ps.serial_number,
          b.zone || '' - '' || b.position || '' - '' || b.shelf,
          p.product_number,
          p.edi_number,
          p.description),

      s6 AS (
        SELECT
          prod_id,
          sum(invntry_on_hand_qty - invntry_on_reserve_qty - invntry_unavailable_qty) AS qty_avail_e01
        FROM
          dcs.invntry_snpsht_dcs_daily
        WHERE
          snapshot_dte = current_date
          AND warehouse_id = ''E01''
        GROUP BY
        prod_id),

      s7 AS (  --may pull this out, probably not needed
        SELECT DISTINCT
          p.product_number AS kit_product_number,
          p.edi_number     AS Kit_edi,
          ps.serial_number
        FROM
          sms.stock s
          LEFT JOIN sms.product p ON s.product_id = p.id
          LEFT JOIN sms.product_serial ps ON ps.id = s.serial_id
          LEFT JOIN sms.bin b ON b.id = s.container_id AND s.container_type = 1
        WHERE
          s.inventory_type = 3
          AND s.stock_type IN (3, 4)
          AND s.location_type = 1
          AND s.location_id = 370
          AND b.zone LIKE ''G % ''),

      s8 AS (
        SELECT DISTINCT
          p2.product_number                                     AS kit_prod_number,
          p2.edi_number                                         AS kit_edi,
          p2.description                                        AS kit_description,
          b.zone || '' - '' || b.position || '' - '' || b.shelf AS kit_bin
        FROM
          sms.stock s2
          LEFT JOIN sms.product p2 ON s2.product_id = p2.id
          LEFT JOIN sms.bin b ON s2.container_id = b.id AND s2.container_type = 1
        WHERE
          s2.location_type = 1
          AND s2.location_id = 370
          AND s2.stock_type IN (3, 4)
          AND p2.product_number IS NOT NULL
          AND b.zone LIKE ''G % ''),


      s9 AS (
        SELECT
          s1.kit_product_number,
          s1.kit_edi,
          s1.kit_description,
          s7.serial_number,
          s1.component_product_number,
          s1.component_prod_id,
          s1.component_description,
          s1.component_quantity_in_kit
        FROM
          s1
          LEFT JOIN s7 ON s1.kit_product_number = s7.kit_product_number)

  SELECT
    s9.kit_product_number,
    s9.kit_edi,
    s9.kit_description,
    s9.serial_number,
    s8.kit_bin,
    s9.component_product_number,
    s9.component_prod_id,
    s9.component_description,
    s9.component_quantity_in_kit                             AS component_quantity_in_kit_std,
    coalesce(s5.quantity_available, 0)                       AS qty_in_kit,
    s2.qty_avail_sh,
    s2.component_bin,
    s6.qty_avail_e01,
    s4.percent_invalid,
    sum(s9.component_quantity_in_kit - coalesce(s5.quantity_available, 0))
    OVER (
      PARTITION BY s9.kit_product_number, s9.serial_number ) AS Pieces_missing
  FROM
    s9
    LEFT JOIN s5 ON s9.kit_product_number = s5.kit_prod_number AND s9.serial_number = s5.serial_number AND
                    s9.component_prod_id = s5.component_edi
    LEFT JOIN s4 ON s9.kit_product_number = s4.kit_prod_number AND s9.kit_edi = s4.kit_edi
    LEFT JOIN s2 ON s9.component_product_number = s2.product_number AND s9.component_prod_id = s2.edi_number
    LEFT JOIN s6 ON s9.component_prod_id = s6.prod_id
    LEFT JOIN s8 ON s9.kit_product_number = s8.kit_prod_number
  WHERE
    s8.kit_bin IS NOT NULL
    AND s9.kit_product_number = KIT_ID --From input of function
  ORDER BY
    s4.percent_invalid DESC,
    s9.kit_product_number,
    s9.serial_number,
    s9.component_product_number;
END
$BODY$
LANGUAGE plpgsql;
