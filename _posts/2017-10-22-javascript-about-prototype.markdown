---
layout: post
title:  "Javascript 中的继承"
date:   2017-10-22 12:23:10
categories: javascript
tags: [javascript, prototype]
---

http://www.ecma-international.org/ecma-262/8.0/#sec-ordinary-and-exotic-objects-behaviours

### prototype

每一个普通的对象都有一个内部的slot被称作[[Prototype]].这个内部slot的值是null或者是一个对象，它被用作实现继承。prototype 对象中的属性值是被继承的（并且作为子对象的属性）为了获得访问权限，但是没有写入权限。存取器的继承能获得读取和写入的权限。

每一个普通的对象内部都有一个布尔类型的[[Extensible]] solt,它控制着属性能否被添加到对象中。如果对象内部solt[[Extensible]]的值是false,那么其它的属性值将不能被添加到这个对象中。 除此之外，如果[[Extensible]] 的值是false，那么这个对象的内部solt[[Prototype]]将不能被修改。当一个对象的[[Extensible]]内部slot被设为false，它可能将无法立马转换为true.

### 继承的实现方式

#### 原型继承

#### 构造方式继承


