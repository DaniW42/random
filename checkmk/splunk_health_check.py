#!/usr/bin/env python3
#
# Checkmk local check for Splunk Forwarder Health
# - Monitors Splunk Health: Acts as a Checkmk local check to monitor the health of a Splunk forwarder.
# - Reads Log Efficiently: Uses the tail command to read only the last 200 lines of the Splunk health log, ensuring it works quickly even on large files.
# - Finds Latest Status: Identifies the most recent block of log entries (all lines with the same timestamp).
# - Determines Worst Status: It checks the color (green, yellow, or red) of all components in that recent block and reports the single worst status (e.g., if one component is red, the whole check is red).
# - Formats for Checkmk: It prints a single line of output for Checkmk with the service name "Splunk Health".
# - Provides Full Details: If the status is "WARN" or "CRIT", the summary line includes the log timestamp and a short problem summary. The detailed output (visible in the Checkmk service) includes the full, raw log lines of all failing components.
#
# Place this script in /usr/lib/check_mk_agent/local/ on your Splunk forwarder host.
# Make sure it is executable: chmod +x /usr/lib/check_mk_agent/local/splunk_health_check.py
#
# Author: Generated with the help of AI! Double-check yourself!
# Date: 2025-11-14

import re
import os
import subprocess

# --- Configuration ---
# Path to the Splunk health log file.
# Adjust this path if your Splunk installation is in a different location.
SPLUNK_HEALTH_LOG = '/opt/splunkforwarder/var/log/splunk/health.log'
# --- End Configuration ---

def parse_attributes(attribute_string):
    """Parses a string of key-value pairs into a dictionary."""
    attributes = {}
    # This regex handles both quoted and unquoted values
    regex = r'([a-zA-Z0-9_]+)=("([^"]*)"|([^"\s]+))'
    matches = re.finditer(regex, attribute_string)
    for match in matches:
        key = match.group(1)
        # Group 3 is for quoted values, Group 4 for unquoted
        value = match.group(3) if match.group(3) is not None else match.group(4)
        attributes[key] = value
    return attributes

def get_latest_log_block(log_file_path):
    """
    Reads the log file and returns the most recent block of health status lines
    and its timestamp. Uses 'tail' for efficiency on large log files.
    """
    try:
        # Run 'tail -n 200' to get only the end of the file.
        process = subprocess.run(
            ['tail', '-n', '200', log_file_path],
            capture_output=True,
            text=True,
            check=False
        )

        if process.returncode != 0:
            # --- MODIFIED: Return (None, None, error) ---
            return None, None, f"Error running 'tail' command: {process.stderr}"

        tailed_lines = process.stdout.strip().split('\n')
        lines = [line for line in tailed_lines if 'PeriodicHealthReporter' in line]

    except IOError as e:
        return None, None, f"Error reading log file: {e}"
    except FileNotFoundError:
        return None, None, "Error: 'tail' command not found. Is this a standard Linux system?"

    if not lines:
        return None, None, "No 'PeriodicHealthReporter' entries found in the last 200 lines of the log."

    last_line = lines[-1]
    timestamp_match = re.match(r'^\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2}\.\d{3} [+-]\d{4}', last_line)
    if not timestamp_match:
        return None, None, "Could not determine timestamp from the last log entry."

    latest_timestamp_prefix = timestamp_match.group(0)

    latest_block = []
    for line in reversed(lines):
        if line.startswith(latest_timestamp_prefix):
            latest_block.insert(0, line)
        else:
            break
            
    # --- MODIFIED: Return (block, timestamp, no error) ---
    return latest_block, latest_timestamp_prefix, None


def main():
    """Main function to perform the check and print Checkmk output."""
    
    # --- MODIFIED: Receive 'timestamp' from function ---
    latest_block, timestamp, error = get_latest_log_block(SPLUNK_HEALTH_LOG)

    if error:
        print(f"3 \"Splunk Health\" - UNKNOWN: {error}")
        return

    if not latest_block:
        print("3 \"Splunk Health\" - UNKNOWN: Could not find a valid health report block in the log.")
        return

    entries_with_raw = []
    for line in latest_block:
        parts = line.split('PeriodicHealthReporter - ')
        if len(parts) > 1:
            raw_attribute_string = parts[1].strip()
            attributes = parse_attributes(raw_attribute_string)
            entries_with_raw.append((attributes, raw_attribute_string))

    if not entries_with_raw:
        print("3 \"Splunk Health\" - UNKNOWN: No attributes parsed from the latest report.")
        return

    color_precedence = {'red': 2, 'yellow': 1, 'green': 0}
    worst_color_str = 'green'
    worst_color_level = 0

    for entry_dict, raw_string in entries_with_raw:
        color_str = entry_dict.get('color', 'green').lower()
        if color_str in color_precedence:
            color_level = color_precedence[color_str]
            if color_level > worst_color_level:
                worst_color_level = color_level
                worst_color_str = color_str

    overall_color = worst_color_str

    status_map = {
        'green': (0, 'OK'),
        'yellow': (1, 'WARN'),
        'red': (2, 'CRIT'),
    }

    status_code, status_text = status_map.get(overall_color, (3, 'UNKNOWN'))

    # --- MODIFIED: Add 'timestamp' to the output summary ---
    output_summary = f"{status_text}: Overall status is {overall_color.upper()} (Log Time: {timestamp})"

    problem_lines_raw = []
    problems_summary_list = [] # For the one-line summary

    if status_code > 0:
        # Collect details for problematic components
        for entry_dict, raw_string in entries_with_raw:
            if entry_dict.get('color', 'green').lower() != 'green':
                problem_lines_raw.append(raw_string)
                color = entry_dict.get('color', 'N/A').upper()
                name = entry_dict.get('feature') or entry_dict.get('node_path') or 'Component'
                problems_summary_list.append(f"[{color}] {name}")

    if problem_lines_raw:
        problems_summary = ", ".join(problems_summary_list[:2])
        output_summary += f" (Issues: {problems_summary}...)"

        # Join the summary and the detail lines with the literal '\\n'
        final_output = output_summary + "\\n" + "\\n".join(problem_lines_raw)
    else:
        final_output = output_summary

    # Print the final output as ONE single line, with the service name quoted.
    print(f"{status_code} \"Splunk Health\" - {final_output}")


if __name__ == '__main__':
    main()
