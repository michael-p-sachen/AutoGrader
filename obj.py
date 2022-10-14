import numpy as np
from scipy.spatial import KDTree
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


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

    def flatten(self, original):

        flattened_verts = []
        # This Loop Gives us all 2d points
        for i, _ in enumerate(original.v):
            if i > 0:
                # Original Textures
                vt_og = np.array(original.vt[i])
                vt_prior_og = np.array(original.vt[i - 1])

                # Original Vertices
                v_og = np.array(original.v[i])
                v_prior_og = np.array(original.v[i-1])

                # New Verts
                v_n = np.array(self.v[i])
                v_prior_n = np.array(self.v[i-1])

                # Calculate direction vector from vt og i - 1 to i
                vt_og_direction = normalized(vt_og - vt_prior_og)

                # Calculate 2D Magnitude from vt og
                vt_og_magnitude = magnitude(vt_og, vt_prior_og)

                # Calculate Magnitude from v og i - 1 to i
                v_og_magnitude = magnitude(v_og, v_prior_og)

                # Calculate ratio of |v| / |vt| for og
                scaled_magnitude_ratio = vt_og_magnitude / v_og_magnitude

                # Calculate magnitude from vn i-1 to i
                v_magnitude = magnitude(v_n, v_prior_n)

                # Multiply magnitude by scalar ratio
                scaled_n_magnitude = v_magnitude * scaled_magnitude_ratio

                # place point at scaled magnitude x direction
                new_point = (scaled_n_magnitude * vt_og_direction) + flattened_verts[i-1]

            else:
                new_point = (0, 0)

            flattened_verts.append(new_point)

            if i > 70:
                xs = [x[0] for x in flattened_verts]
                ys = [x[1] for x in flattened_verts]
                plt.plot(xs, ys, "ro")
                plt.show()
                plt.axis('equal')
                print("a")


        return flattened_verts