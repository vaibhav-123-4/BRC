import math
import mmap
import multiprocessing
from collections import defaultdict

def round_inf(x):
    """
    Rounds a float upward to the nearest 0.1.
    
    Parameters:
        x (float): The number to round.
        
    Returns:
        float: The rounded value.
    """
    return math.ceil(x * 10) / 10

def default_city_data():
    """
    Default data structure for storing city statistics.
    
    Returns:
        list: [min_value, max_value, total_score, count]
    """
    return [float('inf'), float('-inf'), 0.0, 0]

def process_chunk(filename, start_offset, end_offset):
    """
    Processes a file chunk, aggregating statistics per city.
    
    Parameters:
        filename (str): The path to the input file.
        start_offset (int): Starting byte offset of the chunk.
        end_offset (int): Ending byte offset of the chunk.
        
    Returns:
        defaultdict: Mapping from city (bytes) to statistics list.
    """
    data = defaultdict(default_city_data)
    with open(filename, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            size = len(mm)
            # Adjust start_offset to the next newline if not at beginning.
            if start_offset != 0:
                newline_pos = mm.find(b'\n', start_offset)
                if newline_pos != -1:
                    start_offset = newline_pos + 1

            # Adjust end_offset to include the whole line.
            newline_pos = mm.find(b'\n', end_offset)
            if newline_pos != -1:
                end_offset = newline_pos + 1
            else:
                end_offset = size

            # Extract the chunk.
            chunk = mm[start_offset:end_offset]

    # Process each line in the chunk.
    for line in chunk.split(b'\n'):
        if not line:
            continue
        
        semicolon_pos = line.find(b';')
        if semicolon_pos == -1:
            continue
        
        city = line[:semicolon_pos]
        score_str = line[semicolon_pos + 1:]
        try:
            score = float(score_str)
        except ValueError:
            continue
        
        entry = data[city]
        entry[0] = min(entry[0], score)
        entry[1] = max(entry[1], score)
        entry[2] += score
        entry[3] += 1
    
    return data

def merge_data(data_list):
    """
    Merges multiple dictionaries of city statistics into one.
    
    Parameters:
        data_list (list): List of defaultdicts with city data.
        
    Returns:
        defaultdict: Merged city data.
    """
    final = defaultdict(default_city_data)
    for data in data_list:
        for city, stats in data.items():
            final_entry = final[city]
            final_entry[0] = min(final_entry[0], stats[0])
            final_entry[1] = max(final_entry[1], stats[1])
            final_entry[2] += stats[2]
            final_entry[3] += stats[3]
    return final

def main(input_file_name="testcase.txt", output_file_name="output.txt"):
    """
    Main routine to process the file and output the computed statistics.
    
    Parameters:
        input_file_name (str): The input file path.
        output_file_name (str): The output file path.
    """
    # Determine file size.
    with open(input_file_name, "rb") as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            file_size = len(mm)
    
    # Define the number of processes and chunk size.
    num_procs = multiprocessing.cpu_count() * 2
    chunk_size = file_size // num_procs
    chunks = [
        (i * chunk_size, (i + 1) * chunk_size if i < num_procs - 1 else file_size)
        for i in range(num_procs)
    ]

    # Process file chunks in parallel.
    with multiprocessing.Pool(num_procs) as pool:
        tasks = [(input_file_name, start, end) for start, end in chunks]
        results = pool.starmap(process_chunk, tasks)
    
    final_data = merge_data(results)
    
    # Prepare output lines sorted by city name.
    out = []
    for city in sorted(final_data.keys()):
        mn, mx, total, count = final_data[city]
        avg = round_inf(total / count)
        out.append(f"{city.decode()}={round_inf(mn):.1f}/{avg:.1f}/{round_inf(mx):.1f}\n")
    
    # Write the results to the output file.
    with open(output_file_name, "w") as f:
        f.writelines(out)

if __name__ == "__main__":
    main()
