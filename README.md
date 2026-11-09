# treegen: procedural tree generator core

An engine-agnostic core that grows a tree year by year (crown and roots) and
exports meshes plus the full growth history. The first species is silver birch
(*Betula pendula*).

## Cambium 0.9: install and grow

The model is published as **Cambium**: install it with pip, then grow a tree from Python or the command
line. `cambium` is a thin public layer over the `treegen` engine below; it gives the same tree as
`cli.py` for the same seed. Python 3.12 to 3.14. Documentation: https://rar-file.github.io/cambium/

```
pip install pycambium
cambium grow --species birch --seed 7 --years 60              # stats.json and stats.csv
cambium grow --species birch --seed 7 --years 30 --export glb # game-ready .glb, three levels of detail
cambium forest --species birch --seed 1 --years 40            # a forest plot
cambium species
```

```python
import cambium
tree = cambium.grow(species="birch", seed=7, years=60)
print(tree.height_m, tree.dbh_cm)
tree.stats.to_csv("birch7.csv")
tree.export("birch7", format="glb")    # or format="usd"
```

Licence: Apache-2.0 (`LICENSE`). Citing: `CITATION.cff`. Contributing: `docs/site/contributing.md`.

## The research checkout

```
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python cli.py --species betula_pendula --seed 1 --years 60           # open-grown
.venv\Scripts\python cli.py --species betula_pendula --seed 1 --years 60 --stand   # in a stand
.venv\Scripts\python tools/sweep.py seeds --seeds 1-10 --modes open,stand --out out/sweep.json
.venv\Scripts\python tools/plot.py --trees 25 --years 60 --seed 1 --out out/plot_1    # a plot of real competitors
.venv\Scripts\python tools/render_stand.py plot out/plot_1 out/plot_1_winter.png winter  # eye-level stand view
.venv\Scripts\python -m pytest
```

Output is deterministic for a given seed. Open-grown runs go to `out/<seed>/`,
stand runs to `out/<seed>_stand/`.

## Layout

| path | role |
|---|---|
| `species/betula_pendula.yaml` | every species parameter, each with its source; estimates are marked `VERIFY` |
| `environments/sweden_open_field.yaml` | site: latitude, season, sky, diffuse fraction, and the soil (rootable depth field, moisture by depth, stones, bulk density) |
| `treegen/growth.py` | yearly cycle: light, shedding, water, Borchert–Honda allocation, shoot growth, pipe model, mechanics |
| `treegen/light.py` | shadow propagation, layer by layer in 2-D Fourier space; Beer–Lambert exposure; periodic stand cell |
| `treegen/hydraulics.py` | pipe-model water transport: leaf water potential, stomatal opening, turgor-limited expansion |
| `treegen/roots.py` | root system grown by bud competition for soil water; zone of rapid taper; anchorage numbers |
| `treegen/mechanics.py` | bending of every internode under its added load (stiffness ∝ r⁴) and reaction-wood posture control |
| `treegen/environment.py` | light directions and weights (CIE overcast sky, sun path) and the soil; both swappable |
| `treegen/structure.py` | node store shared by crown and roots |
| `treegen/kernels.py` | compiled (numba) tree passes: subtree sums, bending and posture control; bit-identical to the numpy level loops they replaced |
| `treegen/plot.py`, `tools/plot.py` | a plot of independent trees sharing one periodic light field and the soil, thinned from below |
| `tools/birch-stem-tracer.html`, `tools/serve_tracer.py`, `tools/stem_metrics.py` | hand-tracing of stem centrelines on the reference photos (served locally, traces saved to `reference/stem_traces.json`) and the tracer's measurements in Python for model stems |
| `tools/render_stand.py` | eye-level stand view framed like a photograph (level camera, focal length and horizon row given), hero meshes for every tree in view |
| `treegen/mesh.py` | generalised-cylinder meshes, built a chunk of whole branches at a time; crown and roots are meshed as one surface |
| `treegen/export.py` | streaming GLB and USD writers, the binary timeline (writer and reader), `stats.json` |
| `treegen/preview.py` | silhouettes, a z-buffer rasterizer for shaded views, root views |
| `treegen/reference.py` | published Swedish/European growth figures used to check `stats.json` |
| `reference/` | freely licensed photos of leafless silver birch for visual comparison only (`CREDITS.md`); never used in outputs |

## Output (`out/<seed>[_stand]/`)

