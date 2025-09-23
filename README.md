## 官网

```
https://www.freeshell.cn
```

## python 3.10.4  安装依赖

```
pip install pyside6==6.9.1
pip install paramiko==4.0.0
pip install pyinstaller==6.15.0
```

## 打包为exe文件

### 最好不要打包为1个文件,1个文件每次解压,影响运行速度

### 编译后的exe文件在dist目录下

```
 pyinstaller FreeShell.spec 
```

## 参考

```
依赖软件
xterm.js 5.5.0  https://github.com/xtermjs/xterm.js
addon-fit 0.10.0  https://github.com/xtermjs/xterm.js/tree/master/addons/addon-fit
pyside 6.9.1
paramiko 4.0.0
pyinstaller 6.15.0
python 3.10.4
version='version.txt'
```
