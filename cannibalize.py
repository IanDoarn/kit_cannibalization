import pgsql
from prettytable import PrettyTable

KIT = '57-5962-032-00'
SERIAL = '83'


kit_std, kit_report = pgsql.create_cannibalization_data(KIT, write_json=True, report=False)

table = PrettyTable(kit_std['headers'])
for row in kit_std['std']:
    table.add_row([v for k,v in row.items()])

print(table)