/**
 * The small behaviours of the site.
 *
 * Everything degrades gracefully: without JavaScript the page still reads
 * and navigates, it just does not show the progress, the copy buttons or
 * the reading time.
 */
(function () {
  'use strict';

  /* ------------------------------------------------------------------ */
  /* Reading progress of a post                                         */
  /* ------------------------------------------------------------------ */
  var progress = document.querySelector('.reading-progress');
  var article = document.querySelector('.markdown-body');

  function updateProgress() {
    if (!progress || !article) {
      return;
    }

    var rect = article.getBoundingClientRect();
    var viewport = window.innerHeight;
    var scrollable = rect.height - viewport;
    var ratio;

    if (scrollable <= 0) {
      ratio = rect.top <= viewport / 2 ? 1 : 0;
    } else {
      ratio = -rect.top / scrollable;
    }

    ratio = Math.max(0, Math.min(1, ratio));
    progress.style.setProperty('--progress', ratio.toFixed(4));
  }

  /* ------------------------------------------------------------------ */
  /* Copy buttons on the code blocks                                    */
  /* ------------------------------------------------------------------ */
  function addCopyButtons() {
    var blocks = document.querySelectorAll('.markdown-body pre');

    Array.prototype.forEach.call(blocks, function (pre) {
      var wrapper = document.createElement('div');
      var button = document.createElement('button');
      var code = pre.querySelector('code');
      var language = '';

      /* Shiki marks the block with `data-language` and keeps the language
         class on the <code> element; Rouge puts it on the wrapper
         (`div.language-js.highlighter-rouge`). */
      var language = pre.getAttribute('data-language') || '';

      var preMatch = !language && pre.className ? pre.className.match(/language-([\w-]+)/) : null;

      if (preMatch) {
        language = preMatch[1];
      }

      var highlighter = pre.closest ? pre.closest('.highlighter-rouge') : null;

      if (highlighter && !language) {
        Array.prototype.forEach.call(highlighter.classList, function (name) {
          if (name.indexOf('language-') === 0 && !language) {
            language = name.slice('language-'.length);
          }
        });
      }

      if (!language && code) {
        var match = code.className.match(/language-([\w-]+)/);

        if (match) {
          language = match[1];
        }
      }

      wrapper.className = 'code-block';
      pre.parentNode.insertBefore(wrapper, pre);

      /* The bar of the block: the language on the left, the copy action
         on the right, the way an editor draws it. */
      var head = document.createElement('div');
      var languageLabel = document.createElement('span');

      head.className = 'code-head';
      languageLabel.className = 'code-lang';
      languageLabel.textContent = language || 'code';

      head.appendChild(languageLabel);

      wrapper.appendChild(head);
      wrapper.appendChild(pre);

      button.type = 'button';
      button.className = 'copy-code';
      button.innerHTML = '<span class="copy-action">复制</span>';

      button.addEventListener('click', function () {
        var text = code ? code.innerText : pre.innerText;
        var action = button.querySelector('.copy-action');

        if (!navigator.clipboard) {
          return;
        }

        navigator.clipboard.writeText(text).then(function () {
          button.classList.add('is-copied');

          if (action) {
            action.textContent = '已复制';
          }

          window.setTimeout(function () {
            button.classList.remove('is-copied');

            if (action) {
              action.textContent = '复制';
            }
          }, 1600);
        });
      });

      head.appendChild(button);
    });
  }

  /* ------------------------------------------------------------------ */
  /* Reading time                                                       */
  /* ------------------------------------------------------------------ */
  function addReadingTime() {
    var target = document.querySelector('[data-read-time]');

    if (!target || !article) {
      return;
    }

    var text = article.innerText || '';
    var cjk = text.match(/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/g) || [];
    var latin = text.replace(/[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]/g, ' ').match(/[A-Za-z0-9]+/g) || [];
    var minutes = Math.max(1, Math.round(cjk.length / 400 + latin.length / 220));

    target.textContent = '约 ' + minutes + ' 分钟';
  }

  /* ------------------------------------------------------------------ */
  /* Back to top                                                        */
  /* ------------------------------------------------------------------ */
  function addBackToTop() {
    if (!article) {
      return;
    }

    var button = document.createElement('button');

    button.type = 'button';
    button.className = 'back-to-top';
    button.setAttribute('aria-label', '回到顶部');
    button.textContent = '↑';

    button.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    document.body.appendChild(button);

    function update() {
      button.classList.toggle('is-visible', window.scrollY > 600);
    }

    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ------------------------------------------------------------------ */
  /* A missing cover image should not leave a hole in the card          */
  /* ------------------------------------------------------------------ */
  function hideBrokenImages() {
    var images = document.querySelectorAll('.img img, .markdown-body img');

    Array.prototype.forEach.call(images, function (image) {
      image.addEventListener('error', function () {
        var cover = image.closest('.cover');

        if (cover) {
          cover.remove();
        } else {
          image.remove();
        }
      });
    });
  }

  /* ------------------------------------------------------------------ */
  /* Sharing. On a phone the Web Share API opens the system share sheet, */
  /* which already contains X, WeChat and the other apps of the visitor.  */
  /* On the desktop there is no such sheet, so a small menu with the     */
  /* intent links takes its place.                                       */
  /* ------------------------------------------------------------------ */
  function initShare() {
    var root = document.querySelector('[data-share]');

    if (!root) {
      return;
    }

    var toggle = root.querySelector('[data-share-toggle]');
    var menu = root.querySelector('.share-menu');
    var copy = root.querySelector('[data-share-copy]');
    var url = root.getAttribute('data-url') || window.location.href;
    var title = root.getAttribute('data-title') || document.title;

    if (!toggle || !menu) {
      return;
    }

    function closeMenu() {
      menu.hidden = true;
      toggle.setAttribute('aria-expanded', 'false');
    }

    toggle.addEventListener('click', function () {
      if (navigator.share) {
        navigator
          .share({ title: title, text: title, url: url })
          .catch(function (error) {
            /* The visitor closed the sheet, nothing to do. */
            if (!error || error.name !== 'AbortError') {
              closeMenu();
            }
          });

        return;
      }

      var open = menu.hidden;

      menu.hidden = !open;
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });

    if (copy) {
      var label = copy.querySelector('[data-share-copy-label]');
      var copied = copy.getAttribute('data-share-copied-label') || label.textContent;

      copy.addEventListener('click', function () {
        function done() {
          if (label) {
            label.textContent = copied;
          }

          window.setTimeout(function () {
            if (label) {
              label.textContent = label.getAttribute('data-share-default') || label.textContent;
            }
          }, 2000);
        }

        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(done).catch(done);
        } else {
          done();
        }

        closeMenu();
      });

      if (label) {
        label.setAttribute('data-share-default', label.textContent);
      }
    }

    document.addEventListener('click', function (event) {
      if (!root.contains(event.target)) {
        closeMenu();
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        closeMenu();
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* The language switch above the article list                           */
  /*                                                                     */
  /* Every article shows up once. Switching the language swaps the       */
  /* title, the summary, the date and the links of the cards that have    */
  /* a translation; the others stay as they are.                         */
  /* ------------------------------------------------------------------ */
  function setupLanguageFilter() {
    var root = document.querySelector('[data-lang-filter]');

    if (!root) {
      return;
    }

    var buttons = root.querySelectorAll('[data-lang-filter-item]');
    var cards = document.querySelectorAll('#main .article[data-lang]');
    var languages = ['zh', 'en'];

    function moreLabel(language) {
      return language === 'en' ? 'Read more' : '阅读全文';
    }

    function badgeLabel(language) {
      return language === 'en' ? 'EN' : '中文';
    }

    function apply(language) {
      Array.prototype.forEach.call(buttons, function (button) {
        var active = button.getAttribute('data-lang-filter-item') === language;

        button.classList.toggle('is-active', active);
        button.setAttribute('aria-pressed', active ? 'true' : 'false');
      });

      Array.prototype.forEach.call(cards, function (card) {
        var data;

        try {
          data = JSON.parse(card.getAttribute('data-i18n') || '{}');
        } catch (error) {
          return;
        }

        var entry = data[language];

        if (!entry) {
          return;
        }

        /* The title of a card is a second level heading; the first level
           one belongs to the page itself. */
        var title = card.querySelector('h2 a') || card.querySelector('h1 a');
        var tip = card.querySelector('.tip');
        var date = card.querySelector('.date span');
        var more = card.querySelector('.more');
        var cover = card.querySelector('.cover');
        var badge = card.querySelector('.lang-badge');
        var cat = card.querySelector('.cat');

        if (title) {
          title.textContent = entry.title;
          title.setAttribute('href', entry.url);
        }

        if (tip) {
          tip.textContent = entry.desc;
        }

        if (date) {
          date.textContent = entry.date;
        }

        if (more) {
          more.setAttribute('href', entry.url);

          var label = more.querySelector('span');

          if (label) {
            label.textContent = moreLabel(language);
          }
        }

        if (cat && entry.cat) {
          cat.textContent = entry.cat;
        }

        if (cover) {
          cover.setAttribute('href', entry.url);
        }

        if (badge) {
          var other = languages.filter(function (item) {
            return item !== language;
          })[0];
          var otherEntry = data[other];

          badge.textContent = badgeLabel(other);

          if (otherEntry) {
            badge.setAttribute('href', otherEntry.url);
          }
        }
      });

      var url = new URL(window.location.href);

      url.searchParams.set('lang', language);

      window.history.replaceState({}, '', url);
    }

    Array.prototype.forEach.call(buttons, function (button) {
      button.addEventListener('click', function () {
        apply(button.getAttribute('data-lang-filter-item'));
      });
    });

    var initial = new URLSearchParams(window.location.search).get('lang');

    apply(languages.indexOf(initial) >= 0 ? initial : 'zh');
  }

  /* ------------------------------------------------------------------ */
  /* The bar grows a hairline shadow once the page is scrolled           */
  /* ------------------------------------------------------------------ */
  function updateBar() {
    var bar = document.querySelector('.top-line');

    if (!bar) {
      return;
    }

    bar.classList.toggle('is-scrolled', window.scrollY > 8);
  }

  /* ------------------------------------------------------------------ */
  /* The appearance switch                                               */
  /* ------------------------------------------------------------------ */
  var THEME_KEY = 'theme';

  function storedTheme() {
    try {
      return window.localStorage.getItem(THEME_KEY);
    } catch (error) {
      return null;
    }
  }

  function systemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function currentTheme() {
    var stored = storedTheme();

    return stored === 'light' || stored === 'dark' ? stored : systemTheme();
  }

  function applyTheme(theme) {
    var root = document.documentElement;
    var button = document.querySelector('.theme-toggle');
    var meta = document.querySelector('meta[name="theme-color"]');
    var dark = theme === 'dark';

    root.setAttribute('data-theme', theme);
    root.style.colorScheme = theme;

    if (meta) {
      meta.setAttribute('content', dark ? '#000000' : '#ffffff');
    }

    if (button) {
      button.setAttribute('aria-pressed', dark ? 'true' : 'false');
      button.setAttribute('aria-label', dark ? '切换到明亮模式' : '切换到暗黑模式');
      button.setAttribute('title', dark ? '切换到明亮模式' : '切换到暗黑模式');
    }
  }

  function initTheme() {
    applyTheme(currentTheme());

    var button = document.querySelector('.theme-toggle');

    if (!button) {
      return;
    }

    button.addEventListener('click', function () {
      var next = currentTheme() === 'dark' ? 'light' : 'dark';

      try {
        window.localStorage.setItem(THEME_KEY, next);
      } catch (error) {
        /* A private window refuses to keep the choice. The page still
           switches, it just starts over on the next visit. */
      }

      applyTheme(next);
    });

    /* The system keeps its say as long as the visitor has not chosen. */
    var query = window.matchMedia('(prefers-color-scheme: dark)');

    function onChange(event) {
      if (!storedTheme()) {
        applyTheme(event.matches ? 'dark' : 'light');
      }
    }

    if (query.addEventListener) {
      query.addEventListener('change', onChange);
    } else if (query.addListener) {
      query.addListener(onChange);
    }
  }

  /* ------------------------------------------------------------------ */
  /* A link to every heading of the body                                 */
  /* ------------------------------------------------------------------ */
  function addHeadingAnchors() {
    var headings = document.querySelectorAll('.markdown-body h2, .markdown-body h3');

    Array.prototype.forEach.call(headings, function (heading) {
      if (!heading.id) {
        return;
      }

      var anchor = document.createElement('a');

      anchor.className = 'heading-anchor';
      anchor.href = '#' + heading.id;
      anchor.setAttribute('aria-label', '链接到 ' + heading.textContent);
      anchor.textContent = '#';

      heading.appendChild(anchor);
    });
  }

  /* ------------------------------------------------------------------ */
  /* The table of contents follows the reader                             */
  /* ------------------------------------------------------------------ */
  function updateToc() {
    var toc = document.querySelector('.toc');

    if (!toc) {
      return;
    }

    var items = toc.querySelectorAll('.toc-item');

    if (!items.length) {
      return;
    }

    var offset = 120;
    var current = null;

    Array.prototype.forEach.call(items, function (item) {
      var link = item.querySelector('a');
      var heading = link ? document.getElementById(link.getAttribute('href').slice(1)) : null;

      if (heading && heading.getBoundingClientRect().top - offset <= 0) {
        current = item;
      }
    });

    Array.prototype.forEach.call(items, function (item) {
      item.classList.toggle('is-active', item === current);
    });
  }

  /* ------------------------------------------------------------------ */
  /* Boot                                                               */
  /* ------------------------------------------------------------------ */
  var ticking = false;

  function onScroll() {
    if (ticking) {
      return;
    }

    ticking = true;
    window.requestAnimationFrame(function () {
      updateProgress();
      updateBar();
      updateToc();
      ticking = false;
    });
  }

  initTheme();
  addCopyButtons();
  addReadingTime();
  addBackToTop();
  addHeadingAnchors();
  hideBrokenImages();
  setupLanguageFilter();
  initShare();
  updateProgress();
  updateBar();
  updateToc();

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
})();
