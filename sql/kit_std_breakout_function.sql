-- Function: kit_std_breakout(character varying)

-- DROP FUNCTION kit_std_breakout(character varying);

CREATE OR REPLACE FUNCTION kit_std_breakout(IN kit_product_id CHARACTER VARYING)
  RETURNS TABLE(
    kit_number             CHARACTER VARYING,
    kit_edi                CHARACTER VARYING,
    kit_id                 BIGINT,
    product_number         CHARACTER VARYING,
    edi                    CHARACTER VARYING,
    description            CHARACTER VARYING,
    component_qty_standard BIGINT
  ) AS
$BODY$
BEGIN
  /* Kit Standard Breakout

    Returns kit standard fir given kit.
    Shows what components are associated with
    a given kit.

    Query written by: Patrick K. Schenkel
    Function written by: Ian Doarn
    Maintainers: Patrick K. Schenkel,
           Ian Doarn
  */

  RETURN QUERY

  WITH unique_kits AS (
      SELECT DISTINCT s.product_id
      FROM
        sms.stock s
        LEFT JOIN sms.product p ON s.product_id = p.id
      WHERE
        s.inventory_type = 3
        AND s.stock_type IN (3, 4)
  )

  SELECT
    p.product_number AS kit_number,
    p.edi_number     AS kit_edi,
    p.id             AS kit_id,
    p2.product_number,
    p2.edi_number    AS edi,
    p2.description,
    pc.quantity      AS component_qty_standard
  FROM
    unique_kits u
    LEFT JOIN sms.product p ON u.product_id = p.id
    LEFT JOIN sms.product_component pc ON u.product_id = pc.product_id
    LEFT JOIN sms.product p2 ON pc.component_product_id = p2.id
  WHERE
    p.product_number = KIT_PRODUCT_ID
  ORDER BY
    p.product_number,
    p2.product_number;

END
$BODY$
LANGUAGE plpgsql;