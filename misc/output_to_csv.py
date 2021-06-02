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


def count(s: str):
    return (s.count(',') - 1) // 2


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
        return max(count(line) for line in self.lines)

    def str(self, n_features: int):
        return '\n'.join([
            line + ("," * 2 * (n_features - count(line))) + self.selection_data for line in self.lines
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
            part = line.split(",", 1)[1].strip().replace(" ", "")
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
        "TGT,MODEL,MSE,"
        + ','.join([f'C{i},C{i}_ERR' for i in range(0, max_features)])
        + ',width,window,length,shadow radius,start x,start y,target x,target y,vertical,image'
)
rls = [[len(s) for s in row.split(',')] for row in selections[0].str(max_features).splitlines()]
rls.append([len(s) for s in header.split(',')])
rls = ['{0:>' + str(max(row)) + 's}' for row in zip(*rls)]

header = ', '.join([fmt.format(field) for field, fmt in zip(header.split(','), rls)])

rows = '\n'.join([selection.str(max_features) for selection in selections])
rows = '\n'.join(
    ', '.join([
        fmt.format(field)
        for field, fmt in zip(row.split(','), rls)
    ]) for row in rows.splitlines()
)

print(header)
print(rows)
assert (
        header.count(',')
        == max(row.count(',') for row in rows.splitlines())
        == min(row.count(',') for row in rows.splitlines())
), print(
    f"""
{header.count(',')}
{max(count(row) for row in rows.splitlines())}
{min(count(row) for row in rows.splitlines())}
    """
)
