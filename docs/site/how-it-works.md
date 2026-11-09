# How it works

Cambium follows the self-organising tree model of Palubicki et al. (2009). Buds compete for light, and the tree's shape comes out of that competition rather than from rules about shape. Cambium adds water transport, roots that compete for water, carbon costs and mechanics.

The model works on nodes: one node is an internode with its leaf and its side bud. Crown and roots share one store of nodes.

## The yearly cycle

Each year:

1. **Light.** Shade is passed down from every leaf, layer by layer. Light falls off as in a closed birch canopy (extinction coefficient 0.37, measured). The sky is a standard overcast sky plus the sun's path for the site's latitude.
2. **Shedding.** A branch dies of light, when its leaves are too shaded, or of carbon, when its own leaves no longer pay the upkeep of its wood. Ageing only lowers vigour.
3. **Water.** Leaf water potential is solved through the sapwood, from roots to leaves (the pipe model). It sets how far the stomata open, which limits carbon, and the turgor that drives expansion.
4. **Carbon.** The tree fixes carbon in proportion to the light its leaves get and how far their stomata are open. It pays maintenance respiration for its living wood, then growth respiration for what it builds. Whole-tree carbon use efficiency comes out near the published 0.47.
5. **Allocation.** Carbon is split between crown and roots by functional balance: the drier the leaves, the more goes to the roots. Within each, the Borchert-Honda model shares it out among buds and root tips.
6. **Growth.** Shoots grow towards light and roots towards water. The leader grows up to the site-index curve of Eriksson et al. (1997) unless light, water or carbon hold it back.
7. **Wood.** The stem and branches thicken by annual rings, never thinner than the pipe model needs, and thick enough to keep bending stress under a safe limit.
8. **Mechanics.** Every internode bends under the load added to it. Reaction wood corrects the stem's posture, so stems lean and sweep slightly.

## Roots

Roots compete for soil water the way shoots compete for light. The main roots start at the root collar and radiate around the stem. At the collar they match the stem base. Within a zone of rapid taper, 2.2 times the stem diameter, their extra anchoring wood fades out. Beyond it they follow their own pipe model. The soil's rootable depth varies over the ground.

From the roots, the model works out anchorage: the moment that would turn the tree over, the root plate's resistance, and the breaking force of each main root.

## Leaves

Each short shoot's leaves take their size and thickness from their light. Sun leaves are small and thick, shade leaves large and thin (Hagemeier & Leuschner 2019).

## Damage and old age

- Moose browse the leader of young trees (0.3-3 m tall) at the yearly rate measured in southern Swedish birch stands, 16.8 % (Bergqvist et al. 2014). A side shoot takes over as leader, which can leave a crook or a fork.
- In forests, wind, snow and old age (Elfving 2010) can kill trees.
- From age 30, once the leader's growth has fallen below half its peak, a vigorous, well-lit upper limb becomes a new top every 5 years. Old crowns get an irregular head of a few major limbs instead of one spire.

## Stands and forests

- **One tree in a stand** (`stand=True`): the neighbours are copies of the tree, so they grow with it. Stem density follows a Swedish birch thinning programme keyed to top height.
- **A forest** (`cambium.forest`): separate trees, each with its own seed, sharing one light field and one soil. Crowding, vigour and old age decide which trees die. See [Forests](forests.md).

## Same seed, same tree

All randomness comes from the seed, and the maths libraries run on one thread, so a seed gives the same tree, bit for bit, every time it runs on the same machine with the same library versions. See [Install](install.md#one-maths-thread-on-purpose).

## Where the code is

The public package `cambium` is a thin layer over the engine package `treegen`.

| Module | What it does |
|---|---|
| `treegen/growth.py` | The yearly cycle |
| `treegen/light.py` | Shade, passed down layer by layer |
| `treegen/hydraulics.py` | Water through the pipe model |
| `treegen/roots.py` | Roots, and anchorage |
| `treegen/mechanics.py` | Bending and posture |
| `treegen/environment.py` | Sky, sun and soil |
| `treegen/plot.py`, `treegen/thinning.py` | Forests, and mortality from crowding and vigour |
| `treegen/mesh.py`, `treegen/export.py` | Meshes and file writers |

Every value the model reads is in the species file, with its source. See [Species and sources](species.md).

## Reference

Palubicki W., Horel K., Longay S., Runions A., Lane B., Měch R., Prusinkiewicz P. 2009. Self-organizing tree models for image synthesis. ACM Transactions on Graphics 28(3):58.
