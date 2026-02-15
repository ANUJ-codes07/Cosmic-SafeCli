
import subprocess
import time

def test_copilot():
    print("Testing copilot with --model gpt-4.1 ...")
    start = time.time()
    try:
        # Using explicit path or just 'copilot'
        completed = subprocess.run(
            ['copilot', '--prompt', 'test', '--model', 'gpt-4.1'],
            capture_output=True, text=True, timeout=20,
            encoding='utf-8', errors='replace'
        )
        print(f"Process completed in {time.time() - start:.2f}s")
        print("STDOUT:", completed.stdout)
        print("STDERR:", completed.stderr)
        print("Return Code:", completed.returncode)
    except subprocess.TimeoutExpired as e:
        print(f"Timeout expired after {time.time() - start:.2f}s")
        print("STDOUT (partial):", e.stdout)
        print("STDERR (partial):", e.stderr)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_copilot()
