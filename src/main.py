import multiprocessing as mp
import os
import math

NUM_WORKERS = 2  # Explicitly set for a 2-core CPU
CHUNK_SIZE = 100_000  # Process 100k lines per batch for efficiency

def ceil_round(value, decimals=1):
    """Rounds a number upward (toward +∞) to IEEE 754 standard."""
    factor = 10 ** decimals
    return math.ceil(value * factor) / factor

def process_chunk(chunk):
    """Processes a chunk of lines and returns aggregated city statistics."""
    local_data = {}

    for line in chunk:
        try:
            city, score_str = line.strip().split(";")
            score = float(score_str)
        except ValueError:
            continue  # Skip malformed data

        if city in local_data:
            mn, total, mx, count = local_data[city]
            local_data[city] = (min(mn, score), total + score, max(mx, score), count + 1)
        else:
            local_data[city] = (score, score, score, 1)

    return local_data

def process_file(input_filename="testcase.txt", output_filename="output.txt"):
    """Efficiently processes large files in streaming mode using multiprocessing."""
    manager = mp.Manager()
    city_data = manager.dict()  # Shared dictionary for multiprocessing

    def update_global_data(local_data):
        """Merge local process data into global dictionary efficiently."""
        for city, (mn, total, mx, count) in local_data.items():
            if city in city_data:
                old_mn, old_total, old_mx, old_count = city_data[city]
                city_data[city] = (min(old_mn, mn), old_total + total, max(old_mx, mx), old_count + count)
            else:
                city_data[city] = (mn, total, mx, count)

    pool = mp.Pool(NUM_WORKERS)
    chunk = []

    # Stream through file line-by-line to avoid high memory usage
    with open(input_filename, "r", buffering=2**20) as infile:
        for line in infile:
            chunk.append(line)
            if len(chunk) >= CHUNK_SIZE:
                pool.apply_async(process_chunk, (chunk,), callback=update_global_data)
                chunk = []

        if chunk:  # Process any remaining lines
            pool.apply_async(process_chunk, (chunk,), callback=update_global_data)

    pool.close()
    pool.join()

    # Write results efficiently
    with open(output_filename, "w") as outfile:
        for city in sorted(city_data.keys()):
            mn, total, mx, count = city_data[city]
            mean = total / count
            outfile.write(f"{city}={ceil_round(mn, 1):.1f}/"
                          f"{ceil_round(mean, 1):.1f}/"
                          f"{ceil_round(mx, 1):.1f}\n")

if __name__ == "__main__":
    process_file()
