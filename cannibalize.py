import pgsql
import json
from prettytable import PrettyTable
import sys

# KIT = sys.argv[1]
# SERIALS = sys.argv[2].replace(' ','').split(',')

KIT = '57-5962-032-00'
SERIALS = ['73', '76', '77', '79', '81',
           '82', '83', '84', '85', '86',
           '87']

class Cannibalizer:

    def __init__(self, kit_id, serial_numbers, write_json=True, kit_std=True, kit_report=True):
        self.kit_number = kit_id
        self.serial_numbers = serial_numbers
        self.kit_std, self.kit_report = pgsql.create_cannibalization_data(kit_id,
                                                                          write_json=write_json,
                                                                          std=kit_std,
                                                                          report=kit_report)
        self.kit_data = self.kit_report['report']
        self._kit_std = self.generate_kit_std()
        self.total_component_count = {}


    def generate_diff(self, serial):
        pieces_missing = 0
        components_missing = []
        serial_data = []
        for row in self.kit_data:
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

        data = {'pieces_missing': pieces_missing, 'components_missing': components_missing}

        return data


    def generate_kit_breakout(self):
        breakout = {'kit_number': self.kit_number,
                    'serials': {k: {'breakout': [], 'diff': []} for k in self.serial_numbers}}
        for row in self.kit_data:
            for serial in self.serial_numbers:
                if row['serial_number'] == serial:
                    data = {"component_product_number": row["component_product_number"],
                            "component_prod_id": row["component_prod_id"],
                            "component_description": row["component_description"],
                            "qty_in_kit": row["qty_in_kit"],
                            "qty_avail_sh": row["qty_avail_sh"],
                            "qty_avail_e01": row["qty_avail_e01"]}

                    breakout['serials'][serial]['breakout'].append(data)
        for serial in self.serial_numbers:
            breakout['serials'][serial]['diff'].append(self.generate_diff(serial))


        return breakout

    def generate_kit_std(self):
        kit_std_data = {}
        for row in self.kit_std["std"]:
            kit_std_data[row["product_number"]] = {"edi": row["edi"],
                                                   "description": row["description"],
                                                   "component_qty_standard": int(row["component_qty_standard"])}
        kit_std_data['total_pieces'] = len(self.kit_std["std"])
        kit_std_data["kit_number"] = self.kit_std["kit_id"]

        return kit_std_data

    def get_total_components_count(self, breakout):
        components = {k: {"qty_std": k["component_qty_standard"]} for k in self._kit_std.keys()}
        print(components)
        # for serial in breakout['serials']:



    # def get_total_possible_valid_count(self, breakout):
    #     breakout = self.generate_kit_breakout()


if __name__ == '__main__':
    cnblzr = Cannibalizer(KIT, SERIALS, write_json=False)
    breakout = cnblzr.generate_kit_breakout()
    with open('{}_breakout.json'.format(KIT), 'w')as f:
        json.dump(breakout, f, indent=4, ensure_ascii=True)
    with open('{}_std.json'.format(KIT), 'w')as f:
        json.dump(cnblzr.generate_kit_std(), f, indent=4, ensure_ascii=True)


    cnblzr.get_total_components_count(breakout)
