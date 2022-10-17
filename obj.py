import numpy as np
from scipy.spatial import KDTree


def normalized(point):
    return point / np.linalg.norm(point)


def magnitude(v1, v2):
    return np.linalg.norm(v1-v2)


class Obj:

    def __init__(self, path, obj_info=None):
        v = []
        vt = []
        vn = []
        f = []

        if obj_info is not None:
            v = obj_info['v']
            f = obj_info['f']
            vn = obj_info['vn']
            vt = obj_info['vt']

        elif path is not None:
            with open(path, 'r') as item:
                lines = item.readlines()

                for line in lines:
                    line = line.split()
                    key = line.pop(0)
                    if key not in ['v', 'vn', 'vt', 'f']:
                        continue

                    if key == "v":
                        line = [float(x) for x in line]
                        v.append(line)
                    if key == "vn":
                        line = [float(x) for x in line]
                        vn.append(line)
                    if key == "vt":
                        line = [float(x) for x in line]
                        vt.append(line)
                    if key == "f":
                        f.append(line)

        self.v = np.array(v)
        self.vn = np.array(vn)
        self.vt = np.array(vt)
        self.f = np.array(f)

    def to_ground(self):
        min_x = min(self.v[:, 1])
        self.v = np.array([x + abs(min_x) for x in self.v])
        return min_x

    def translate_y(self, translation):
        self.v = np.array([x + abs(translation) for x in self.v])

    def to_tree(self):
        return KDTree(self.v)

    def to_file(self, path):
        lines = []

        for v in self.v:
            lines.append(f"v {str(v[0])} {str(v[1])} {str(v[2])}\n")
        for vn in self.vn:
            lines.append(f"vn {str(vn[0])} {str(vn[1])} {str(vn[2])}\n")
        for vt in self.vt:
            lines.append(f"vt {str(vt[0])} {str(vt[1])}\n")
        for f in self.f:
            lines.append(f"f {str(f[0])} {str(f[1])} {str(f[2])}\n")

        with open(path, 'w') as file:
            file.writelines(lines)

    def flat(self, flattened_verts):
        # Take our flattened verts, and create an obj using the faces from the self object

        lines = []

        for i in range(len(flattened_verts)):
            a = flattened_verts[i]
            lines.append(f"v {a[0]} {a[1]} {a[2]}\n")
        for f in self.f:
            lines.append(f"f {str(f[0])} {str(f[1])} {str(f[2])}\n")

        with open("./test.obj", 'w') as f:
            f.writelines(lines)
