"""The leaf colours in species/betula_pendula.yaml (appearance.leaves), from measured spectra.

LOPEX93 (Hosgood et al. 1993, EcoSIS, CC0) has five fresh Betula pendula leaves (samples 306-310,
chlorophyll a+b 36.7 ug/cm2, carotenoids 8.6) and no yellow birch leaf.  So the ramp has three
measured anchors, only the first of them birch:
  fraction 1.0    birch, 306-310;
  fraction 0.5    the broadleaves with half that chlorophyll: largeleaf linden 86-90 (chl 18.5) and
                  wild grape 11-15 (chl 18.6);
  fraction 0.038  the only yellow leaves in LOPEX: soybean 321-325 (chl 1.4, carotenoids 5.1).
Between anchors the spectra are mixed in log space (absorption adds up as pigment does,
Beer-Lambert): an assumption.  A straight mix from birch to soybean went orange too early: at half
chlorophyll it gave red 0.16, where linden measures 0.10.

Spectra are turned into linear sRGB with the CIE 1931 2-degree observer (the multi-lobe fit of
Wyman, Sloan & Shirley 2013, JCGT 2(2)) under D65 (CIE 15:2004 daylight basis).

    python tools/leaf_colour_table.py            # prints the YAML to paste, reads birch-data read-only
"""
from __future__ import annotations

import re
import sys
import zipfile
import xml.etree.ElementTree as ET

import numpy as np

DATA = "../birch-data/14_appearance/"
M = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
BIRCH = [306, 307, 308, 309, 310]
HALF = [86, 87, 88, 89, 90, 11, 12, 13, 14, 15]
YELLOW = [321, 322, 323, 324, 325]
ANCHORS = (1.0, 0.5, 0.038)
FRACTIONS = [1.0, 0.75, 0.5, 0.35, 0.2, 0.1, 0.038]


def _col(ref: str) -> int:
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_spectra(name: str, last_nm: float = 800.0):
    """Wavelengths, sample numbers and spectra (row per wavelength) up to last_nm."""
    z = zipfile.ZipFile(DATA + name)
    strings = ["".join(t.text or "" for t in si.iter(M + "t")) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(M + "si")]
    rows = []
    with z.open("xl/worksheets/sheet1.xml") as fh:
        for _, el in ET.iterparse(fh):
            if el.tag == M + "row":
                row = {}
                for c in el.findall(M + "c"):
                    v = c.find(M + "v")
                    if v is not None:
                        row[_col(c.get("r"))] = strings[int(v.text)] if c.get("t") == "s" else v.text
                el.clear()
                rows.append(row)
                if len(rows) > 3 and float(rows[-1][0]) >= last_nm:
                    break
    cols = sorted(k for k in rows[0] if k > 0)
    samples = [int(float(rows[0][c])) for c in cols]
    wl = np.array([float(r[0]) for r in rows[3:]])
    return wl, samples, np.array([[float(r.get(c, "nan")) for c in cols] for r in rows[3:]])


def _g(x, mu, s1, s2):
    t = (x - mu) / np.where(x < mu, s1, s2)
    return np.exp(-0.5 * t * t)


def cmf(wl):
    x = 1.056 * _g(wl, 599.8, 37.9, 31.0) + 0.362 * _g(wl, 442.0, 16.0, 26.7) - 0.065 * _g(wl, 501.1, 20.4, 26.2)
    y = 0.821 * _g(wl, 568.8, 46.9, 40.5) + 0.286 * _g(wl, 530.9, 16.3, 31.1)
    z = 1.217 * _g(wl, 437.0, 11.8, 36.0) + 0.681 * _g(wl, 459.0, 26.0, 13.8)
    return np.stack([x, y, z], 1)


