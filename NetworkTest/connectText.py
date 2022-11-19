#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os 
import argparse 
import socket
import struct
import select
import time


ICMP_ECHO_REQUEST = 8 # Platform specific
DEFAULT_TIMEOUT = 2
DEFAULT_COUNT = 4 


class Pinger(object):
    """ Pings to a host -- the Pythonic way"""

    def __init__(self, target_host, count,sleep_time, timeout=DEFAULT_TIMEOUT):
        self.target_host = target_host
        self.count = count
        self.timeout = timeout
        self.send = 0
        self.accept = 0
        self.lost = 0
        self.sleep_time=sleep_time
        self.sumtime = 0
        self.shorttime = 1000
        self.longtime = 0
        self.avgtime = 0
        self.delays = []


    def do_checksum(self, source_string):
        """  Verify the packet integritity """
        sum = 0
        max_count = (len(source_string)/2)*2
        count = 0
        while count < max_count:

            val = source_string[count + 1]*256 + source_string[count]                   
            sum = sum + val
            sum = sum & 0xffffffff 
            count = count + 2

        if max_count<len(source_string):
            sum = sum + ord(source_string[len(source_string) - 1])
            sum = sum & 0xffffffff 

        sum = (sum >> 16)  +  (sum & 0xffff)
        sum = sum + (sum >> 16)
        answer = ~sum
        answer = answer & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        return answer

    def receive_pong(self, sock, ID, timeout):
        """
        Receive ping from the socket.
        """
        time_remaining = timeout
        while True:
            # 开始时间
            start_time = time.time()
            # 实例化select对象
            readable = select.select([sock], [], [], time_remaining)
            # 等待时间
            time_spent = (time.time() - start_time)
            if readable[0] == []: # Timeout
                return -1
            # 记录接收时间
            time_received = time.time()
            # 设置接收的包的字节为1024
            recv_packet, addr = sock.recvfrom(1024)
            # 获取接收包的icmp头
            icmp_header = recv_packet[20:28]
            # 反转编码
            type, code, checksum, packet_ID, sequence = struct.unpack(
       "bbHHh", icmp_header
   )
            if packet_ID == ID:
                bytes_In_double = struct.calcsize("d")
                time_sent = struct.unpack("d", recv_packet[28:28 + bytes_In_double])[0]
                # 返回接收时间-发送时间
                return time_received - time_sent

            time_remaining = time_remaining - time_spent
            if time_remaining <= 0:
                return -1


    def send_ping(self, sock,  ID):
        """
        Send ping to the target host
        """
        target_addr  =  socket.gethostbyname(self.target_host)

        my_checksum = 0

        # Create a dummy heder with a 0 checksum.
        header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, my_checksum, ID, 1)
        bytes_In_double = struct.calcsize("d")
        data = (192 - bytes_In_double) * "Q"
        data = struct.pack("d", time.time()) + bytes(data.encode('utf-8'))

        # Get the checksum on the data and the dummy header.
        my_checksum = self.do_checksum(header + data)
        header = struct.pack(
      "bbHHh", ICMP_ECHO_REQUEST, 0, socket.htons(my_checksum), ID, 1
  )
        packet = header + data
        sock.sendto(packet, (target_addr, 1))


    def ping_once(self):
        """
        Returns the delay (in seconds) or none on timeout.
        """
        icmp = socket.getprotobyname("icmp")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, icmp)
        except socket.error as e:
            if e.errno == 1:
                # Not superuser, so operation not permitted
                e.msg +=  "ICMP messages can only be sent from root user processes"
                raise socket.error(e.msg)
        except Exception as e:
            print ("Exception: %s" %(e))

        my_ID = os.getpid() & 0xFFFF

        self.send_ping(sock, my_ID)
        delay = self.receive_pong(sock, my_ID, self.timeout)
        sock.close()
        return delay


    def ping(self):
        """
        Run the ping process
        """
        for i in range(self.count):
            print ("Ping to %s..." % self.target_host,)
            try:
                delay  =  self.ping_once()
                self.send += 1
            except socket.gaierror as e:
                print ("Ping failed. (socket error: '%s')" % e[1])
                break
            self.delays.append(delay)
            if delay  ==  None:
                print ("Ping failed. (timeout within %ssec.)" % self.timeout)
                self.lost+=1
            if delay == -1:
                print ("Ping failed. (timeout within %ssec.)" % self.timeout)
                self.lost+=1
            else:
                delay  =  delay * 1000
                print ("times %0.4fms" % delay)
                self.accept+=1
                self.sumtime += delay
                if delay > self.longtime:
                    self.longtime = delay
                if delay < self.shorttime:
                    self.shorttime = delay
                time.sleep(self.sleep_time)
        print("数据包：已发送={0}, 接收={1}, 丢失={2}({3:.2%}丢失), ".format(self.send, self.accept, self.lost, self.lost/self.send))
        if(self.accept>0):
            print("往返行程的估计时间：")
            print("\t最短={0:.4f}ms, 最长={1:.4f}ms, 平均={2:.4f}ms".format(self.shorttime,self.longtime,self.sumtime/self.send))
        