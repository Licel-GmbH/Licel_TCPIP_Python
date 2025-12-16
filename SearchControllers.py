#!/usr/bin/env python3
import socket
import select
import ipaddress

# Try to import helpers for enumerating interfaces. Prefer `netifaces`, then `psutil`.
try:
    import netifaces as _netifaces
except Exception:
    _netifaces = None

try:
    import psutil as _psutil
except Exception:
    _psutil = None


def main():
    # Payload: 0x01 followed by seven 0x00 bytes
    payload = bytes([0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

    # Determine broadcast addresses per-interface.
    broadcasts = []

    if _netifaces is not None:
        for iface in _netifaces.interfaces():
            addrs = _netifaces.ifaddresses(iface).get(_netifaces.AF_INET, [])
            for a in addrs:
                addr = a.get('addr')
                bcast = a.get('broadcast')
                netmask = a.get('netmask')
                if not addr:
                    continue
                if not bcast and netmask:
                    try:
                        network = ipaddress.IPv4Network(f"{addr}/{netmask}", strict=False)
                        bcast = str(network.broadcast_address)
                    except Exception:
                        bcast = None
                if bcast:
                    broadcasts.append((addr, bcast))
    elif _psutil is not None:
        for iface, addrs in _psutil.net_if_addrs().items():
            for a in addrs:
                if a.family == socket.AF_INET and a.address:
                    addr = a.address
                    netmask = a.netmask
                    bcast = a.broadcast
                    if not bcast and netmask:
                        try:
                            network = ipaddress.IPv4Network(f"{addr}/{netmask}", strict=False)
                            bcast = str(network.broadcast_address)
                        except Exception:
                            bcast = None
                    if bcast:
                        broadcasts.append((addr, bcast))
    else:
        # Fallback: single global broadcast
        broadcasts.append((None, '255.255.255.255'))

    # For each interface/broadcast, send using a socket bound to the interface address
    socks = []
    try:
        for bind_addr, bcast in broadcasts:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                # If we know a local address, bind to it so the packet goes out that interface
                if bind_addr:
                    try:
                        s.bind((bind_addr, 0))
                    except Exception:
                        # If bind fails, continue without binding
                        pass
                s.sendto(payload, (bcast, 2000))
                socks.append(s)
            except Exception:
                try:
                    s.close()
                except Exception:
                    pass

        # Wait for responses on all sockets (10 second timeout per select)
        sockset = socks[:] if socks else []
        while sockset:
            ready, _, _ = select.select(sockset, [], [], 10)
            if not ready:
                break
            for r in ready:
                try:
                    data, addr = r.recvfrom(100)
                except Exception:
                    try:
                        sockset.remove(r)
                    except ValueError:
                        pass
                    continue
                # Remove first 5 bytes to match original Perl behavior
                data = data[5:] if len(data) > 5 else b""
                ip = addr[0]
                # Decode safely for printing
                text = data.decode("utf-8", errors="replace")
                print(f"{ip}, {text}")
    finally:
        for s in socks:
            try:
                s.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()