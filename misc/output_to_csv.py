"""
Autofit output to csv
"""
import sys

with open(sys.argv[1], "r") as f:
    data = f.readlines()

data_lines = [line.rpartition("|")[2] for line in data]
try:
    data_lines.remove('')
except ValueError:
    pass


def extract(s: str, marker: str, marker2: str = ','):
    return s.partition(marker)[2].partition(marker2)[0]


class Selection:

    def __init__(self, image_id: str):
        self.selection = ""
        self.lines = list()
        self.image_id = image_id

    @property
    def selection_data(self):
        s = self.selection
        init_pos = extract(s, "initial_position=(", ')')
        target_pos = extract(s, "target_position=(", ')')
        vertical = extract(s, "l=")
        shadow_radius = extract(s, "s=")
        width = extract(s, "dth=")
        window = extract(s, "w=")
        length = extract(s, "gth=", ')')
        return f',{width},{window},{length},{shadow_radius},{init_pos},{target_pos},{vertical},{self.image_id}'

    def __len__(self):
        return max(line.count(',') // 2 for line in self.lines)

    def str(self, n_features: int):
        return '\n'.join([
            self.lines[0] + ("," * 2 * (n_features - self.lines[0].count(',') // 2)) + self.selection_data,
            *[line + (',' * 2 * (n_features - line.count(',') // 2)) + (',' * 10) for line in self.lines[1:]]
        ])


selections = list()
current = None
for line in data_lines:
    if line.startswith("ID"):
        current = line.partition(":")[2].strip()
    elif line.startswith("Selection"):
        current = Selection(current)
        current.selection = line
    elif line.startswith("done"):
        selections.append(current)
        current = None
    elif current is not None:
        try:
            part = line.split(",", 3)[3].strip().replace(" ", "")
            if part != '':
                current.lines.append(part)
        except (ValueError, IndexError):
            pass

try:
    selections.remove(None)
except ValueError:
    pass

max_features = max(len(selection) for selection in selections)
header = (
        "MSE,"
        + ','.join([f'C{i},C{i}_ERR' for i in range(0, max_features)])
        + ',width,window,length,shadow radius,start x,start y,target x,target y,vertical,image'
)
rows = '\n'.join([selection.str(max_features) for selection in selections])
print(header)
print(rows)
assert (
        header.count(',')
        == max(row.count(',') for row in rows.splitlines())
        == min(row.count(',') for row in rows.splitlines())
)
