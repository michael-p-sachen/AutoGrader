import numpy as np
from objects.obj import Obj
from constants import STAR_INDICES
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

def find_nearest_integer_smpl(input_avatar: Obj):
    """ The RTW flow uses smpl with integer params to find the nearest size that should be picked """
    pass


def find_garment_pairs(avatar, garment):
    garment_matching = []
    tree = avatar.to_tree()

    # Iterate through garment points
    for garment_point in garment.v:
        # Find closest point from garment to avatar
        a = tree.query(garment_point)
        avatar_point = avatar.v[a[1]]
        direction = garment_point - avatar_point

        garment_matching.append({
            "gp": garment_point,
            "ap": avatar_point,
            "a": a,
            "direction": direction
        })

    return garment_matching


def scale_garment(garment_pairs, avatar):
    """
    garment pairs ==>
        gp, point on garment
        ap, point on source avatar
        a, distance and index of point
        direction, vector from source avatar to garment point
    """

    graded_garment_points = []

    for pair in garment_pairs:
        index = pair["a"][1]
        direction = pair["direction"]
        graded_point = avatar.v[index] + direction
        graded_garment_points.append(graded_point)

    return np.array(graded_garment_points)


def grade_garment(input_avatar, target_avatar, input_garment):
    """
        source: path to source avatar obj
        target: path to target avatar obj
        garment: path to garment obj
        garment and avatar are exported from clo as separate objs
        when the garment is draped on the avatar
    """

    # Convert Everything to np arrays
    input_garment = Obj(input_garment)
    input_avatar = Obj(input_avatar)
    target_avatar = Obj(target_avatar)

    # Move Avatars to ground
    # translation = source.to_ground()
    # garment.translate_y(translation)
    # target.to_ground()

    grade_pairs = find_garment_pairs(input_avatar, input_garment)
    graded_points = scale_garment(grade_pairs, target_avatar)

    # Create graded garment
    obj_info = {"v": graded_points, "f": input_garment.f, "vn": input_garment.vn, "vt": input_garment.vt}
    graded_garment = Obj(None, obj_info)

    # Flatten bc we need original garment
    flat_garment = graded_garment.flatten(input_garment)

    xs = [x[0] - 400 for x in flat_garment]
    ys = [x[1] for x in flat_garment]

    ox = [x[0] for x in input_garment.vt]
    oy = [x[1] for x in input_garment.vt]

    plt.plot(xs, ys, "ro")
    plt.plot(ox, oy, "bo")
    plt.axis('equal')
    plt.show()
    print("a")
    graded_garment.to_file("./graded_garment.obj")

    return graded_garment


if __name__ == "__main__":
    grade_garment("/Users/michaelsachen/Desktop/digicouture/sample_assets/a1.obj",
                  "/Users/michaelsachen/Desktop/digicouture/sample_assets/a2.obj",
                  "/Users/michaelsachen/Desktop/digicouture/sample_assets/g1.obj")