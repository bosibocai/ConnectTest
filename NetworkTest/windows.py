import tkinter as tk
from tkinter import *
from tkinter.ttk import *
from tkinter import scrolledtext
import connectText
import time

DEFAULT_TIMEOUT = 2

win1=tk.Tk()#常见窗口对象
win1.title('Connect Test')#添加窗体名称
win1.geometry('700x500')#设置窗体大小

timeout = DEFAULT_TIMEOUT


var_ip = tk.StringVar()
Label(win1, text="IP  地址：", font=('Arial', 14)).place(x=30, y=20)
ip_entry=Entry(win1, show=None, textvariable=var_ip, font=('Arial', 14))
ip_entry.place(x=140 ,y=20)
var_nums = tk.IntVar()
var_nums.set(1)
Label(win1, text="报文个数：", font=('Arial', 14)).place(x=30, y=60)
num_entry=Entry(win1, show=None, textvariable=var_nums, font=('Arial', 14))
num_entry.place(x=140 ,y=60)
var_times = tk.DoubleVar()
var_times.set(0.5)
Label(win1, text="时间间隔：", font=('Arial', 14)).place(x=30, y=100)
times_entry=Entry(win1, show=None, textvariable=var_times, font=('Arial', 14))
times_entry.place(x=140 ,y=100)


def connect():
    ip = var_ip.get()
    num = var_nums.get()
    times = var_times.get()
    print(ip)
    print(num)
    print(times)
    ping(target_host=ip,count=num,sleep_time=times)
    

def ping(target_host,count,sleep_time):
    """
    Run the ping process
    """
    send = 0
    accept = 0
    lost = 0
    sumtime = 0
    shorttime = 1000
    longtime = 0
    avgtime = 0
    pinger = connectText.Pinger(target_host=target_host,count=count,sleep_time=sleep_time)
    for i in range(count):
        result_text.insert(INSERT, "Ping to %s...\n" % target_host)
        try:
            delay  =  pinger.ping_once()
            send += 1
        except socket.gaierror as e:
            result_text.insert(INSERT, "Ping failed. (socket error: '%s')\n" % e[1])
            break
        if delay  ==  None:
            result_text.insert(INSERT, "Ping failed. (timeout within %ssec.)\n" % timeout)
            lost+=1
        if delay == -1:
            result_text.insert(INSERT, "Ping failed. (timeout within %ssec.)\n" % timeout)
            lost+=1
        else:
            delay  =  delay * 1000
            result_text.insert(INSERT, "times %0.4fms\n" % delay)
            accept+=1
            sumtime += delay
            if delay > longtime:
                longtime = delay
            if delay < shorttime:
                shorttime = delay
            time.sleep(sleep_time)
    result_text.insert(INSERT, "数据包：已发送={0}, 接收={1}, 丢失={2}({3:.2%}丢失)\n".format(send, accept, lost, lost/send))
    if(accept>0):
        result_text.insert(INSERT, "往返行程的估计时间：\n")
        result_text.insert(INSERT, "\t最短={0:.4f}ms, 最长={1:.4f}ms, 平均={2:.4f}ms\n".format(shorttime,longtime,sumtime/send))


button1=Button(win1, text="Connect Test",command=connect).place(x=150 ,y=140)
Label(win1, text="连接结果：", font=('Arial', 14)).place(x=30, y=180)
result_text = scrolledtext.ScrolledText(win1, width=65, height=15, undo=True,autoseparators=False, font=('Arial', 12))
result_text.place(x=60, y=210)
# Label(win1, text="", font=('Arial', 12)).place(x=60, y=220)
win1.mainloop()#执行窗体