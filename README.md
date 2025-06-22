# Fast Real-Time Diffing for Text Editors

## ✂️ `exclude_common_strings()`

A custom diffing function designed for real-time text editing environments, particularly when working within a frequently triggered event or similar setups where performance is crucial.

## ⚡ Performance Snapshot

To give you a rough idea of how fast this function is:

In my typical usage `exclude_common_strings()` mostly runs **10x faster** than Python’s `difflib` in the same scenarios.

This is based on informal but repeated benchmarking in the context of Sublime Text’s `on_modified()` event, where delays are especially noticeable. For small to medium edits, the improvement in latency is material and immediately noticeable in practice.

---

## 🔍 Why This Exists

While developing a Sublime Text plugin for **selective undo**, I ran into a key challenge:
I needed a way to quickly and accurately figure out **what changed** every time the `on_modified()` event fired.

Most existing solutions (like Python’s built-in `difflib`) are very flexible — but **too slow** for what I needed. My environment is lightweight:

> 🖥️ Intel Atom Z3735F, 2GB RAM

> ✍️ Targeting real-time performance in Sublime’s editor loop

That meant I couldn’t afford to run a full-blown diff library in `on_modified()` without sacrificing responsiveness. So I wrote a series of ad hoc tools — `find_diffpoint()`, `simple_diffing()`, `alike()` — all trying to capture edit diffs quickly — but eventually built a more capable and still-performant function:

### ✅ `exclude_common_strings()`

This function works by recursively subtracting common substrings from the inputs, progressively isolating regions of difference.

---

### Key Characteristics

* 🚀 Real-time diffing becomes viable in responsiveness-critical applications
* 🔁 Recursively narrows diff regions by finding and removing common blocks
* ⌛ Optional timeout-based cutoff
* 📐 Region-based output, compatible with editor APIs

---

## 🧪 Example

```python
before = "The quick brown fox jumps over the lazy dog."
after  = "The quick red fox leapt over the lazy dog."

output = exclude_common_strings(before, after)

# Output structure:
# [regions in 'before'], [regions in 'after']
```

Example result:

```python
[
  [(10, 15), (20, 25)],  # From 'before'
  [(10, 13), (18, 23)]   # From 'after'
]
```

This identifies precise changes, which you can then highlight, analyze, or revert.

---

## ⚖️ Why Not Use `difflib`?

Honestly, I didn’t benchmark formally or try to outperform it in every case. I simply found `difflib` too slow in the tight, real-time loop I was working with. This function hits a sweet spot for:

* small to medium edits
* rapid feedback
* my specific tooling needs

That’s all it needs to be.

---

## 🧠 Smarter Alignment: A New Heuristic (June 22, 2025)

### 🔍 Why This Was Needed
The original exclude_common_strings() used a sliding-window mechanism to detect common substrings. This worked well — until both strings were the same length (or their length difference was smaller than the displacement of the common region) and the common region was displaced.

Example:
```
a = "Why the quick brown fox jumped over the lazy dog? Bored?"
b = "The quick brown fox jumped over the lazy dog, who cares!"
```
These strings clearly share "he quick brown fox jumped over the lazy dog", but the sliding approach fails to detect it — because when both strings are the same length, no sliding occurs.
This rare case is unlikely during typical editing events (e.g., tracked via Sublime's `on_modified()`), since real-time edits usually:
* Cannot make multiple distinct modifications at one go
* Displacement would not greater than length difference
* Or no displacement at all

However, in broader diffing applications (e.g., document comparison), this can happen — so a fix was warranted.

---

### 🛠️ The Fix: Interval-Mapped Alignment
I introduced a fallback alignment method using interval maps based on a frequently occurring character (typically a space):
* Identify the most common character (limited to ~100 instances for performance).
* Extract interval maps — counts of characters between each occurrence.
* Slide the shorter map over the longer one to find the best alignment.
* Compare regions based on matching intervals and reconstruct matching spans.

This technique is effective in uncovering displaced common substrings even when the original sliding method fails.

---

### ⚙️ Smart Switching
This new approach is used only when needed, based on a heuristic check:
* If the detected common region is suspiciously short, or
* If the mismatch streak density seems abnormally high

These "fishy" signals trigger the fallback. Otherwise, the faster, original sliding method is used — keeping typical performance optimal.

---

### 🚀 Performance Snapshot
```
before = sublime.get_clipboard()  # contains a block of text with 10000 characters copied from any typical text files
after  = before[1000:3000] + before[5000:10000] + before[:1000] + before[3000:5000]

exclude_common_strings(before, after)
# Output: [[(0, 1000), (3000, 5000)], [(7000, 10000)]]
# Elapsed time: ~0.34s

# Compare with difflib:
SequenceMatcher(None, before, after).get_opcodes()
# Output: [('delete', 0, 1000, 0, 0), ('equal', 1000, 3000, 0, 2000), ('insert', 3000, 3000, 2000, 8000), ('equal', 3000, 5000, 8000, 10000), ('delete', 5000, 10000, 10000, 10000)]
# Elapsed time: ~0.79s
```
✅ My method:
* Faster (~2×)
* More accurate, finding the true longest common block (5,000 characters)

---

### ✨ TL;DR
* Problem: Sliding window failed when both strings were the same length and contained displaced common content.
* Fix: Interval-based alignment using character distribution.
* Behavior: Smart fallback — used only when the match looks suspicious.
* For applications other than real-time editing tracking, this new method should be the default instead. (yes, it's indeed mostly slower than the original sliding-window method but it's more robust on the other hand. so, for applications less sensitive to response time, this could be the better choice.)

---

## 📁 Status

This is currently part of a broader plugin project. Contributions, bug reports, or performance comparisons are welcome.

---

## 📜 License

MIT — do whatever you want, but attribution is appreciated.

# If you appreciate my work, i will be very grateful if you can support my work by making small sum donation thru PayPal with `Send payment to` entered as `headwindtrend@gmail.com`. Thank you very much for your support.
