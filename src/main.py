"""Myers O(ND) diff (linear-space, middle-snake version).

    python main.py lines     A B   -> Part A: minimal line diff
    python main.py highlight A B   -> Part B: line diff + changed-character ranges
"""
import sys


# ----------------------------------------------------------------------
# Core: Myers diff on two lists of non-negative ints.
# Returns two bytearrays: del_flags (len(a)) and ins_flags (len(b)),
# where 1 means "this element is deleted from a" / "inserted into b".
# ----------------------------------------------------------------------
def _middle(a, b):
    """Find the middle snake of a and b (both non-empty, no common
    prefix/suffix). Returns (x, y) = a split point on an optimal path,
    or None if none was found."""
    n = len(a)
    m = len(b)
    ra = a[::-1]
    rb = b[::-1]
    # Distinct sentinels so snake loops need no bounds checks.
    a.append(-1)
    ra.append(-1)
    b.append(-2)
    rb.append(-2)

    max_d = (n + m + 1) // 2
    off = max_d + 1
    size = 2 * max_d + 4
    v1 = [-1] * size  # forward furthest-reaching x per diagonal
    v2 = [-1] * size  # backward furthest-reaching x per diagonal
    v1[off + 1] = 0
    v2[off + 1] = 0
    delta = n - m
    front = delta & 1
    k1s = k1e = k2s = k2e = 0

    for d in range(max_d + 1):
        # ---------------- forward ----------------
        for k1 in range(-d + k1s, d - k1e + 1, 2):
            ko = off + k1
            if k1 == -d or (k1 != d and v1[ko - 1] < v1[ko + 1]):
                x = v1[ko + 1]
            else:
                x = v1[ko - 1] + 1
            y = x - k1
            if x > n:
                v1[ko] = x
                k1e += 2
                continue
            if y > m:
                v1[ko] = x
                k1s += 2
                continue
            while a[x] == b[y]:  # follow the snake
                x += 1
                y += 1
            v1[ko] = x
            if front:
                k2o = off + delta - k1
                if 0 <= k2o < size:
                    x2 = v2[k2o]
                    if x2 != -1 and x >= n - x2:
                        return x, y
        # ---------------- backward ----------------
        for k2 in range(-d + k2s, d - k2e + 1, 2):
            ko = off + k2
            if k2 == -d or (k2 != d and v2[ko - 1] < v2[ko + 1]):
                x = v2[ko + 1]
            else:
                x = v2[ko - 1] + 1
            y = x - k2
            if x > n:
                v2[ko] = x
                k2e += 2
                continue
            if y > m:
                v2[ko] = x
                k2s += 2
                continue
            while ra[x] == rb[y]:
                x += 1
                y += 1
            v2[ko] = x
            if not front:
                k1o = off + delta - k2
                if 0 <= k1o < size:
                    x1 = v1[k1o]
                    if x1 != -1 and x1 >= n - x:
                        return x1, x1 - (k1o - off)
    return None


def _solve(a, b, rd, ri):
    one = b"\x01"
    stack = [(0, len(a), 0, len(b))]
    while stack:
        alo, ahi, blo, bhi = stack.pop()
        # strip common prefix / suffix
        while alo < ahi and blo < bhi and a[alo] == b[blo]:
            alo += 1
            blo += 1
        while alo < ahi and blo < bhi and a[ahi - 1] == b[bhi - 1]:
            ahi -= 1
            bhi -= 1
        if alo == ahi:
            if blo < bhi:
                ri[blo:bhi] = one * (bhi - blo)
            continue
        if blo == bhi:
            rd[alo:ahi] = one * (ahi - alo)
            continue
        res = _middle(a[alo:ahi], b[blo:bhi])
        if res is None:  # safety net, should not happen
            rd[alo:ahi] = one * (ahi - alo)
            ri[blo:bhi] = one * (bhi - blo)
            continue
        x, y = res
        stack.append((alo + x, ahi, blo + y, bhi))
        stack.append((alo, alo + x, blo, blo + y))


def diff_seq(a, b):
    """Minimal edit script between sequences a and b of non-negative ints."""
    na, nb = len(a), len(b)
    sa = set(a)
    sb = set(b)
    # Elements that occur in only one sequence can never match: they are
    # always deleted / inserted. Remove them to shrink the real problem.
    ia = [i for i, x in enumerate(a) if x in sb]
    ib = [j for j, x in enumerate(b) if x in sa]
    dflags = bytearray(b"\x01") * na
    iflags = bytearray(b"\x01") * nb
    if ia and ib:
        ra = [a[i] for i in ia]
        rb = [b[j] for j in ib]
        rd = bytearray(len(ra))
        ri = bytearray(len(rb))
        _solve(ra, rb, rd, ri)
        for p, i in enumerate(ia):
            if not rd[p]:
                dflags[i] = 0
        for p, j in enumerate(ib):
            if not ri[p]:
                iflags[j] = 0
    elif ia or ib:
        pass  # nothing can match; everything stays deleted/inserted
    return dflags, iflags


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def read_lines(path):
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    return lines


def ranges(flags):
    out = []
    n = len(flags)
    p = flags.find(1)
    while p != -1:
        q = flags.find(0, p)
        if q == -1:
            q = n
        out.append("%d-%d" % (p, q))
        p = flags.find(1, q) if q < n else -1
    return ",".join(out) if out else "."


def highlight(la, lb):
    if la == lb:
        return b"? . | ."
    sa = la.decode("utf-8", "replace")
    sb = lb.decode("utf-8", "replace")
    ca = [ord(c) for c in sa]
    cb = [ord(c) for c in sb]
    d, i = diff_seq(ca, cb)
    return ("? %s | %s" % (ranges(d), ranges(i))).encode("ascii")


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("lines", "highlight"):
        sys.stderr.write("usage: main.py lines|highlight A B\n")
        return 2
    hl = sys.argv[1] == "highlight"
    try:
        A = read_lines(sys.argv[2])
        B = read_lines(sys.argv[3])
    except OSError as e:
        sys.stderr.write("error: cannot read input file: %s\n" % e)
        return 2

    ids = {}
    ia = [ids.setdefault(l, len(ids)) for l in A]
    ib = [ids.setdefault(l, len(ids)) for l in B]
    dflags, iflags = diff_seq(ia, ib)
    n, m = len(A), len(B)

    out = []
    i = j = 0
    while i < n or j < m:
        if (i < n and dflags[i]) or (j < m and iflags[j]):
            i2 = dflags.find(0, i) if i < n else n
            if i2 == -1:
                i2 = n
            j2 = iflags.find(0, j) if j < m else m
            if j2 == -1:
                j2 = m
            if i2 > i:
                out.append(b"-" + b"\n-".join(A[i:i2]) + b"\n")
            if j2 > j:
                if not hl:
                    out.append(b"+" + b"\n+".join(B[j:j2]) + b"\n")
                else:
                    pairs = min(i2 - i, j2 - j)
                    for t in range(j2 - j):
                        lb = B[j + t]
                        out.append(b"+" + lb + b"\n")
                        if t < pairs:
                            out.append(highlight(A[i + t], lb) + b"\n")
            i, j = i2, j2
        else:
            e1 = dflags.find(1, i) if i < n else n
            if e1 == -1:
                e1 = n
            e2 = iflags.find(1, j) if j < m else m
            if e2 == -1:
                e2 = m
            r = min(e1 - i, e2 - j)
            if r <= 0:
                break
            out.append(b" " + b"\n ".join(A[i:i + r]) + b"\n")
            i += r
            j += r

    sys.stdout.buffer.write(b"".join(out))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
