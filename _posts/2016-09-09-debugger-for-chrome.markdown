---
layout: post
title:  "使用VS Code调试JavaScript代码"
date:   2016-09-09 12:44:10
categories: ide
tags: [microsoft, javascript]
---

在VS Code中，配合Debugger for Chrome插件，可以实现在编辑器中对JavaScript代码进行调试的功能，能更加方便的开发以Tatami为框架的单页面应用。

安装插件

![](//whhbio.oss-cn-beijing.aliyuncs.com/blog/install.gif)

创建配置文件

![](//whhbio.oss-cn-beijing.aliyuncs.com/blog/config.gif)

插件存在两种运行模式，一是启动Chrome浏览器并跳转到你的应用页面，二是连接一个运行的Chrome实例。两种模式都可以通过.vscode/launch.json文件配置，VS Code可以为你自动生成一个配置文件，当然你也可以自己手动编写。

```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Launch Chrome against localhost, with sourcemaps",
            "type": "chrome",
            "request": "launch",
            "url": "http://localhost:8088",
            "sourceMaps": true,
            "webRoot": "${workspaceRoot}"
        },
        {
            "name": "Attach to Chrome, with sourcemaps",
            "type": "chrome",
            "request": "attach",
            "port": 9222,
            "sourceMaps": true,
            "webRoot": "${workspaceRoot}"
        }
    ]
}
```

上面的样例配置文件中，分别对应了两种启动模式，可以通过更改webRoot属性改变项目的根目录。request属性为launch的配置，可以指定url作为你应用所需要启动的页面地址。


启动调试前，需要利用命令行，打开Chrome的远程调试功能

![](//whhbio.oss-cn-beijing.aliyuncs.com/blog/iterm.gif)

__Windows__

* Right click the Chrome shortcut, and select properties
* In the "target" field, append `--remote-debugging-port=9222`
* Or in a command prompt, execute `<path to chrome>/chrome.exe --remote-debugging-port=9222`

__OS X__

* In a terminal, execute `/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`

__Linux__

* In a terminal, launch `google-chrome --remote-debugging-port=9222`


启动调试

![](//whhbio.oss-cn-beijing.aliyuncs.com/blog/attach.gif)