def d65(wl):
    w = np.arange(380, 790, 10.0)
    s0 = np.array([63.4, 65.8, 94.8, 104.8, 105.9, 96.8, 113.9, 125.6, 125.5, 121.3, 121.3, 113.5, 113.1, 110.8, 106.5, 108.8, 105.3, 104.4, 100.0, 96.0, 95.1,
                   89.1, 90.5, 90.3, 88.4, 84.0, 85.1, 81.9, 82.6, 84.9, 81.3, 71.9, 74.3, 76.4, 63.3, 71.7, 77.0, 65.2, 47.7, 68.6, 65.0])
    s1 = np.array([38.5, 35.0, 43.4, 46.3, 43.9, 37.1, 36.7, 35.9, 32.6, 27.9, 24.3, 20.1, 16.2, 13.2, 8.6, 6.1, 4.2, 1.9, 0.0, -1.6, -3.5,
                   -3.5, -5.8, -7.2, -8.6, -9.5, -10.9, -10.7, -12.0, -14.0, -13.6, -12.0, -13.3, -12.9, -10.6, -11.6, -12.2, -10.2, -7.8, -11.2, -10.4])
    s2 = np.array([3.0, 1.2, -1.1, -0.5, -0.7, -1.2, -2.6, -2.9, -2.8, -2.6, -2.6, -1.8, -1.5, -1.3, -1.2, -1.0, -0.5, -0.3, 0.0, 0.2, 0.5,
                   2.1, 3.2, 4.1, 4.7, 5.1, 6.7, 7.3, 8.6, 9.8, 10.2, 8.3, 9.6, 8.5, 7.0, 7.6, 8.0, 6.7, 5.2, 7.4, 6.8])
    xd, yd = 0.31272, 0.32903
    m = 0.0241 + 0.2562 * xd - 0.7341 * yd
    return np.interp(wl, w, s0 + (-1.3515 - 1.7703 * xd + 5.9114 * yd) / m * s1 + (0.0300 - 31.4424 * xd + 30.0717 * yd) / m * s2)


XYZ_TO_RGB = np.array([[3.2406, -1.5372, -0.4986], [-0.9689, 1.8758, 0.0415], [0.0557, -0.2040, 1.0570]])


def linear_srgb(wl, spectrum):
    """Linear sRGB of a reflectance or transmittance spectrum under D65 (white = 1, 1, 1)."""
    c, e = cmf(wl), d65(wl)
    xyz = (np.asarray(spectrum)[..., None] * c * e[:, None]).sum(-2) / (c[:, 1] * e).sum()
    return np.maximum(xyz @ XYZ_TO_RGB.T, 0.0)


def ramp(birch, half, yellow, fractions=FRACTIONS):
    """Spectra at each chlorophyll fraction, mixed in log space between the anchors."""
    logs = [np.log(np.maximum(x, 1e-4)) for x in (yellow, half, birch)]
    at = [ANCHORS[2], ANCHORS[1], ANCHORS[0]]
    return {f: np.exp(np.stack([np.interp(f, at, [l[i] for l in logs]) for i in range(len(birch))])) for f in fractions}


def main() -> int:
    wl, samples, refl = read_spectra("Lopex1993_Reflectance.xlsx")
    wl_t, samples_t, trans = read_spectra("Lopex1993_Transmittance.xlsx")
    vis = (wl >= 380) & (wl <= 780)
    wl, refl, trans = wl[vis], refl[vis], trans[(wl_t >= 380) & (wl_t <= 780)]

    def mean(S, ids, sample_list):
        return S[:, [sample_list.index(i) for i in ids]].mean(1)

    Rr = ramp(mean(refl, BIRCH, samples), mean(refl, HALF, samples), mean(refl, YELLOW, samples))
    Tr = ramp(mean(trans, BIRCH, samples_t), mean(trans, HALF, samples_t), mean(trans, YELLOW, samples_t))
    print("    chlorophyll_ramp:")
    for f in FRACTIONS:
        r, t = linear_srgb(wl, Rr[f]), linear_srgb(wl, Tr[f])
        print(f"      - {{chlorophyll_fraction: {f}, reflectance_linear: [{r[0]:.4f}, {r[1]:.4f}, {r[2]:.4f}], transmittance_linear: [{t[0]:.4f}, {t[1]:.4f}, {t[2]:.4f}]}}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
