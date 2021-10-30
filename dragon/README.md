# dragon (腾龙)
## 椰泰
- 用途
  - 简道云 交互 服务器 
- 版本:
    - stable 0.1.1
  
# 虚拟机部署

```angular2html

vmware-hgfsclient github # 挂载共享文件

/usr/bin/vmhgfs-fuse .host:/ /mnt/hgfs -o subtype=vmhgfs-fuse,allow_other

netstat -apn  | grep 8083 # 查看指定占用端口

如果是后台程序，你用 ps aux | grep 进程名字。然后找到pid , 然后 kill -9 pid

cd /mnt/hgfs/github

部署

gunicorn main:fast_app -b 0.0.0.0:6666  -w 4 -k uvicorn.workers.UvicornH11Worker --daemon

nohup python3.9 main.py>/dev/null 2>&1 &

ps aux | grep gunicorn

kill -9 3604
```