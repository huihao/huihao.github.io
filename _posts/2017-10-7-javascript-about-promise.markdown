---
layout: post
title:  "介绍JavaScript中的Promise"
date:   2017-10-07 17:23:10
categories: javascript
tags: [promise,asyn,wait]
---

一个Promise对象被用于作为某个延迟（或者异步）操作返回的最终结果的占位。

每一个Promise对象会拥有三种互斥状态中的一种状态：fulfilled, rejected, 和 pending。

- 一个Promise对象的状态变为fulfilled,如果有p.then(f, r) ，会立即调用f函数。
- 一个Promise对象的状态变为rejected，如果有p.then(f, r)，会立即执行r函数。
- 一个Promise对象的的状态没有变为rejected或fulfilled，那么它的状态是pending。

一个Promise对象被称为settled，如果它不处于pending状态或者说它的状态变为了fulfilled或者rejected。

一个Promise对象如果已经是settled或者为了匹配其他Promise对象的状态已经被“locked in”，那么可以称它已经是resolved。将一个已经是resolved的Promise对象变为fulfilled或者rejected的操作都将是无效的。一个Promise如果还没有resolved，那么它是unresolved的。一个unresolved的Promise对象的状态始终是pending。一个resolved的Promise对象的状态可能是 pending, fulfilled 或者 rejected。

### 创建一个Promise对象

`
// mdn 上的例子
let myFirstPromise = new Promise(function(resolve, reject){
    //当异步代码执行成功时，我们才会调用resolve(...), 当异步代码失败时就会调用reject(...)
    //在本例中，我们使用setTimeout(...)来模拟异步代码，实际编码时可能是XHR请求或是HTML5的一些API方法.
    setTimeout(function(){
        resolve("成功!"); //代码正常执行！
    }, 250);
});

myFirstPromise.then(function(successMessage){
    //successMessage的值是上面调用resolve(...)方法传入的值.
    //successMessage参数不一定非要是字符串类型，这里只是举个例子
    console.log("Yay! " + successMessage);
});
`

Promise 构造器是一个内部对象企且是全局对象属性Promise的初始值。把Promise当作构造器使用的时候，它会创建并初始化一个新的Promise对象。当Promise被当作函数调用的时候，会抛出一个错误。

当使用Promise构造器的时候，需要传入一个executor参数，executor参数必须是一个函数对象。在executor中初始化并记录可能的延迟操作的完成状态。executor函数执行的时候将会带入两个参数resolve 和 reject。这两个方法可能被用于报告延迟操作的最终结果是完成还是失败。executor 函数中return并不表示这延迟操作已经完成,但是表示延迟操作向最终表现的请求已经被接受。

 作为参数传入executor函数的resolve函数会接收到一个参数。executor中代码最终可能会调用resolve方法用以表明相关联的 Promise 对象已经解决。传入resolve函数的参数表示着延迟操作的最终结果，它可以是任意的实现的值或者是其他的会在完成时传值的Promise对象。

 作为参数传入executor函数的reject函数会接收到一个参数。executor中代码最终可能会调用reject方法用以表明相关联的Promise已经被拒绝并且将永远无法将状态变为fulfilled。传入reject的参数被用作promise被拒绝的值，这个值通常是Error 对象。

 被Promise构造器传入的resolve和reject方法能确实的resolve或reject相关联的promise。子类可能拥有不用的构造行为通过自定义的resolve和reject值。

 https://github.com/mattdesl/promise-cookbook
 https://github.com/xieranmaya/blog/issues/3
 http://www.ecma-international.org/ecma-262/8.0/#sec-promise-objects
 http://www.ituring.com.cn/article/66566

 ### 原型方法

 #### Promise.prototype.then ( onFulfilled, onRejected )

---未完成 























