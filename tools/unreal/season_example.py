"""Leaf colour that follows the day of the year while the game runs, from what the export already holds.

A worked example for docs/unreal.md, tested in the test project (tools/unreal/game_route.py and
render_shot.py).  It needs no second mesh and no re-import.  What it adds to a foliage master:

  * a Material Parameter Collection, MPC_Season, with one number, Day (1-365), that the game sets
    whenever it likes (Python: unreal.MaterialLibrary.set_scalar_parameter_value; C++:
    UKismetMaterialLibrary::SetScalarParameterValue, or an MPC instance);
  * a custom node that reads each leaf's data from its UV channels (UV2: days later or earlier than the
    tree's average to colour, and how sunlit it is), works out its chlorophyll, and picks and blends the
    two nearest columns of the leaf atlas, the same atlas the export baked for one day.

In the game's build_materials.py it would be one more line in build_master's foliage branch:

    colour_out = season_colour(material, colour, colour_out)

Numbers come from the export's species file: game.unreal.chlorophyll_by_day, leaf_levels,
leaf_level_range, and leaves.light_effect.sun_chlorophyll_factor.
"""
import unreal

mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
MPC_PATH = "/Game/World/Materials/MPC_Season"

CODE = """
// Chlorophyll of this leaf today, then the two nearest columns of the atlas.
const int Points = {points};
const float Days[{points}] = {{ {days} }};
const float Chl[{points}] = {{ {values} }};
float D = Day > {last_full} ? Day - Turn : Day;     // a leaf's delay only moves it in autumn
float C = Chl[Points - 1];
if (D <= Days[0]) C = Chl[0];
else for (int k = 1; k < Points; ++k) {{
    if (D <= Days[k]) {{ C = lerp(Chl[k - 1], Chl[k], (D - Days[k - 1]) / (Days[k] - Days[k - 1])); break; }}
}}
C *= 1.0f + ({sun_factor} - 1.0f) * Sun;
float N = {levels}.0f;
float L = saturate((C - {low}) / ({high} - {low})) * (N - 1.0f);
float I = floor(L);
float Cell = frac(UV.x * N);
float3 A = Texture2DSample(Tex, TexSampler, float2((I + Cell) / N, UV.y)).rgb;
float3 B = Texture2DSample(Tex, TexSampler, float2((min(I + 1.0f, N - 1.0f) + Cell) / N, UV.y)).rgb;
return lerp(A, B, L - I);
"""


def make_collection(day=200.0):
    """MPC_Season, with Day."""
    if eal.does_asset_exist(MPC_PATH):
        eal.delete_asset(MPC_PATH)
    folder, name = MPC_PATH.rsplit("/", 1)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mpc = tools.create_asset(name, folder, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    p = unreal.CollectionScalarParameter()
    p.set_editor_property("parameter_name", "Day")
    p.set_editor_property("default_value", float(day))
    mpc.set_editor_property("scalar_parameters", [p])
    eal.save_asset(MPC_PATH, only_if_is_dirty=False)
    return mpc


def season_colour(material, colour, colour_out, cfg):
    """A custom node in place of the leaf's colour map.  ``colour``: the master's BaseColor node; a
    texture object of the same parameter name reads whichever atlas an instance sets on it."""
    table = cfg["chlorophyll_by_day"]
    top = max(v for _, v in table)
    last_full = max(d for d, v in table if v == top)
    code = CODE.format(points=len(table), days=", ".join(f"{d:.1f}f" for d, _ in table), values=", ".join(f"{v:.3f}f" for _, v in table),
                       last_full=f"{last_full:.1f}f", sun_factor=f"{cfg['sun_chlorophyll_factor']:.3f}f", levels=int(cfg["leaf_levels"]),
                       low=f"{cfg['leaf_level_range'][0]:.3f}f", high=f"{cfg['leaf_level_range'][1]:.3f}f")
    custom = mel.create_material_expression(material, unreal.MaterialExpressionCustom, -700, -500)
    custom.set_editor_property("code", code)
    custom.set_editor_property("description", "Leaf colour by day of year")
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    pins = []
    for pin in ("Tex", "UV", "Turn", "Sun", "Day"):
        item = unreal.CustomInput()
        item.set_editor_property("input_name", pin)
        pins.append(item)
    custom.set_editor_property("inputs", pins)
    atlas = mel.create_material_expression(material, unreal.MaterialExpressionTextureObjectParameter, -1200, -700)
    atlas.set_editor_property("parameter_name", "BaseColor")
    atlas.set_editor_property("texture", colour.get_editor_property("texture"))
    uv0 = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1200, -620)
    uv0.set_editor_property("coordinate_index", 0)
    uv2 = mel.create_material_expression(material, unreal.MaterialExpressionTextureCoordinate, -1200, -560)
    uv2.set_editor_property("coordinate_index", 2)
    turn = mel.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1000, -560)
    sun = mel.create_material_expression(material, unreal.MaterialExpressionComponentMask, -1000, -500)
    for mask, red in ((turn, True), (sun, False)):
        mask.set_editor_property("r", red)
        mask.set_editor_property("g", not red)
        mask.set_editor_property("b", False)
        mask.set_editor_property("a", False)
        mel.connect_material_expressions(uv2, "", mask, "")
    day = mel.create_material_expression(material, unreal.MaterialExpressionCollectionParameter, -1000, -440)
    day.set_editor_property("collection", unreal.load_asset(MPC_PATH))
    day.set_editor_property("parameter_name", "Day")
    for source, pin in ((atlas, "Tex"), (uv0, "UV"), (turn, "Turn"), (sun, "Sun"), (day, "Day")):
        if not mel.connect_material_expressions(source, "", custom, pin):
            raise RuntimeError(f"season: pin {pin} did not connect")
    return custom, ""
