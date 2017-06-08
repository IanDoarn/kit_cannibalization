import pgsql
import json
from prettytable import PrettyTable
import sys

KIT = sys.argv[1]
SERIALS = sys.argv[2].replace(' ','').split(',')

kit_std, kit_report = pgsql.create_cannibalization_data(KIT, write_json=True)

with open('kit_report_{}.json'.format(KIT), 'r')as f: data = json.load(f)
with open('kit_std_{}.json'.format(KIT), 'r')as f: std_data = json.load(f)

kit_data = data['report']

def generate_diff(serial, print_diff=True):
    pieces_missing = 0
    components_missing = []
    serial_data = []
    for row in kit_data:
        if row['serial_number'] == serial:
            serial_data.append(row)
            pieces_missing = int(row['pieces_missing']) if pieces_missing is 0 else pieces_missing

    for row in serial_data:
        qty_in_kit = int(row["qty_in_kit"])
        component = {"component_product_number": row["component_product_number"],
                     "component_prod_id": row["component_prod_id"],
                     "component_description": row["component_description"]}
        if qty_in_kit == 0:
            components_missing.append(component)

    data = {'kit': KIT, 'serial': serial, 'pieces_missing': pieces_missing,
            'diff': components_missing}

    return data

for SERIAL in SERIALS:
    data = generate_diff(SERIAL)
    header_table = PrettyTable(['kit', 'serial', 'pieces missing'])
    table = PrettyTable([k for k, v in data['diff'][0].items()])
    for row in data['diff']:
        table.add_row([v for k, v in row.items()])

    header_table.add_row([data['kit'], data['serial'], str(data['pieces_missing'])])

    print(header_table)
    print(table)