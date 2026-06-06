# Static Analysis of Meschach (cppcheck)

Static analysis of the **Meschach** linear-algebra library that `weeks` links
against at build time. Meschach source is **not** vendored in this repository;
it is provided by the system `libmeschach-dev` package and resolved at link
time. This report analyzes the upstream library source for due diligence, not
code maintained here.

## Method

- **Tool:** cppcheck 2.13.0
- **Date:** 2026-06-06
- **Source:** Debian source package `meschach 1.2b-17build1` (matches the linked
  `libmeschach` version), reconstructed with `dpkg-source -x` (orig tarball +
  Debian patches applied).
- **Scope:** the 65 library `.c` files. The 8 torture/tutorial harnesses
  (`*tort.c`, `torture.c`, `tutorial.c`, `tutadv.c`) were excluded — they are
  test drivers, not library code.
- **Invocation:**
  ```
  cppcheck --enable=warning,style,performance,portability \
           --std=c89 --language=c -I . \
           --suppress=missingIncludeSystem --inconclusive \
           --xml --xml-version=2 <library .c files>
  ```

## Headline

**922 findings:** 10 error, 355 warning, 537 style, 20 portability.

After triaging the 10 error-severity findings against the source, **none are
real defects on any code path `weeks` exercises.** `weeks` uses only the dense
complex routines (`zm_get`, `zm_inverse`, `v_get`); the one genuine (low-impact)
bug is in sparse code that `weeks` never calls.

## The 10 error-severity findings, triaged

Every error-severity finding was read against the source. They fall into three
groups.

### 1. False positives — non-returning `error()` macro (6 findings)

| Location | id |
|---|---|
| memory.c:67 | doubleFree |
| memory.c:67 | deallocuse |
| memory.c:149 | deallocret |
| zmemory.c:96 | doubleFree |
| zmemory.c:96 | deallocuse |
| zmemory.c:144 | deallocret |

These sit on out-of-memory paths shaped like:

```c
{ free(matrix->base); free(matrix); error(E_MEM,"m_get"); }
```

cppcheck assumes `error()` returns and that execution falls through to reuse the
freed pointer. It does not: `error()` (`err.h:73`) expands to `ev_err()`, which
on a real (non-warning) error always `longjmp`s, `abort`s, or `exit`s and
**never returns** (`err.c`). There is no actual double-free or use-after-free.
These are analyzer false positives caused by cppcheck not modeling the
non-returning macro. The same blind spot inflates the `nullPointerRedundantCheck`
style count (see appendix).

### 2. Real but low-impact — realloc-on-OOM leak (3 findings)

| Location | id |
|---|---|
| spchfctr.c:167 | memleakOnRealloc |
| spchfctr.c:168 | memleakOnRealloc |
| spchfctr.c:169 | memleakOnRealloc |

```c
scan_row = (int *)realloc((char *)scan_row, new_len*sizeof(int));
```

Classic mistake: if `realloc` fails it returns `NULL` and the original buffer is
leaked. Genuinely a latent bug, but it only triggers on allocation failure,
which is immediately followed by `error(E_MEM,"set_scan")` aborting the process
— so the leak is moot in practice. This is in the **sparse Cholesky** code path.

### 3. Configuration noise (1 finding)

| Location | id |
|---|---|
| zvecop.c:147 | unknownMacro |

cppcheck needs the `zv_map` macro defined to parse the region. Not a bug.

## Relevance to `weeks`

**None of the above affects `weeks`.** `weeks` calls only dense complex
routines — `zm_get`, `zm_inverse`, `v_get`:

- The memory.c / zmemory.c findings are false positives (the routines are
  correct).
- The one real finding (`spchfctr.c`) is in sparse Cholesky code, which `weeks`
  never invokes.

The library is clean for this project's purposes.

## The remaining 912 findings (warning / style / portability)

Typical early-1990s K&R C idioms; not actionable for a third-party dependency
linked at build time:

- `nullPointerRedundantCheck` (301) — largely the same non-returning-`error()`
  blind spot.
- `variableScope` (251) — variables declarable in a tighter scope.
- `funcArgNamesDifferent` (110) — prototype vs definition parameter names differ.
- `constParameterPointer` / `constVariablePointer` (79) — missing `const`.
- `unsignedLessThanZero` (30), `invalidPrintfArgType_sint` (25),
  `invalidPointerCast` (20), `selfAssignment` (17), and a long tail.

## Conclusion

Meschach 1.2b is clean for `weeks`: **zero real defects on any code path
`weeks` exercises.** The single genuine bug (a realloc-on-OOM leak in unused
sparse code) is harmless in practice. The 10 error-severity findings are 6
false positives + 3 benign + 1 configuration note. The ~900 remaining
warning/style items are legacy-C idioms in upstream code this project does not
maintain.

## Appendix — full finding counts by check id

```
301 nullPointerRedundantCheck
251 variableScope
110 funcArgNamesDifferent
 54 constParameterPointer
 30 unsignedLessThanZero
 25 invalidPrintfArgType_sint
 25 constVariablePointer
 22 unreadVariable
 20 invalidPointerCast
 17 selfAssignment
 13 unusedVariable
  8 invalidScanfArgType_int
  8 constParameterCallback
  7 redundantAssignment
  4 shadowVariable
  4 knownConditionTrueFalse
  3 memleakOnRealloc
  2 moduloofone
  2 duplicateCondition
  2 doubleFree
  2 deallocuse
  2 deallocret
  2 arrayIndexThenCheck
  1 unknownMacro
  1 uninitvar
  1 truncLongCastAssignment
  1 negativeIndex
  1 invalidPrintfArgType_float
  1 constVariable
  1 constParameter
  1 arrayIndexOutOfBoundsCond
```

## Reproducing

```bash
# 1. Fetch and reconstruct the Debian source (matches linked libmeschach version)
cd /tmp && mkdir meschach-analysis && cd meschach-analysis
BASE=http://archive.ubuntu.com/ubuntu/pool/universe/m/meschach
curl -O $BASE/meschach_1.2b-17build1.dsc
curl -O $BASE/meschach_1.2b.orig.tar.gz
curl -O $BASE/meschach_1.2b-17build1.debian.tar.xz
dpkg-source -x meschach_1.2b-17build1.dsc src

# 2. Analyze library sources (exclude torture/tutorial harnesses)
cd src
cppcheck --enable=warning,style,performance,portability \
         --std=c89 --language=c -I . \
         --suppress=missingIncludeSystem --inconclusive \
         $(ls *.c | grep -vE '(tort|torture|tutorial|tutadv)\.c$')
```
