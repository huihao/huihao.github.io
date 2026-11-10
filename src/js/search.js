/**
 * 站内搜索：索引由 Pagefind 在构建时生成（npm run build:search），
 * 这里只负责查询与渲染，界面沿用站点的设计系统。
 */
(function () {
    'use strict';

    var root = document.querySelector('[data-search]');

    if (!root) {
        return;
    }

    var input = root.querySelector('[data-search-input]');
    var results = root.querySelector('[data-search-results]');
    var status = root.querySelector('[data-search-status]');
    var clear = root.querySelector('[data-search-clear]');
    var pagefindUrl = root.getAttribute('data-pagefind') || '/pagefind/pagefind.js';
    var timer = null;
    var ready = null;

    function text(value) {
        return value === undefined || value === null ? '' : String(value);
    }

    function render(items) {
        results.innerHTML = '';

        if (!items.length) {
            status.textContent = '没有找到相关内容，换个关键词试试。';
            return;
        }

        items.forEach(function (item) {
            var li = document.createElement('li');
            var link = document.createElement('a');
            var title = document.createElement('span');
            var excerpt = document.createElement('span');

            link.className = 'search-result';
            link.href = item.url;

            // Pagefind v1 把标题放在 meta 里，摘要在 excerpt 里
            title.className = 'search-result-title';
            title.textContent = (item.meta && item.meta.title) || item.url;

            excerpt.className = 'search-result-excerpt';
            excerpt.innerHTML = item.excerpt || '';

            link.appendChild(title);
            link.appendChild(excerpt);

            li.appendChild(link);
            results.appendChild(li);
        });
    }

    function run(query) {
        var term = text(query).trim();

        if (!term) {
            results.innerHTML = '';
            status.textContent = '输入关键词开始搜索。';
            clear.hidden = true;
            return;
        }

        clear.hidden = false;
        status.textContent = '搜索中…';

        // 索引可能还在加载，先等它就绪再查
        ready
            .then(function (module) {
                return module ? module.search(term) : null;
            })
            .then(function (response) {
                if (!response) {
                    return;
                }

                var list = response.results.slice(0, 20);

                return Promise.all(
                    list.map(function (result) {
                        return result.data();
                    })
                ).then(function (data) {
                    status.textContent = '找到 ' + data.length + ' 条结果';
                    render(data);
                });
            })
            .catch(function () {
                status.textContent = '搜索失败，请稍后再试。';
            });
    }

    function schedule(query) {
        window.clearTimeout(timer);
        timer = window.setTimeout(function () {
            run(query);
        }, 180);
    }

    input.addEventListener('input', function () {
        schedule(input.value);
    });

    input.addEventListener('keydown', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            run(input.value);

            var first = results.querySelector('.search-result');

            if (first) {
                first.focus();
            }
        }
    });

    clear.addEventListener('click', function () {
        input.value = '';
        input.focus();
        run('');
    });

    ready = import(pagefindUrl).then(function (module) {
        if (typeof module.options === 'function') {
            module.options({ excerptLength: 32 });
        }

        return module;
    });

    status.textContent = '正在加载搜索索引…';

    ready
        .then(function () {
            var params = new URLSearchParams(window.location.search);
            var initial = params.get('q');

            if (initial) {
                input.value = initial;
                run(initial);
            } else {
                status.textContent = '输入关键词开始搜索。';
            }
        })
        .catch(function () {
            status.textContent = '搜索索引尚未生成，请在本地运行 npm run build:search。';
        });
}());
