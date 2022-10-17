import math

import numpy as np
import trimesh

from obj import Obj
import matplotlib.pyplot as plt


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
    return {x: mesh.vertices[x] for x in mesh.faces[index]}


def init_mesh_position(mesh, index):
    first_face_verts = list(verts_for_face(index, mesh).values())

    p1 = first_face_verts[0]
    f_n = mesh.face_normals[index]

    r = trimesh.geometry.plane_transform(p1, f_n)
    mesh.apply_transform(r)

    return mesh


def get_intersections(x0, y0, r0, x1, y1, r1):
    # https://stackoverflow.com/questions/55816902/finding-the-intersection-of-two-circles
    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1

    d = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

    if d > r0 + r1:
        return None, None
    # One circle within other
    if d < abs(r0 - r1):
        return None, None
    # coincident circles
    if d == 0 and r0 == r1:
        return None, None
    else:
        a = (r0 ** 2 - r1 ** 2 + d ** 2) / (2 * d)
        h = math.sqrt(r0 ** 2 - a ** 2)
        x2 = x0 + a * (x1 - x0) / d
        y2 = y0 + a * (y1 - y0) / d
        x3 = x2 + h * (y1 - y0) / d
        y3 = y2 - h * (x1 - x0) / d

        x4 = x2 - h * (y1 - y0) / d
        y4 = y2 + h * (x1 - x0) / d

        return np.array([x3, y3, 0]), np.array([x4, y4, 0])