Meshes come in two versions, both built and written a chunk at a time (no step
holds the whole mesh in memory):

- **Hero** (full detail, for Nanite and close-ups):
  - `tree.glb` (crown), `tree_roots.glb` and `tree_pruned.glb` (shed history). glTF is Y-up; each file is one primitive.
  - `tree.usdc` (Z-up, metres): `/Tree/Living`, `/Tree/Roots` and `/Tree/PrunedHistory` (invisible). The meshes sit in part files under `tree_parts/`, which are loaded as payloads.
- **Reduced** (twigs below a radius threshold dropped, under 10 % of the hero triangles): `tree_reduced.glb`, `tree_reduced_roots.glb` and `tree_reduced.usdc`. The threshold is about 1 cm radius at 60 years, so a reduced tree has no fine twigs at all; a leafless stand drawn from reduced meshes looks bare beyond the hero trees (see `KNOWN_ISSUES.md`, phase 11). Far trees need the hero mesh or twig cards.

Every vertex carries `birth_year`, `death_year`, `branch_order`, `radius` and `node_id`; root vertices also carry `depth_below_ground`. In GLB these are float32 custom attributes (`_BIRTH_YEAR`, …). The Roots prim carries the anchorage numbers. Crown and roots share the ground-line ring of the stem, so together they form one continuous surface.

- **`timeline.json` + `timeline.npz`**: the JSON is a small header that describes every array in the `.npz`:
  - **Crown (`shoot_*`) and roots (`root_*`):** per-node arrays for parent, birth and death year, order, axis and position.
  - **Radius:** float16 samples at the birth year, every 5th year and the last year, interpolated linearly in between. A node whose interpolation would be off by more than 2 % is stored every year instead. The header records the largest error.
  - **Bending:** crown positions every 5 years, as float16 offsets from the final position.
  - **Spurs:** short shoots, as attachment points for leaves, with the leaf size (m²) and LMA (g m⁻²) of each (`spur_leaf_area_m2`, `spur_lma_g_m2`; `shoot_leaf_area_m2`, `shoot_lma_g_m2` for long-shoot tips).
  - **Annual rings:** for every crown and root internode thicker than 1 cm, the width of each year's ring (`shoot_ring_node`, `shoot_ring_count`, `shoot_ring_width_m`; `root_*` likewise), for cut wood and stumps.

  `treegen.export.Timeline` reads it (`radius_at(year)`, `positions_at(year)`).
- **`stats.json`** reports, per year:
  - height, DBH, crown width, crown base and crown ratio;
  - branch and internode counts, leaf area and mean hanging-twig length;
  - water status, carbon fixed (model resource units), root depth and spread;
  - every 5 years and from age 50 on, scaffold statistics: limbs over 5 and 10 cm, limb-to-trunk ratios, and leaf area by height and by distance from the trunk.

  It also includes published reference figures, leaf-area index (stand: leaf area × stems per hectare; open-grown: leaf area per crown projection) and anchorage: the critical turning moment (ForestGALES-style regression on silver-birch pulling tests, adjusted for rooting depth and root asymmetry by wind direction), root-plate overturning resistance, and breaking force per main root.
- **`manifest.json`**: file sizes, triangle counts, runtime and peak memory per stage.
- **`previews/`** contains:
  - side and top silhouettes at 5, 15, 30 and 60, plus a summary sheet;
  - shaded 3/4 views at 30 and 60, an eye-level perspective view at 60 (`photo_age60.png`, as a photograph from 1.6 m at 1.3 tree heights), and a hanging-twig close-up;
  - roots below ground at 15, 30 and 60, root spread under the crown outline, and a close-up of the root flare (structural roots only).

## Model

