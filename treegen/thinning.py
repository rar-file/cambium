"""Mortality that answers to crowding and to a tree's vigour, for natural plots
(species block ``mortality``, off by default; treegen/plot.py).

The carbon rule alone doesn't thin a stand: a suppressed tree sheds its crown,
its upkeep falls with it (it pays for living internodes and leaves, not for its
stem), and it stands on for decades with a metre of leaf and no new wood.  Here
each tree has a yearly hazard, the sum of:

1. Self-thinning.  How crowded the tree's neighbourhood is, as Reineke's stand
   density index over the local maximum, RD = SDI / sdi_max, SDI = sum over
   stems of (DBH over bark / 25 cm) ^ slope per hectare, blurred over a
   Gaussian neighbourhood so that a gap and a thicket differ.  Above ``onset``
   the neighbourhood loses stems at rate_at_max * ((RD - onset) / (1 - onset)) ^
   shape a year.  Who goes is shared out by size and vigour, relative to the
   neighbours (step 2), so the rate holds however the trees are growing.
2. Size and vigour: the weights of step 1.  Size follows Fridman & Stahl's
   probability against DBH (as Heureka shares its stand mortality out among
   trees), vigour is the width of the tree's recent rings.
3. Suppression: a tree that has stopped laying wood dies even where its
   neighbourhood isn't over-full.
4. Background: Bengtsson 1978's deciduous rate, what Heureka uses in stands
   below the self-thinning density, shared out by size.
5. Old age: Elfving 2010's p = 1 / (1 + exp(10 - 12 A / Amax)).
"""
from __future__ import annotations

import math

import numpy as np


def over_bark_cm(d_ub_cm, bark) -> np.ndarray:
    """Over-bark DBH (cm) of a stem whose wood DBH is d_ub_cm (the model has no
    bark).  bark: (b0, b1, b2) of double bark thickness (mm) = b0 + b1 DBH + b2 d
    (tools/bark.py); at breast height d = DBH."""
    b0, b1, b2 = (float(x) for x in bark)
    d = np.asarray(d_ub_cm, float)
    return np.where(d > 0.0, np.maximum(d + b0 / 10.0, 0.0) / (1.0 - (b1 + b2) / 10.0), 0.0)