def flatten(garment_path):
    # https://stackoverflow.com/questions/963084/decomposing-a-3d-mesh-into-a-2d-net
    mesh = trimesh.load(file_obj=trimesh.util.wrap_as_stream(open(garment_path, 'r').read()), file_type="obj")
    graph = trimesh.graph.face_adjacency(mesh=mesh)

    # Init mesh position
    init_mesh_position(mesh, graph[0][0])

    # Init Flattened Points maps vert index to flattened point
    flattened_points = verts_for_face(graph[0][0], mesh)

    # Make z coord of each flattened point exactly 0
    for key in flattened_points:
        flattened_points[key][2] = 0

    # Map verts to graph nodes, then we grab through thier queues
    verts_to_graph_nodes = {}

    for node in graph:
        face_a_verts = verts_for_face(node[0], mesh)
        face_b_verts = verts_for_face(node[1], mesh)

        # If in verts to graph nodes then append the node so we can look it up later
        for key in list(face_a_verts.keys()) + list(face_b_verts.keys()):
            if key in verts_to_graph_nodes:
                verts_to_graph_nodes[key].append(node)
            else:
                verts_to_graph_nodes[key] = [node]

    for i in verts_to_graph_nodes.keys():
        for node in verts_to_graph_nodes[i]:
            face_a = node[0]
            face_b = node[1]

            face_a_verts = verts_for_face(face_a, mesh)
            face_b_verts = verts_for_face(face_b, mesh)
            shared_verts = list(set(face_a_verts.keys()) & set(face_b_verts.keys()))

            lone_verts_a = (set(face_a_verts.keys()) - set(shared_verts)).pop()
            lone_verts_b = (set(face_b_verts.keys()) - set(shared_verts)).pop()
            if lone_verts_b not in flattened_points and lone_verts_a in flattened_points:
                try:

                    # Get the edge lengths e1, e2 from shared verts to face_b lone vert in 3D
                    e1 = np.linalg.norm(mesh.vertices[lone_verts_b] - mesh.vertices[shared_verts[0]])
                    e2 = np.linalg.norm(mesh.vertices[lone_verts_b] - mesh.vertices[shared_verts[1]])

                    # Find the intersection of the corresponding flattened points and circles that correspond
                    # to the 3d edge lengths
                    intersection_a, intersection_b = get_intersections(
                        x0=flattened_points[shared_verts[0]][0], y0=flattened_points[shared_verts[0]][1], r0=e1,
                        x1=flattened_points[shared_verts[1]][0], y1=flattened_points[shared_verts[1]][1], r1=e2)

                    # This is the new position of the unfolded vertex... this needs to be mapped to 2d vertices by index
                    # We pick the intersection furthest from the flattened A lone intersection

                    if intersection_a is None or intersection_b is None:
                        continue
                    dist_a = np.linalg.norm(flattened_points[lone_verts_a] - intersection_a)
                    dist_b = np.linalg.norm(flattened_points[lone_verts_a] - intersection_b)

                    if dist_a > dist_b:
                        flattened_points[lone_verts_b] = intersection_a
                    else:
                        flattened_points[lone_verts_b] = intersection_b
                except:
                    pass
            if lone_verts_a not in flattened_points and lone_verts_b in flattened_points:
                try:
                    # Get the edge lengths e1, e2 from shared verts to face_b lone vert in 3D
                    e1 = np.linalg.norm(mesh.vertices[lone_verts_a] - mesh.vertices[shared_verts[0]])
                    e2 = np.linalg.norm(mesh.vertices[lone_verts_a] - mesh.vertices[shared_verts[1]])

                    # Find the intersection of the corresponding flattened points and circles that correspond
                    # to the 3d edge lengths
                    intersection_a, intersection_b = get_intersections(
                        x0=flattened_points[shared_verts[0]][0], y0=flattened_points[shared_verts[0]][1], r0=e1,
                        x1=flattened_points[shared_verts[1]][0], y1=flattened_points[shared_verts[1]][1], r1=e2)

                    # This is the new position of the unfolded vertex... this needs to be mapped to 2d vertices by index
                    # We pick the intersection furthest from the flattened A lone intersection
                    if intersection_a is None or intersection_b is None:
                        continue
                    dist_a = np.linalg.norm(flattened_points[lone_verts_b] - intersection_a)
                    dist_b = np.linalg.norm(flattened_points[lone_verts_b] - intersection_b)

                    if dist_a > dist_b:
                        flattened_points[lone_verts_a] = intersection_a
                    else:
                        flattened_points[lone_verts_a] = intersection_b
                except:
                    ...


    # try:
        # for node in graph:
                # face_a = node[0]
                # face_b = node[1]
                #
                # # Find Shared Vertices from Faces
                # face_a_verts = verts_for_face(face_a, mesh)
                # face_b_verts = verts_for_face(face_b, mesh)
                #
                # # Shared Verts should exist in flat space
                # shared_verts = list(set(face_a_verts.keys()) & set(face_b_verts.keys()))
                #
                # # Find Lone Verts for A and B
                # lone_verts_a = (set(face_a_verts.keys()) - set(shared_verts)).pop()
                # lone_verts_b = (set(face_b_verts.keys()) - set(shared_verts)).pop()

                # if lone_verts_b not in flattened_points and lone_verts_a in flattened_points:
                #
                #     # Get the edge lengths e1, e2 from shared verts to face_b lone vert in 3D
                #     e1 = np.linalg.norm(mesh.vertices[lone_verts_b] - mesh.vertices[shared_verts[0]])
                #     e2 = np.linalg.norm(mesh.vertices[lone_verts_b] - mesh.vertices[shared_verts[1]])
                #
                #     # Find the intersection of the corresponding flattened points and circles that correspond
                #     # to the 3d edge lengths
                #     intersection_a, intersection_b = get_intersections(
                #         x0=flattened_points[shared_verts[0]][0], y0=flattened_points[shared_verts[0]][1], r0=e1,
                #         x1=flattened_points[shared_verts[1]][0], y1=flattened_points[shared_verts[1]][1], r1=e2)
                #
                #     # This is the new position of the unfolded vertex... this needs to be mapped to 2d vertices by index
                #     # We pick the intersection furthest from the flattened A lone intersection
                #     dist_a = np.linalg.norm(flattened_points[lone_verts_a] - intersection_a)
                #     dist_b = np.linalg.norm(flattened_points[lone_verts_a] - intersection_b)
                #
                #     if dist_a > dist_b:
                #         flattened_points[lone_verts_b] = intersection_a
                #     else:
                #         flattened_points[lone_verts_b] = intersection_b
                #
                # if lone_verts_a not in flattened_points and lone_verts_b in flattened_points:
                #     # Get the edge lengths e1, e2 from shared verts to face_b lone vert in 3D
                #     e1 = np.linalg.norm(mesh.vertices[lone_verts_a] - mesh.vertices[shared_verts[0]])
                #     e2 = np.linalg.norm(mesh.vertices[lone_verts_a] - mesh.vertices[shared_verts[1]])
                #
                #     # Find the intersection of the corresponding flattened points and circles that correspond
                #     # to the 3d edge lengths
                #     intersection_a, intersection_b = get_intersections(
                #         x0=flattened_points[shared_verts[0]][0], y0=flattened_points[shared_verts[0]][1], r0=e1,
                #         x1=flattened_points[shared_verts[1]][0], y1=flattened_points[shared_verts[1]][1], r1=e2)
                #
                #     # This is the new position of the unfolded vertex... this needs to be mapped to 2d vertices by index
                #     # We pick the intersection furthest from the flattened A lone intersection
                #     dist_a = np.linalg.norm(flattened_points[lone_verts_b] - intersection_a)
                #     dist_b = np.linalg.norm(flattened_points[lone_verts_b] - intersection_b)
                #
                #     if dist_a > dist_b:
                #         flattened_points[lone_verts_a] = intersection_a
                #     else:
                #         flattened_points[lone_verts_a] = intersection_b
    # except:
    #     xs = [x[0] for x in list(flattened_points.values())]
    #     ys = [x[1] for x in list(flattened_points.values())]
    #     plt.plot(xs, ys, 'b.')
    #     plt.show()


    return flattened_points



if __name__ == "__main__":
    garment_path = "./garm.obj"
    # garment_path = "./sample_assets/sample_triangle.obj"
    # import seperate_meshes
    # _, b = seperate_meshes.parse_combined_mesh(open(garment_path, 'r').read())
    # garm = b[list(b.keys())[1]]
    #
    # # Write garm list to file
    # with open("garm.obj", "w") as f:
    #     for i in garm:
    #         f.write(str(i) + "\n")

    a = flatten(garment_path)
    xs = [x[0] for x in list(a.values())]
    ys = [x[1] for x in list(a.values())]
    plt.plot(xs, ys, 'b.')
    plt.axis('equal')
    plt.show()




