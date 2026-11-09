// A few of the model's passes in plain C++, to measure what a port gains: evidence for reports/cpp_port_plan.md, not the port.
// tools/cpp_kernels.py builds this with the server's g++, hands each function the arrays a real tree reached, and compares time and bits
// with the Python, numpy or numba it stands for.  Each repeats its original operation for operation: sums in numpy's order, no fused
// multiply-add unless the build asks for it.  Nothing here is used by the model.
#include <algorithm>
#include <cmath>
#include <complex>
#include <cstdint>
#include <cstring>
#include <limits>
#include <vector>

using i64 = int64_t;
using i32 = int32_t;

namespace
{
// numpy's pairwise sum (fast.py _block, np_sum)
double block(const double* a, i64 n)
{
	if (n < 8)
	{
		double res = 0.0;
		for (i64 i = 0; i < n; ++i)
			res += a[i];
		return res;
	}
	double r[8];
	for (int k = 0; k < 8; ++k)
		r[k] = a[k];
	i64 i = 8;
	const i64 m = n - (n % 8);
	for (; i < m; i += 8)
		for (int k = 0; k < 8; ++k)
			r[k] += a[i + k];
	double res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
	for (; i < n; ++i)
		res += a[i];
	return res;
}

double pairwise(const double* a, i64 n)
{
	if (n <= 128)
		return block(a, n);
	i64 m2 = n / 2;
	m2 -= m2 % 8;
	const double left = pairwise(a, m2);
	const double right = pairwise(a + m2, n - m2);
	return left + right;
}

inline double np_sum(const double* a, i64 n)
{
	return 0.0 + pairwise(a, n);
}

inline double dmax(double a, double b)
{
	return a >= b ? a : b; // np.maximum on numbers
}

inline double dmin(double a, double b)
{
	return a <= b ? a : b;
}

inline double clip01(double v)
{
	return dmin(dmax(v, 0.0), 1.0);
}

inline void basipetal(const i64* up, i64 nup, const i32* par, double* acc)
{
	for (i64 j = 0; j < nup; ++j)
		acc[par[up[j]]] += acc[up[j]];
}
}

