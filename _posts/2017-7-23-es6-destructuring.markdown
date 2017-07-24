---
layout: post
title:  "学习ES6解构 Destructuring"
date:   2017-07-23 22:00:10
categories: javascript
tags: [es6]
---

解构赋值作为一个较为实用的特性出现在ES6中，这篇文章记录了解构的基本使用和用途。

### 定义

解构是将数组中的值或对象的属性值提取到不同的变量中。

### 使用方法

#### 数组的解构


	var [a] = [1]
	console.log(a) //a
	
	
	var b = 2,c = 3
	[b,c] = ["b","c"]
	console.log(b,c)//b c

多维数组的解构

	var [a,[b,c],d] = [1,[2,3],4]
	
	console.log(a,b,c,d) //1 2 3 4

不定参数

	var [a,...inner] = [1,2,3,4,5]
	console.log(a,inner)// 1 [2,3,4,5]

#### 对象的解构
	
	var {a:a} = {a:"hello"}
	console.log(a) //hello
	
	
当属性名与变量名一致的时候，可以使用简写

	
	var {a,b} = {"a":"a","b":"b"}
	console.log(a,b) //a b

嵌套对象的节解构

	var {
		"name":name,
			"info":{
				"age":age,
				"sex":sex
			}
		} = {
			"name":"jay",
			"info":{
				"age":32,
				"sex":"man"
				}
			}
	console.log(name,age,sex) //jay 32 man
	

#### 数组和对象的混合解构

	var {
		"name":name,
		"list":[a,...list]
	} = {
		"name":"leehome",
		"list":[1,2,3,4]
		}
	
	console.log(name,a,list) //leehome 1 [2,3,4]


### 解构赋值的用途

- 交换变量的值

- 函数参数的定义
	
````
	var a = {"name":"jay","age":12,"sex":"man"}
	function fun({name,age,sex}){
		console.log(name,age,sex)
	}
	fun(a) //jay 12 man
````
- 函数返回多个值

````
	function foo(){
		return {
			"a":"a",
			"b":"b"
		}
	}
	var {a,b} = foo()
	console.log(a,b)//a b
````

- import 模块调用

