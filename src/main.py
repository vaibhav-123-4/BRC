import math
import mmap
import multiprocessing
import struct
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

def round_inf(x):
    return math.ceil(x * 10) / 10  

def process_chunk(filename, start_offset, end_offset):
    """Process a chunk using multithreading."""
    with open(filename, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        size = len(mm)

        # Align to newline
        if start_offset != 0:
            while start_offset < size and mm[start_offset] != ord('\n'):
                start_offset += 1
            start_offset += 1

        if end_offset < size:
            while end_offset < size and mm[end_offset] != ord('\n'):
                end_offset += 1
            end_offset += 1
        
        chunk = mm[start_offset:end_offset]
        mm.close()

    # Split the chunk into two halves
    mid = len(chunk) // 2
    while mid < len(chunk) and chunk[mid] != ord('\n'):
        mid += 1
    mid += 1

    sub_chunks = [chunk[:mid], chunk[mid:]]
    
    def process_sub_chunk(sub_chunk):
        """Threaded function to process part of the chunk."""
        data = {}
        pos = 0
        end = len(sub_chunk)

        while pos < end:
            semicolon = sub_chunk.find(b';', pos)
            newline = sub_chunk.find(b'\n', semicolon)

            if semicolon == -1 or newline == -1:
                break  # End of valid data

            city = sub_chunk[pos:semicolon]
            score = float(sub_chunk[semicolon + 1:newline])

            if city in data:
                mn, mx, total, count = data[city]
                data[city] = (min(mn, score), max(mx, score), total + score, count + 1)
            else:
                data[city] = (score, score, score, 1)

            pos = newline + 1
        
        return data

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = executor.map(process_sub_chunk, sub_chunks)

    # Merge thread results
    final_data = {}
    for result in results:
        for city, stats in result.items():
            if city in final_data:
                mn, mx, total, count = final_data[city]
                final_data[city] = (min(mn, stats[0]), max(mx, stats[1]), total + stats[2], count + stats[3])
            else:
                final_data[city] = stats
    
    return final_data

def merge_data(results):
    """Merge results from multiple processes."""
    final_data = {}
    for data in results:
        for city, stats in data.items():
            if city in final_data:
                mn, mx, total, count = final_data[city]
                final_data[city] = (min(mn, stats[0]), max(mx, stats[1]), total + stats[2], count + stats[3])
            else:
                final_data[city] = stats
    return final_data

def main(input_file_name="testcase.txt", output_file_name="output.txt"):
    """Main function to process the file with maximum performance."""
    with open(input_file_name, "rb") as f:
        file_size = f.seek(0, 2)

    num_procs = min(multiprocessing.cpu_count(), 8)  # Use at most 8 cores
    chunk_size = file_size // num_procs
    chunks = [(i * chunk_size, (i + 1) * chunk_size if i < num_procs - 1 else file_size)
              for i in range(num_procs)]

    with multiprocessing.Pool(num_procs) as pool:
        tasks = [(input_file_name, start, end) for start, end in chunks]
        results = pool.starmap(process_chunk, tasks)

    final_data = merge_data(results)

    # Write output
    with open(output_file_name, "w") as f:
        f.writelines(
            f"{city.decode()}={round_inf(mn):.1f}/{round_inf(total / count):.1f}/{round_inf(mx):.1f}\n"
            for city, (mn, mx, total, count) in sorted(final_data.items())
        )

if _name_ == "_main_":
    main()