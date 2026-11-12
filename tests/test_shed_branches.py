"""The mesh of shed branches (cli.export_all: tree_pruned.glb, /Tree/PrunedHistory), on made-up structures.

An open-grown seed-1 birch could not be exported as USD: its first leader was lost at 1.4 m, one node of it lived on as a stub, and
the two nodes past the stub had died.  The mesher took those dead nodes and a shed twig high in the crown for one trunk.
"""
from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from treegen import mesh

GEOMETRY = SimpleNamespace(junction_blend=0.6, collar_extra=0.35, collar_length=1.5, root_flare_extra=0.35, root_flare_height=0.45)


def _tree(parent, axis, laterals, dead, pos):
    n = len(parent)
    parent = np.asarray(parent)
    depth = np.zeros(n, np.int64)
    for k in range(1, n):
        depth[k] = depth[parent[k]] + 1
    is_lat = np.zeros(n, bool)
    is_lat[laterals] = True
    death = np.full(n, -1)
    death[dead] = 10
    return SimpleNamespace(n=n, pos=np.asarray(pos, float), parent=parent, axis=np.asarray(axis), is_lateral=is_lat, order=np.asarray(axis),
                           birth=np.zeros(n, np.int64), death=death, depth=depth)


def _lost_leader_with_a_living_stub():
    """A stem of 5 nodes; from its last node (4) a lateral that became the leader (8-15, alive); the old leader past it: one
    living node (5), then two dead (6, 7).  A shed twig high on the new leader (16-18) and a shed branch low on the stem (19, 20)."""
    parent = [-1, 0, 1, 2, 3, 4, 5, 6, 4, 8, 9, 10, 11, 12, 13, 14, 13, 16, 17, 2, 19]
    axis = [0] * 8 + [1] * 8 + [2] * 3 + [3] * 2
    pos = ([[0.0, 0.0, 0.3 * k] for k in range(8)] + [[0.05 * k, 0.0, 1.2 + 0.3 * k] for k in range(1, 9)]
           + [[0.3 + 0.2 * k, 0.0, 3.0 + 0.1 * k] for k in range(1, 4)] + [[0.0, 0.2 * k, 0.6] for k in range(1, 3)])
    tree = _tree(parent, axis, [8, 16, 19], [6, 7, 16, 17, 18, 19, 20], pos)
    radius = np.r_[np.full(5, 0.05), [0.004, 0.003, 0.003], np.linspace(0.04, 0.01, 8), np.full(3, 0.004), np.full(2, 0.006)]
    return tree, radius


def test_shed_branches_mesh_when_the_lost_leaders_dead_end_is_past_a_living_stub():
    tree, radius = _lost_leader_with_a_living_stub()
    dead = tree.death >= 0
    parts = list(mesh.build_mesh_chunks(tree, dead, radius, GEOMETRY))       # was: RuntimeError, axis chains are not contiguous
    # the trunk has not ended at the fork: its dead end lies further on, so no shed branch is drawn as its continuation
    assert mesh.continue_trunk(tree, dead, radius) is tree
    nodes = np.concatenate([p.attributes["node_id"] for p in parts])
    z = np.concatenate([p.vertices[:, 2] for p in parts])
    assert set(nodes.tolist()) == {6, 7, 16, 17, 18, 19, 20}                 # every shed node, and no living one
    for p in parts:
        tube = tree.axis[p.attributes["node_id"]][p.faces]
        assert np.all(tube == tube[:, :1])                                   # no triangle joins two branches
    assert z[np.isin(nodes, [6, 7])].max() < 2.2 < z[np.isin(nodes, [16, 17, 18])].min()    # the leader's dead end stops where it stopped


def test_a_shed_top_whose_leader_had_been_replaced_is_still_one_tube():
    # the stem's last two nodes (3, 4) and the lateral that went on from its end (5-7) all died: there the trunk did end
    tree = _tree([-1, 0, 1, 2, 3, 4, 5, 6], [0] * 5 + [1] * 3, [5], [3, 4, 5, 6, 7], [[0.0, 0.0, 0.3 * k] for k in range(8)])
    view = mesh.continue_trunk(tree, tree.death >= 0, np.full(8, 0.01))
    assert np.all(view.axis == 0) and not view.is_lateral[5]
    assert tree.axis[5] == 1 and tree.is_lateral[5]
