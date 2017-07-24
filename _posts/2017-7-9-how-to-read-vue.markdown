---
layout: post
title:  "如何阅读VUE2.0的源码"
date:   2017-07-09 22:42:10
categories: javascript
tags: [vue, es6]
---

  阅读优秀程序员的代码是一种非常有用的学习方式，大到框架架构，小到代码片段，只要方法得当，相信肯定能从中汲取到自身所需的营养。Vue作为现今国内最火的前端框架之一，它的源码风格以优雅著称，从简练高效的API中就可以感受一二，自然阅读Vue的源码便成了工作之余提升的方式之一。

## 学习ES6

  Vue2采用了ES6编写，学习ES6自然也成了阅读Vue源码的前提。

## 阅读他人撰写的Vue源码分析

  面对一个庞大的框架，即使你已经有了丰富的Vue程序编写经验，要立马理解它的源码，也是一件非常苦难的事情。再此之前有不少人已经为后人铺好了路，我们可以顺着他们的路走下去，理解基本的原理，有了大概的思路之后，再进入到源码中便会轻松很多

## 断点调试

  在github上clone Vue项目到自己的电脑上，npm install 所需的依赖项，便可以开始在编辑器中浏览Vue的源码了。单纯的阅读源码，会是件十分枯燥的事情，我可以运行项目中的example或者自己编写事例在浏览器中运行去观察代码的运行。

  我们可以看到package.json里的运行命令

````
  "dev": "rollup -w -c build/config.js --environment     TARGET:web-full-dev",
````

  Vue 使用了rollup 去打包源文件，我们可以加上soursesMap选项，生成sourcemap文件，更好的帮助我们去阅读源码。

````
  "dev": "rollup -w -c build/config.js --sourcemap --environment TARGET:web-full-dev",
````