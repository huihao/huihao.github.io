---
layout: post
title:  "vue项目如何进行单元测试"
date:   2018-10-23 11:00:10
categories: javascript
tags: [vue, test]
---

## 单元测试所需要用到的npm包介绍

### Vue Test Utils

 Vue.js 官方提供了Vue Test Utils 测试实用工具库，我们可以单独安装进行使用，也可以在使用vue cli的时候进行配置安装。
 
### mocha & mocha-webpack
 
 mocha 是一个运行在nodejs和浏览器上的测试框架，它提供了众多特性可以用于进行单元测试。
 
 mocha-webpack 是 mocha 测试的管理工具，集成了webpack 预编译的功能。
 
### jsdom 
 
 一个DOM和HTML标准的Javascript实现，运行于Node.js环境，测试环境通过jsdom可以模拟真实浏览器的相关行为和调用相应的API进行单元测试。
 
### Chai

断言库

### axios-mock-adapter

通过这个库测试中可以拦截axios发出的请求，并返回指定的mock数据，用于组件中包含异步请求数据的情况。

### flush-promises

会清除所有等待完成的 Promise 具柄


## 项目初始化

如果你的项目是用vue cli进行初始化的，那么你可以根据官网的教程完成mocha-webpack单元测试环境的配置。如果你的项目原来并不支持mocha-webpack单元测试,那么可以根据这个官方的example https://github.com/vuejs/vue-test-utils-mocha-webpack-example 进行单元测试环境的配置。

在这里 我们使用vue cli创建一个项目用于介绍。

```

npm install -g @vue/cli
vue create vue-test-unit

//Manually select features
//勾选Babel，Router，Vuex，Unit Testing
//Pick a unit testing solution: Mocha + Chai

```

## Vue Test Utils 使用介绍

### 挂载


Vue Test Utils 的基础操作是通过mount()函数和或shallowMount()函数挂载组件，函数会返回一个包裹器 Wrapper 对象，通过包裹器提供的API，我们可以对组件进行观察和测试。

mount() 和 shallowMount() 之间的区别在于被存根的子组件。shallowMount() 不会渲染子组件，而是用一个空的div块代替组件的渲染，因为没有渲染，所有子组件声明周期中的函数也不会被执行。Vue Test Utils 提供了stubs配置选项，通过这一选项替换默认的存根，方便我们在测试中测试子组件的渲染情况但又不会被子组件干扰。

```
describe('HelloWorld.vue', () => {
  it('renders props.msg when passed', () => {
    const msg = 'new message'
    const wrapper = shallowMount(HelloWorld, {
      propsData: { msg },
	  stubs: {
		  child: "<div>child</div>"   // child 组件就会被渲染成<div>child</div>
	  }
    })
	console.log(wrapper.html());
    expect(wrapper.text()).to.include(msg)
  })
})

```

### 包裹器

Vue Test Utils 中另一个重要的概念就是包裹器，通过包裹器我们可以获得一种类似于JQuery操作的方式去对组件进行测试。find()和findAll()函数将会是测试中较为常用的一个函数，通过传入一个选择器,find()返回一个包裹器对象或dom节点，findAll()返回一个包含包裹器数组的对象（WrapperArray）。选择器可以是一个 CSS 选择器、一个 Vue 组件或是一个查找选项对象。如果返回的包裹器包裹了一个vue组件，可以通过访问wrapper.vm字段去访问到这个实例。包裹器提供了一个isVueInstance()方法用于判断该包裹器是否是一个vue组件包裹器。所有包裹器都拥有element属性，可以访问到包裹器的根 DOM 节点。

包裹器提供了众多方法可以获得挂载组件的渲染情况用于断言测试。比如isVisible()可以判断是否可以，exists()可以判断是否存在等等，都可以在官网的文档中找到。


### 操作模拟

除了验证组件的渲染情况外，通常我们还需要通过改变组件的数据流状态或者触发组件的事件去验证组件的功能，Vue Test Utils也提供了众多方法供我们去实现这方面的验证。

通过setData() 和 setProps()方法，可以改变组件的数据流状态。

通过trigger()可以触发组件绑定的事件。

但是在执行这些方法的过程中，经常会碰到异步渲染的问题，在这里我推荐使用flush-promises 配合 aync/await 去编写测试用例。flush-promises 会清除所有等待完成的 Promise 具柄。

```

import { shallowMount } from '@vue/test-utils'
import flushPromises from 'flush-promises'
import Foo from './Foo'
jest.mock('axios')

test('Foo', () => {
  it('fetches async when a button is clicked', async () => {
    const wrapper = shallowMount(Foo)
    wrapper.find('button').trigger('click')
    await flushPromises()
    expect(wrapper.vm.value).toBe('value')
  })
})

```


###  请求模拟

通常项目中编写的组件是业务相关的，会包含异步请求在其中，为了验证组件的正确渲染，需要对这些请求行为进行模拟。如果你在项目中使用了axios，那么就可以通过axios-mock-adapter去实现这一需求。


```
import axios from "axios";
import MockAdapter from "axios-mock-adapter";
....

describe("请求模拟测试", () => {
	  beforeEach(() => {
		var mock = new MockAdapter(axios);

		mock.onGet("/test").reply(200,{
			msg: "test"
		   }
		);

	  });
	  it("正确模拟组件中的请求", async function () {
		 
			const wrapper = shallowMount(test);
			await flushPromises();
			expect(wrapper.find(".test").test()).to.equal('test');
	  });
});

	
	
```


### 单元测试编写中遇到的坑

#### Element-UI 中 Select 选择器无法Mount的问题

在使用Vue 进行开发的过程中，难免会使用第三方的UI库，Element 就是其中较为常见的组件库之一。因为项目中使用了Element组件，进行测试的时候就必须引用它，所有就碰到了一些意想不到的状况，比如Select组件在渲染的过程中会报错，导致测试用例无法正常执行。

 报错
 
 ```
 
 try to mount a component with el-select inside throw :

---> <ElSelectDropdown>
       <Transition>
         <ElSelect>
           <ElFormItem>
             <ElForm>
               <Anonymous>
                 <Root>
TypeError: Cannot read property '$el' of undefined
at VueComponent.mounted (/Users/mhanne/src/report-builder/viewer/node_modules/element-ui/lib/element-ui.common.js:9131:54)
at callHook (/Users/mhanne/src/report-builder/viewer/node_modules/vue/dist/vue.runtime.common.js:2919:21)
at Object.insert (/Users/mhanne/src/report-builder/viewer/node_modules/vue/dist/vue.runtime.common.js:4156:7)
at invokeInsertHook (/Users/mhanne/src/report-builder/viewer/node_modules/vue/dist/vue.runtime.common.js:5958:28)

 ```
 
 最后发现是因为Vue Test Utils 使用了默认的存根transitionStub，导致了组件中出现了错误，通过禁用默认后，解决这个错误。
 
  ```
  import { config } from '@vue/test-utils'
  config.stubs.transition = false
  ```
 
#### jsdom 中getComputedStyle()调用报错。
 
 重写window中的getComputedStyle方法后解决这个错误。
 
   ```
   
   const { getComputedStyle } = window;
window.getComputedStyle = function getComputedStyleStub(el) {
	return {
		...getComputedStyle(el),
		transitionDelay: "",
		transitionDuration: "",
		animationDelay: "",
		animationDuration: "",
		getPropertyValue() {}
	};
};
