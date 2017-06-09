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
  p.product_number = '57-5962-032-00'
ORDER BY
  p.product_number,
  p2.product_number