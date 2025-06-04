import sublime
import time
from itertools import accumulate
import math

def subtract_region(regions, start, end, final=True):
	"""Removes the first occurrence of the region (from `start` to `end`) from regions."""
	for i, (rBeg, rEnd) in enumerate(regions):
		if rEnd > rBeg and rBeg <= start < rEnd and end <= rEnd:  # Found the region to modify
			new_regions = []

			if not final or rBeg < start:  # Keep left portion
				new_regions.append((rBeg, start))
			
			if not final or end < rEnd:  # Keep right portion
				new_regions.append((end, rEnd))

			regions[i:i+1] = new_regions  # Directly modify regions
			return  # Exit after modifying the first match

def exclude_common_strings(a, b, start_time=0, a_base=0, b_base=0, final=True, max_tolerence=3):
	if not start_time:
		start_time = time.time()

	def likeness_terrain(a, b, start_time, max_tolerence):
		if a == b:
			return list(1 for _ in range(len(a))), 0
		len_a, len_b = len(a), len(b)
		if len_a * len_b == 0:
			return list(0 for _ in range(len_a + len_b)), len_a + len_b
		if len_a == len_b:
			return [(ca == cb) + 0 for ca, cb in zip(a, b)], 0

		len_delta = abs(len_a - len_b)
		shorter_len = min(len_a, len_b)
		a_is_shorter = len_a == shorter_len
		b_is_shorter = len_b == shorter_len

		bao = 0  # best alignment offset
		least_diff = shorter_len + 1  # set higher than possible max
		# Find the best alignment
		for offset in range(len_delta + 1):
			if time.time() - start_time > max_tolerence:
				return False, False
			beg, end = offset, offset + shorter_len
			mismatch_count = sum(ca != cb for ca, cb in zip(
				a if a_is_shorter else a[beg:end],
				b if b_is_shorter else b[beg:end]
			))
			if mismatch_count < least_diff:
				least_diff = mismatch_count
				bao = offset

		return [(ca == cb) + 0 for ca, cb in zip(
			a if a_is_shorter else a[bao:bao+shorter_len],
			b if b_is_shorter else b[bao:bao+shorter_len]
		)], bao

	def find_longest_ones(stream, bao=0):
		if not stream:  # probably due to max_tolerence reached
			return False

		def current_streak_length(acc, x):
			return (acc[0] + 1) * x[0]

		def current_start(acc, x):
			return acc[1] * x[0] + (x[1] * (acc[0] == 0)) * x[0]

		max_d_len = (int(math.log10(len(stream) - 1)) + 1)
		scale = 10 ** max_d_len  # Auto-scale for start pos encoding
		
		# Track (current_streak_length, current_start, max_encoded)
		encoded = list(accumulate(
			((int(bit), i, 0) for i, bit in enumerate(stream)),
			lambda acc, x: (
				current_streak_length(acc, x),
				current_start(acc, x),
				max(acc[2], current_streak_length(acc, x) + round((len(stream) - current_start(acc, x)) / scale, max_d_len))
			)
		))

		max_encoded = encoded[-1][2]
		length = int(max_encoded)
		start = len(stream) - round((max_encoded - length) * scale)
		return ((start, length) if max_encoded else (0, 0)), bao + start

	def longest_common_string(a, b, start_time, max_tolerence):
		return find_longest_ones(*likeness_terrain(a, b, start_time, max_tolerence))

	len_a, len_b = len(a), len(b)

	if a == b:
		return [
			[] if final else [(a_base, a_base), (a_base + len_a, a_base + len_a)],
			[] if final else [(b_base, b_base), (b_base + len_b, b_base + len_b)]
		]
	if a in b:
		at_pos = b.find(a)
		return [
			[] if final else [(a_base, a_base), (a_base + len_a, a_base + len_a)],
			[(region[0] + b_base, region[1] + b_base) for region in [(0, at_pos), (at_pos + len_a, len_b)] if not final or region[1] > region[0]]
		]
	if b in a:
		at_pos = a.find(b)
		return [
			[(region[0] + a_base, region[1] + a_base) for region in [(0, at_pos), (at_pos + len_b, len_a)] if not final or region[1] > region[0]],
			[] if final else [(b_base, b_base), (b_base + len_b, b_base + len_b)]
		]

	a_list, b_list = [(0, len_a)], [(0, len_b)]

	def exclude_common_strings_core():
		if len_a > 1 and len_b > 1:
			lcs_tuple = longest_common_string(a, b, start_time, max_tolerence)
			if not lcs_tuple:  # max_tolerence reached
				return False
			(offset, length), pos = lcs_tuple  # the start pos of the common string in the shorter string, and its length, as well as the start pos of the common string in the longer string
			if offset + length == 0:
				return True
			subtract_region(a_list if len_a <= len_b else b_list, offset, offset + length, False)
			subtract_region(b_list if len_a <= len_b else a_list, pos, pos + length, False)
			result = {}
			for index in range(2):
				if not (a_list[index][1] == a_list[index][0] and b_list[index][1] == b_list[index][0] or a[a_list[index][0]:a_list[index][1]] == b[b_list[index][0]:b_list[index][1]]):  # not (both have "end pos == start pos" or with same content)
					result[index] = exclude_common_strings(a[a_list[index][0]:a_list[index][1]], b[b_list[index][0]:b_list[index][1]], start_time, a_list[index][0], b_list[index][0], False, max_tolerence)  # call itself for the new targets/regions after "subtraction"
			if result.get(0):  # lhs of the subtracted common string
				a_list[0:1], b_list[0:1] = result[0][0], result[0][1]  # insert the process results of the region into the lists
			if result.get(1):  # rhs of the subtracted common string
				a_list[-1:], b_list[-1:] = result[1][0], result[1][1]  # insert the process results of the region into the lists
			for j in range(len(a_list)-1, -1, -1):  # clean up the lists
				if a_list[j][1] == a_list[j][0] and b_list[j][1] == b_list[j][0] or a[a_list[j][0]:a_list[j][1]] == b[b_list[j][0]:b_list[j][1]]:  # both have "end pos == start pos" or with same content
					a_list[j:j+1], b_list[j:j+1] = [], []  # take this pair (as at `j`) off the lists
		return None

	succeeded = exclude_common_strings_core()

	return [
		[
			(region[0] + a_base, region[1] + a_base)
				for region in a_list
					if not final
						or region[1] > region[0]
		],
		[
			(region[0] + b_base, region[1] + b_base)
				for region in b_list
					if not final
						or region[1] > region[0]
		]
	] + (["Error - time's up, unfinished."] if succeeded == False else [])
