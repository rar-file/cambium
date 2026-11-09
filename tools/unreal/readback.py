"""Inside Unreal: what a mesh holds, through geometry script (the game's plugin-free route can't see it)."""
import traceback

import unreal


def _limits(pts, n):
    if not pts:
        return None
    return {"min": [round(min(p[i] for p in pts), 4) for i in range(n)], "max": [round(max(p[i] for p in pts), 4) for i in range(n)]}


def sample_mesh(mesh, limit, kinds=("source", "render")):
    """UV sets and vertex colours as Unreal holds them, in its source mesh and in its render data (for a
    Nanite mesh that is the fallback)."""
    out = {}
    uvs = unreal.GeometryScript_UVs
    lists = unreal.GeometryScript_List
    types = {"source": unreal.GeometryScriptLODType.SOURCE_MODEL, "render": unreal.GeometryScriptLODType.RENDER_DATA}
    for kind in kinds:
        try:
            opts = unreal.GeometryScriptCopyMeshFromAssetOptions()
            opts.set_editor_property("request_tangents", True)
            lod = unreal.GeometryScriptMeshReadLOD()
            lod.set_editor_property("lod_type", types[kind])
            lod.set_editor_property("lod_index", 0)
            result = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(mesh, unreal.DynamicMesh(), opts, lod)
            dyn = result[0] if isinstance(result, tuple) else result
            n_uv = unreal.GeometryScript_MeshQueries.get_num_uv_sets(dyn)
            d = {"outcome": str(result[1]) if isinstance(result, tuple) and len(result) > 1 else "", "uv_sets": n_uv, "triangles": dyn.get_triangle_count(),
                 "vertices": unreal.GeometryScript_MeshQueries.get_vertex_count(dyn), "uv": {}}
            res = unreal.GeometryScript_VertexColors.get_mesh_per_vertex_colors(dyn)
            colour_list = next((x for x in res if isinstance(x, unreal.GeometryScriptColorList)), None)
            if colour_list is not None:
                arr = list(lists.convert_color_list_to_array(colour_list))
                vals = [(c.r, c.g, c.b, c.a) for c in arr[:: max(1, len(arr) // limit)]]
                d["colour_count"] = len(arr)
                d["colour_limits"] = _limits(vals, 4)
                levels = sorted({round(v[0], 6) for v in vals})
                d["colour_distinct_r"] = len(levels)
                d["colour_r_smallest_step"] = round(min((y - x for x, y in zip(levels, levels[1:])), default=0.0), 6)
                d["colour_first"] = [[round(x, 5) for x in v] for v in vals[:6]]
            for k in range(n_uv):
                res = uvs.get_mesh_per_vertex_u_vs(dyn, k)
                uv_list = next((x for x in res if isinstance(x, unreal.GeometryScriptUVList)), None)
                arr = list(lists.convert_uv_list_to_array(uv_list))
                pts = [(q.x, q.y) for q in arr[:: max(1, len(arr) // limit)]]
                xs = sorted({round(q[0], 4) for q in pts})
                d["uv"][k] = {**(_limits(pts, 2) or {}), "first": [[round(x, 4) for x in q] for q in pts[:5]], "distinct_x": len(xs), "smallest_x_step": round(min((y - x for x, y in zip(xs, xs[1:])), default=0.0), 5)}
            out[kind] = d
        except Exception as error:
            out[kind] = {"error": str(error), "trace": traceback.format_exc()[-600:]}
    return out
