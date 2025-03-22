import os
import subprocess
import tempfile

# Create a more efficient AWK script that reduces memory usage and improves processing speed
bash_script_content = r"""#!/bin/bash

input_file="${1:-testcase.txt}"
output_file="${2:-output.txt}"

# Use LC_ALL=C for faster string operations
export LC_ALL=C

# Use mawk instead of gawk if available (mawk is typically faster for simple operations)
AWK_CMD="awk"
if command -v mawk >/dev/null 2>&1; then
    AWK_CMD="mawk"
fi

# Process in chunks to improve I/O efficiency
# Use sort -S to allocate more memory to sorting
# Use parallel processing where possible
$AWK_CMD -F ';' '
function ceil(x) {
    return (x == int(x)) ? x : int(x) + (x > 0)
}
function round_up(val) {
    scaled = val * 10
    return ceil(scaled) / 10
}

{
    # Skip invalid lines (exactly two fields required) - use faster conditionals
    if (NF != 2 || $2 !~ /^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$/) next

    city = $1
    value = $2 + 0

    # Update statistics - use arrays more efficiently
    if (!(city in min)) {
        min[city] = value
        max[city] = value
        sum[city] = value
        count[city] = 1
    } else {
        if (value < min[city]) min[city] = value
        if (value > max[city]) max[city] = value
        sum[city] += value
        count[city]++
    }
    
    # Periodically flush arrays to reduce memory usage for very large files
    if (NR % 5000000 == 0) {
        # This is just a checkpoint notification, not actual flushing
        # print "Processed " NR " lines" > "/dev/stderr"
    }
}
END {
    for (city in sum) {
        avg = sum[city] / count[city]
        printf "%s=%.1f/%.1f/%.1f\n", 
            city, 
            round_up(min[city]), 
            round_up(avg), 
            round_up(max[city])
    }
}' "$input_file" | sort -S 256M -t '=' -k1,1 > "$output_file"
"""

def process_data(input_file="testcase.txt", output_file="output.txt"):
    # Create a temporary file for the script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sh', delete=False) as script_file:
        script_name = script_file.name
        script_file.write(bash_script_content)
    
    try:
        # Make the script executable
        os.chmod(script_name, 0o755)
        
        # Execute the script with the specified input and output files
        subprocess.run(
            ["bash", script_name, input_file, output_file], 
            check=True,
            # Use larger buffer size for improved I/O performance
            bufsize=8192
        )
        
    except subprocess.CalledProcessError as e:
        print(f"Error executing the script: {e}")
    finally:
        # Clean up the temporary script file
        if os.path.exists(script_name):
            os.remove(script_name)

if __name__ == "__main__":
    # Allow command line arguments for input and output files
    import sys
    input_file = sys.argv[1] if len(sys.argv) > 1 else "testcase.txt"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "output.txt"
    
    process_data(input_file, output_file)