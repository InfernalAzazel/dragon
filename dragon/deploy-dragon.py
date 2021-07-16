import os

path = os.getcwd()
# 项目名称
project = 'dragon'
# 应用名称
out_app = 'dragon'
# 命令
cmd = f'cd {path} && python -m zipapp {project} -o {out_app}.pyz -m "main:main"'

if __name__ == '__main__':
    os.system(cmd)
    print(f'[+] 项目: {project} 打包完毕..')
    print(f'[+] 所在目录: {path} 文件名: {out_app}.pyz')
