import math
import mmap
import multiprocessing

def round_inf(x):
    return math.ceil(x * 10) / 10  

def process_chunk(filename, start_offset, end_offset):
    data = {}
    with open(filename, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        file_size = len(mm)

        # If start_offset is beyond the file, return empty data
        if start_offset >= file_size:
            mm.close()
            return data

        # Align start_offset: skip partial line
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

        # Align end_offset: include the full line
        end_offset = min(end_offset, file_size)
        mm.seek(end_offset)
        nl = mm.find(b'\n')
        if nl != -1:
            end_offset += nl + 1
        end_offset = min(end_offset, file_size)

        # Read the entire chunk at once
        mm.seek(start_offset)
        chunk = mm.read(end_offset - start_offset)
        mm.close()

    # Process lines using splitlines (fast on bytes)
    for line in chunk.splitlines():
        if not line:
            continue
        try:
            city, score_str = line.split(b';', 1)
            score = float(score_str)
        except Exception:
            continue

        # Use decoded city name as key to avoid repeated decoding
        city_key = city.decode()
        if city_key not in data:
            data[city_key] = [float('inf'), float('-inf'), 0.0, 0]

        stats = data[city_key]
        if score < stats[0]:
            stats[0] = score
        if score > stats[1]:
            stats[1] = score
        stats[2] += score
        stats[3] += 1

    return data

def merge_data(results):
    final = {}
    for data in results:
        for city, stats in data.items():
            if city not in final:
                final[city] = [float('inf'), float('-inf'), 0.0, 0]
            
            fstats = final[city]
            if stats[0] < fstats[0]:
                fstats[0] = stats[0]
            if stats[1] > fstats[1]:
                fstats[1] = stats[1]
            fstats[2] += stats[2]
            fstats[3] += stats[3]
    return final

def main(input_file_name="testcase.txt", output_file_name="output.txt"):
    with open(input_file_name, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        file_size = len(mm)
        mm.close()

    num_procs = multiprocessing.cpu_count()
    chunk_size = file_size // num_procs
    # Compute chunk boundaries
    chunks = [(i * chunk_size, file_size if i == num_procs - 1 else (i + 1) * chunk_size)
              for i in range(num_procs)]
    
    with multiprocessing.Pool(num_procs) as pool:
        tasks = [(input_file_name, start, end) for start, end in chunks]
        results = pool.starmap(process_chunk, tasks)
    
    final_data = merge_data(results)
    
    # Sort cities alphabetically before writing output
    sorted_cities = sorted(final_data.keys())
    out_lines = []
    for city in sorted_cities:
        mn, mx, total, count = final_data[city]
        avg = round_inf(total / count)
        out_lines.append(f"{city}={round_inf(mn):.1f}/{avg:.1f}/{round_inf(mx):.1f}\n")
    
    # Write output in one batch
    with open(output_file_name, "w") as f:
        f.writelines(out_lines)

if __name__ == "__main__":
    main()