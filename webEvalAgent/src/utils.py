import platform
import subprocess
import os
import signal

def stop_log_server():
    """Stop any running log server by sending a signal to the process."""
    try:
        if platform.system() == 'Windows':
            # On Windows, we use netstat to find processes using the port
            cmd = f"netstat -ano | findstr :5009"
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            for line in output.split('\n'):
                if 'LISTENING' in line:
                    # Extract PID
                    pid = line.split()[-1]
                    os.kill(int(pid), signal.SIGTERM)
                    return True
        elif platform.system() == 'Darwin':  # macOS
            # On macOS, we use lsof to find processes using the port
            cmd = f"lsof -i:5009 -t"
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            for pid in output.split('\n'):
                if pid:
                    os.kill(int(pid), signal.SIGTERM)
                    return True
        else:  # Linux and other UNIX-like systems
            # On Linux, we use fuser to find processes using the port
            cmd = f"fuser 5009/tcp 2>/dev/null"
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            for pid in output.split():
                if pid:
                    os.kill(int(pid), signal.SIGTERM)
                    return True
    except Exception:
        # If any error occurs, just log it and continue
        pass
    
    return False