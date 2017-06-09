from ryport.pgsql.postgres import Postgres
from collections import OrderedDict
import json

class KitData:

    def __init__(self):
        self.pg = Postgres(username='reader', password='ZimmerBiomet',
                           host='vsbslgprd01.zmr.zimmer.com', database='postgres')

    def create_kit_component_standard(self, kit_id):
        self.pg.establish_connection()
        kit_compnt_std, headers = self.pg.execute("SELECT * FROM "
                                                  "doarni.kit_std_breakout('{}')".format(kit_id))
        self.pg.close_connection()
        return kit_compnt_std, headers

    def create_kit_southaven_report(self, kit_id):
        self.pg.establish_connection()
        kit_report, headers = self.pg.execute("SELECT * FROM "
                                              "doarni.kit_breakout('{}')".format(kit_id))
        self.pg.close_connection()
        return kit_report, headers

def create_cannibalization_data(KIT, std=True, report=True,
                                write_json=False):
    kd = KitData()

    kit_std, kit_report = [], []
    __std, __report = None, None

    if std:
        _std, _std_headers = kd.create_kit_component_standard(KIT)
        for row in _std:
            for cell in range(len(row)):
                row[cell] = str(row[cell])
            headers = [value['name'] for value in _std_headers['data']]
            row_dict = OrderedDict(zip(headers, row))
            kit_std.append(row_dict)
        __std = {'kit_id': KIT, 'std': kit_std, 'headers': [value['name'] for value in _std_headers['data']]}

    if report:
        _report, _report_headers = kd.create_kit_southaven_report(KIT)
        for row in _report:
            for cell in range(len(row)):
                row[cell] = str(row[cell])
            headers = [value['name'] for value in _report_headers['data']]
            row_dict = OrderedDict(zip(headers, row))
            kit_report.append(row_dict)
        __report = {'kit_id': KIT, 'report': kit_report, 'headers': [value['name'] for value in _report_headers['data']]}

    if write_json:
        if std:
            with open('kit_std_{}.json'.format(KIT), 'w')as f:
                json.dump(__std, f, indent=4, ensure_ascii=True)
        if report:
            with open('kit_report_{}.json'.format(KIT), 'w')as f:
                json.dump(__report, f, indent=4, ensure_ascii=True)

    return __std, __report