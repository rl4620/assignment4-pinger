from socket import *
import os
import sys
import struct
import time
import select
import binascii
import statistics
# Should use stdev

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = (string[count + 1]) * 256 + (string[count])
        csum += thisVal
        csum &= 0xffffffff
        count += 2

    if countTo < len(string):
        csum += (string[len(string) - 1])
        csum &= 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)
    return answer



def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while 1:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)
        if whatReady[0] == []:  # Timeout
            return -1

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Fill in start

        # Fetch the ICMP header from the IP packet
        ip_header = recPacket[0: 20]
        icmp_header = recPacket[20:28]
        version_header_length, type_of_service, datagram_length, identifier, flags_and_offset, ttl, upper_protocol, header_checksum, source_ip, dest_ip = struct.unpack("bbhhhbbhii", ip_header)
        type, code, checksum, p_id, sequence = struct.unpack("bbHHh", icmp_header)
        # print("received header version and length: " + str(version_header_length))
        # print("received header type of service: " + str(type_of_service))
        # print("received header datagram length: " + str(datagram_length))
        # print("received header identifier: " + str(identifier))
        # print("received header flag and offset: " + str(flags_and_offset))
        # print("received header TTL: " + str(ttl))
        # print("received header upper protocol: " + str(upper_protocol))
        # print("received header checksum: " + str(header_checksum))
        # print("received header source IP: " + str(source_ip))
        # print("received header dest IP: " + str(dest_ip))
        # print("received header type: " + str(type))
        # print("received header code: " + str(code))
        # print("received header checksum: " + str(checksum)) 
        # print("received header p_id: " + str(p_id))
        # print("received header sequence: " + str(sequence))
        if p_id == ID and type == ICMP_ECHO_REPLY and code == ICMP_ECHO_REPLY:
            delay = howLongInSelect * 1000
            print("Reply from " + destAddr + ": bytes=" + str(datagram_length) + " time=" + str(delay) + "ms TTL=" + str(ttl))
            return delay

        # Fill in end
        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return -1


def sendOnePing(mySocket, destAddr, ID):
    # Header is type (8), code (8), checksum (16), id (16), sequence (16)

    myChecksum = 0
    # Make a dummy header with a 0 checksum
    # struct -- Interpret strings as packed binary data
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())
    # Calculate the checksum on the data and the dummy header.
    myChecksum = checksum(header + data)

    # Get the right checksum, and put in the header

    if sys.platform == 'darwin':
        # Convert 16-bit integers from host to network  byte order
        myChecksum = htons(myChecksum) & 0xffff
    else:
        myChecksum = htons(myChecksum)


    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))  # AF_INET address must be tuple, not str


    # Both LISTS and TUPLES consist of a number of objects
    # which can be referenced by their position number within the object.

def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")


    # SOCK_RAW is a powerful socket type. For more details:   https://sock-raw.org/papers/sock_raw
    mySocket = socket(AF_INET, SOCK_RAW, icmp)

    myID = os.getpid() & 0xFFFF  # Return the current process i
    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)
    mySocket.close()
    return delay


def ping(host, timeout=1):
    # timeout=1 means: If one second goes by without a reply from the server,  	
    # the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print("Pinging " + dest + " using Python:")
    print("")
    
    #Send ping requests to a server separated by approximately one second
    #Add something here to collect the delays of each ping in a list so you can calculate vars after your ping
    delays = []
    packet_received = 0
    for i in range(0,4): #Four pings will be sent (loop runs for i=0, 1, 2, 3)
        delay = doOnePing(dest, timeout)
        # print(delay)
        if delay < 0:
            print("Request timed out.")
            delays.insert(i, 0.0)
        else:
            delays.insert(i, delay)
            packet_received = packet_received + 1
        time.sleep(1)  # one second
        
    #You should have the values of delay for each ping here; fill in calculation for packet_min, packet_avg, packet_max, and stdev
    packet_min = min(delays)
    packet_max = max(delays)
    packet_avg = sum(delays)/len(delays)
    stdev_var = statistics.stdev(delays)
    vars = [str(round(packet_min, 8)), str(round(packet_avg, 8)), str(round(packet_max, 8)),str(round(stdev_var, 8))]
    print("--- " + host + " ping statistics ---")
    print("4 packets transmitted, " + str(packet_received) + " packets received, " + str(100 * (1 - packet_received/4)) + "% packet loss")
    print("round-trip min/avg/max/stdev = " + "/".join(vars) + " ms")

    return vars

if __name__ == '__main__':
    ping("google.co.il")
    ping("127.0.0.2")
    # ping("No.no.e")
