import numpy as np
import trimesh

from obj import Obj


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

    return flat_garment

def verts_for_face(index, mesh):
    """ Given an index of a face, return the vertices of that face """
    return [mesh.vertices[x] for x in mesh.faces[0]]


def flatten(garment_path):
    mesh = trimesh.load(file_obj=trimesh.util.wrap_as_stream(open(garment_path, 'r').read()), file_type="obj")

    # Convert the mesh to a graph so we can iterate through edges
    graph = trimesh.graph.face_adjacency(mesh = mesh)

    # Rotate the mesh so that the first face on the graph is on the xy plane
    intitial_face_verts = verts_for_face(1, mesh)

    # Transform poi
    p1 = intitial_face_verts[0]
    p3 = intitial_face_verts[2]

    # Transform mesh so that v0 is at 0,0,0
    mesh.apply_translation(-p1)

    # Rotate mesh to lay on xy plane
    v1 = p3 - p1
    target = [1, 1, 0]

    rotation = trimesh.geometry.align_vectors(v1, target)
    mesh.apply_transform(rotation)

    flattened_points = []

    # Put initial face in the plants

    # Mesh should now be on the plane i.e. all z values should be 0 and we start alg
    for node in graph:
        face_a = node[0]
        face_b = node[1]

        # Find Shared Vertices from Faces

        # Find Lone Verts for A and B

        # Get the edgelengths e1, e2 from shared verts to face_b lone vert

        # Draw 2 circles in the plane with radius e1 and e2

        # Find the intersection of the 2 circles furthest from lone vert a

        # This is the new position of the unfolded vertex








if __name__ == "__main__":
    garment_path = "./sample_assets/Garm_Colorway_1.obj"
    flatten(garment_path)



