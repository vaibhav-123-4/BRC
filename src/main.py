import math
import mmap
import multiprocessing
from collections import defaultdict
from multiprocessing import shared_memory

def round_inf(x):
    return math.ceil(x * 10) / 10  

def process_chunk(shm_name, start_offset, end_offset, size):
    # Attach to the shared memory block
    shm = shared_memory.SharedMemory(name=shm_name)
    mm = mmap.mmap(-1, size, access=mmap.ACCESS_READ, offset=0)
    mm.write(shm.buf)
    mm.seek(0)

    data = {}
    if start_offset != 0:
        while start_offset < size and mm[start_offset] != ord('\n'):
            start_offset += 1
        start_offset += 1
    
    end = end_offset
    while end < size and mm[end] != ord('\n'):
        end += 1
    if end < size:
        end += 1
    
    chunk = mm[start_offset:end]
    mm.close()

    for line in chunk.split(b'\n'):
        if not line:
            continue
        
        parts = line.split(b';')
        if len(parts) != 2:
            continue
        
        city, score_str = parts
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        if city not in data:
            data[city] = [float('inf'), float('-inf'), 0.0, 0]
        
        entry = data[city]
        entry[0] = min(entry[0], score)
        entry[1] = max(entry[1], score)
        entry[2] += score
        entry[3] += 1
    
    shm.close()
    return data

def merge_data(data_list):
    final = {}
    for data in data_list:
        for city, stats in data.items():
            if city not in final:
                final[city] = [float('inf'), float('-inf'), 0.0, 0]
            
            final_entry = final[city]
            final_entry[0] = min(final_entry[0], stats[0])
            final_entry[1] = max(final_entry[1], stats[1])
            final_entry[2] += stats[2]
            final_entry[3] += stats[3]
    return final

def main(input_file_name="testcase.txt", output_file_name="output.txt"):
    # Determine file size and split into chunks
    with open(input_file_name, "rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        file_size = len(mm)
        
        # Create shared memory and copy file data
        shm = shared_memory.SharedMemory(create=True, size=file_size)
        shm.buf[:file_size] = mm[:file_size]
        mm.close()
    
    num_procs = multiprocessing.cpu_count() * 2  
    chunk_size = file_size // num_procs
    chunks = [(i * chunk_size, (i + 1) * chunk_size if i < num_procs - 1 else file_size)
              for i in range(num_procs)]
    
    with multiprocessing.Pool(num_procs) as pool:
        tasks = [(shm.name, start, end, file_size) for start, end in chunks]
        results = pool.starmap(process_chunk, tasks)
    
    shm.close()
    shm.unlink()
    
    final_data = merge_data(results)
    
    out = []
    for city in sorted(final_data.keys()):
        mn, mx, total, count = final_data[city]
        avg = round_inf(total / count)
        out.append(f"{city.decode()}={round_inf(mn):.1f}/{avg:.1f}/{round_inf(mx):.1f}\n")
    
    with open(output_file_name, "w") as f:
        f.writelines(out)

if __name__ == "__main__":
    main()