The core follows Palubicki et al. (2009). Each year:
1. Light is propagated as shade.
2. Branches die of light (their leaves below the 21 % at which birch shade leaves die) or of carbon (their own leaves no longer pay the upkeep of their wood); ageing only lowers vigour.
3. Leaf water potential is solved through the pipe-model xylem from roots to leaves; it sets stomatal opening (carbon) and turgor (expansion).
4. Carbon is split between crown and roots by functional balance. The tree first pays maintenance respiration for its living wood, then growth respiration (0.25 g C per g C built). Whole-tree carbon use efficiency (NPP/GPP) comes out near the published 0.47.
5. Borchert–Honda allocation distributes it to buds and root tips.
6. Shoots and roots grow toward light or water under tropisms.
7. Wood grows by annual rings (Pressler's rule, disused pipes kept), never thinner than the pipe model's radius.
8. Every internode bends under its added load.

Roots compete for soil water in the same way that shoots compete for light. The main roots come from the root collar. Its primordia sit at a fixed divergence around the taproot and stay viable for several years. They share resources without favouring deeper primordia, so the main roots radiate around the stem.

At the collar, root radii match the stem base. Within the zone of rapid taper (2.2 × DBH) the extra anchoring wood fades out, and beyond it roots follow their own pipe model. The rootable soil depth varies smoothly over the ground.

Shoots and leaves expand according to pre-dawn water potential (soil minus the gravity gradient), and midday water potential closes the stomata.

Bud light leaves out the shade of the bud's own shoot (exactly, from the impulse response of the light propagation), so no shoot shades itself. Water is conducted through additive pipe-model sapwood, at a measured 1.24e-4 m² of xylem per m² of leaf. A limb's meristems start at the physiological age the stem had when it made them, so limbs born high on an old stem do not overtop the leader. First-order limbs leave the stem at the measured 43°.

Each short shoot's leaves take their size and LMA from their light relative to the best-lit buds of the crown. Sun leaves are small and thick, shade leaves large and thin (Hagemeier & Leuschner 2019). The sympodial deviation at each year's joint is spread as a curvature over the new shoot, and direction noise is correlated along the shoot, so hanging twigs fall in smooth arcs. A herb layer that shades the lowest 0.6 m can be switched on in the environment file; it is off by default (see `KNOWN_ISSUES.md`). A shoot that reaches the ground stops, and a branch lying in the ground layer dies. Near the collar, growing roots keep clear of the stem and of each other, and the seedling taproot decays below the deepest main lateral. Branch autonomy (Sprugel et al. 1991) is implemented but off; see `KNOWN_ISSUES.md`.

In `--stand` mode, neighbours are copies of the focal crown, so they grow with it. They stand at random positions (no two closer than 0.6 × the mean spacing), each turned and scaled by its own size, so light arrives unevenly. Stem density follows a Swedish birch thinning programme keyed to top height. Below a closed canopy shade does not fade with depth.

Light is attenuated with the extinction coefficient measured in closed birch stands (0.37). Each year the leader, and the stem's posture target inside the crown, turn towards the side of the crown that catches more light. Reaction wood corrects posture at a rate limited by new wood (∝ ṙ/r²) and in proportion to the deviation (sine law). Stems therefore lean and sweep slightly.

Moose browse the leader of young trees (0.3–3 m tall) at the yearly rate measured in southern Swedish birch stands (16.8 %, Bergqvist et al. 2014). The last annual shoot dies, and the two uppermost buds or young laterals below it take over as leaders. Whether one wins (a crook) or both persist (a fork) is left to growth.

The stem base rises in ridges over the main structural roots: each ridge is as wide and as high at the ground line as its root is thick, and the largest reaches the uppermost root collar (Laasasenaho 1982: 0.49 DBH[cm] + 0.50 H[m] cm for birch).

`tools/plot.py` grows a plot of separate trees (100 at 1800/ha, thinned from below to 25 at 450/ha) that share one periodic light field and one soil: stones and rootable depth are laid out once, and every tree's absorbing roots draw down the same soil-water field. The trees differ in seed, germination year (0–3) and a heritable growth factor.

Plot modes (`--mode`):
- `managed` (default) thins from below by the programme.
- `natural` never thins. A tree dies when its own carbon no longer pays the upkeep of its living wood, as in an unmanaged reserve.

Every 5 years each tree's yearly history (radii and positions) moves to disk, its arrays are trimmed, the plot is pickled to `checkpoint.pkl` and `plot.json` is rewritten. Memory then holds only the trees' current state, and `--resume` continues a stopped run exactly. Trees that leave the plot are exported at once (timeline and stats); trees alive at the end also get meshes.

Each year's ring is also at least what keeps the self-weight bending stress under a safe limit (green MOR / safety factor, `pipe_model.stress_floor`).

From age 30, once the leader's growth has fallen below half its peak, the most vigorous well-lit upper limb becomes a reiterated complex every 5 years (Barthélémy & Caraglio 2007): partly rejuvenated, with an orthotropic axis of its own. This replaces the single spire top with an irregular head of a few major limbs.

All parameters, sources and estimates are in the species and environment YAML files.