extern "C" {

// hydraulics.solve, when K_root > 0
void hydraulics_solve(i64 n, const i32* par, const double* radius, const double* length, const double* pos, const uint8_t* alive, const double* area,
	const i64* bud, i64 nb, const double* leaf_area, const double* light, const i64* up, i64 nup, const i64* down, i64 ndown, double e_max, double ks, double p_open,
	double p_close, double r_ref, double c, double K_root, double psi_soil, double* psi, double* phi, double* flow, double* collar)
{
	const double RHO_G = 0.0098;
	std::vector<double> R(n), E(n, 0.0), base(n), acc(n), D(n), E1(nb), wE(nb), Db(nb), bb(nb), tmp(nb);
	for (i64 i = 0; i < n; ++i)
	{
		const double ks_r = ks * dmin(1.0, std::pow(dmax(radius[i], 1e-5) / r_ref, c));
		R[i] = alive[i] ? length[i] / (ks_r * dmax(area[i], 1e-12)) : 0.0;
		base[i] = psi_soil - RHO_G * dmax(pos[3 * i + 2], 0.0);
	}
	for (i64 j = 0; j < nb; ++j)
	{
		E1[j] = e_max * leaf_area[j] * light[j];
		E[bud[j]] += E1[j];
	}
	basipetal(up, nup, par, E.data());
	const std::vector<double>& F = E;
	for (i64 i = 0; i < n; ++i)
		acc[i] = F[i] * R[i];
	for (i64 j = 0; j < ndown; ++j)
		acc[down[j]] += acc[par[down[j]]];
	const double root_drop = F[0] / dmax(K_root, 1e-12);
	for (i64 i = 0; i < n; ++i)
		D[i] = root_drop + acc[i];
	const double total = dmax(np_sum(E1.data(), nb), 1e-30);
	for (i64 j = 0; j < nb; ++j)
	{
		wE[j] = E1[j] / total;
		Db[j] = D[bud[j]];
		bb[j] = base[bud[j]];
	}
	const double span = p_open - p_close;
	auto mean_phi = [&](double sv)
	{
		for (i64 j = 0; j < nb; ++j)
			tmp[j] = wE[j] * clip01((bb[j] - sv * Db[j] - p_close) / span);
		return np_sum(tmp.data(), nb);
	};
	double lo = 0.0, hi = 1.0;
	if (mean_phi(1.0) >= 1.0)
		lo = hi = 1.0;
	else
		for (int k = 0; k < 40; ++k)
		{
			const double mid = 0.5 * (lo + hi);
			if (mean_phi(mid) > mid)
				lo = mid;
			else
				hi = mid;
		}
	const double s_eq = 0.5 * (lo + hi);
	for (i64 i = 0; i < n; ++i)
		psi[i] = base[i] - s_eq * D[i];
	for (i64 j = 0; j < nb; ++j)
		phi[j] = clip01((psi[bud[j]] - p_close) / span);
	*collar = psi_soil - s_eq * root_drop;
	*flow = s_eq * F[0];
}

// fast.level_order
i64 level_order(i64 n, const uint8_t* mask, const i32* depth, const uint8_t* is_lateral, i64* idx, i64* down, i64* up)
{
	i64 count = 0, dmaxv = 0;
	for (i64 i = 0; i < n; ++i)
		if (mask[i])
		{
			++count;
			dmaxv = std::max<i64>(dmaxv, depth[i]);
		}
	std::vector<i64> bounds(dmaxv + 2, 0);
	for (i64 i = 0; i < n; ++i)
		if (mask[i])
			bounds[depth[i] + 1] += 1;
	for (i64 k = 0; k <= dmaxv; ++k)
		bounds[k + 1] += bounds[k];
	std::vector<i64> fill(bounds.begin(), bounds.end() - 1);
	for (i64 i = 0; i < n; ++i)
		if (mask[i])
			idx[fill[depth[i]]++] = i;
	const i64 nd = count - bounds[1];
	std::memcpy(down, idx + bounds[1], sizeof(i64) * nd);
	i64 w = 0;
	for (i64 k = dmaxv; k > 0; --k)
	{
		for (i64 j = bounds[k]; j < bounds[k + 1]; ++j)
			if (!is_lateral[idx[j]])
				up[w++] = idx[j];
		for (i64 j = bounds[k]; j < bounds[k + 1]; ++j)
			if (is_lateral[idx[j]])
				up[w++] = idx[j];
	}
	return nd;
}

// fast.sweep_rows
void sweep_rows(std::complex<float>* H, const uint8_t* has, i64 nz, i64 nx, i64 nyf, i64 K, i64 top, i64 bottom, const float* Tr, const float* Ti, const float* wk, const i64* diff_z,
	i64 ndz, const float* wd, float* Dfr, float* Dfi)
{
	std::vector<float> Br(K * nyf), Bi(K * nyf), Sr(nyf), Si(nyf), Dr(nyf), Di(nyf);
	const i64 layer = nx * nyf;
	for (i64 x = 0; x < nx; ++x)
	{
		std::fill(Br.begin(), Br.end(), 0.f);
		std::fill(Bi.begin(), Bi.end(), 0.f);
		const float* tr = Tr + x * K * nyf;
		const float* ti = Ti + x * K * nyf;
		for (i64 z = top; z >= bottom; --z)
		{
			std::complex<float>* row = H + z * layer + x * nyf;
			if (has[z])
			{
				const float* rc = reinterpret_cast<const float*>(row);
				for (i64 y = 0; y < nyf; ++y)
				{
					Dr[y] = rc[2 * y];
					Di[y] = rc[2 * y + 1];
				}
			}
			else
			{
				std::fill(Dr.begin(), Dr.end(), 0.f);
				std::fill(Di.begin(), Di.end(), 0.f);
			}
			std::fill(Sr.begin(), Sr.end(), 0.f);
			std::fill(Si.begin(), Si.end(), 0.f);
			for (i64 k = 0; k < K; ++k)
			{
				float* __restrict__ br = Br.data() + k * nyf;
				float* __restrict__ bi = Bi.data() + k * nyf;
				const float* __restrict__ r = tr + k * nyf;
				const float* __restrict__ i = ti + k * nyf;
				const float w = wk[k];
				float* __restrict__ sr = Sr.data();
				float* __restrict__ si = Si.data();
				const float* __restrict__ dr = Dr.data();
				const float* __restrict__ di = Di.data();
				for (i64 y = 0; y < nyf; ++y)
				{
					const float a = br[y] * r[y] - bi[y] * i[y] + dr[y];
					const float b = br[y] * i[y] + bi[y] * r[y] + di[y];
					br[y] = a;
					bi[y] = b;
					sr[y] += w * a;
					si[y] += w * b;
				}
			}
			float* out = reinterpret_cast<float*>(row);
			for (i64 y = 0; y < nyf; ++y)
			{
				out[2 * y] = Sr[y];
				out[2 * y + 1] = Si[y];
			}
			for (i64 d = 0; d < ndz; ++d)
				if (diff_z[d] == z)
				{
					float* fr = Dfr + (d * nx + x) * nyf;
					float* fi = Dfi + (d * nx + x) * nyf;
					for (i64 k = 0; k < K; ++k)
					{
						const float* br = Br.data() + k * nyf;
						const float* bi = Bi.data() + k * nyf;
						const float w = wd[k];
						for (i64 y = 0; y < nyf; ++y)
						{
							fr[y] += w * br[y];
							fi[y] += w * bi[y];
						}
					}
				}
		}
	}
}

// fast.blur_layers.  Returns nothing; has: each layer's flag on the way out
void blur_layers(float* a, float* b, const double* w, i64 h, i64 nz, i64 nx, i64 ny, uint8_t wrap, uint8_t* has)
{
	const double wc = w[h];
	std::vector<double> line(ny), ext(ny + 2 * h);
	std::vector<float> zero(ny, 0.f), tmp(nx * ny);
	const i64 lay = nx * ny;
	std::vector<uint8_t> flags(nz, 0);
	for (i64 z = 0; z < nz; ++z)
	{
		float* layer = a + z * lay;
		bool empty = true;
		for (i64 i = 0; i < lay; ++i)
			if (layer[i] != 0.f)
			{
				empty = false;
				break;
			}
		if (empty)
			continue;
		flags[z] = 1;
		for (i64 x = 0; x < nx; ++x)
		{
			const float* row = layer + x * ny;
			for (i64 y = 0; y < ny; ++y)
				line[y] = double(row[y]) * wc;
			for (i64 j = h; j > 0; --j)
			{
				i64 lo = x - j, hi = x + j;
				if (wrap)
				{
					lo = ((lo % nx) + nx) % nx;
					hi = hi % nx;
				}
				const float* rl = (lo >= 0 && lo < nx) ? layer + lo * ny : zero.data();
				const float* rh = (hi >= 0 && hi < nx) ? layer + hi * ny : zero.data();
				const double wj = w[h - j];
				for (i64 y = 0; y < ny; ++y)
					line[y] += (double(rl[y]) + double(rh[y])) * wj;
			}
			float* out = tmp.data() + x * ny;
			for (i64 y = 0; y < ny; ++y)
				out[y] = float(line[y]);
		}
		for (i64 x = 0; x < nx; ++x)
		{
			const float* row = tmp.data() + x * ny;
			for (i64 y = 0; y < ny; ++y)
				ext[h + y] = row[y];
			for (i64 j = 0; j < h; ++j)
			{
				if (wrap)
				{
					ext[h - 1 - j] = ext[h + (((ny - 1 - j) % ny) + ny) % ny];
					ext[h + ny + j] = ext[h + j % ny];
				}
				else
				{
					ext[h - 1 - j] = 0.0;
					ext[h + ny + j] = 0.0;
				}
			}
			for (i64 y = 0; y < ny; ++y)
				line[y] = ext[h + y] * wc;
			for (i64 j = h; j > 0; --j)
			{
				const double wj = w[h - j];
				for (i64 y = 0; y < ny; ++y)
					line[y] += (ext[h + y - j] + ext[h + y + j]) * wj;
			}
			float* out = layer + x * ny;
			for (i64 y = 0; y < ny; ++y)
				out[y] = float(line[y]);
		}
	}
	for (i64 z = 0; z < nz; ++z)
	{
		bool near = false;
		for (i64 k = std::max<i64>(z - h, 0); k <= std::min<i64>(z + h, nz - 1); ++k)
			if (flags[k])
			{
				near = true;
				break;
			}
		has[z] = near;
		if (!near)
			continue;
		for (i64 x = 0; x < nx; ++x)
		{
			const float* row = a + z * lay + x * ny;
			for (i64 y = 0; y < ny; ++y)
				line[y] = double(row[y]) * wc;
			for (i64 j = h; j > 0; --j)
			{
				const i64 lo = z - j, hi = z + j;
				const float* rl = lo >= 0 ? a + lo * lay + x * ny : zero.data();
				const float* rh = hi < nz ? a + hi * lay + x * ny : zero.data();
				const double wj = w[h - j];
				for (i64 y = 0; y < ny; ++y)
					line[y] += (double(rl[y]) + double(rh[y])) * wj;
			}
			float* out = b + z * lay + x * ny;
			for (i64 y = 0; y < ny; ++y)
				out[y] = float(line[y]);
		}
	}
}

// LightField.optimal_direction on a repeating cell (speed.light_layers): a soft minimum of the shade over a bud's probe directions.  Single precision
// where numpy's is, since the field is float32
void optimal_direction(i64 m, i64 K, const double* pos, const double* heading, const double* dirs, double r, double cos_lim, double softmin, double C, const float* S, i64 nz, i64 nx, i64 ny, i64 lox,
	i64 loy, i64 loz, double vs, double* out)
{
	std::vector<float> s(K);
	const i64 lay = nx * ny;
	const i64 dims[3] = { nx, ny, nz };
	const float ground = float(10.0 * C);
	const float inf = std::numeric_limits<float>::infinity();
	const float soft = float(std::max(softmin, 1e-6));
	for (i64 q = 0; q < m; ++q)
	{
		const double* P = pos + 3 * q;
		const double* H = heading + 3 * q;
		float smin = inf;
		for (i64 k = 0; k < K; ++k)
		{
			const double* d = dirs + 3 * k;
			const double cosang = H[0] * d[0] + H[1] * d[1] + H[2] * d[2];
			double p[3], c[3];
			for (int h = 0; h < 3; ++h)
				p[h] = P[h] + r * d[h];
			c[0] = p[0] / vs - double(lox) - 0.5;
			c[1] = p[1] / vs - double(loy) - 0.5;
			c[2] = p[2] / vs - double(loz) - 0.5;
			for (int h = 0; h < 2; ++h)
			{
				double mod = std::fmod(c[h], double(dims[h]));
				if (mod < 0.0)
					mod += double(dims[h]);
				c[h] = mod;
			}
			i64 lo[3];
			double wt[3];
			for (int h = 0; h < 3; ++h)
			{
				double v = c[h];
				const i64 ln = dims[h];
				if (v < 0.0)
					v = ln <= 1 ? 0.0 : v + double(ln * (i64(-v / double(ln)) + 1));
				else if (v > double(ln - 1))
					v = ln <= 1 ? 0.0 : v - double(ln * i64(v / double(ln)));
				const double fl = std::floor(v);
				lo[h] = i64(fl);
				wt[h] = v - fl;
			}
			const i64 x0 = lo[0] % nx, x1 = (lo[0] + 1) % nx, y0 = lo[1] % ny, y1 = (lo[1] + 1) % ny, z0 = lo[2] % nz, z1 = (lo[2] + 1) % nz;
			const double a0 = 1.0 - wt[0], a1 = wt[0], b0 = 1.0 - wt[1], b1 = wt[1], g0 = 1.0 - wt[2], g1 = wt[2];
			double t = 0.0;
			t += double(S[z0 * lay + x0 * ny + y0]) * a0 * b0 * g0;
			t += double(S[z1 * lay + x0 * ny + y0]) * a0 * b0 * g1;
			t += double(S[z0 * lay + x0 * ny + y1]) * a0 * b1 * g0;
			t += double(S[z1 * lay + x0 * ny + y1]) * a0 * b1 * g1;
			t += double(S[z0 * lay + x1 * ny + y0]) * a1 * b0 * g0;
			t += double(S[z1 * lay + x1 * ny + y0]) * a1 * b0 * g1;
			t += double(S[z0 * lay + x1 * ny + y1]) * a1 * b1 * g0;
			t += double(S[z1 * lay + x1 * ny + y1]) * a1 * b1 * g1;
			float v = float(t);
			if (c[2] < -0.5 || c[2] > double(nz) - 0.5)
				v = 0.f;
			if (p[2] < 0.05)
				v = v + ground;
			if (!(cosang >= cos_lim))
				v = inf;
			s[k] = v;
			if (v < smin)
				smin = v;
		}
		double vx = 0.0, vy = 0.0, vz = 0.0;
		for (i64 k = 0; k < K; ++k)
		{
			if (s[k] == inf)
				continue;
			const double wv = double(std::exp(-(s[k] - smin) / soft));
			const double* d = dirs + 3 * k;
			vx += wv * d[0];
			vy += wv * d[1];
			vz += wv * d[2];
		}
		const double n = std::sqrt((vx * vx + vy * vy) + vz * vz);
		if (n > 1e-9)
		{
			const double nm = std::max(n, 1e-12);
			out[3 * q] = vx / nm;
			out[3 * q + 1] = vy / nm;
			out[3 * q + 2] = vz / nm;
		}
		else
		{
			out[3 * q] = H[0];
			out[3 * q + 1] = H[1];
			out[3 * q + 2] = H[2];
		}
	}
}

// mechanics.bend_and_correct with compiled=True: all of it
static void compose(const i64* down, i64 nd, const i32* par, double* qtot, const double* qloc)
{
	for (i64 j = 0; j < nd; ++j)
	{
		const i64 i = down[j], p = par[i];
		const double aw = qtot[4 * p], ax = qtot[4 * p + 1], ay = qtot[4 * p + 2], az = qtot[4 * p + 3];
		const double bw = qloc[4 * i], bx = qloc[4 * i + 1], by = qloc[4 * i + 2], bz = qloc[4 * i + 3];
		qtot[4 * i] = aw * bw - ax * bx - ay * by - az * bz;
		qtot[4 * i + 1] = aw * bx + ax * bw + ay * bz - az * by;
		qtot[4 * i + 2] = aw * by - ax * bz + ay * bw + az * bx;
		qtot[4 * i + 3] = aw * bz + ax * by - ay * bx + az * bw;
	}
}

static void positions(const i64* down, i64 nd, const i32* par, double* pos, double* dirs, const double* length, double zmin)
{
	for (i64 j = 0; j < nd; ++j)
	{
		const i64 i = down[j], p = par[i];
		const double L = length[i];
		if (pos[3 * p + 2] + L * dirs[3 * i + 2] < zmin)
		{
			const double dz = std::min(std::max((zmin - pos[3 * p + 2]) / L, -1.0), 1.0);
			const double hx = dirs[3 * i], hy = dirs[3 * i + 1];
			const double hn = std::sqrt(hx * hx + hy * hy);
			const double scale = std::sqrt(std::max(1.0 - dz * dz, 0.0)) / std::max(hn, 1e-12);
			if (hn > 1e-9)
			{
				dirs[3 * i] = hx * scale;
				dirs[3 * i + 1] = hy * scale;
			}
			else
			{
				dirs[3 * i] = 0.0;
				dirs[3 * i + 1] = 0.0;
			}
			dirs[3 * i + 2] = dz;
		}
		pos[3 * i] = pos[3 * p] + L * dirs[3 * i];
		pos[3 * i + 1] = pos[3 * p + 1] + L * dirs[3 * i + 1];
		pos[3 * i + 2] = pos[3 * p + 2] + L * dirs[3 * i + 2];
	}
}

static void apply_rotation(const i64* alive_idx, i64 na, const i64* down, i64 nd, const i32* par, const double* qtot, double* pos, double* dirs, double* term_dir, double* lat_dir, double* ref,
	const double* length, double zmin)
{
	double* arrs[4] = { dirs, term_dir, lat_dir, ref };
	for (i64 j = 0; j < na; ++j)
	{
		const i64 i = alive_idx[j];
		const double ux = qtot[4 * i + 1], uy = qtot[4 * i + 2], uz = qtot[4 * i + 3];
		if (std::fabs(ux) + std::fabs(uy) + std::fabs(uz) > 0)
		{
			const double w = qtot[4 * i];
			for (double* a : arrs)
			{
				const double vx = a[3 * i], vy = a[3 * i + 1], vz = a[3 * i + 2];
				const double tx = 2.0 * (uy * vz - uz * vy);
				const double ty = 2.0 * (uz * vx - ux * vz);
				const double tz = 2.0 * (ux * vy - uy * vx);
				a[3 * i] = vx + w * tx + (uy * tz - uz * ty);
				a[3 * i + 1] = vy + w * ty + (uz * tx - ux * tz);
				a[3 * i + 2] = vz + w * tz + (ux * ty - uy * tx);
			}
			const double dx = dirs[3 * i], dy = dirs[3 * i + 1], dz = dirs[3 * i + 2];
			const double s = std::sqrt(dx * dx + dy * dy + dz * dz);
			dirs[3 * i] = dx / s;
			dirs[3 * i + 1] = dy / s;
			dirs[3 * i + 2] = dz / s;
		}
	}
	positions(down, nd, par, pos, dirs, length, zmin);
}

void mechanics_year(i64 n, const i32* par, const double* radius, const double* length, const uint8_t* alive, const i64* idx, i64 nidx, const i64* alive_idx, i64 na, const i64* down, i64 nd,
	const i64* up, i64 nup, double* pos, double* dirs, double* term_dir, double* lat_dir, double* ref, const double* leaves_now, const double* leaves_prev, const double* r_prev,
	const double* setpoint, double zmin, const double* target_dir, uint8_t has_target, const uint8_t* stem, const uint8_t* limbs, uint8_t has_limbs, double pend_r, double pend_r_limb, double pend_p,
	double E_wood, double E_shoot, double wood_density, double leaf_mass, i64 steps, double cap, double rwc, uint8_t sine, double sin_sat)
{
	const double PI = 3.141592653589793, G = 9.81;
	std::vector<double> s(n), EI(n), dm(n, 0.0), acc(4 * n, 0.0), qloc(4 * n, 0.0), qtot(4 * n, 0.0), budget(n, 0.0);
	for (i64 i = 0; i < n; ++i)
	{
		const double r = radius[i];
		const double rp = std::pow(dmax(r, 1e-9) / pend_r, pend_p);
		double v = rp / (1.0 + rp);
		if (has_limbs && limbs[i])
		{
			const double rl = std::pow(dmax(r, 1e-9) / pend_r_limb, pend_p);
			v = rl / (1.0 + rl);
		}
		if (stem[i])
			v = 1.0;
		s[i] = v;
		const double E = E_shoot + (E_wood - E_shoot) * v;
		EI[i] = E * PI * std::pow(r, 4.0) / 4.0;
		qtot[4 * i] = 1.0;
	}
	for (i64 q = 0; q < nidx; ++q)
	{
		const i64 i = idx[q];
		dm[i] = wood_density * PI * dmax(radius[i] * radius[i] - r_prev[i] * r_prev[i], 0.0) * length[i] + leaf_mass * (leaves_now[i] - leaves_prev[i]);
	}
	const double b0 = -G * 0.0, b1 = -G * 0.0, b2 = -G * 1.0;
	for (i64 st = 0; st < steps; ++st)
	{
		for (i64 j = 0; j < na; ++j)
		{
			const i64 i = alive_idx[j];
			const double d = dm[i] / double(steps);
			const double h = 0.5 * length[i];
			acc[4 * i] = d;
			acc[4 * i + 1] = d * (pos[3 * i] - h * dirs[3 * i]);
			acc[4 * i + 2] = d * (pos[3 * i + 1] - h * dirs[3 * i + 1]);
			acc[4 * i + 3] = d * (pos[3 * i + 2] - h * dirs[3 * i + 2]);
		}
		for (i64 j = 0; j < nup; ++j)
		{
			const i64 i = up[j], p = par[i];
			for (int c = 0; c < 4; ++c)
				acc[4 * p + c] += acc[4 * i + c];
		}
		for (i64 j = 0; j < nidx; ++j)
		{
			const i64 i = idx[j], p = par[i];
			const double a0 = acc[4 * i + 1] - acc[4 * i] * pos[3 * p];
			const double a1 = acc[4 * i + 2] - acc[4 * i] * pos[3 * p + 1];
			const double a2 = acc[4 * i + 3] - acc[4 * i] * pos[3 * p + 2];
			const double m0 = a1 * b2 - a2 * b1;
			const double m1 = a2 * b0 - a0 * b2;
			const double m2 = a0 * b1 - a1 * b0;
			const double e = EI[i] > 1e-30 ? EI[i] : 1e-30;
			const double f = length[i] / e;
			double ox = m0 * f, oy = m1 * f, oz = m2 * f;
			const double mag = std::sqrt(ox * ox + oy * oy + oz * oz);
			const double mm = mag > 1e-12 ? mag : 1e-12;
			double lim = cap / mm;
			lim = lim < 1.0 ? lim : 1.0;
			ox *= lim;
			oy *= lim;
			oz *= lim;
			const double th = std::sqrt(ox * ox + oy * oy + oz * oz);
			const double tm = th > 1e-12 ? th : 1e-12;
			const double sh = std::sin(0.5 * th);
			qloc[4 * i] = std::cos(0.5 * th);
			qloc[4 * i + 1] = sh * (ox / tm);
			qloc[4 * i + 2] = sh * (oy / tm);
			qloc[4 * i + 3] = sh * (oz / tm);
		}
		compose(down, nd, par, qtot.data(), qloc.data());
		apply_rotation(alive_idx, na, down, nd, par, qtot.data(), pos, dirs, term_dir, lat_dir, ref, length, zmin);
	}
	// posture
	for (i64 q = 0; q < nidx; ++q)
	{
		const i64 i = idx[q];
		const double r = radius[i];
		const double x = dmax(r, 1e-9);
		const double rate = rwc * dmax(r - r_prev[i], 0.0) / (x * x) * s[i];
		budget[i] = rate * length[i];
	}
	std::fill(qtot.begin(), qtot.end(), 0.0);
	for (i64 i = 0; i < n; ++i)
		qtot[4 * i] = 1.0;
	for (i64 j = 0; j < nd; ++j)
	{
		const i64 i = down[j], p = par[i];
		const double qw = qtot[4 * p], qx = qtot[4 * p + 1], qy = qtot[4 * p + 2], qz = qtot[4 * p + 3];
		const double vx = dirs[3 * i], vy = dirs[3 * i + 1], vz = dirs[3 * i + 2];
		const double tx = 2.0 * (qy * vz - qz * vy);
		const double ty = 2.0 * (qz * vx - qx * vz);
		const double tz = 2.0 * (qx * vy - qy * vx);
		const double dx = vx + qw * tx + (qy * tz - qz * ty);
		const double dy = vy + qw * ty + (qz * tx - qx * tz);
		const double dz = vz + qw * tz + (qx * ty - qy * tx);
		const double hn = std::sqrt(dx * dx + dy * dy + 0.0 * 0.0);
		double hx, hy, hz;
		if (hn > 1e-6)
		{
			const double hm = std::max(hn, 1e-12);
			hx = dx / hm;
			hy = dy / hm;
			hz = 0.0 / hm;
		}
		else
		{
			hx = 1.0;
			hy = 0.0;
			hz = 0.0;
		}
		const double cg = std::cos(setpoint[i]), sg = std::sin(setpoint[i]);
		double ex = cg * 0.0 + sg * hx;
		double ey = cg * 0.0 + sg * hy;
		double ez = cg * 1.0 + sg * hz;
		if (has_target && std::isfinite(target_dir[3 * i]))
		{
			ex = target_dir[3 * i];
			ey = target_dir[3 * i + 1];
			ez = target_dir[3 * i + 2];
		}
		const double err = std::acos(std::min(std::max(dx * ex + dy * ey + dz * ez, -1.0), 1.0));
		double ax = dy * ez - dz * ey;
		double ay = dz * ex - dx * ez;
		double az = dx * ey - dy * ex;
		const double an = std::sqrt(ax * ax + ay * ay + az * az);
		if (an > 1e-9)
		{
			const double am = std::max(an, 1e-12);
			ax /= am;
			ay /= am;
			az /= am;
		}
		else
		{
			ax = 0.0;
			ay = 0.0;
			az = 0.0;
		}
		const double gain = sine ? std::min(1.0, std::sin(err) / sin_sat) : 1.0;
		const double corr = std::min(err, budget[i] * gain);
		const double ox = ax * corr, oy = ay * corr, oz = az * corr;
		const double th = std::sqrt(ox * ox + oy * oy + oz * oz);
		const double tm = std::max(th, 1e-12);
		const double sh = std::sin(0.5 * th);
		const double bw = std::cos(0.5 * th), bx = sh * (ox / tm), by = sh * (oy / tm), bz = sh * (oz / tm);
		qtot[4 * i] = bw * qw - bx * qx - by * qy - bz * qz;
		qtot[4 * i + 1] = bw * qx + bx * qw + by * qz - bz * qy;
		qtot[4 * i + 2] = bw * qy - bx * qz + by * qw + bz * qx;
		qtot[4 * i + 3] = bw * qz + bx * qy - by * qx + bz * qw;
	}
	apply_rotation(alive_idx, na, down, nd, par, qtot.data(), pos, dirs, term_dir, lat_dir, ref, length, zmin);
}

}
