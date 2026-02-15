
import subprocess
import sys

def debug_copilot():
    print("running... copilot -p 'hello'")
    try:
        # Try basic command
        res = subprocess.run(['copilot', '-p', 'hello'], 
                             capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"Return Code: {res.returncode}")
        print(f"STDOUT: '{res.stdout}'")
        print(f"STDERR: '{res.stderr}'")
        
        # Try with --allow-all-tools
        print("\nrunning... copilot -p 'hello' --allow-all-tools")
        res = subprocess.run(['copilot', '-p', 'hello', '--allow-all-tools'], 
                             capture_output=True, text=True, encoding='utf-8', errors='replace')
        print(f"Return Code: {res.returncode}")
        print(f"STDOUT: '{res.stdout}'")
        print(f"STDERR: '{res.stderr}'")

    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_copilot()
