import math
import mmap
import multiprocessing
from collections import defaultdict

def round_inf(x):
    return math.ceil(x * 10) / 10  

def default_city_data():
    return [float('inf'), float('-inf'), 0.0, 0]

def process_chunk(filename, start_offset, end_offset):
    data = defaultdict(default_city_data)
    try:
        with open(filename, "rb") as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            file_size = len(mm)

            if start_offset >= file_size:
                mm.close()
                return data  # Prevents processing beyond file size

            # Align start_offset: if not at beginning, skip partial line
            if start_offset:
                mm.seek(start_offset)
                nl = mm.find(b'\n')
                if nl == -1:
                    mm.close()
                    return data
                start_offset += nl + 1
                if start_offset >= file_size:
                    mm.close()
                    return data

            end_offset = min(end_offset, file_size)
            mm.seek(end_offset)
            nl = mm.find(b'\n')
            if nl != -1:
                end_offset += nl + 1
            end_offset = min(end_offset, file_size)

            mm.seek(start_offset)
            chunk = mm.read(end_offset - start_offset)
            mm.close()

        for line in chunk.splitlines():
            if not line:
                continue
            try:
                city, score_str = line.split(b';', 1)
                score = float(score_str)
            except (ValueError, IndexError):
                continue  # Skip invalid lines safely

            stats = data[city]
            stats[0] = min(stats[0], score)
            stats[1] = max(stats[1], score)
            stats[2] += score
            stats[3] += 1

    except Exception as e:
        print(f"Error processing chunk {start_offset}-{end_offset}: {e}")
    return data

def merge_data(results):
    final = defaultdict(default_city_data)
    for data in results:
        for city, stats in data.items():
            fstats = final[city]
            fstats[0] = min(fstats[0], stats[0])
            fstats[1] = max(fstats[1], stats[1])
            fstats[2] += stats[2]
            fstats[3] += stats[3]
    return final

def main(input_file_name="testcase.txt", output_file_name="output.txt"):
    try:
        with open(input_file_name, "rb") as f:
            mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
            file_size = len(mm)
            mm.close()
        
        num_procs = min(multiprocessing.cpu_count(), 4)  # Limit max processes
        chunk_size = max(1, file_size // num_procs)  # Prevent zero division
        
        chunks = [(i * chunk_size, file_size if i == num_procs - 1 else (i + 1) * chunk_size)
                  for i in range(num_procs)]

        with multiprocessing.Pool(num_procs) as pool:
            tasks = [(input_file_name, start, end) for start, end in chunks]
            results = pool.starmap(process_chunk, tasks)
        
        final_data = merge_data(results)

        out_lines = []
        for city in sorted(final_data.keys()):
            mn, mx, total, count = final_data[city]
            avg = round_inf(total / count) if count else 0
            out_lines.append(f"{city.decode()}={round_inf(mn):.1f}/{avg:.1f}/{round_inf(mx):.1f}\n")

        with open(output_file_name, "w") as f:
            f.writelines(out_lines)

    except Exception as e:
        print(f"Fatal error in main: {e}")

if _name_ == "_main_":
    main()