class Neighbourhood:
    """A Gaussian blur over a periodic ground grid: what's around each point of
    a rectangular plot, per square metre."""

    def __init__(self, lx: float, ly: float, x0: float, y0: float, grid_m: float, sigma_m: float):
        self.nx, self.ny = max(1, int(round(lx / grid_m))), max(1, int(round(ly / grid_m)))
        self.cx, self.cy = lx / self.nx, ly / self.ny
        self.x0, self.y0 = float(x0), float(y0)
        fx = np.fft.fftfreq(self.nx, self.cx)[:, None]
        fy = np.fft.rfftfreq(self.ny, self.cy)[None, :]
        # the transform of a unit Gaussian on a periodic grid: nothing is lost
        self.ft = np.exp(-2.0 * (math.pi * float(sigma_m)) ** 2 * (fx ** 2 + fy ** 2))

    def cells(self, xy: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        i = np.floor((xy[:, 0] - self.x0) / self.cx).astype(int) % self.nx
        j = np.floor((xy[:, 1] - self.y0) / self.cy).astype(int) % self.ny
        return i, j

    def blur(self, i: np.ndarray, j: np.ndarray, values: np.ndarray) -> np.ndarray:
        """The blurred sum of values, per square metre, at cells (i, j)."""
        grid = np.zeros((self.nx, self.ny))
        np.add.at(grid, (i, j), values)
        out = np.fft.irfft2(np.fft.rfft2(grid) * self.ft, s=grid.shape) / (self.cx * self.cy)
        return np.maximum(out[i, j], 0.0)


class Mortality:
    def __init__(self, mp, lx: float, ly: float, x0: float, y0: float):
        self.p = mp
        self.bark = tuple(float(x) for x in mp.bark_double_mm)
        self.hood = Neighbourhood(lx, ly, x0, y0, float(mp.grid_m), float(mp.neighbourhood_sigma_m))
        self.fs_d = np.asarray(mp.size_weight.dbh_cm, float)
        self.fs_lnp = np.log(np.asarray(mp.size_weight.p5, float))
        fit = np.polyfit(self.fs_d, self.fs_lnp, 1)   # beyond the table: the same line, in ln p
        self.fs_fit = (float(fit[0]), float(fit[1]))

    def size_weight(self, d_ob: np.ndarray) -> np.ndarray:
        """Fridman & Stahl's 5-year probability against DBH over bark, read
        off the table; a straight line in ln p beyond it."""
        out = np.interp(d_ob, self.fs_d, self.fs_lnp)
        off = (d_ob < self.fs_d[0]) | (d_ob > self.fs_d[-1])
        out[off] = self.fs_fit[0] * d_ob[off] + self.fs_fit[1]
        return np.exp(out)

    def ring_mm(self, history: list) -> float:
        """Mean ring width (mm a year) over the vigour window, from the tree's
        wood DBH (cm) at the end of each recent year; 0 below breast height."""
        n = len(history) - 1
        if n <= 0 or history[-1] <= 0.0:
            return 0.0
        return 5.0 * (history[-1] - history[0]) / n   # dDBH cm / 2 * 10 mm, a year

    def relative_density(self, d_ob: np.ndarray, i: np.ndarray, j: np.ndarray) -> np.ndarray:
        """Each tree's neighbourhood: SDI / sdi_max."""
        p = self.p
        sdi = self.hood.blur(i, j, (d_ob / 25.0) ** float(p.self_thinning_slope)) * 1e4
        return sdi / float(p.sdi_max)

    def thinning_rate(self, rd: np.ndarray) -> np.ndarray:
        """Stems lost per stem and year (hazard) in a neighbourhood at relative density rd."""
        p = self.p
        x = np.clip((rd - float(p.onset)) / (1.0 - float(p.onset)), 0.0, None)
        return np.minimum(float(p.rate_at_max) * x ** float(p.shape), float(p.rate_cap))

    def background_rate(self, dg_ob_cm: float, stand_age: float) -> float:
        """Bengtsson 1978's deciduous rate, per stem and year: % of volume a year,
        taken at the closest limit outside its range and reduced as Heureka does."""
        b = self.p.background
        d = float(np.clip(dg_ob_cm, *b.d_range_cm))
        a = float(np.clip(stand_age, *b.age_range_years))
        return max(float(b.intercept) + float(b.per_d) * d + float(b.per_age) * a, 0.0) * float(b.reduced_to) / 100.0

    def old_age_rate(self, age: np.ndarray) -> np.ndarray:
        """Elfving 2010: p = 1 / (1 + exp(10 - 12 A / Amax)); a year."""
        amax = float(self.p.old_age.max_age_years)
        return 1.0 / (1.0 + np.exp(10.0 - 12.0 * age / amax))

    def hazards(self, xy: np.ndarray, d_ub_cm: np.ndarray, rings_mm: np.ndarray, age: np.ndarray, stand_age: float) -> dict:
        """Each tree's yearly hazard by cause, and its neighbourhood's relative density."""
        p = self.p
        v = p.vigour
        d_ob = over_bark_cm(d_ub_cm, self.bark)
        i, j = self.hood.cells(xy)
        rd = self.relative_density(d_ob, i, j)
        size = self.size_weight(d_ob)
        slow = np.exp(-np.maximum(rings_mm, 0.0) / float(v.ring_scale_mm))
        weight = size * (float(v.floor) + (1.0 - float(v.floor)) * slow)
        # shared among neighbours: the mean weight around each tree is one
        count = self.hood.blur(i, j, np.ones(len(xy)))
        around = self.hood.blur(i, j, weight) / np.maximum(count, 1e-12)
        competition = self.thinning_rate(rd) * weight / np.maximum(around, 1e-12)
        suppressed = np.where(d_ub_cm > 0.0, float(v.suppressed_hazard) * slow, 0.0)
        past = d_ob[d_ob > 0.0]
        dg = 100.0 * math.sqrt(float(np.mean((past / 100.0) ** 2))) if len(past) else 0.0
        slope = getattr(v, "relative_size_slope", None)
        if slope and dg > 0.0:
            # a slow-ringed tree above the stand's quadratic mean diameter dies less of it, as the odds of
            # mortality fall with relative diameter in Maleki & Kiviste 2016; below the mean it holds as tuned
            d_rel = d_ob / dg
            suppressed = suppressed * np.exp(-float(slope) * np.maximum(d_rel - float(getattr(v, "relative_size_from", 1.0)), 0.0))
        around_size = self.hood.blur(i, j, size) / np.maximum(count, 1e-12)
        background = self.background_rate(dg, stand_age) * size / np.maximum(around_size, 1e-12)
        # with damage's old age on, trees die of age there, on its own clock
        old = np.zeros(len(age)) if getattr(self, "old_age_elsewhere", False) else self.old_age_rate(age)
        return {"self-thinned": competition, "suppressed": suppressed, "background": background, "old age": old, "rd": rd}

    def draw(self, hz: dict, rng) -> list:
        """Which trees die this year: (position in the arrays, cause), each
        tree's cause drawn in proportion to its hazards."""
        causes = ("self-thinned", "suppressed", "background", "old age")
        h = np.stack([hz[c] for c in causes], 1)
        total = h.sum(1)
        die = np.nonzero(rng.random(len(total)) < 1.0 - np.exp(-total))[0]
        out = []
        for n in die.tolist():
            pick = rng.random() * total[n]
            out.append((n, causes[int(np.searchsorted(np.cumsum(h[n]), pick))]))
        return out


def top_height_m(d: np.ndarray, h: np.ndarray, area_m2: float, per_ha: int = 100) -> float:
    """Mean height of the thickest stems, ``per_ha`` of them a hectare."""
    n = max(1, int(round(per_ha * area_m2 / 1e4)))
    return float(h[np.argsort(-d, kind="stable")[:n]].mean()) if len(d) else 0.0


def gap_fraction(pts: np.ndarray | None, x0: float, y0: float, lx: float, ly: float, cell_m: float, above_m: float) -> float:
    """Share of the ground with no leaf above ``above_m`` directly over it, on
    cells of ``cell_m``: Brokaw's canopy gap, a hole in the canopy down to 2 m."""
    nx, ny = max(1, int(round(lx / cell_m))), max(1, int(round(ly / cell_m)))
    if pts is None or not len(pts):
        return 1.0
    high = pts[pts[:, 2] >= above_m]
    if not len(high):
        return 1.0
    i = np.floor((high[:, 0] - x0) / (lx / nx)).astype(int) % nx
    j = np.floor((high[:, 1] - y0) / (ly / ny)).astype(int) % ny
    grid = np.zeros((nx, ny), bool)
    grid[i, j] = True
    return float(1.0 - grid.mean())
