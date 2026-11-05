"""Light environment: where the light comes from.

The growth model only needs a set of light *travel* directions (unit vectors
pointing from the sky down into the scene) with relative weights that sum to
one, plus the full-light exposure ``C`` of an unshaded bud (Palubicki et al.
2009, Sec. 4.2).  Anything that implements :class:`LightEnvironment` can be
swapped in, e.g. a measured sky, an HDRI, or a forest gap.

Coordinate frame: x = east, y = north, z = up, metres.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

import numpy as np


class LightEnvironment(Protocol):
    full_light: float

    def light_directions(self) -> tuple[np.ndarray, np.ndarray]:
        """Return ``(dirs, weights)``: (K, 3) unit travel directions with
        dirs[:, 2] < 0, and (K,) non-negative weights summing to 1."""
        ...


def sun_vector(latitude_deg: float, day_of_year: np.ndarray, solar_hour: np.ndarray) -> np.ndarray:
    """Unit vector towards the sun (x east, y north, z up).

    Declination from Cooper (1969); standard spherical astronomy for the rest.
    """
    phi = np.radians(latitude_deg)
    decl = np.radians(23.44) * np.sin(2.0 * np.pi * (284.0 + day_of_year) / 365.0)
    h = np.radians(15.0 * (solar_hour - 12.0))
    east = -np.cos(decl) * np.sin(h)
    north = np.cos(phi) * np.sin(decl) - np.sin(phi) * np.cos(decl) * np.cos(h)
    up = np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.cos(h)
    return np.stack([east, north, up], axis=-1)


@dataclass
class SkySunEnvironment:
    """Diffuse sky dome plus the growing-season sun path at one latitude."""

    latitude_deg: float
    season_start_doy: int
    season_end_doy: int
    diffuse_fraction: float
    sky_model: str
    sky_elevations_deg: list
    sky_azimuth_count: int
    sun_day_step: int
    sun_hour_step: float
    min_sun_elevation_deg: float
    atmospheric_transmittance: float
    full_light: float = 1.0

    @classmethod
    def from_params(cls, p) -> "SkySunEnvironment":
        s, sun = p.sky, p.sun
        return cls(
            latitude_deg=p.site.latitude_deg,
            season_start_doy=p.season.start_doy,
            season_end_doy=p.season.end_doy,
            diffuse_fraction=p.radiation.diffuse_fraction,
            sky_model=s.model,
            sky_elevations_deg=list(s.elevations_deg),
            sky_azimuth_count=s.azimuth_count,
            sun_day_step=sun.day_step,
            sun_hour_step=sun.hour_step,
            min_sun_elevation_deg=sun.min_elevation_deg,
            atmospheric_transmittance=sun.atmospheric_transmittance,
            full_light=p.radiation.full_light,
        )

    # -- diffuse sky -------------------------------------------------------
    def sky_samples(self) -> tuple[np.ndarray, np.ndarray]:
        elev = np.radians(np.asarray(self.sky_elevations_deg, dtype=float))
        # band edges halfway between sample elevations
        edges = np.concatenate([[0.0], 0.5 * (elev[1:] + elev[:-1]), [np.pi / 2]])
        dirs, weights = [], []
        for i, e in enumerate(elev):
            # fewer azimuth samples towards the zenith (equal-ish solid angle)
            n_az = max(1, int(round(self.sky_azimuth_count * np.cos(e))))
            band = 2.0 * np.pi * (np.sin(edges[i + 1]) - np.sin(edges[i]))  # solid angle
            if self.sky_model == "cie_overcast":
                # CIE standard overcast sky, Moon & Spencer (1942): L ~ (1 + 2 sin e) / 3
                radiance = (1.0 + 2.0 * np.sin(e)) / 3.0
            elif self.sky_model == "uniform":
                radiance = 1.0
            else:
                raise ValueError(f"unknown sky model {self.sky_model!r}")
            az = (np.arange(n_az) + 0.5 * (i % 2)) * 2.0 * np.pi / n_az
            to_sky = np.stack([np.cos(e) * np.sin(az), np.cos(e) * np.cos(az), np.full(n_az, np.sin(e))], axis=1)
            dirs.append(-to_sky)
            # spherical receiver (randomly oriented foliage): weight = L * dOmega
            weights.append(np.full(n_az, radiance * band / n_az))
        d = np.concatenate(dirs)
        w = np.concatenate(weights)
        return d, w / w.sum()

    # -- direct sun --------------------------------------------------------
    def sun_samples(self) -> tuple[np.ndarray, np.ndarray]:
        days = np.arange(self.season_start_doy, self.season_end_doy + 1, self.sun_day_step, dtype=float)
        hours = np.arange(0.0, 24.0, self.sun_hour_step) + 0.5 * self.sun_hour_step
        D, H = np.meshgrid(days, hours, indexing="ij")
        v = sun_vector(self.latitude_deg, D, H)
        sin_e = v[..., 2]
        ok = sin_e > np.sin(np.radians(self.min_sun_elevation_deg))
        # beam irradiance on a sphere with a simple air-mass attenuation
        beam = np.where(ok, self.atmospheric_transmittance ** (1.0 / np.maximum(sin_e, 1e-3)), 0.0)
        # collapse the season onto one direction per clock hour (weighted mean)
        dirs, weights = [], []
        for j in range(len(hours)):
            w = beam[:, j]
            if w.sum() <= 0:
                continue
            m = (v[:, j] * w[:, None]).sum(0)
            dirs.append(-m / np.linalg.norm(m))
            weights.append(w.sum())
        d = np.array(dirs)
        w = np.array(weights)
        return d, w / w.sum()

    def light_directions(self) -> tuple[np.ndarray, np.ndarray]:
        sky_d, sky_w = self.sky_samples()
        f = self.diffuse_fraction
        if f >= 1.0:
            return sky_d, sky_w
        sun_d, sun_w = self.sun_samples()
        d = np.concatenate([sky_d, sun_d])
        w = np.concatenate([f * sky_w, (1.0 - f) * sun_w])
        return d, w / w.sum()

    def diffuse_weights(self) -> np.ndarray:
        """Weights of the sky alone, aligned with ``light_directions()``: the
        sky samples sum to 1 and the sun samples are 0.  Output only."""
        _, sky_w = self.sky_samples()
        if self.diffuse_fraction >= 1.0:
            return sky_w
        sun_d, _ = self.sun_samples()
        return np.concatenate([sky_w, np.zeros(len(sun_d))])


def make_environment(params) -> LightEnvironment:
    kind = getattr(params, "type", "sky_sun")
    if kind == "sky_sun":
        return SkySunEnvironment.from_params(params)
    raise ValueError(f"unknown environment type {kind!r}")


def _herb(g) -> dict:
    if g is None or not bool(getattr(g, "enabled", True)):
        return {}
    return {"herb_height": float(g.height_m), "herb_lai": float(g.leaf_area_index), "herb_extinction": float(g.extinction),
            "herb_recovery_half_life": float(getattr(g, "recovery_half_life_years", 0.0) or 0.0)}


def _hash01(ix, iy, seed):
    h = (ix * 73856093) ^ (iy * 19349663) ^ (int(seed) * 2654435761 + 40503)
    h = (h ^ (h >> 13)) * 1274126177
    return ((h ^ (h >> 16)) & 0xFFFFFF) / float(0x1000000)


@dataclass
class Soil:
    """Rooting medium: depth to an impermeable layer, plant-available water by
    depth, stoniness and bulk density.  Depths are metres below ground (>= 0).
    Stones are a fixed random field of cells, placed by hashing the cell index
    with the seed, so they do not depend on how large a grid looks at them.
    They lie in the mineral soil, below the stone-free organic layer, except
    where a stone reaches the surface (a share ``surface_stone_cover`` of the
    ground: the top cell of that column is stone up to the surface).
    The rootable depth varies over the ground the same way: a smooth random
    field (value noise on a lattice of the correlation length) around the
    mean depth."""

    depth: float                       # mean rootable depth
    moisture_depths: list
    moisture_values: list
    stone_depths: list
    stone_fractions: list
    stone_size: float
    bulk_density: float
    water_potential: float
    depth_sd: float = 0.0
    depth_correlation: float = 4.0
    depth_min: float = 0.0
    depth_max: float = 0.0
    herb_height: float = 0.0       # ground vegetation (field layer): height (m)
    herb_lai: float = 0.0          # its leaf area index
    herb_extinction: float = 0.5   # its Beer-Lambert extinction coefficient
    herb_recovery_half_life: float = 0.0   # years for the field layer to half cover bared soil (0: always full)
    organic_layer: float = 0.0     # stone-free organic (humus) layer over the mineral soil (m)
    surface_stone_cover: float = 0.0   # share of the ground where a stone reaches the surface

    @classmethod
    def from_params(cls, p) -> "Soil":
        s = p.soil
        mean = float(s.depth_m)
        return cls(
            depth=mean,
            moisture_depths=[float(x[0]) for x in s.moisture_profile],
            moisture_values=[float(x[1]) for x in s.moisture_profile],
            stone_depths=[float(x[0]) for x in s.stone_profile],
            stone_fractions=[float(x[1]) for x in s.stone_profile],
            stone_size=float(s.stone_size_m),
            bulk_density=float(s.bulk_density),
            water_potential=float(s.water_potential_mpa),
            depth_sd=float(getattr(s, "depth_sd_m", 0.0)),
            depth_correlation=float(getattr(s, "depth_correlation_m", 4.0)),
            depth_min=float(getattr(s, "depth_min_m", mean)),
            depth_max=float(getattr(s, "depth_max_m", mean)),
            organic_layer=float(getattr(s, "organic_layer_m", 0.0) or 0.0),
            surface_stone_cover=float(getattr(s, "surface_stone_cover", 0.0) or 0.0),
            **_herb(getattr(p, "ground_vegetation", None)),
        )

    @property
    def max_depth(self) -> float:
        return max(self.depth, self.depth_max) if self.depth_sd > 0 else self.depth

    def depth_at(self, xy: np.ndarray, seed: int) -> np.ndarray:
        """Rootable depth (m) under horizontal positions ``xy`` (..., 2)."""
        xy = np.asarray(xy, dtype=float)
        if self.depth_sd <= 0.0:
            return np.full(xy.shape[:-1], self.depth)
        g = xy / self.depth_correlation
        i0 = np.floor(g).astype(np.int64)
        f = g - i0
        f = f * f * (3.0 - 2.0 * f)            # smoothstep: C1 between lattice points
        v = np.zeros(xy.shape[:-1])
        for dx in (0, 1):
            for dy in (0, 1):
                w = (f[..., 0] if dx else 1.0 - f[..., 0]) * (f[..., 1] if dy else 1.0 - f[..., 1])
                v = v + w * _hash01(i0[..., 0] + dx, i0[..., 1] + dy, seed)
        # uniform lattice values have sd 1/sqrt(12); smoothing lowers it to ~0.74 of that
        z = (v - 0.5) / (0.74 / math.sqrt(12.0))
        return np.clip(self.depth + self.depth_sd * z, self.depth_min, self.depth_max)

    def moisture(self, depth: np.ndarray) -> np.ndarray:
        """Relative plant-available water (0..1) at depth below ground (the
        local rootable depth is applied by the caller)."""
        d = np.asarray(depth, dtype=float)
        m = np.interp(d, self.moisture_depths, self.moisture_values)
        return np.where((d < 0.0) | (d > self.max_depth), 0.0, m)

    def stone_fraction(self, depth: np.ndarray) -> np.ndarray:
        return np.interp(np.asarray(depth, dtype=float), self.stone_depths, self.stone_fractions)

    def is_stone(self, pos: np.ndarray, seed: int) -> np.ndarray:
        """True where a point (x, y, z; z < 0 below ground) lies in a stone."""
        c = np.floor(pos / self.stone_size).astype(np.int64)
        h = (c[:, 0] * 73856093) ^ (c[:, 1] * 19349663) ^ (c[:, 2] * 83492791) ^ (int(seed) * 2654435761)
        h = (h ^ (h >> 13)) * 1274126177
        u = ((h ^ (h >> 16)) & 0xFFFFFF) / float(0x1000000)
        depth = -(c[:, 2] + 0.5) * self.stone_size
        stone = (u < self.stone_fraction(depth)) & (-pos[:, 2] > self.organic_layer)
        if self.surface_stone_cover > 0.0:
            top = (c[:, 2] == -1) & (_hash01(c[:, 0], c[:, 1], int(seed) + 7919) < self.surface_stone_cover)
            stone |= top
        return stone


def make_soil(params) -> Soil:
    return Soil.from_params(params)
