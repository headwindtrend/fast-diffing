import sublime
import time
from itertools import accumulate, groupby
from collections import Counter
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

def exclude_common_strings(a, b, depth=0, start_time=0, a_base=0, b_base=0, final=True, max_tolerence=3):
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

	def likeness_terrain_v2(a, b, start_time, max_tolerence):
		if a == b:
			return list(1 for _ in range(len(a))), 0
		len_a, len_b = len(a), len(b)
		if len_a * len_b == 0:
			return list(0 for _ in range(len_a + len_b)), len_a + len_b

		if len_a + len_b < 200:
			print("relatively short, so goes raw.")
			shtr_str = a if len_a <= len_b else b
			lngr_str = b if len_a <= len_b else a
			shtr_len = len_a if len_a <= len_b else len_b
			lngr_len = len_b if len_a <= len_b else len_a
			max_start, max_len, index_of_max = 0, 0, 0
			for i in range(1 - shtr_len, lngr_len):
				css_filled, current_streak_start, current_streak_len = False, 0, 0
				si = i - (lngr_len - shtr_len)
				start, end = round((abs(i) - i) / 2), shtr_len - round((abs(si) + si) / 2)
				for j in range(start, end):
					if time.time() - start_time > max_tolerence:
						return False, False
					if lngr_str[i+j:i+j+1] == shtr_str[j:j+1]:
						if not css_filled:
							current_streak_start, css_filled = j, True
						current_streak_len += 1
						if current_streak_len > max_len:
							index_of_max = i
							max_start = current_streak_start
							max_len = current_streak_len
					else:
						css_filled, current_streak_start, current_streak_len = False, 0, 0
			shtr_adj = 1 if max_start > 0 and max_start + index_of_max > 0 else 0
			shtr_headroom = max_start - shtr_adj
			lngr_adj = 1 if max_start > 0 and max_start + index_of_max > 0 else 0
			lngr_headroom = max_start + index_of_max - lngr_adj
			offset_a = shtr_headroom if len_a <= len_b else lngr_headroom
			offset_b = lngr_headroom if len_a <= len_b else shtr_headroom
		else:

			def my_favorite_member(iterable):
				counter, length = Counter(iterable), len(iterable)
				if counter and counter.most_common(1)[0][1] > 100:
					for k, v in counter.most_common():
						if v < 100:
							print("mfm:", k, v)
							return k
					print("mfm:", k, v)
					return k
				else:
					return counter.most_common(1)[0][0]

			def extract_interval_map(iterable, target_member=" "):
				indices = [i for i, m in enumerate(iterable) if m == target_member]
				indices.insert(0, -1)
				indices.append(len(iterable))
				return [j - i - 1 for i, j in zip(indices, indices[1:])]

			def my_list_get(target_list, target_index, default_value=None):
				return target_list[target_index] if target_index >= 0 and target_index < len(target_list) else default_value

			mfm = my_favorite_member(a if len(a) <= len(b) else b)
			a_map = extract_interval_map(a, mfm)
			b_map = extract_interval_map(b, mfm)
			longer_map = b_map if len(a_map) <= len(b_map) else a_map
			shorter_map = a_map if len(a_map) <= len(b_map) else b_map
			max_start, max_len, index_of_max = 0, 0, 0
			# debug = {}
			for i in range(1 - len(shorter_map), len(longer_map)):
				# debug[i] = []
				css_filled, current_streak_start, current_streak_len = False, 0, 0
				si = i - (len(longer_map) - len(shorter_map))
				start, end = round((abs(i) - i) / 2), len(shorter_map) - round((abs(si) + si) / 2)
				for j in range(start, end):
					if time.time() - start_time > max_tolerence:
						return False, False
					shtr_interval = my_list_get(shorter_map, j, "out of shorter_map range")
					lngr_interval = my_list_get(longer_map, i+j, "out of longer_map range")
					if lngr_interval == shtr_interval:
						# debug[i].append((i+j, j, shorter_map[j]))
						if not css_filled:
							current_streak_start, css_filled = j, True
						current_streak_len += shorter_map[j] + 1
						if current_streak_len > max_len:
							index_of_max = i
							max_start = current_streak_start
							max_len = current_streak_len
					else:
						# debug[i].append((i+j, j, 0))
						css_filled, current_streak_start, current_streak_len = False, 0, 0
			shtr_adj = 1 if max_start > 0 and max_start + index_of_max > 0 else 0
			shtr_headroom = sum(shorter_map[j] + 1 for j in range(max_start)) - shtr_adj
			lngr_adj = 1 if max_start > 0 and max_start + index_of_max > 0 else 0
			lngr_headroom = sum(longer_map[j] + 1 for j in range(max_start + index_of_max)) - lngr_adj
			offset_a = shtr_headroom if len(a_map) <= len(b_map) else lngr_headroom
			offset_b = lngr_headroom if len(a_map) <= len(b_map) else shtr_headroom
			# print("best alignment:")
			# print('  "a" string from pos', offset_a)
			# print('  "b" string from pos', offset_b)
			# adj_a = shtr_adj if len(a_map) <= len(b_map) else lngr_adj
			# adj_b = lngr_adj if len(a_map) <= len(b_map) else shtr_adj
			# adj_a -= 0 if offset_a+max_len+adj_a < len(a) and offset_b+max_len+adj_b < len(b) else 1
			# adj_b -= 0 if offset_a+max_len+adj_a < len(a) and offset_b+max_len+adj_b < len(b) else 1
			# print("  a:", repr(a[offset_a:offset_a+max_len+adj_a]))
			# print("  b:", repr(b[offset_b:offset_b+max_len+adj_b]))

		bao = abs(offset_a - offset_b)
		return [(ca == cb) + 0 for ca, cb in zip(
			a[bao:bao+len_a+len_b] if offset_a > offset_b else a,
			b if offset_a > offset_b else b[bao:bao+len_a+len_b]
		)], bao, offset_a > offset_b or len_a > len_b

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
				max(acc[2], current_streak_length(acc, x) + round(((len(stream) - current_start(acc, x)) % len(stream)) / scale, max_d_len))
			)
		))

		max_encoded = encoded[-1][2]
		length = int(max_encoded)
		start = (len(stream) - round((max_encoded - length) * scale)) % len(stream)
		return ((start, length) if max_encoded else (0, 0)), bao + start

	def find_longest_ones_v2(stream, bao=0, flip_scenario=False):
		if not stream:  # probably due to max_tolerence reached
			return False

		# Track (current_streak_key, current_streak_start, current_streak_length, max_streak_start, max_streak_length)
		groups = [(k, 0, len(list(g)), 0, 0) for k, g in groupby(stream)]
		groups.insert(0, (0, 0, 0, 0, 0))
		result = list(accumulate(
			groups,
			lambda acc, x: (
				x[0],
				acc[1] + acc[2],
				x[2],
				acc[1] + acc[2] if x[0] == 1 and x[2] > acc[4] else acc[3],
				max(acc[4], x[2] if x[0] == 1 else 0)
			)
		))

		start = result[-1][3]
		length = result[-1][4]
		return (((bao if flip_scenario else 0) + start, length) if result and len(result) == len(groups) else (0, 0)), (0 if flip_scenario else bao) + start, len(groups)

	def longest_common_string(a, b, start_time, max_tolerence):
		return find_longest_ones_v2(*likeness_terrain(a, b, start_time, max_tolerence))
		# return find_longest_ones(*likeness_terrain(a, b, start_time, max_tolerence))

	def longest_common_string_v2(a, b, start_time, max_tolerence):
		return find_longest_ones_v2(*likeness_terrain_v2(a, b, start_time, max_tolerence))

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
			(offset, length), pos, streaks_count = lcs_tuple  # the start pos of the common string in the shorter string, and its length, as well as the start pos of the common string in the longer string
			if offset + length == 0:
				return True
			if depth == 0:
				# if fishy (the longest_common_string is relatively short or too many streaks in place), redo it with v2
				shorter_len = min(len_a, len_b)
				if (shorter_len / length) > 10 or (shorter_len / streaks_count) < 20 and shorter_len > 500:
					print("kinda fishy")
					lcs_tuple = longest_common_string_v2(a, b, start_time, max_tolerence)
					if not lcs_tuple:
						return False
					(offset, length), pos, streaks_count = lcs_tuple
					if offset + length == 0:
						return True
			subtract_region(a_list if len_a <= len_b else b_list, offset, offset + length, False)
			subtract_region(b_list if len_a <= len_b else a_list, pos, pos + length, False)
			result = {}
			for index in range(2):
				if not (a_list[index][1] == a_list[index][0] and b_list[index][1] == b_list[index][0] or a[a_list[index][0]:a_list[index][1]] == b[b_list[index][0]:b_list[index][1]]):  # not (both have "end pos == start pos" or with same content)
					result[index] = exclude_common_strings(a[a_list[index][0]:a_list[index][1]], b[b_list[index][0]:b_list[index][1]], depth+1, start_time, a_list[index][0], b_list[index][0], False, max_tolerence)  # call itself for the new targets/regions after "subtraction"
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
