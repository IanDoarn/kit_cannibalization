import pgsql
import json
from collections import OrderedDict
from prettytable import PrettyTable
import sys


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
        components = {k: 0 for k in self._kit_std.keys()}
        for serial, values in breakout['serials'].items():
            for component_details in values['breakout']:
                component_number = component_details["component_product_number"]
                qty_in_kit = int(component_details["qty_in_kit"])
                components[component_number] += qty_in_kit
        total = 0
        for key, value in components.items():
            if key not in ['total_pieces', 'kit_number']:
                total += value
        components['total_pieces'] = total
        components['kit_number'] = breakout['kit_number']
        return components

    def get_total_possible_valid_count(self, component_count):
        total_pieces = component_count['total_pieces']
        kit_number = component_count['kit_number']

        new_kit_assembly = {'kit_number': kit_number, 'assembly': []}

        for serial in self.serial_numbers:
            current_kit = {'serial': serial, 'build': [], 'status': None}
            for component, qty in component_count.items():
                if component not in ['total_pieces', 'kit_number']:
                    std_component_qty = self._kit_std[component]["component_qty_standard"]
                    if qty >= std_component_qty:
                        data = {'component': component, 'qty': std_component_qty}
                        if data not in current_kit['build']:
                            current_kit['build'].append(data)
                            component_count[component] -= std_component_qty
                            total_pieces -= std_component_qty
            if len(current_kit['build']) == self._kit_std["total_pieces"]:
                current_kit['status'] = 'valid'
                new_kit_assembly['assembly'].append(current_kit)
            else:
                current_kit['status'] = 'invalid'
                new_kit_assembly['assembly'].append(current_kit)

        return new_kit_assembly

def create_new_kit_assembly(kit_number, serials, save_data=True, write_json=False, print_results=False):
    cnblzr = Cannibalizer(kit_number, serials, write_json=write_json)
    breakout = cnblzr.generate_kit_breakout()
    component_count = cnblzr.get_total_components_count(breakout)
    kit_assembly = cnblzr.get_total_possible_valid_count(component_count)

    if save_data:
        with open('{}_breakout.json'.format(KIT), 'w')as f:
            json.dump(breakout, f, indent=4, ensure_ascii=True)
        with open('{}_std.json'.format(KIT), 'w')as f:
            json.dump(cnblzr.generate_kit_std(), f, indent=4, ensure_ascii=True)
        with open('{}_total_components.json'.format(KIT), 'w')as f:
            json.dump(component_count, f, indent=4, ensure_ascii=True)
        with open('{}_new_kit_assembly.json'.format(KIT), 'w')as f:
            json.dump(kit_assembly, f, indent=4, ensure_ascii=True)

    if print_results:
        valid = 0
        invalid = 0
        total_pieces = component_count['total_pieces']
        for row in kit_assembly['assembly']:
            if row['status'] == 'valid': valid += 1
            if row['status'] == 'invalid': invalid += 1

        head = PrettyTable(['Kit', '# valid possible', '# invalid possible', 'total pieces'])
        head.add_row([KIT, valid, invalid, total_pieces])

        for serial in kit_assembly['assembly']:
            header = PrettyTable(['kit', 'serial', 'status'])
            header.add_row([KIT, serial['serial'], serial['status']])
            table = PrettyTable(['component', 'qty'])
            for component in serial['build']:
                table.add_row([component['component'],component['qty']])

            print(header)
            print(table)

        print(head)

    return kit_assembly

if __name__ == '__main__':
    usage = "Kit Cannibaliztion\n" \
            "usgae: canniblize.py kit_number serial1 serial2 serial3 ..."

    if len(sys.argv) < 2:
        print(usage)
    else:
        KIT = sys.argv[1]
        SERIALS = [str(i) for i in sys.argv[2:]]

        create_new_kit_assembly(KIT, SERIALS, print_results=True)


