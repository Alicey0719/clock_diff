import socket
import struct
import time
import sys
import math
import argparse

NTP_DELTA = 2208988800
PORT = 123
BUF_SIZE = 1024

def get_ntp_time(timestamp_bytes):
    """NTPパケットの64bitタイムスタンプをUNIX時間に変換"""
    seconds, fraction = struct.unpack("!II", timestamp_bytes)
    return (seconds - NTP_DELTA) + (fraction / 2**32)

def main():
    # --- 引数パース (argparse) ---
    parser = argparse.ArgumentParser(description="NTP Drift Monitor")
    
    # -s / --server option
    parser.add_argument('-s', '--server', type=str, default='ntp.nict.jp',
                        help='Target NTP server hostname or IP (default: ntp.nict.jp)')
    
    # -i / --interval option
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='Polling interval in seconds (default: 1.0)')

    args = parser.parse_args()
    
    target_server = args.server
    interval = args.interval

    # --- run ---
    results = []
    
    print(f"========================================================")
    print(f" NTP Drift Monitor")
    print(f" Target Server : {target_server}")
    print(f" Interval      : {interval} sec")
    print(f" Stop Command  : Press [Ctrl + C] to show result summary")
    print(f"========================================================")
    print(f"{'Seq':<4} | {'Time':<8} | {'Offset (s)':>13} | {'RoundTrip (s)':>15}")

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.settimeout(2.0)

    sequence = 0

    try:
        while True:
            sequence += 1
            msg = b'\x1b' + 47 * b'\0' # NTP v3, Client
            
            try:
                # --- 通信開始 ---
                t1 = time.time()
                client.sendto(msg, (target_server, PORT))
                
                data, address = client.recvfrom(BUF_SIZE)
                t4 = time.time()
                
                # --- 解析 ---
                if data:
                    t2 = get_ntp_time(data[32:40])
                    t3 = get_ntp_time(data[40:48])

                    delay = (t4 - t1) - (t3 - t2)
                    offset = ((t2 - t1) + (t3 - t4)) / 2
                    
                    results.append({'offset': offset, 'delay': delay})
                    
                    current_time_str = time.strftime("%H:%M:%S", time.localtime(t4))
                    offset_str = f"{offset:+.6f}"
                    
                    print(f"{sequence:<4} | {current_time_str} | {offset_str:>13} | {delay:15.6f}")
                
            except socket.timeout:
                print(f"{sequence:<4} | {'Request Timed Out'}")
            except socket.gaierror:
                print(f"{sequence:<4} | Error: Could not resolve hostname '{target_server}'")
                time.sleep(1)
            except Exception as e:
                print(f"{sequence:<4} | Error: {e}")

            time.sleep(interval)

    except KeyboardInterrupt:
        # --- show summary ---
        print("\n\n================ [ STOPPED ] Summary Report ================")
        
        if results:
            offsets = [r['offset'] for r in results]
            delays = [r['delay'] for r in results]
            
            count = len(offsets)
            avg_offset = sum(offsets) / count
            max_offset = max(offsets)
            min_offset = min(offsets)
            avg_delay = sum(delays) / count
            
            variance = sum((x - avg_offset) ** 2 for x in offsets) / count
            std_dev = math.sqrt(variance)
            
            print(f" Target        : {target_server}")
            print(f" Count         : {count} samples")
            print(f" Average Offset: {avg_offset:+.6f} s")
            print(f" Max Offset    : {max_offset:+.6f} s")
            print(f" Min Offset    : {min_offset:+.6f} s")
            print(f" Std Deviation : {std_dev:.6f} s (Jitter)")
            print(f" Average Delay : {avg_delay:.6f} s")
            print("--------------------------------------------------------")
            
            if abs(avg_offset) <= 0.5:
                print(" Result: Clock is ACCURATE (Within 0.5s)")
            else:
                print(" Result: Clock is DRIFTING (Check NTP settings)")
        else:
            print(" No data collected.")
        
        print("========================================================")
        client.close()

if __name__ == "__main__":
    main()

