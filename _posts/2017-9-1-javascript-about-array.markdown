---
layout: post
title:  "JavaScript中的数组操作总结"
date:   2017-09-01 20:22:13
categories: javascript
tags: [数组]
---

数组作为JavaScript中最为常用的几个内建对象之一，较好的掌握数组的用法，能在日常的编码中起到事半功倍的作用。

## 执行后被操作数组发生改变
### Array.prototype.pop ( )

移除数组中的最后一个元素并返回该元素。

如果你在一个空数组上调用 pop()，它返回  undefined。

### Array.prototype.push ( ...items )

push方法按照参数出现的次序，将所有参数添加到数组的末尾，并返回新的数组长度。

当参数个数+原数组长度大于2的53次方-1时，将会抛出TypeError错误。

push方法的length属性值为1.

### Array.prototype.shift ( )

shift 移除数组中的第一个元素并返回该元素。

### Array.prototype.unshift ( ...items )

push方法按照参数出现的次序，将所有参数添加到数组的头部，并返回新的数组长度。

当参数个数+原数组长度大于2的53次方-1时，将会抛出TypeError错误。

unshift方法的length属性值为1.

### Array.prototype.reduce ( callbackfn [ , initialValue ] )

传入的callbackfn应该是一个带有4个参数的函数。reduce 方法自数组的第1个元素开始，依次为每个元素调用一次callbackfn函数。

callbackfn函数被调用的时候将会传入4个参数：
previousValue（前一次callbackfn函数调用时返回的值）
currentValue（当前元素）
currentIndex（当前元素的坐标）
当前的执行对象

在callbackfn函数第一次被调用的时候，previousValue和currentValue可能会有不同的取值。如果reduce调用的时候有传入initialValue参数， previousValue将会等于传入的initialValue参数值，currentValue将会等于数组的第一个元素。如果没有传入initialValue参数，previousValue将会等于数组的第一个元素，currentValue将会等于数组的第2个元素。如果对空数组执行reduce方法，并且没有传入initialValue参数，将会抛出TypeError错误。

reduce并不会直接改变调用它的对象，但是对象有可能在callbackfn函数调用的时候被改变。

reducec所处理的数据的范围在第一次调用callbackfn之前就已经确定了，reduce方法开始执行之后所添加的元素都不会被callbackfn函数访问到。如果数组中某个元素的值发生了改变，传入callbackfn的值将是访问到这个元素时这个元素的取值。如果元素在被访问到之前或者reduce方法执行之前被删除了，那么这个元素将不会被访问到。

### Array.prototype.splice ( start, deleteCount, ...items )

splice在中文是绞接，剪接的意思。在splice方被调用的时候，start和deleteCount是必要的2个参数，这2个参数之后还可以传入0个或者多个参数。splice操作将会从下标start开始，删除deleteCount个元素，如果传入了items参数，items将会在start这个位置插入到数组中。操作返回一个包含被删除元素的数组。

### Array.prototype.fill ( value [ , start [ , end ] ] )

fill方法将传入的value值填充到调用的数组中，start和end参数是可选的，如果没传，start默认是0，end默认是数组的长度。如果start的值为负数，则start值变为长度+start，如果end的值为负数，则end的值变为长度+end。方法调用后，自下标start开始一直到end为止(不包含end)，元素的值都转变为value。

### Array.prototype.every ( callbackfn [ , thisArg ] )

### Array.prototype.some ( callbackfn [ , thisArg ] )

## 执行后被操作数组维持不变

### Array.prototype.concat ( ...arguments )

concat方法可以传入0或多个参数，执行后返回一个新的数组，包含原来的数组元素以及传入的参数。传入的参数将会依次跟在原数组元素后面，如果参数一个数组，那么它将会被展开连接到数组后面。

### Array.prototype.slice ( start, end )

slice在中文是切片的意思。slice的调用需要start和end两个参数，截取原数组自下标start开始至end(不包括)的一段返回(如果end未传入，则截取到数组的最后)，原数组不会被改变。如果start是一个负数，则从数组的下标start+length开始（lenth为数组的长度）。如果end是一个负数，则截取到数组的下标end+length(lenth为数组的长度,不包括这个位置。)

### Array.prototype.filter ( callbackfn [ , thisArg ] )

filter的调用需要传入callbackfn这个回调函数，callbackfn函数接受3个参数并且返回一个会被强制转换为布尔量的值。filter方法会为数组中的每个元素按升序调用一次callbackf函数，如果元素调用过callbackfn之后返回的值为true,那么这些元素会被放到一个新的数组中返回。callbackfn只会被数组中真正存在的元素调用，如果元素不存在，则callbackfn不会被调用。

如果传入了thisArg参数，那么它将作为被调用的callbackfn的this变量使用，如果没有传入thisArg，那么callbackfn调用时的this变量值为undefined。
callbackfn调用的时候会传入3个参数，当前元素的值，当前元素的下标，以及正在被遍历的对象。

filter 函数的调用并不会直接改变数组本身，但在callbackfn调用的过程中，对象可能会被改变。

filter所处理的数据的范围在第一次调用callbackfn之前就已经确定了，filter方法开始执行之后所添加的元素都不会被callbackfn函数访问到。如果数组中某个元素的值发生了改变，传入callbackfn的值将是访问到这个元素时这个元素的取值。如果元素在被访问到之前或者filter方法执行之前被删除了，那么这个元素将不会被访问到。

### Array.prototype.map ( callbackfn [ , thisArg ] )

http://www.ecma-international.org/ecma-262/8.0/#sec-array.prototype.reduce 

回调函数 callbackfn 将会接受3个参数。map方法会对数组中的每个元素按升序调用一遍，并且返回一个新的数组。当数组中的元素真实存在的时候，callbackfn才会被调用，当元素不存在的时候，callbackfn不会被调用。

如果提供了thisArg参数，thisArg 将作为this的值在callbackfn被调用的时候被使用，如果没有传入thisArg参数，this的值将会是undefined。

callbackfn 被调用的时候将会传入3个参数，当前遍历的元素的值，元素的下标，以及被遍历的数组元素。

map 函数的调用并不会直接改变数组本身，但在callbackfn调用的过程中，对象可能会被改变。






	




