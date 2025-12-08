
# ./.pytest_cache/README.md

# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.
-e


# ./.venv/lib/python3.12/site-packages/altair/jupyter/js/README.md

# JupyterChart
This directory contains the JavaScript portion of the Altair `JupyterChart`. The `JupyterChart` is based on the [AnyWidget](https://anywidget.dev/) project.
-e


# ./.venv/lib/python3.12/site-packages/fastapi_sso-0.10.0.dist-info/LICENSE.md

# MIT License

Copyright (c) 2021 Tomas Votava <info@tomasvotava.eu>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-e


# ./.venv/lib/python3.12/site-packages/httpcore-1.0.9.dist-info/licenses/LICENSE.md

Copyright © 2020, [Encode OSS Ltd](https://www.encode.io/).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-e


# ./.venv/lib/python3.12/site-packages/httpx-0.28.1.dist-info/licenses/LICENSE.md

Copyright © 2019, [Encode OSS Ltd](https://www.encode.io/).
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-e


# ./.venv/lib/python3.12/site-packages/idna-3.11.dist-info/licenses/LICENSE.md

BSD 3-Clause License

Copyright (c) 2013-2025, Kim Davies and contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-e


# ./.venv/lib/python3.12/site-packages/langsmith/cli/README.md

# DOCKER-COMPOSE MOVED
All documentation for docker-compose has been moved to the helm repository.
You can find it [here](https://github.com/langchain-ai/helm/blob/main/charts/langsmith/docker-compose/docker-compose.yaml)
-e


# ./.venv/lib/python3.12/site-packages/libcst/_parser/conversions/README.md

# Parser Conversions Developer Guide

Parser conversions take grammar productions and convert them to CST nodes, or to some
"partial" value that will later be converted to a CST node.

The grammar production that parser conversions are associated with is co-located
alongside the conversion function using our `@with_production` decorator. This is
similar to the API that [rply](https://github.com/alex/rply/) uses.

Grammar productions are collected when the parser is first called, and converted into a
state machine by Parso's pgen2 fork.

Unlike rply's API, productions are not automatically gathered, because that would be
dependent on implicit import-time side-effects. Instead all conversion functions must be
listed in `_grammar.py`.

# What's a production?

A production is a line in our BNF-like grammar definition. A production has a name (the
first argument of `@with_production`), and a sequence of children (the second argument
of `@with_production`).

Python's full grammar is here: https://docs.python.org/3/reference/grammar.html

We use Parso's fork of pgen2, and therefore support the same BNF-like syntax that
Python's documentation uses.

# Why is everything `Any`-typed? Isn't that bad?

Yes, `Any` types indicate a gap in static type coverage. Unfortunately, this isn't
easily solved.

The value of `children` given to a conversion function is dependent on textual grammar
representation and pgen2's implementation, which the type system is unaware of. Unless
we extend the type system to support pgen2 (unlikely) or add a layer of
machine-generated code (possible, but we're not there), there's no way for the type
system to validate any annotations on `children`.

We could add annotations to `children`, but they're usually complicated types (so they
wouldn't be very human-readable), and they wouldn't actually provide any type safety
because the type checker doesn't know about them.

Similarly, we could annotate return type annotations, but that's just duplicating the
type we're already expressing in our return statement (so it doesn't improve readability
much), and it's not providing any static type safety.

We do perform runtime type checks inside tests, and we hope that this test coverage will
help compensate for the lack of static type safety.

# Where's the whitespace?

The most important differentiation between an Abstract Syntax Tree and a Concrete Syntax
Tree (for our purposes) is that the CST contains enough information to exactly reproduce
the original program. This means that we must somehow capture and store whitespace.

The grammar does not contain whitespace information, and there are no explicit tokens
for whitespace. If the grammar did contain whitespace information, the grammar likely
wouldn't be LL(1), and while we could use another context free grammar parsing
algorithm, it would add complexity and likely wouldn't be as efficient.

Instead, we have a hand-written re-entrant recursive-descent parser for whitespace. It's
the responsibility of conversion functions to call into this parser given whitespace
states before and after a token.

# Token and WhitespaceState Data Structures

A token is defined as:

```
class Token:
    type: TokenType
    string: str
    # The start of where `string` is in the source, not including leading whitespace.
    start_pos: Tuple[int, int]
    # The end of where `string` is in the source, not including trailing whitespace.
    end_pos: Tuple[int, int]
    whitespace_before: WhitespaceState
    whitespace_after: WhitespaceState
```

Or, in the order that these pieces appear lexically in a parsed program:

```
+-------------------+--------+-------------------+
| whitespace_before | string | whitespace_after  |
| (WhitespaceState) | (str)  | (WhitespaceState) |
+-------------------+--------+-------------------+
```

Tokens are immutable, but only shallowly, because their whitespace fields are mutable
WhitespaceState objects.

WhitespaceStates are opaque objects that the whitespace parser consumes and mutates.
WhitespaceState nodes are shared across multiple tokens, so `whitespace_after` is the
same object as `whitespace_before` in the next token.

# Parser Execution Order

The parser generator we use (`pgen2`) is bottom-up, meaning that children productions
are called before their parents. In contrast, our hand written whitespace parser is
top-down.

Inside each production, child conversion functions are called from left to right.

As an example, assume we're given the following simple grammar and program:

```
add_expr: NUMBER ['+' add_expr]
```

```
1 + 2 + 3
```

which forms the parse tree:

```
     [H] add_expr
    /      |      \
[A] 1   [B] '+'   [G] add_expr
                 /      |      \
             [C] 2   [D] '+'   [F] add_expr
                                    |
                                  [E] 3
```

The conversion functions would be called in the labeled alphabetical order, with `A`
converted first, and `H` converted last.

# Who owns whitespace?

There's a lot of holes between you and a correct whitespace representation, but these
can be divided into a few categories of potential mistakes:

## Forgetting to Parse Whitespace

Fortunately, the inverse (parsing the same whitespace twice) should not be possible,
because whitespace is "consumed" by the whitespace parser.

This kind of mistake is easily caught with tests.

## Assigning Whitespace to the Wrong Owner

This is probably the easiest mistake to make. The general convention is that the
top-most possible node owns whitespace, but in a bottom-up parser like ours, the
children are parsed before their parents.

In contrast, the best owner for whitespace in our tree when there's multiple possible
owners is usually the top-most node.

As an example, assume we have the following grammar and program:

```
simple_stmt: (pass_stmt ';')* NEWLINE
```

```
pass; # comment
```

Since both `cst.Semicolon` and `cst.SimpleStatement` can both store some whitespace
after themselves, there's some ambiguity about who should own the space character before
the comment. However, since `cst.SimpleStatement` is the parent, the convention is that
it should own it.

Unfortunately, since nodes are processed bottom-to-top and left-to-right, the semicolon
under `simple_stmt` will get processed before `simple_stmt` is. This means that in a
naive implementation, the semicolon's conversion function would have a chance to consume
the whitespace before `simple_stmt` can.

To solve this problem, you must "fix" the whitespace in the parent node's conversion
function or grammar. This can be done in a number of ways. In order of preference:

1. Split the child's grammar production into two separate productions, one that consumes
   it's leading or trailing whitespace, and one that doesn't. Depending on the parent,
   use the appropriate version of the child.
2. Construct a "partial" node in the child that doesn't consume the whitespace, and then
   consume the correct whitespace in the parent. Be careful about what whitespace a
   node's siblings consume.
3. "Steal" the whitespace from the child by replacing the child with a new version that
   doesn't have the whitespace.

This mistake is probably hard to catch with tests, because the CST will still reprint
correctly, but it creates ergonomic issues for tools consuming the CST.

## Consuming Whitespace in the Wrong Order

This mistake is probably is the hardest to make by accident, but it could still happen,
and may be hard to catch with tests.

Given the following piece of code:

```
pass # trailing
# empty line
pass
```

The first statement should own `# trailing` (parsed using `parse_trailing_whitespace`).
The second statement then should `# empty line` (parsed using `parse_empty_lines`).

However, it's possible that if you somehow called `parse_empty_lines` on the second
statement before calling `parse_trailing_whitespace` on the first statement,
`parse_empty_lines` could accidentally end up consuming the `# trailing` comment,
because `parse_trailing_whitespace` hasn't yet consumed it.

However, this circumstance is unlikely, because you'd explicitly have to handle the
children out-of-order, and we have assertions inside the whitespace parser to prevent
some possible mistakes, like the one described above.
-e


# ./.venv/lib/python3.12/site-packages/mdit_py_plugins/container/README.md

# markdown-it-container

[![Build Status](https://img.shields.io/travis/markdown-it/markdown-it-container/master.svg?style=flat)](https://travis-ci.org/markdown-it/markdown-it-container)
[![NPM version](https://img.shields.io/npm/v/markdown-it-container.svg?style=flat)](https://www.npmjs.org/package/markdown-it-container)
[![Coverage Status](https://img.shields.io/coveralls/markdown-it/markdown-it-container/master.svg?style=flat)](https://coveralls.io/r/markdown-it/markdown-it-container?branch=master)

> Plugin for creating block-level custom containers for [markdown-it](https://github.com/markdown-it/markdown-it) markdown parser.

__v2.+ requires `markdown-it` v5.+, see changelog.__

With this plugin you can create block containers like:

```
::: warning
*here be dragons*
:::
```

.... and specify how they should be rendered. If no renderer defined, `<div>` with
container name class will be created:

```html
<div class="warning">
<em>here be dragons</em>
</div>
```

Markup is the same as for [fenced code blocks](http://spec.commonmark.org/0.18/#fenced-code-blocks).
Difference is, that marker use another character and content is rendered as markdown markup.


## Installation

node.js, browser:

```bash
$ npm install markdown-it-container --save
$ bower install markdown-it-container --save
```


## API

```js
var md = require('markdown-it')()
            .use(require('markdown-it-container'), name [, options]);
```

Params:

- __name__ - container name (mandatory)
- __options:__
   - __validate__ - optional, function to validate tail after opening marker, should
     return `true` on success.
   - __render__ - optional, renderer function for opening/closing tokens.
   - __marker__ - optional (`:`), character to use in delimiter.


## Example

```js
var md = require('markdown-it')();

md.use(require('markdown-it-container'), 'spoiler', {

  validate: function(params) {
    return params.trim().match(/^spoiler\s+(.*)$/);
  },

  render: function (tokens, idx) {
    var m = tokens[idx].info.trim().match(/^spoiler\s+(.*)$/);

    if (tokens[idx].nesting === 1) {
      // opening tag
      return '<details><summary>' + md.utils.escapeHtml(m[1]) + '</summary>\n';

    } else {
      // closing tag
      return '</details>\n';
    }
  }
});

console.log(md.render('::: spoiler click me\n*content*\n:::\n'));

// Output:
//
// <details><summary>click me</summary>
// <p><em>content</em></p>
// </details>
```

## License

[MIT](https://github.com/markdown-it/markdown-it-container/blob/master/LICENSE)
-e


# ./.venv/lib/python3.12/site-packages/mdit_py_plugins/deflist/README.md

# markdown-it-deflist

[![Build Status](https://img.shields.io/travis/markdown-it/markdown-it-deflist/master.svg?style=flat)](https://travis-ci.org/markdown-it/markdown-it-deflist)
[![NPM version](https://img.shields.io/npm/v/markdown-it-deflist.svg?style=flat)](https://www.npmjs.org/package/markdown-it-deflist)
[![Coverage Status](https://img.shields.io/coveralls/markdown-it/markdown-it-deflist/master.svg?style=flat)](https://coveralls.io/r/markdown-it/markdown-it-deflist?branch=master)

> Definition list (`<dl>`) tag plugin for [markdown-it](https://github.com/markdown-it/markdown-it) markdown parser.

__v2.+ requires `markdown-it` v5.+, see changelog.__

Syntax is based on [pandoc definition lists](http://johnmacfarlane.net/pandoc/README.html#definition-lists).


## Install

node.js, browser:

```bash
npm install markdown-it-deflist --save
bower install markdown-it-deflist --save
```

## Use

```js
var md = require('markdown-it')()
            .use(require('markdown-it-deflist'));

md.render(/*...*/);
```

_Differences in browser._ If you load script directly into the page, without
package system, module will add itself globally as `window.markdownitDeflist`.


## License

[MIT](https://github.com/markdown-it/markdown-it-deflist/blob/master/LICENSE)
-e


# ./.venv/lib/python3.12/site-packages/mdit_py_plugins/texmath/README.md

[![License](https://img.shields.io/github/license/goessner/markdown-it-texmath.svg)](https://github.com/goessner/markdown-it-texmath/blob/master/licence.txt)
[![npm](https://img.shields.io/npm/v/markdown-it-texmath.svg)](https://www.npmjs.com/package/markdown-it-texmath)
[![npm](https://img.shields.io/npm/dt/markdown-it-texmath.svg)](https://www.npmjs.com/package/markdown-it-texmath)

# markdown-it-texmath

Add TeX math equations to your Markdown documents rendered by [markdown-it](https://github.com/markdown-it/markdown-it) parser. [KaTeX](https://github.com/Khan/KaTeX) is used as a fast math renderer.

## Features
Simplify the process of authoring markdown documents containing math formulas.
This extension is a comfortable tool for scientists, engineers and students with markdown as their first choice document format.

* Macro support
* Simple formula numbering
* Inline math with tables, lists and blockquote.
* User setting delimiters:
  * `'dollars'` (default)
    * inline: `$...$`
    * display: `$$...$$`
    * display + equation number: `$$...$$ (1)`
  * `'brackets'`
    * inline: `\(...\)`
    * display: `\[...\]`
    * display + equation number: `\[...\] (1)`
  * `'gitlab'`
    * inline: ``$`...`$``
    * display: `` ```math ... ``` ``
    * display + equation number: `` ```math ... ``` (1)``
  * `'julia'`
    * inline: `$...$`  or ``` ``...`` ```
    * display: `` ```math ... ``` ``
    * display + equation number: `` ```math ... ``` (1)``
  * `'kramdown'`
    * inline: ``$$...$$``
    * display: `$$...$$`
    * display + equation number: `$$...$$ (1)`

## Show me

View a [test table](https://goessner.github.io/markdown-it-texmath/index.html).

[try it out ...](https://goessner.github.io/markdown-it-texmath/markdown-it-texmath-demo.html)

## Use with `node.js`

Install the extension. Verify having `markdown-it` and `katex` already installed .
```
npm install markdown-it-texmath
```
Use it with JavaScript.
```js
let kt = require('katex'),
    tm = require('markdown-it-texmath').use(kt),
    md = require('markdown-it')().use(tm,{delimiters:'dollars',macros:{"\\RR": "\\mathbb{R}"}});

md.render('Euler\'s identity \(e^{i\pi}+1=0\) is a beautiful formula in $\\RR 2$.')
```

## Use in Browser
```html
<html>
<head>
  <meta charset='utf-8'>
  <link rel="stylesheet" href="katex.min.css">
  <link rel="stylesheet" href="texmath.css">
  <script src="markdown-it.min.js"></script>
  <script src="katex.min.js"></script>
  <script src="texmath.js"></script>
</head>
<body>
  <div id="out"></div>
  <script>
    let md;
    document.addEventListener("DOMContentLoaded", () => {
        const tm = texmath.use(katex);
        md = markdownit().use(tm,{delimiters:'dollars',macros:{"\\RR": "\\mathbb{R}"}});
        out.innerHTML = md.render('Euler\'s identity $e^{i\pi}+1=0$ is a beautiful formula in //RR 2.');
    })
  </script>
</body>
</html>
```
## CDN

Use following links for `texmath.js` and `texmath.css`
* `https://gitcdn.xyz/cdn/goessner/markdown-it-texmath/master/texmath.js`
* `https://gitcdn.xyz/cdn/goessner/markdown-it-texmath/master/texmath.css`

## Dependencies

* [`markdown-it`](https://github.com/markdown-it/markdown-it): Markdown parser done right. Fast and easy to extend.
* [`katex`](https://github.com/Khan/KaTeX): This is where credits for fast rendering TeX math in HTML go to.

## ToDo

 nothing yet

## FAQ

* __`markdown-it-texmath` with React Native does not work, why ?__
  * `markdown-it-texmath` is using regular expressions with `y` [(sticky) property](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/RegExp/sticky) and cannot avoid this. The use of the `y` flag in regular expressions means the plugin is not compatible with React Native (which as of now doesn't support it and throws an error `Invalid flags supplied to RegExp constructor`).

## CHANGELOG

###  [0.6.0] on October 04, 2019
* Add support for [Julia Markdown](https://docs.julialang.org/en/v1/stdlib/Markdown/) on [request](https://github.com/goessner/markdown-it-texmath/issues/15).

###  [0.5.5] on February 07, 2019
* Remove [rendering bug with brackets delimiters](https://github.com/goessner/markdown-it-texmath/issues/9).

###  [0.5.4] on January 20, 2019
* Remove pathological [bug within blockquotes](https://github.com/goessner/mdmath/issues/50).

###  [0.5.3] on November 11, 2018
* Add support for Tex macros (https://katex.org/docs/supported.html#macros) .
* Bug with [brackets delimiters](https://github.com/goessner/markdown-it-texmath/issues/9) .

###  [0.5.2] on September 07, 2018
* Add support for [Kramdown](https://kramdown.gettalong.org/) .

###  [0.5.0] on August 15, 2018
* Fatal blockquote bug investigated. Implemented workaround to vscode bug, which has finally gone with vscode 1.26.0 .

###  [0.4.6] on January 05, 2018
* Escaped underscore bug removed.

###  [0.4.5] on November 06, 2017
* Backslash bug removed.

###  [0.4.4] on September 27, 2017
* Modifying the `block` mode regular expression with `gitlab` delimiters, so removing the `newline` bug.

## License

`markdown-it-texmath` is licensed under the [MIT License](./license.txt)

 © [Stefan Gössner](https://github.com/goessner)
-e


# ./.venv/lib/python3.12/site-packages/narwhals-2.12.0.dist-info/licenses/LICENSE.md

MIT License

Copyright (c) 2024, Marco Gorelli

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-e


# ./.venv/lib/python3.12/site-packages/numpy/random/LICENSE.md

**This software is dual-licensed under the The University of Illinois/NCSA
Open Source License (NCSA) and The 3-Clause BSD License**

# NCSA Open Source License
**Copyright (c) 2019 Kevin Sheppard. All rights reserved.**

Developed by: Kevin Sheppard (<kevin.sheppard@economics.ox.ac.uk>,
<kevin.k.sheppard@gmail.com>)
[http://www.kevinsheppard.com](http://www.kevinsheppard.com)

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal with
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimers.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimers in the documentation and/or
other materials provided with the distribution.

Neither the names of Kevin Sheppard, nor the names of any contributors may be
used to endorse or promote products derived from this Software without specific
prior written permission.

**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS WITH
THE SOFTWARE.**


# 3-Clause BSD License
**Copyright (c) 2019 Kevin Sheppard. All rights reserved.**

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

**THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
THE POSSIBILITY OF SUCH DAMAGE.**

# Components

Many parts of this module have been derived from original sources,
often the algorithm's designer. Component licenses are located with
the component code.
-e


# ./.venv/lib/python3.12/site-packages/opentelemetry/sdk/metrics/_internal/exponential_histogram/mapping/ieee_754.md

# IEEE 754 Explained

IEEE 754 is a standard that defines a way to represent certain mathematical
objects using binary numbers.

## Binary Number Fields

The binary numbers used in IEEE 754 can have different lengths, the length that
is interesting for the purposes of this project is 64 bits. These binary
numbers are made up of 3 contiguous fields of bits, from left to right:

1. 1 sign bit
2. 11 exponent bits
3. 52 mantissa bits

Depending on the values these fields have, the represented mathematical object
can be one of:

* Floating point number
* Zero
* NaN
* Infinite

## Floating Point Numbers

IEEE 754 represents a floating point number $f$ using an exponential
notation with 4 components: $sign$, $mantissa$, $base$ and $exponent$:

$$f = sign \times mantissa \times base ^ {exponent}$$

There are two possible representations of floating point numbers:
_normal_ and _denormal_, which have different valid values for
their $mantissa$ and $exponent$ fields.

### Binary Representation

$sign$, $mantissa$, and $exponent$ are represented in binary, the
representation of each component has certain details explained next.

$base$ is always $2$ and it is not represented in binary.

#### Sign

$sign$ can have 2 values:

1. $1$ if the `sign` bit is `0`
2. $-1$ if the `sign` bit is `1`.

#### Mantissa

##### Normal Floating Point Numbers

$mantissa$ is a positive fractional number whose integer part is $1$, for example
$1.2345 \dots$. The `mantissa` bits represent only the fractional part and the
$mantissa$ value can be calculated as:

$$mantissa = 1 + \sum_{i=1}^{52} b_{i} \times 2^{-i} = 1 + \frac{b_{1}}{2^{1}} + \frac{b_{2}}{2^{2}} + \dots + \frac{b_{51}}{2^{51}} + \frac{b_{52}}{2^{52}}$$

Where $b_{i}$ is:

1. $0$ if the bit at the position `i - 1` is `0`.
2. $1$ if the bit at the position `i - 1` is `1`.

##### Denormal Floating Point Numbers

$mantissa$ is a positive fractional number whose integer part is $0$, for example
$0.12345 \dots$. The `mantissa` bits represent only the fractional part and the
$mantissa$ value can be calculated as:

$$mantissa = \sum_{i=1}^{52} b_{i} \times 2^{-i} = \frac{b_{1}}{2^{1}} + \frac{b_{2}}{2^{2}} + \dots + \frac{b_{51}}{2^{51}} + \frac{b_{52}}{2^{52}}$$

Where $b_{i}$ is:

1. $0$ if the bit at the position `i - 1` is `0`.
2. $1$ if the bit at the position `i - 1` is `1`.

#### Exponent

##### Normal Floating Point Numbers

Only the following bit sequences are allowed: `00000000001` to `11111111110`.
That is, there must be at least one `0` and one `1` in the exponent bits.

The actual value of the $exponent$ can be calculated as:

$$exponent = v - bias$$

where $v$ is the value of the binary number in the exponent bits and $bias$ is $1023$.
Considering the restrictions above, the respective minimum and maximum values for the
exponent are:

1. `00000000001` = $1$, $1 - 1023 = -1022$
2. `11111111110` = $2046$, $2046 - 1023 = 1023$

So, $exponent$ is an integer in the range $\left[-1022, 1023\right]$.


##### Denormal Floating Point Numbers

$exponent$ is always $-1022$. Nevertheless, it is always represented as `00000000000`.

### Normal and Denormal Floating Point Numbers

The smallest absolute value a normal floating point number can have is calculated
like this:

$$1 \times 1.0\dots0 \times 2^{-1022} = 2.2250738585072014 \times 10^{-308}$$

Since normal floating point numbers always have a $1$ as the integer part of the
$mantissa$, then smaller values can be achieved by using the smallest possible exponent
( $-1022$ ) and a $0$ in the integer part of the $mantissa$, but significant digits are lost.

The smallest absolute value a denormal floating point number can have is calculated
like this:

$$1 \times 2^{-52} \times 2^{-1022} = 5 \times 10^{-324}$$

## Zero

Zero is represented like this:

* Sign bit: `X`
* Exponent bits: `00000000000`
* Mantissa bits: `0000000000000000000000000000000000000000000000000000`

where `X` means `0` or `1`.

## NaN

There are 2 kinds of NaNs that are represented:

1. QNaNs (Quiet NaNs): represent the result of indeterminate operations.
2. SNaNs (Signalling NaNs): represent the result of invalid operations.

### QNaNs

QNaNs are represented like this:

* Sign bit: `X`
* Exponent bits: `11111111111`
* Mantissa bits: `1XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`

where `X` means `0` or `1`.

### SNaNs

SNaNs are represented like this:

* Sign bit: `X`
* Exponent bits: `11111111111`
* Mantissa bits: `0XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX1`

where `X` means `0` or `1`.

## Infinite

### Positive Infinite

Positive infinite is represented like this:

* Sign bit: `0`
* Exponent bits: `11111111111`
* Mantissa bits: `0000000000000000000000000000000000000000000000000000`

where `X` means `0` or `1`.

### Negative Infinite

Negative infinite is represented like this:

* Sign bit: `1`
* Exponent bits: `11111111111`
* Mantissa bits: `0000000000000000000000000000000000000000000000000000`

where `X` means `0` or `1`.
-e


# ./.venv/lib/python3.12/site-packages/pyarrow/tests/data/orc/README.md

<!---
  Licensed to the Apache Software Foundation (ASF) under one
  or more contributor license agreements.  See the NOTICE file
  distributed with this work for additional information
  regarding copyright ownership.  The ASF licenses this file
  to you under the Apache License, Version 2.0 (the
  "License"); you may not use this file except in compliance
  with the License.  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing,
  software distributed under the License is distributed on an
  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
  KIND, either express or implied.  See the License for the
  specific language governing permissions and limitations
  under the License.
-->

The ORC and JSON files come from the `examples` directory in the Apache ORC
source tree:
https://github.com/apache/orc/tree/main/examples
-e


# ./.venv/lib/python3.12/site-packages/pymupdf-1.26.6.dist-info/README.md

# PyMuPDF

**PyMuPDF** is a high performance **Python** library for data extraction, analysis, conversion & manipulation of [PDF (and other) documents](https://pymupdf.readthedocs.io/en/latest/the-basics.html#supported-file-types).

# Community
Join us on **Discord** here: [#pymupdf](https://discord.gg/TSpYGBW4eq)


# Installation

**PyMuPDF** requires **Python 3.10 or later**, install using **pip** with:

`pip install PyMuPDF`

There are **no mandatory** external dependencies. However, some [optional features](#pymupdf-optional-features) become available only if additional packages are installed.

You can also try without installing by visiting [PyMuPDF.io](https://pymupdf.io/#examples).


# Usage

Basic usage is as follows:

```python
import pymupdf # imports the pymupdf library
doc = pymupdf.open("example.pdf") # open a document
for page in doc: # iterate the document pages
  text = page.get_text() # get plain text encoded as UTF-8

```


# Documentation

Full documentation can be found on [pymupdf.readthedocs.io](https://pymupdf.readthedocs.io).



# <a id="pymupdf-optional-features"></a>Optional Features

* [fontTools](https://pypi.org/project/fonttools/) for creating font subsets.
* [pymupdf-fonts](https://pypi.org/project/pymupdf-fonts/) contains some nice fonts for your text output.
* [Tesseract-OCR](https://github.com/tesseract-ocr/tesseract) for optical character recognition in images and document pages.



# About

**PyMuPDF** adds **Python** bindings and abstractions to [MuPDF](https://mupdf.com/), a lightweight **PDF**, **XPS**, and **eBook** viewer, renderer, and toolkit. Both **PyMuPDF** and **MuPDF** are maintained and developed by [Artifex Software, Inc](https://artifex.com).

**PyMuPDF** was originally written by [Jorj X. McKie](mailto:jorj.x.mckie@outlook.de).


# License and Copyright

**PyMuPDF** is available under [open-source AGPL](https://www.gnu.org/licenses/agpl-3.0.html) and commercial license agreements. If you determine you cannot meet the requirements of the **AGPL**, please contact [Artifex](https://artifex.com/contact/pymupdf-inquiry.php) for more information regarding a commercial license.




-e


# ./.venv/lib/python3.12/site-packages/starlette-0.49.3.dist-info/licenses/LICENSE.md

Copyright © 2018, [Encode OSS Ltd](https://www.encode.io/).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-e


# ./.venv/lib/python3.12/site-packages/uvicorn-0.38.0.dist-info/licenses/LICENSE.md

Copyright © 2017-present, [Encode OSS Ltd](https://www.encode.io/).
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-e


# ./Backlog/DYNAMIC_TOOL_BACKLOG.md

Dynamic Open WebUI Tools - Phased Requirements Document
Version: 1.0
Author: System Architecture
Date: 2024-11-30
Estimated Total Time: 16-20 hours (2-3 weeks part-time)

Executive Summary
Transform hardcoded Open WebUI tools into dynamic, registry-aware tools that automatically discover available agents, tools, and workflows. Split monolithic @queue tool into 4 specialized tools with comprehensive test coverage and distributed tracing.
Goals

Eliminate hardcoded task types - Query registry APIs dynamically
Improve user experience - Separate tools for different purposes
Enable discoverability - Users can explore available resources
Maintain observability - Full telemetry and test coverage
Production readiness - 80%+ test coverage, comprehensive tracing


System Architecture
┌─────────────────────────────────────────────────────┐
│              Open WebUI Tools Layer                 │
├─────────────────────────────────────────────────────┤
│  @discover  │  @queue  │  @agent  │  @workflow     │
│  (explore)  │  (smart) │ (direct) │  (direct)      │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│           Backend Registry APIs                     │
├─────────────────────────────────────────────────────┤
│  /admin/agents  │  /admin/tools  │  /admin/workflows│
│  /tasks/agent   │  /tasks (existing)                │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│              Registry Layer                         │
├─────────────────────────────────────────────────────┤
│  AgentRegistry  │  ToolRegistry  │  WorkflowRegistry│
└─────────────────────────────────────────────────────┘

Phase 1: Backend Registry APIs (4-5 hours)
Functional Requirements
FR1.1: Agent Registry Endpoint
Endpoint: GET /admin/agents
Response Format:
json{
  "agents": [
    {
      "name": "research",
      "description": "Research agent for deep topic investigation",
      "config": {
        "model": "gpt-4-turbo",
        "temperature": 0.7
      },
      "tools": ["web_search", "document_reader"]
    }
  ]
}
Requirements:

Returns all registered agents from agent_registry
Includes agent name, description, config, and tools
Returns empty list if no agents registered
Response time: < 100ms (no database queries)
Requires mTLS authentication


FR1.2: Tool Registry Endpoint
Endpoint: GET /admin/tools
Response Format:
json{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web using Brave Search API",
      "schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "Search query"},
          "max_results": {"type": "integer", "default": 5}
        },
        "required": ["query"]
      }
    }
  ]
}
Requirements:

Returns all registered tools from tool_registry
Includes tool name, description, and JSON schema
Schema shows parameters, types, defaults, required fields
Returns empty list if no tools registered
Response time: < 100ms


FR1.3: Workflow Registry Endpoint
Endpoint: GET /admin/workflows
Response Format:
json{
  "workflows": [
    {
      "name": "research_assessment",
      "description": "Research with iterative assessment and refinement",
      "strategy": "iterative_refinement",
      "max_iterations": 3,
      "steps": [
        {
          "name": "research",
          "agent_type": "research",
          "description": "Conduct initial research",
          "tools": ["web_search"]
        },
        {
          "name": "assessment",
          "agent_type": "assessment",
          "description": "Assess research quality"
        }
      ]
    }
  ]
}
Requirements:

Returns all registered workflows from workflow_registry
Includes workflow name, description, strategy, max_iterations
Includes all steps with agent_type, tools, description
Returns empty list if no workflows registered
Response time: < 200ms (includes YAML parsing)


FR1.4: Direct Agent Execution Endpoint
Endpoint: POST /tasks/agent
Request Format:
json{
  "agent_type": "research",
  "input": {
    "topic": "AI safety governance"
  },
  "user_id": "user@example.com",
  "tenant_id": "production"
}
Response Format:
json{
  "id": "uuid-task-id",
  "status": "pending",
  "type": "agent:research",
  "created_at": "2024-11-30T12:00:00Z"
}
Requirements:

Creates task for single agent execution (no workflow)
Validates agent exists in registry
Returns 400 if agent not found (with available agents list)
Accepts same input format as workflow tasks
Creates task in database with status "pending"
Worker processes task using specified agent


Non-Functional Requirements
NFR1.1: Performance

All registry endpoints: < 200ms response time
No database queries (in-memory registry lookup only)
Support 100+ concurrent requests

NFR1.2: Security

All endpoints require mTLS authentication
Tenant isolation enforced
No sensitive data in responses (e.g., API keys in config)

NFR1.3: Caching

Registry data cached for 60 seconds
Cache invalidated on registry updates
Optional: ?refresh=true query param to bypass cache


Testing Requirements
TR1.1: Unit Tests (12 tests minimum)
File: tests/test_admin_registry_endpoints.py
pythonclass TestAgentRegistryEndpoint:
    def test_list_agents_success(self):
        """Test /admin/agents returns registered agents."""

    def test_list_agents_empty_registry(self):
        """Test /admin/agents with no agents registered."""

    def test_list_agents_includes_tools(self):
        """Test agent response includes tools list."""

    def test_list_agents_mTLS_required(self):
        """Test endpoint requires mTLS authentication."""

class TestToolRegistryEndpoint:
    def test_list_tools_success(self):
        """Test /admin/tools returns registered tools."""

    def test_list_tools_includes_schema(self):
        """Test tool response includes JSON schema."""

    def test_list_tools_empty_registry(self):
        """Test /admin/tools with no tools registered."""

class TestWorkflowRegistryEndpoint:
    def test_list_workflows_success(self):
        """Test /admin/workflows returns registered workflows."""

    def test_list_workflows_includes_steps(self):
        """Test workflow response includes all steps."""

    def test_list_workflows_empty_registry(self):
        """Test /admin/workflows with no workflows registered."""

class TestDirectAgentEndpoint:
    def test_create_agent_task_success(self):
        """Test POST /tasks/agent creates task."""

    def test_create_agent_task_unknown_agent(self):
        """Test error when agent not found."""
Coverage Target: 90%+ for admin endpoints

TR1.2: Integration Tests (4 tests minimum)
File: tests/test_registry_api_integration.py
pythonclass TestRegistryAPIIntegration:
    def test_discover_agents_tools_workflows(self):
        """Test complete registry discovery flow."""
        # Register agents, tools, workflows
        # Call all 3 endpoints
        # Verify all resources returned

    def test_agent_execution_uses_registry(self):
        """Test /tasks/agent uses agent from registry."""
        # Register agent
        # Create task via /tasks/agent
        # Verify task created with correct agent_type

    def test_registry_updates_reflected_in_api(self):
        """Test dynamic registration reflected in API."""
        # Call /admin/agents (empty)
        # Register new agent
        # Call /admin/agents again
        # Verify new agent present

    def test_workflow_references_valid_agents(self):
        """Test workflow steps reference registered agents."""
        # Call /admin/workflows
        # Extract all agent_types from steps
        # Call /admin/agents
        # Verify all agent_types exist
Coverage Target: 85%+ for integration scenarios

Telemetry Requirements
TM1.1: Distributed Tracing
Trace all registry API calls:
python# app/routers/admin.py

@router.get("/admin/agents")
async def list_agents():
    """List all registered agents."""
    with tracer.start_as_current_span(
        "admin.list_agents",
        attributes={
            "http.method": "GET",
            "http.route": "/admin/agents",
        }
    ) as span:
        agents = agent_registry.list_all()
        span.set_attribute("agent.count", len(agents))

        # ... build response ...

        return {"agents": agents}
Required attributes:

http.method - HTTP method
http.route - API route
agent.count / tool.count / workflow.count - Number of items
cache.hit - Whether response from cache
response.time_ms - Response generation time


TM1.2: Structured Logging
Log all registry queries:
pythonimport structlog

logger = structlog.get_logger(__name__)

@router.get("/admin/agents")
async def list_agents():
    logger.info(
        "registry.api.agents.list",
        agent_count=len(agents),
        response_time_ms=elapsed_ms,
        cache_hit=False,
    )
Required log fields:

event - Event name (e.g., "registry.api.agents.list")
agent_count / tool_count / workflow_count
response_time_ms
cache_hit (if caching implemented)
tenant_id (if multi-tenant)


TM1.3: Metrics
Prometheus metrics for registry APIs:
pythonfrom prometheus_client import Counter, Histogram

registry_requests = Counter(
    "registry_api_requests_total",
    "Total registry API requests",
    ["endpoint", "status"]
)

registry_response_time = Histogram(
    "registry_api_response_seconds",
    "Registry API response time",
    ["endpoint"]
)

@router.get("/admin/agents")
async def list_agents():
    with registry_response_time.labels(endpoint="agents").time():
        # ... handle request ...
        registry_requests.labels(endpoint="agents", status="success").inc()
Required metrics:

registry_api_requests_total{endpoint, status} - Request counter
registry_api_response_seconds{endpoint} - Response time histogram
registry_cache_hits_total{endpoint} - Cache hit counter (if caching)


Acceptance Criteria
Phase 1 is complete when:

✅ All 4 endpoints implemented (/admin/agents, /admin/tools, /admin/workflows, /tasks/agent)
✅ 12+ unit tests passing (90%+ coverage)
✅ 4+ integration tests passing (85%+ coverage)
✅ All endpoints traced with OpenTelemetry
✅ Structured logging on all endpoints
✅ Prometheus metrics exported
✅ Response time < 200ms for all endpoints
✅ Documentation updated (API docs, README)

Verification:
bash# Test endpoints
curl -X GET https://localhost:8000/admin/agents --cert client.pem --key client.key
curl -X GET https://localhost:8000/admin/tools --cert client.pem --key client.key
curl -X GET https://localhost:8000/admin/workflows --cert client.pem --key client.key

# Test direct agent execution
curl -X POST https://localhost:8000/tasks/agent \
  --cert client.pem --key client.key \
  -H "Content-Type: application/json" \
  -d '{"agent_type": "research", "input": {"topic": "test"}, "user_id": "test@example.com"}'

# Verify metrics
curl http://localhost:8000/metrics | grep registry_api

# Run tests
pytest tests/test_admin_registry_endpoints.py -v --cov=app/routers/admin
pytest tests/test_registry_api_integration.py -v

Phase 2: @discover Tool (3-4 hours)
Functional Requirements
FR2.1: Tool Structure
File: openwebui_tools/discover.py
Tool metadata:
python"""
title: Registry Discovery Tool
author: system
version: 1.0
description: Discover available agents, tools, and workflows in the backend system
requirements: requests, asyncio
"""
Valves configuration:
pythonclass Valves(BaseModel):
    task_api_url: str = Field(
        default=os.getenv("TASK_API_URL", "http://task-api:8000"),
        description="Base URL for Task API"
    )
    # ... mTLS cert paths (same as existing queue tool) ...
    cache_ttl_seconds: int = Field(
        default=60,
        description="Cache registry data for N seconds"
    )

FR2.2: Discovery Commands
Command: @discover or @discover all
Output:
markdown# Available Resources

## Agents (3)
- **research**: Research agent for deep topic investigation
  - Tools: web_search, document_reader
  - Model: gpt-4-turbo
- **assessment**: Assessment agent for quality evaluation
  - Model: gpt-4-turbo
- **analysis**: Data analysis agent
  - Tools: calculator, database_query

## Tools (4)
- **web_search**: Search the web using Brave Search API
  - Parameters: query (required), max_results (optional)
- **calculator**: Safe mathematical expression evaluator
  - Parameters: expression (required)
- **document_reader**: Fetch and extract text from URLs
  - Parameters: url (required), max_length (optional)
- **database_query**: Query internal database
  - Parameters: query_type (required), limit (optional)

## Workflows (2)
- **research_assessment**: Research with iterative assessment
  - Strategy: iterative_refinement (max 3 iterations)
  - Steps: 2 agents (research → assessment)
- **simple_sequential**: Simple sequential workflow
  - Strategy: sequential
  - Steps: 2 agents

Command: @discover agents
Output:
markdown# Available Agents (3)

**research**
- Description: Research agent for deep topic investigation
- Tools: web_search, document_reader
- Model: gpt-4-turbo
- Temperature: 0.7

**assessment**
- Description: Assessment agent for quality evaluation
- Model: gpt-4-turbo
- Temperature: 0.3

**analysis**
- Description: Data analysis agent
- Tools: calculator, database_query
- Model: gpt-4-turbo

Command: @discover tools
Output:
markdown# Available Tools (4)

**web_search**
- Description: Search the web using Brave Search API
- Parameters:
  - query (string, required): Search query
  - max_results (integer, optional, default=5): Max results to return

**calculator**
- Description: Safe mathematical expression evaluator
- Parameters:
  - expression (string, required): Mathematical expression to evaluate

**document_reader**
- Description: Fetch and extract text from URLs
- Parameters:
  - url (string, required): URL to fetch
  - max_length (integer, optional, default=10000): Max text length

**database_query**
- Description: Query internal database safely
- Parameters:
  - query_type (string, required): Type of query (task_stats, cost_by_user, recent_tasks)
  - user_id_hash (string, optional): User ID for filtering
  - limit (integer, optional, default=10): Number of results

Command: @discover workflows
Output:
markdown# Available Workflows (2)

**research_assessment**
- Description: Research with iterative assessment and refinement
- Strategy: iterative_refinement
- Max Iterations: 3
- Steps:
  1. research (research agent)
     - Description: Conduct initial research
     - Tools: web_search
  2. assessment (assessment agent)
     - Description: Assess research quality
     - Convergence: Check approved=true

**simple_sequential**
- Description: Simple sequential two-agent workflow
- Strategy: sequential
- Steps:
  1. step_one (research agent)
  2. step_two (assessment agent)

---

**Usage:**
- Execute workflow: `@workflow research_assessment "your topic"`
- Execute agent: `@agent research "your query"`
- Queue task: `@queue "your task description"`

FR2.3: Error Handling
Scenario: Backend API unreachable
Output:
markdown❌ **Error: Cannot connect to backend**

The registry API is unavailable. Please check:
1. Backend service is running
2. mTLS certificates are configured correctly
3. Network connectivity

Error details: Connection refused to http://task-api:8000/admin/agents

Scenario: No resources registered
Output:
markdown# Available Resources

⚠️ **No agents registered**

⚠️ **No tools registered**

⚠️ **No workflows registered**

The system is running but no resources have been configured.
Please check the agent/tool/workflow registries.

FR2.4: Caching
Requirements:

Cache registry responses for cache_ttl_seconds (default: 60s)
Cache key: registry:{type} (e.g., registry:agents)
Cache invalidation: TTL-based (no manual invalidation)
Cache bypass: Internal flag (no user-facing option)

Implementation:
pythonclass Tools:
    def __init__(self):
        self.valves = self.Valves()
        self._cache: dict[str, tuple[float, Any]] = {}  # key -> (timestamp, data)

    async def _get_cached_or_fetch(
        self,
        cache_key: str,
        fetch_func: Callable,
    ) -> Any:
        """Get from cache or fetch from API."""
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if now - timestamp < self.valves.cache_ttl_seconds:
                return data

        # Cache miss - fetch from API
        data = await fetch_func()
        self._cache[cache_key] = (now, data)
        return data

Non-Functional Requirements
NFR2.1: Performance

Total discovery time: < 3 seconds (all 3 API calls)
Cached discovery: < 100ms
UI status updates: Every 500ms during discovery

NFR2.2: User Experience

Real-time status updates via __event_emitter__
Clear formatting with markdown
Helpful error messages
Examples in output

NFR2.3: Maintainability

Separate formatting functions per resource type
Reusable API client methods
Comprehensive docstrings


Testing Requirements
TR2.1: Unit Tests (15 tests minimum)
File: tests/test_discover_tool.py
pythonclass TestDiscoverTool:
    def test_discover_all_formats_correctly(self, mock_api):
        """Test @discover all returns formatted output."""

    def test_discover_agents_only(self, mock_api):
        """Test @discover agents returns only agents."""

    def test_discover_tools_only(self, mock_api):
        """Test @discover tools returns only tools."""

    def test_discover_workflows_only(self, mock_api):
        """Test @discover workflows returns only workflows."""

    def test_discover_empty_registry(self, mock_api):
        """Test @discover with no resources registered."""

    def test_discover_api_error(self, mock_api):
        """Test @discover handles API errors gracefully."""

    def test_discover_network_error(self, mock_api):
        """Test @discover handles network errors."""

    def test_discover_invalid_response(self, mock_api):
        """Test @discover handles malformed API responses."""

class TestDiscoverCaching:
    def test_cache_hit(self, mock_api):
        """Test cached response returns quickly."""

    def test_cache_miss(self, mock_api):
        """Test cache miss fetches from API."""

    def test_cache_expiry(self, mock_api):
        """Test cache expires after TTL."""

    def test_cache_per_resource_type(self, mock_api):
        """Test separate cache per resource type."""

class TestDiscoverFormatting:
    def test_format_agent_with_tools(self):
        """Test agent formatting includes tools."""

    def test_format_tool_with_schema(self):
        """Test tool formatting includes parameter schema."""

    def test_format_workflow_with_steps(self):
        """Test workflow formatting includes all steps."""
Coverage Target: 85%+ for discover tool

TR2.2: Integration Tests (3 tests minimum)
File: tests/test_discover_tool_integration.py
pythonclass TestDiscoverToolIntegration:
    def test_discover_real_backend(self, test_backend):
        """Test @discover against real backend."""
        # Start test backend with real registries
        # Call @discover all
        # Verify all resources returned

    def test_discover_trace_propagation(self, test_backend):
        """Test @discover creates trace spans."""
        # Call @discover
        # Verify trace spans created
        # Verify span attributes set

    def test_discover_emits_status_updates(self, test_backend):
        """Test @discover emits UI status updates."""
        # Mock event emitter
        # Call @discover
        # Verify status updates emitted
Coverage Target: 80%+ for integration

Telemetry Requirements
TM2.1: Distributed Tracing
Trace @discover operations:
pythonasync def at_discover(
    self,
    query: str = "",
    __event_emitter__: Any = None,
) -> str:
    """Discover available resources."""

    # Create root span
    trace_id = generate_trace_id()
    span_id = generate_span_id()

    with tracer.start_span(
        "openwebui.discover",
        attributes={
            "discover.query": query or "all",
            "discover.user_request": True,
        }
    ) as root_span:
        # Fetch agents
        with tracer.start_span(
            "openwebui.discover.fetch_agents",
            parent=root_span,
        ) as span:
            agents = await self._fetch_agents()
            span.set_attribute("discover.agents.count", len(agents))

        # Fetch tools
        with tracer.start_span(
            "openwebui.discover.fetch_tools",
            parent=root_span,
        ) as span:
            tools = await self._fetch_tools()
            span.set_attribute("discover.tools.count", len(tools))

        # Fetch workflows
        with tracer.start_span(
            "openwebui.discover.fetch_workflows",
            parent=root_span,
        ) as span:
            workflows = await self._fetch_workflows()
            span.set_attribute("discover.workflows.count", len(workflows))

        root_span.set_attribute("discover.total_resources",
                                len(agents) + len(tools) + len(workflows))

        return formatted_output
Required attributes:

discover.query - Query type (all, agents, tools, workflows)
discover.agents.count - Number of agents
discover.tools.count - Number of tools
discover.workflows.count - Number of workflows
discover.total_resources - Total resources found
discover.cache_hit - Whether response from cache
discover.response_time_ms - Total response time


TM2.2: Structured Logging
Log discovery operations:
pythonlogger.info(
    "openwebui.discover.complete",
    query=query or "all",
    agents_count=len(agents),
    tools_count=len(tools),
    workflows_count=len(workflows),
    cache_hit=cache_hit,
    response_time_ms=elapsed_ms,
)

Acceptance Criteria
Phase 2 is complete when:

✅ @discover tool implemented with all commands
✅ Supports @discover, @discover all, @discover agents, @discover tools, @discover workflows
✅ 15+ unit tests passing (85%+ coverage)
✅ 3+ integration tests passing (80%+ coverage)
✅ Caching implemented (60s TTL)
✅ Distributed tracing on all operations
✅ Structured logging on all operations
✅ Error handling for all failure modes
✅ User documentation (README, examples)

Verification:
bash# Test in Open WebUI
User: @discover
User: @discover agents
User: @discover tools
User: @discover workflows

# Run tests
pytest tests/test_discover_tool.py -v --cov=openwebui_tools/discover
pytest tests/test_discover_tool_integration.py -v

# Verify traces in Jaeger
# Verify logs in structured format

Phase 3: Enhanced @queue Tool (3-4 hours)
Functional Requirements
FR3.1: Dynamic Workflow Selection
Update: Replace _infer_task_type() with dynamic lookup
Old implementation (hardcoded):
pythondef _infer_task_type(self, user_message: str) -> str:
    """Infer task type from user message."""
    if "research" in message_lower:
        return "workflow:research_assessment"
    if "summarize" in message_lower:
        return "summarize_document"
    # etc...
New implementation (dynamic):
pythonasync def _smart_workflow_selection(
    self,
    instruction: str,
    __event_emitter__: Any = None,
) -> str | None:
    """
    Dynamically select workflow based on available workflows.

    Selection strategy:
    1. Exact workflow name match in instruction
    2. Keyword match in workflow descriptions
    3. Fallback to default workflow (research_assessment)
    """
    instruction_lower = instruction.lower()

    # Fetch available workflows (cached)
    workflows = await self._get_cached_or_fetch(
        "registry:workflows",
        self._fetch_workflows
    )

    if not workflows:
        return "workflow:research_assessment"  # Fallback

    # Strategy 1: Exact name match
    for workflow in workflows:
        if workflow['name'] in instruction_lower:
            await self._emit_status(
                __event_emitter__,
                f"Selected workflow: {workflow['name']}",
                False
            )
            return f"workflow:{workflow['name']}"

    # Strategy 2: Keyword matching
    matches = []
    for workflow in workflows:
        desc_lower = workflow.get('description', '').lower()
        keywords = set(desc_lower.split())
        user_words = set(instruction_lower.split())

        # Calculate keyword overlap
        overlap = len(keywords & user_words)
        if overlap > 0:
            matches.append((workflow, overlap))

    if matches:
        # Sort by overlap (best match first)
        matches.sort(key=lambda x: x[1], reverse=True)
        best_match = matches[0][0]

        await self._emit_status(
            __event_emitter__,
            f"Matched workflow: {best_match['name']}",
            False
        )
        return f"workflow:{best_match['name']}"

    # Strategy 3: Fallback
    await self._emit_status(
        __event_emitter__,
        "Using default workflow: research_assessment",
        False
    )
    return "workflow:research_assessment"

FR3.2: Workflow Suggestions
Enhancement: Show workflow suggestions on ambiguous input
Scenario: User query matches multiple workflows
Output:
markdown📋 **Multiple workflows match your query:**

1. **research_assessment** (3 keyword matches)
   - Research with iterative assessment and refinement
   - Use: `@workflow research_assessment "your topic"`

2. **deep_research** (2 keyword matches)
   - Deep research with multiple sources
   - Use: `@workflow deep_research "your topic"`

**Auto-selected:** research_assessment (best match)

Proceeding with research_assessment workflow...
```

---

#### FR3.3: Backward Compatibility

**Requirement:** Existing `@queue` commands continue to work

**Test cases:**
```
@queue summarize this document
  → Should still create summarize_document task

@queue analyze this table
  → Should still create analyze_table task

@queue research AI safety
  → Should dynamically select workflow (new behavior)

Non-Functional Requirements
NFR3.1: Performance

Workflow selection: < 500ms (including API call)
Cached workflow selection: < 50ms
No degradation for non-workflow tasks

NFR3.2: User Experience

Clear feedback on workflow selection
Show matched keywords (if multiple matches)
Graceful fallback to default workflow


Testing Requirements
TR3.1: Unit Tests (18 tests minimum)
File: tests/test_queue_tool_dynamic.py
pythonclass TestSmartWorkflowSelection:
    def test_exact_workflow_name_match(self, mock_api):
        """Test exact workflow name in instruction."""

    def test_keyword_matching(self, mock_api):
        """Test keyword-based workflow matching."""

    def test_multiple_matches_best_selected(self, mock_api):
        """Test best match selected with multiple options."""

    def test_no_match_uses_default(self, mock_api):
        """Test fallback to default workflow."""

    def test_empty_workflow_registry(self, mock_api):
        """Test behavior when no workflows registered."""

class TestBackwardCompatibility:
    def test_summarize_task_still_works(self):
        """Test @queue summarize creates summarize_document task."""

    def test_analyze_task_still_works(self):
        """Test @queue analyze creates analyze_table task."""

    def test_compare_task_still_works(self):
        """Test @queue compare creates compare_options task."""

class TestWorkflowSuggestions:
    def test_multiple_matches_shows_suggestions(self, mock_api):
        """Test suggestions shown for multiple matches."""

    def test_suggestion_format(self, mock_api):
        """Test suggestion output format."""

class TestQueueCaching:
    def test_workflow_list_cached(self, mock_api):
        """Test workflow list cached for performance."""

    def test_cache_ttl_respected(self, mock_api):
        """Test cache expires after TTL."""

class TestQueueErrorHandling:
    def test_api_error_fallback(self, mock_api):
        """Test fallback when API unavailable."""

    def test_invalid_workflow_response(self, mock_api):
        """Test handling of malformed API response."""

    def test_network_timeout(self, mock_api):
        """Test handling of network timeout."""

class TestQueueTracing:
    def test_trace_context_propagated(self, mock_tracer):
        """Test trace context passed to backend."""

    def test_workflow_selection_traced(self, mock_tracer):
        """Test workflow selection creates span."""

    def test_trace_attributes_set(self, mock_tracer):
        """Test trace attributes include workflow info."""
Coverage Target: 90%+ for queue tool

TR3.2: Integration Tests (5 tests minimum)
File: tests/test_queue_tool_integration.py
pythonclass TestQueueToolIntegration:
    def test_queue_dynamic_workflow_end_to_end(self, test_backend):
        """Test @queue with dynamic workflow selection."""

    def test_queue_backward_compatible(self, test_backend):
        """Test @queue with legacy task types."""

    def test_queue_workflow_suggestions(self, test_backend):
        """Test workflow suggestions on ambiguous input."""

    def test_queue_trace_propagation(self, test_backend):
        """Test trace propagation through workflow."""

    def test_queue_with_real_registries(self, test_backend):
        """Test @queue against real backend registries."""
Coverage Target: 85%+ for integration

Telemetry Requirements
TM3.1: Distributed Tracing
Trace workflow selection:
pythonasync def _smart_workflow_selection(
    self,
    instruction: str,
    __event_emitter__: Any = None,
) -> str | None:
    """Dynamically select workflow."""

    with tracer.start_span(
        "openwebui.queue.workflow_selection",
        attributes={
            "instruction": instruction[:100],
        }
    ) as span:
        # Fetch workflows
        with tracer.start_span(
            "openwebui.queue.fetch_workflows",
            parent=span,
        ) as fetch_span:
            workflows = await self._get_cached_or_fetch(...)
            fetch_span.set_attribute("workflows.count", len(workflows))

        # Match workflow
        selected = self._match_workflow(instruction, workflows)

        span.set_attribute("workflow.selected", selected)
        span.set_attribute("workflow.selection_strategy", strategy)

        return selected

TM3.2: Structured Logging
pythonlogger.info(
    "openwebui.queue.workflow_selected",
    instruction=instruction[:100],
    workflow_name=selected_workflow,
    selection_strategy=strategy,
    match_score=overlap_score,
    alternatives_count=len(matches),
)

Acceptance Criteria
Phase 3 is complete when:

✅ Dynamic workflow selection implemented
✅ Backward compatibility maintained
✅ Workflow suggestions on ambiguous input
✅ 18+ unit tests passing (90%+ coverage)
✅ 5+ integration tests passing (85%+ coverage)
✅ Distributed tracing on workflow selection
✅ Structured logging on all operations
✅ Performance: < 500ms workflow selection

Verification:
bash# Test dynamic workflow selection
User: @queue research quantum computing
  → Should auto-select research_assessment workflow

User: @queue deep_research AI safety
  → Should select deep_research workflow (if exists)

User: @queue summarize this document
  → Should create summarize_document task (backward compatible)

# Run tests
pytest tests/test_queue_tool_dynamic.py -v --cov
pytest tests/test_queue_tool_integration.py -v
```

---

## Phase 4: @agent Tool (2-3 hours)

### Functional Requirements

#### FR4.1: Direct Agent Execution

**Command:** `@agent <agent_name> <instruction>`

**Examples:**
```
@agent research "quantum computing trends 2024"
@agent assessment "review this research quality"
@agent analysis "calculate revenue projections"
Behavior:

Parse agent name from command
Verify agent exists in registry
Create task with type: "agent:{agent_name}"
Wait for task completion
Return formatted result


FR4.2: Agent Discovery
Command: @agent (no arguments)
Output:
markdown# Available Agents

You can execute any of these agents directly:

**research**
- Description: Research agent for deep topic investigation
- Tools: web_search, document_reader
- Usage: `@agent research "your query"`

**assessment**
- Description: Assessment agent for quality evaluation
- Usage: `@agent assessment "your evaluation request"`

**analysis**
- Description: Data analysis agent
- Tools: calculator, database_query
- Usage: `@agent analysis "your analysis task"`

---

**Examples:**
```
@agent research "AI safety governance"
@agent assessment "review the research above"
@agent analysis "calculate growth rate"
```

FR4.3: Agent Validation
Scenario: Unknown agent
Input: @agent unknown_agent "test query"
Output:
markdown❌ **Unknown agent: unknown_agent**

**Available agents:**
- research
- assessment
- analysis

**Usage:** `@agent <agent_name> <instruction>`

**Example:** `@agent research "your query"`

FR4.4: Error Handling
Scenario: Missing instruction
Input: @agent research
Output:
markdown❌ **Missing instruction**

**Usage:** `@agent <agent_name> <instruction>`

**Example:** `@agent research "quantum computing trends"`

Scenario: Agent execution error
Output:
markdown❌ **Agent Execution Error**

Agent: research
Error: LLM API rate limit exceeded

**Task ID:** `abc123-def456-...`

You can check task status: `@queue status abc123-def456-...`

Non-Functional Requirements
NFR4.1: Performance

Agent validation: < 100ms (cached)
Task creation: < 500ms
Total execution time: Same as workflow tasks

NFR4.2: User Experience

Clear agent selection
Helpful error messages
Examples in help text


Testing Requirements
TR4.1: Unit Tests (12 tests minimum)
File: tests/test_agent_tool.py
pythonclass TestAgentTool:
    def test_agent_execution_success(self, mock_api):
        """Test @agent executes agent successfully."""

    def test_agent_list_available(self, mock_api):
        """Test @agent with no args lists agents."""

    def test_agent_unknown_agent(self, mock_api):
        """Test @agent with unknown agent shows error."""

    def test_agent_missing_instruction(self, mock_api):
        """Test @agent with missing instruction shows error."""

    def test_agent_validation_cached(self, mock_api):
        """Test agent list cached for performance."""

class TestAgentToolFormatting:
    def test_agent_list_format(self):
        """Test agent list output format."""

    def test_agent_error_format(self):
        """Test error message format."""

    def test_agent_help_includes_examples(self):
        """Test help text includes examples."""

class TestAgentToolTracing:
    def test_agent_execution_traced(self, mock_tracer):
        """Test @agent creates trace spans."""

    def test_trace_includes_agent_name(self, mock_tracer):
        """Test trace includes agent name attribute."""

    def test_trace_propagates_to_backend(self, mock_tracer):
        """Test trace propagates to backend."""

class TestAgentToolIntegration:
    def test_agent_creates_correct_task_type(self, test_backend):
        """Test @agent creates agent:* task type."""

    def test_agent_waits_for_completion(self, test_backend):
        """Test @agent waits for task completion."""
Coverage Target: 85%+ for agent tool

Telemetry Requirements
TM4.1: Distributed Tracing
pythonasync def at_agent(
    self,
    command: str,
    __event_emitter__: Any = None,
) -> str:
    """Execute agent directly."""

    with tracer.start_span(
        "openwebui.agent.execute",
        attributes={
            "agent.command": command[:100],
        }
    ) as span:
        # Parse agent name
        agent_name = self._parse_agent_name(command)
        span.set_attribute("agent.name", agent_name)

        # Validate agent
        with tracer.start_span(
            "openwebui.agent.validate",
            parent=span,
        ) as validate_span:
            is_valid = await self._validate_agent(agent_name)
            validate_span.set_attribute("agent.valid", is_valid)

        # Execute
        task_id = await self._create_agent_task(...)
        span.set_attribute("task.id", task_id)

        return result
```

---

### Acceptance Criteria

**Phase 4 is complete when:**

1. ✅ `@agent` tool implemented
2. ✅ Supports agent execution and discovery
3. ✅ 12+ unit tests passing (85%+ coverage)
4. ✅ Distributed tracing on all operations
5. ✅ Structured logging
6. ✅ Documentation (README, examples)

---

## Phase 5: @workflow Tool (2-3 hours)

### Functional Requirements

#### FR5.1: Direct Workflow Execution

**Command:** `@workflow <workflow_name> <topic>`

**Examples:**
```
@workflow research_assessment "quantum computing"
@workflow simple_sequential "market analysis"
@workflow custom_workflow "user query"

FR5.2: Workflow Discovery
Command: @workflow (no arguments)
Output:
markdown# Available Workflows

**research_assessment**
- Description: Research with iterative assessment and refinement
- Strategy: iterative_refinement (max 3 iterations)
- Steps: research → assessment
- Usage: `@workflow research_assessment "your topic"`

**simple_sequential**
- Description: Simple sequential two-agent workflow
- Strategy: sequential
- Steps: step_one → step_two
- Usage: `@workflow simple_sequential "your topic"`

---

**Examples:**
```
@workflow research_assessment "AI safety governance"
@workflow simple_sequential "quarterly revenue analysis"
```

**Note:** You can also use `@queue` for smart workflow selection.

FR5.3: Workflow Validation
Similar to @agent validation - Show available workflows on error.

Testing Requirements
Similar to @agent tool - 12+ unit tests, 85%+ coverage, tracing, logging.

Acceptance Criteria
Phase 5 is complete when:

✅ @workflow tool implemented
✅ 12+ unit tests passing (85%+ coverage)
✅ Distributed tracing
✅ Documentation


Phase 6: Documentation & Polish (2 hours)
Documentation Requirements
DR6.1: API Documentation
File: docs/REGISTRY_API.md
Contents:
markdown# Registry API Documentation

## Endpoints

### GET /admin/agents
Returns all registered agents.

**Response:**
```json
{
  "agents": [...]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/agents \
  --cert client.pem \
  --key client.key
```

### GET /admin/tools
...

### GET /admin/workflows
...

### POST /tasks/agent
...

DR6.2: Open WebUI Tools Guide
File: docs/OPENWEBUI_TOOLS.md
Contents:
markdown# Open WebUI Tools Guide

## Available Tools

### @discover - Registry Explorer
Discover available agents, tools, and workflows.

**Usage:**
- `@discover` - Show all resources
- `@discover agents` - Show only agents
- `@discover tools` - Show only tools
- `@discover workflows` - Show only workflows

### @queue - Smart Task Queue
Submit tasks with automatic workflow selection.

**Usage:**
- `@queue research AI safety` - Auto-selects workflow
- `@queue summarize document` - Legacy task type

### @agent - Direct Agent Execution
Execute a specific agent directly.

**Usage:**
- `@agent research "your query"`
- `@agent assessment "your evaluation"`

### @workflow - Direct Workflow Execution
Execute a specific workflow by name.

**Usage:**
- `@workflow research_assessment "your topic"`
- `@workflow simple_sequential "your task"`

## Examples

### Research Workflow
```
User: @discover workflows
User: @workflow research_assessment "quantum computing trends"
  → Executes multi-agent research workflow
```

### Direct Agent Usage
```
User: @agent research "AI safety governance"
  → Executes research agent only
```
```

---

#### DR6.3: README Updates

Update main README with:
- New registry endpoints
- New Open WebUI tools
- Examples
- Architecture diagram

---

### Polish Requirements

#### PR6.1: Code Quality
- All files pass linting (ruff)
- Type hints on all functions
- Docstrings on all classes/methods
- No TODO/FIXME comments

#### PR6.2: Error Messages
- All errors have helpful messages
- Suggest corrections
- Include examples

#### PR6.3: Logging
- Consistent log levels
- Structured logging throughout
- No sensitive data in logs

---

### Acceptance Criteria

**Phase 6 is complete when:**

1. ✅ Complete API documentation
2. ✅ Complete Open WebUI tools guide
3. ✅ README updated
4. ✅ All code linted
5. ✅ All docstrings complete
6. ✅ Error messages polished

---

## Overall Success Criteria

### Test Coverage Requirements

**Target: 85%+ overall coverage**

| Component | Coverage Target | Tests Required |
|-----------|----------------|----------------|
| Backend Registry APIs | 90%+ | 16+ tests |
| @discover Tool | 85%+ | 15+ tests |
| @queue Tool | 90%+ | 18+ tests |
| @agent Tool | 85%+ | 12+ tests |
| @workflow Tool | 85%+ | 12+ tests |

**Total Tests Required:** 73+ tests

**Test Execution Time:** < 10 seconds

---

### Telemetry Requirements

#### Distributed Tracing Coverage

**All operations must be traced:**
- ✅ Registry API calls
- ✅ Tool executions (@discover, @queue, @agent, @workflow)
- ✅ Workflow selection logic
- ✅ Cache operations

**Required trace attributes:**
- `http.method`, `http.route` (API calls)
- `agent.name`, `tool.name`, `workflow.name` (execution)
- `cache.hit` (cache operations)
- `error.type`, `error.message` (errors)

---

#### Structured Logging Coverage

**All operations must log:**
- ✅ INFO: Successful operations
- ✅ WARN: Fallbacks, cache misses
- ✅ ERROR: Failures, exceptions

**Required log fields:**
- `event` - Event name
- `duration_ms` - Operation duration
- `cache_hit` - Cache status
- `error` - Error details (if applicable)

---

#### Metrics Coverage

**Required Prometheus metrics:**
```
registry_api_requests_total{endpoint, status}
registry_api_response_seconds{endpoint}
registry_cache_hits_total{endpoint}
openwebui_tool_executions_total{tool, status}
openwebui_tool_response_seconds{tool}
openwebui_workflow_selections_total{strategy}

Timeline Summary
PhaseTimeTestsCoverageDeliverablePhase 14-5h16+90%+Registry APIsPhase 23-4h15+85%+@discover toolPhase 33-4h18+90%+Enhanced @queuePhase 42-3h12+85%+@agent toolPhase 52-3h12+85%+@workflow toolPhase 62h--DocumentationTotal16-21h73+85%+Complete system

Verification Checklist
✅ Phase 1 Complete

 All 4 endpoints implemented
 16+ tests passing
 90%+ coverage
 Tracing implemented
 Metrics exported
 Documentation updated

✅ Phase 2 Complete

 @discover tool implemented
 15+ tests passing
 85%+ coverage
 Caching working
 Tracing implemented
 User guide updated

✅ Phase 3 Complete

 Dynamic workflow selection implemented
 18+ tests passing
 90%+ coverage
 Backward compatibility maintained
 Tracing implemented

✅ Phase 4 Complete

 @agent tool implemented
 12+ tests passing
 85%+ coverage
 Tracing implemented

✅ Phase 5 Complete

 @workflow tool implemented
 12+ tests passing
 85%+ coverage
 Tracing implemented

✅ Phase 6 Complete

 All documentation complete
 Code linted
 Error messages polished

✅ Overall System Complete

 73+ total tests passing
 85%+ overall coverage
 All telemetry working
 Production deployment ready


Out of Scope
Not included in this project:
❌ Agent/Tool/Workflow creation via Open WebUI
❌ Registry editing via Open WebUI
❌ Advanced workflow orchestration
❌ Multi-modal support
❌ Real-time registry updates (WebSocket)
❌ User-specific agent/tool customization
These can be added in future iterations.é
-e


# ./Backlog/IMPROVED_TESTING_BACKLOG.md

# Testing Improvement Requirements

**Project:** Agents Playground - Task Orchestration System
**Current State:** 362 tests, 78.18% coverage, 4.81s execution time
**Document Version:** 1.0
**Created:** November 2025

---

## Executive Summary

This document outlines a phased approach to improving test quality for the Agents Playground project. The current test suite provides good foundational coverage but has gaps in critical areas including error handling paths, concurrent operations, and property-based testing. The improvements are organized into four phases, each with clear success criteria and deliverables.

---

## Phase 1: Technical Debt & Coverage Gaps

**Duration:** 1-2 weeks
**Priority:** Critical
**Goal:** Eliminate dead code and achieve baseline coverage on all production modules

### 1.1 Dead Code Elimination

| Item | Action | Rationale |
|------|--------|-----------|
| `app/worker_backup.py` (0% coverage) | Delete or archive | 114 statements with zero tests indicates abandoned code |
| Pydantic v1 `class Config` usage | Migrate to `ConfigDict` | Deprecation warnings will become errors in Pydantic v3 |
| `ast.Num` usage in calculator.py | Replace with `ast.Constant` | Deprecated in Python 3.12, removed in 3.14 |

### 1.2 Critical Coverage Gaps

Target modules requiring immediate attention:

| Module | Current | Target | Missing Lines |
|--------|---------|--------|---------------|
| `app/text_utils.py` | 17.65% | 80% | 9-20, 25-39, 44-53 |
| `app/instance.py` | 40% | 75% | 27-48, 53 |
| `app/db_utils.py` | 54.17% | 80% | 63-92, 146-147, 154-160, 203-222, 241-292, 314-324 |
| `app/main.py` | 51.20% | 65% | 43-47, 54-72, 128-150, 167-211 |

### 1.3 Required Test Additions

```
tests/
├── test_text_utils.py          # NEW: Text processing edge cases
├── test_instance.py            # NEW: Instance lifecycle management
├── test_db_utils_errors.py     # NEW: Database error handling paths
└── test_main_lifecycle.py      # NEW: Application startup/shutdown
```

### Success Criteria - Phase 1

- [ ] `worker_backup.py` removed from codebase or fully tested
- [ ] Zero Pydantic deprecation warnings in test output
- [ ] Zero `ast.Num` deprecation warnings in test output
- [ ] All modules at minimum 50% coverage (current floor)
- [ ] `text_utils.py` coverage ≥ 80%
- [ ] `db_utils.py` coverage ≥ 75%
- [ ] No module with 0% coverage remains in production code

**Verification Command:**
```bash
pytest --cov=app --cov-fail-under=50 -v 2>&1 | grep -E "(PASSED|FAILED|warnings)"
# Expected: 0 deprecation warnings, all tests pass
```

---

## Phase 2: Boundary & Invariant Testing

**Duration:** 2-3 weeks
**Priority:** High
**Goal:** Establish property-based testing and encode critical system invariants

### 2.1 Property-Based Testing Setup

**Dependencies to add:**
```toml
[project.optional-dependencies]
test = [
    # ... existing
    "hypothesis>=6.100.0",
    "hypothesis-jsonschema>=0.23.0",
]
```

### 2.2 Invariants to Encode

#### Task State Machine Invariants

```python
# Allowed state transitions
VALID_TRANSITIONS = {
    "pending": {"running", "failed"},
    "running": {"completed", "failed", "pending"},  # pending = retry
    "completed": set(),  # terminal
    "failed": {"pending"},  # retry allowed
}

# Properties to test:
# 1. No transition to invalid state ever succeeds
# 2. Terminal states cannot transition
# 3. Status timestamp always updates on transition
```

#### Lease System Invariants

```python
# Properties to test:
# 1. lease_timeout > locked_at (always)
# 2. Only one worker can hold a lease at a time
# 3. Expired leases can be claimed by any worker
# 4. try_count monotonically increases per task
# 5. try_count <= max_tries when task is running
```

#### Cost Calculation Invariants

```python
# Properties to test:
# 1. total_cost >= 0 (never negative)
# 2. total_cost = f(input_tokens, output_tokens, model) is deterministic
# 3. Zero tokens → zero cost
# 4. Cost scales linearly with token count
```

#### Workflow Invariants

```python
# Properties to test:
# 1. iteration_count <= max_iterations (always)
# 2. Completed workflow has all subtasks in terminal state
# 3. Parent task cost >= sum(subtask costs)
# 4. Workflow state progression is monotonic (no backward steps)
```

### 2.3 Boundary Test Cases

| Component | Boundary | Test Cases |
|-----------|----------|------------|
| Lease timeout | Exact expiry second | `now == lease_timeout`, `now == lease_timeout + 1ms` |
| Max iterations | Iteration limit | `iteration == max - 1`, `iteration == max`, `iteration == max + 1` |
| Retry count | Max tries | `try_count == max_tries - 1`, `try_count == max_tries` |
| Web search results | Result limits | `max_results == 0`, `max_results == 1`, `max_results == 10`, `max_results == 11` |
| Cost precision | Decimal places | Values requiring >6 decimal places, exactly 6, fewer than 6 |
| Task input size | JSON limits | Empty input `{}`, 1MB input, malformed JSON |

### 2.4 Required Test Files

```
tests/
├── test_invariants/
│   ├── __init__.py
│   ├── test_task_state_machine.py      # State transition properties
│   ├── test_lease_invariants.py        # Lease system properties
│   ├── test_cost_invariants.py         # Cost calculation properties
│   └── test_workflow_invariants.py     # Workflow progression properties
├── test_boundaries/
│   ├── __init__.py
│   ├── test_lease_boundaries.py        # Exact timeout boundaries
│   ├── test_iteration_boundaries.py    # Max iteration edge cases
│   └── test_retry_boundaries.py        # Retry count limits
```

### Success Criteria - Phase 2

- [ ] Hypothesis installed and configured in test suite
- [ ] Minimum 20 property-based tests implemented
- [ ] All state machine transitions have explicit allow/deny tests
- [ ] Lease timeout boundary tests pass with 1-second precision
- [ ] Iteration boundary tests cover `max-1`, `max`, `max+1` cases
- [ ] Cost invariant tests prove non-negativity
- [ ] All boundary tests documented with rationale

**Verification Command:**
```bash
pytest tests/test_invariants tests/test_boundaries -v --hypothesis-show-statistics
# Expected: All properties pass, no counterexamples found
```

---

## Phase 3: Mutation Testing & Fault Injection

**Duration:** 2-3 weeks
**Priority:** Medium-High
**Goal:** Verify test suite catches real bugs through mutation testing and chaos engineering

### 3.1 Mutation Testing Setup

**Dependencies:**
```toml
[project.optional-dependencies]
test = [
    # ... existing
    "mutmut>=2.4.0",
]
```

**Configuration (pyproject.toml):**
```toml
[tool.mutmut]
paths_to_mutate = "app/"
tests_dir = "tests/"
runner = "pytest -x -q"
```

### 3.2 Mutation Testing Targets

Priority modules for mutation testing (high complexity, high risk):

| Module | Reason | Expected Mutation Score |
|--------|--------|-------------------------|
| `app/orchestrator/coordination_strategies.py` | Complex state logic | ≥ 85% |
| `app/worker_lease.py` | Concurrency-critical | ≥ 90% |
| `app/worker.py` | Core business logic | ≥ 80% |
| `app/tools/calculator.py` | Parsing edge cases | ≥ 85% |
| `app/cost_tracking.py` (via tasks.py) | Financial calculations | ≥ 95% |

### 3.3 Known Weak Spots to Strengthen

Based on test structure analysis, likely surviving mutants:

| Location | Mutation Type | Required Test |
|----------|---------------|---------------|
| Error messages | String changes | Assert exact error text |
| Numeric comparisons | `<` → `<=`, `>` → `>=` | Boundary value tests |
| Default values | Value changes | Explicit default verification |
| Boolean conditions | `and` → `or`, negation | Truth table coverage |
| Return values | None → empty, swap returns | Return value assertions |

### 3.4 Fault Injection Tests

#### Database Failures

```python
class TestDatabaseFaultInjection:
    """Test resilience to database failures."""

    async def test_connection_drop_during_task_processing(self):
        """Task should be retryable after connection loss."""

    async def test_transaction_timeout(self):
        """Long-running transactions should not corrupt state."""

    async def test_connection_pool_exhaustion(self):
        """System should degrade gracefully when pool exhausted."""
```

#### Network Failures

```python
class TestNetworkFaultInjection:
    """Test resilience to network failures."""

    async def test_api_timeout_during_agent_call(self):
        """Agent timeout should mark task for retry."""

    async def test_partial_response_handling(self):
        """Incomplete API responses should not corrupt state."""
```

#### Concurrent Operation Failures

```python
class TestConcurrencyFaultInjection:
    """Test resilience to race conditions."""

    async def test_double_claim_same_task(self):
        """Only one worker should succeed in claiming."""

    async def test_lease_renewal_during_expiry(self):
        """Renewal at exact expiry moment should be deterministic."""

    async def test_completion_after_lease_expiry(self):
        """Late completion should not overwrite new owner's work."""
```

### 3.5 Required Test Files

```
tests/
├── test_fault_injection/
│   ├── __init__.py
│   ├── test_database_faults.py
│   ├── test_network_faults.py
│   └── test_concurrency_faults.py
├── mutation_results/          # Generated by mutmut
│   └── .gitkeep
```

### Success Criteria - Phase 3

- [ ] mutmut configured and baseline mutation score recorded
- [ ] `worker_lease.py` mutation score ≥ 90%
- [ ] `coordination_strategies.py` mutation score ≥ 85%
- [ ] Cost calculation mutation score ≥ 95%
- [ ] Overall mutation score ≥ 75%
- [ ] All surviving mutants documented with justification (equivalent mutants, etc.)
- [ ] Database fault injection tests pass
- [ ] Network fault injection tests pass
- [ ] Concurrent fault tests prove deterministic behavior

**Verification Commands:**
```bash
# Run mutation testing
mutmut run --paths-to-mutate=app/worker_lease.py
mutmut results

# Run fault injection
pytest tests/test_fault_injection -v --timeout=30
```

---

## Phase 4: Contract Testing & Integration Hardening

**Duration:** 2-3 weeks
**Priority:** Medium
**Goal:** Establish API contracts and comprehensive integration testing

### 4.1 API Contract Testing

**Dependencies:**
```toml
[project.optional-dependencies]
test = [
    # ... existing
    "schemathesis>=3.25.0",
]
```

#### OpenAPI Schema Validation

```python
# tests/test_api_contracts.py

import schemathesis

schema = schemathesis.from_path("openapi.yaml")

@schema.parametrize()
def test_api_contract(case):
    """All API endpoints conform to OpenAPI spec."""
    response = case.call()
    case.validate_response(response)
```

#### Response Schema Tests

| Endpoint | Contract Assertions |
|----------|---------------------|
| `POST /tasks` | Returns TaskResponse with valid UUID |
| `GET /tasks/{id}` | 404 has standard error schema |
| `PUT /tasks/{id}` | Partial update doesn't null other fields |
| `GET /admin/agents` | List schema matches AgentMetadata[] |
| `GET /costs/summary` | Numeric fields are non-negative |

### 4.2 Integration Test Hardening

#### End-to-End Workflow Tests

```python
class TestCompleteWorkflowE2E:
    """Full workflow execution with real components."""

    async def test_sequential_workflow_happy_path(self):
        """Complete sequential workflow from creation to completion."""

    async def test_iterative_workflow_with_refinement(self):
        """Iterative workflow requiring multiple passes."""

    async def test_workflow_failure_recovery(self):
        """Workflow recovers from transient failures."""

    async def test_workflow_timeout_handling(self):
        """Workflow handles agent timeouts gracefully."""
```

#### Multi-Worker Integration Tests

```python
class TestMultiWorkerIntegration:
    """Tests with multiple concurrent workers."""

    async def test_work_distribution_fairness(self):
        """Tasks distributed roughly evenly across workers."""

    async def test_no_duplicate_processing(self):
        """Same task never processed by multiple workers."""

    async def test_worker_failure_recovery(self):
        """Other workers pick up tasks from failed worker."""
```

### 4.3 Performance Baseline Tests

```python
class TestPerformanceBaselines:
    """Establish and verify performance baselines."""

    @pytest.mark.benchmark
    async def test_task_creation_latency(self, benchmark):
        """Task creation < 50ms p99."""

    @pytest.mark.benchmark
    async def test_task_claim_latency(self, benchmark):
        """Task claim < 100ms p99."""

    @pytest.mark.benchmark
    async def test_registry_lookup_latency(self, benchmark):
        """Registry lookup < 1ms p99."""
```

### 4.4 Required Test Files

```
tests/
├── test_contracts/
│   ├── __init__.py
│   ├── test_api_contracts.py           # OpenAPI conformance
│   ├── test_response_schemas.py        # Response structure validation
│   └── test_error_schemas.py           # Error response consistency
├── test_integration/
│   ├── __init__.py
│   ├── test_workflow_e2e.py            # Full workflow tests
│   ├── test_multi_worker.py            # Concurrent worker tests
│   └── test_performance_baselines.py   # Performance regression tests
├── openapi.yaml                        # API specification (if not exists)
```

### Success Criteria - Phase 4

- [ ] OpenAPI specification exists and is complete
- [ ] All endpoints pass schemathesis validation
- [ ] Error responses have consistent schema across all endpoints
- [ ] E2E workflow tests cover happy path, failure, and timeout scenarios
- [ ] Multi-worker tests prove no duplicate processing
- [ ] Performance baselines established and documented
- [ ] CI pipeline includes contract and performance tests

**Verification Commands:**
```bash
# Contract testing
schemathesis run openapi.yaml --base-url=http://localhost:8000

# Performance baselines
pytest tests/test_integration/test_performance_baselines.py --benchmark-only

# Full integration suite
pytest tests/test_integration tests/test_contracts -v --timeout=120
```

---

## Implementation Tracking

### Phase Summary

| Phase | Duration | Tests Added | Coverage Target | Mutation Target |
|-------|----------|-------------|-----------------|-----------------|
| 1 | 1-2 weeks | ~30 | 80% overall | N/A |
| 2 | 2-3 weeks | ~50 | 82% overall | N/A |
| 3 | 2-3 weeks | ~40 | 85% overall | 75% mutation score |
| 4 | 2-3 weeks | ~30 | 85% overall | 80% mutation score |

### Final Success Metrics

After all phases complete:

| Metric | Current | Target |
|--------|---------|--------|
| Total tests | 362 | ~500+ |
| Line coverage | 78.18% | ≥ 85% |
| Branch coverage | Unknown | ≥ 75% |
| Mutation score | Unknown | ≥ 80% |
| Test execution time | 4.81s | < 10s |
| Deprecation warnings | 131 | 0 |

### CI/CD Integration

```yaml
# .github/workflows/test.yml additions
test:
  steps:
    - name: Unit & Integration Tests
      run: pytest -v --cov=app --cov-fail-under=85

    - name: Property-Based Tests
      run: pytest tests/test_invariants -v --hypothesis-seed=0

    - name: Contract Tests
      run: schemathesis run openapi.yaml --base-url=http://localhost:8000

    - name: Mutation Testing (weekly)
      if: github.event_name == 'schedule'
      run: mutmut run && mutmut results --ci
```

---

## Appendix A: Test File Templates

### Property-Based Test Template

```python
"""Property-based tests for [component]."""

from hypothesis import given, strategies as st, settings, Phase
import pytest

class TestComponentInvariants:
    """Invariant tests for [component]."""

    @given(st.integers(min_value=0, max_value=1000))
    @settings(max_examples=100, phases=[Phase.generate, Phase.target])
    def test_invariant_name(self, value):
        """[Invariant description]."""
        result = component.operation(value)
        assert invariant_holds(result), f"Invariant violated for {value}"
```

### Fault Injection Test Template

```python
"""Fault injection tests for [component]."""

import pytest
from unittest.mock import patch, AsyncMock

class TestComponentFaults:
    """Fault injection tests for [component]."""

    @pytest.mark.asyncio
    async def test_handles_connection_failure(self):
        """[Component] gracefully handles connection failure."""
        with patch('app.database.get_db') as mock_db:
            mock_db.side_effect = ConnectionError("Database unavailable")

            result = await component.operation()

            assert result.status == "retry"
            assert "connection" in result.error.lower()
```

---

## Appendix B: Coverage Gap Details

### `app/db_utils.py` Uncovered Lines Analysis

| Line Range | Function/Block | Risk Level | Test Needed |
|------------|----------------|------------|-------------|
| 63-92 | Error handling for bulk operations | High | Partial failure scenarios |
| 146-147 | Connection retry logic | Medium | Transient failure simulation |
| 154-160 | Transaction rollback | High | Rollback trigger conditions |
| 203-222 | Query timeout handling | Medium | Slow query simulation |
| 241-292 | Batch insert optimization | Low | Large batch edge cases |
| 314-324 | Connection pool management | Medium | Pool exhaustion |

### `app/text_utils.py` Uncovered Lines Analysis

| Line Range | Function | Risk Level | Test Needed |
|------------|----------|------------|-------------|
| 9-20 | Text normalization | Medium | Unicode edge cases |
| 25-39 | Chunk boundary detection | High | Edge cases at boundaries |
| 44-53 | Encoding detection | Medium | Various encodings |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 2025 | - | Initial requirements document |
-e


# ./Backlog/STATE_MACHINE_REFACTOR.md

Feature: Refactor Worker to Explicit Dual State Machines
Overview
Refactor app/worker.py from implicit control-flow states to two explicit state machines:

WorkerStateMachine: Manages worker process lifecycle (connection, polling, shutdown)
TaskStateMachine: Manages individual task processing lifecycle (claim, process, report)

This separation enables independent testing, clearer invariants, and future concurrency.

Part 1: Worker State Machine
Functional Requirements
FR1.1: Worker States
pythonclass WorkerState(Enum):
    STARTING = "starting"       # Initializing logging, metrics, tracing
    CONNECTING = "connecting"   # Establishing DB connection
    RUNNING = "running"         # Main loop: poll, delegate to TaskSM, backoff
    RECOVERING = "recovering"   # Checking for expired leases
    BACKING_OFF = "backing_off" # Sleeping due to no tasks
    SHUTTING_DOWN = "shutting_down"  # Graceful shutdown in progress
    STOPPED = "stopped"         # Terminal state
FR1.2: Worker Events
pythonclass WorkerEvent(Enum):
    INITIALIZED = "initialized"
    CONNECTED = "connected"
    CONNECTION_FAILED = "connection_failed"
    RECOVERY_COMPLETE = "recovery_complete"
    POLL_CYCLE_COMPLETE = "poll_cycle_complete"
    NO_TASKS_AVAILABLE = "no_tasks_available"
    BACKOFF_COMPLETE = "backoff_complete"
    SHUTDOWN_REQUESTED = "shutdown_requested"
    SHUTDOWN_COMPLETE = "shutdown_complete"
    ERROR = "error"
FR1.3: Worker Transition Table
pythonWORKER_TRANSITIONS: Dict[Tuple[WorkerState, WorkerEvent], WorkerState] = {
    # Startup sequence
    (WorkerState.STARTING, WorkerEvent.INITIALIZED): WorkerState.CONNECTING,
    (WorkerState.CONNECTING, WorkerEvent.CONNECTED): WorkerState.RECOVERING,
    (WorkerState.CONNECTING, WorkerEvent.CONNECTION_FAILED): WorkerState.CONNECTING,  # Retry with backoff

    # Main loop
    (WorkerState.RECOVERING, WorkerEvent.RECOVERY_COMPLETE): WorkerState.RUNNING,
    (WorkerState.RUNNING, WorkerEvent.NO_TASKS_AVAILABLE): WorkerState.BACKING_OFF,
    (WorkerState.RUNNING, WorkerEvent.POLL_CYCLE_COMPLETE): WorkerState.RUNNING,  # Continue polling
    (WorkerState.BACKING_OFF, WorkerEvent.BACKOFF_COMPLETE): WorkerState.RECOVERING,

    # Shutdown from any active state
    (WorkerState.RUNNING, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.BACKING_OFF, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.RECOVERING, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.CONNECTING, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.SHUTTING_DOWN, WorkerEvent.SHUTDOWN_COMPLETE): WorkerState.STOPPED,

    # Error handling
    (WorkerState.RUNNING, WorkerEvent.ERROR): WorkerState.CONNECTING,  # Reconnect
    (WorkerState.RECOVERING, WorkerEvent.ERROR): WorkerState.CONNECTING,
}
FR1.4: Worker State Machine Class
pythonclass WorkerStateMachine:
    def __init__(self, worker_id: str):
        self.state: WorkerState = WorkerState.STARTING
        self.worker_id = worker_id
        self.context = WorkerContext()

    def transition(self, event: WorkerEvent) -> WorkerState:
        """Execute state transition, emit metrics, return new state."""
        ...

    def can_transition(self, event: WorkerEvent) -> bool:
        """Check if transition is valid."""
        ...

    def is_accepting_tasks(self) -> bool:
        """Returns True if worker should process tasks."""
        return self.state == WorkerState.RUNNING

    def is_running(self) -> bool:
        """Returns True if worker is not stopped."""
        return self.state != WorkerState.STOPPED
FR1.5: Worker Context
python@dataclass
class WorkerContext:
    connection: Optional[Connection] = None
    backoff_count: int = 0
    last_recovery_time: Optional[datetime] = None
    shutdown_requested: bool = False
    current_task_sm: Optional["TaskStateMachine"] = None  # Active task being processed
    tasks_processed: int = 0
    tasks_failed: int = 0
FR1.6: Graceful Shutdown

Signal handlers (SIGTERM, SIGINT) call transition(WorkerEvent.SHUTDOWN_REQUESTED)
SHUTTING_DOWN state waits for context.current_task_sm to reach terminal state
Timeout: 30 seconds, then force stop
Emit shutdown metrics before STOPPED


Part 2: Task State Machine
Functional Requirements
FR2.1: Task States
pythonclass TaskState(Enum):
    PENDING = "pending"         # Task identified, not yet claimed
    CLAIMING = "claiming"       # Attempting to acquire lease
    PROCESSING = "processing"   # Executing task logic
    REPORTING = "reporting"     # Writing results to DB, notifying API
    COMPLETED = "completed"     # Terminal: success
    FAILED = "failed"           # Terminal: error
    ABANDONED = "abandoned"     # Terminal: worker shutdown before completion
FR2.2: Task Events
pythonclass TaskEvent(Enum):
    CLAIM_REQUESTED = "claim_requested"
    CLAIM_SUCCEEDED = "claim_succeeded"
    CLAIM_FAILED = "claim_failed"
    PROCESSING_SUCCEEDED = "processing_succeeded"
    PROCESSING_FAILED = "processing_failed"
    REPORT_SUCCEEDED = "report_succeeded"
    REPORT_FAILED = "report_failed"
    LEASE_EXPIRED = "lease_expired"
    SHUTDOWN_REQUESTED = "shutdown_requested"
FR2.3: Task Transition Table
pythonTASK_TRANSITIONS: Dict[Tuple[TaskState, TaskEvent], TaskState] = {
    # Happy path
    (TaskState.PENDING, TaskEvent.CLAIM_REQUESTED): TaskState.CLAIMING,
    (TaskState.CLAIMING, TaskEvent.CLAIM_SUCCEEDED): TaskState.PROCESSING,
    (TaskState.PROCESSING, TaskEvent.PROCESSING_SUCCEEDED): TaskState.REPORTING,
    (TaskState.REPORTING, TaskEvent.REPORT_SUCCEEDED): TaskState.COMPLETED,

    # Failure paths
    (TaskState.CLAIMING, TaskEvent.CLAIM_FAILED): TaskState.FAILED,
    (TaskState.PROCESSING, TaskEvent.PROCESSING_FAILED): TaskState.REPORTING,  # Report the failure
    (TaskState.REPORTING, TaskEvent.REPORT_FAILED): TaskState.FAILED,  # Log and abandon

    # Lease expiry (detected during processing)
    (TaskState.PROCESSING, TaskEvent.LEASE_EXPIRED): TaskState.ABANDONED,

    # Shutdown interruption
    (TaskState.PROCESSING, TaskEvent.SHUTDOWN_REQUESTED): TaskState.REPORTING,  # Try to report partial
    (TaskState.CLAIMING, TaskEvent.SHUTDOWN_REQUESTED): TaskState.ABANDONED,
}
FR2.4: Task State Machine Class
pythonclass TaskStateMachine:
    def __init__(self, task_id: str, task_type: str, worker_id: str):
        self.state: TaskState = TaskState.PENDING
        self.task_id = task_id
        self.task_type = task_type
        self.worker_id = worker_id
        self.context = TaskContext()

    def transition(self, event: TaskEvent) -> TaskState:
        """Execute state transition, emit metrics, return new state."""
        ...

    def is_terminal(self) -> bool:
        """Returns True if task reached terminal state."""
        return self.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.ABANDONED)

    def execute(self, conn: Connection) -> TaskResult:
        """
        Run task through state machine to completion.

        Called by WorkerStateMachine when in RUNNING state.
        """
        ...
FR2.5: Task Context
python@dataclass
class TaskContext:
    lease_acquired_at: Optional[datetime] = None
    lease_timeout: Optional[datetime] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
FR2.6: Task Result
python@dataclass
class TaskResult:
    task_id: str
    final_state: TaskState
    output: Optional[dict] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    duration_ms: Optional[int] = None

Part 3: Integration
FR3.1: Worker-Task Coordination
python# In WorkerStateMachine.run()
while self.is_running():
    if self.state == WorkerState.RUNNING:
        task_row = claim_next_task(self.context.connection, self.worker_id)
        if task_row:
            task_sm = TaskStateMachine(
                task_id=task_row["id"],
                task_type=task_row["type"],
                worker_id=self.worker_id
            )
            self.context.current_task_sm = task_sm
            result = task_sm.execute(self.context.connection)
            self.context.current_task_sm = None
            self._record_result(result)
            self.transition(WorkerEvent.POLL_CYCLE_COMPLETE)
        else:
            self.transition(WorkerEvent.NO_TASKS_AVAILABLE)
FR3.2: Lease Renewal Integration

renew_lease() called periodically during TaskState.PROCESSING
If renewal fails, emit TaskEvent.LEASE_EXPIRED
Renewal runs in background or between processing chunks

FR3.3: Existing Helper Integration

worker_helpers.py functions called from TaskStateMachine.execute()
worker_lease.py functions called from WorkerStateMachine (recovery) and TaskStateMachine (renewal)
notify_api_async called from TaskStateMachine during REPORTING state


Non-Functional Requirements
NFR1: Cyclomatic Complexity
Function/MethodTargetCurrentWorkerStateMachine.transition()< 5N/A (new)TaskStateMachine.transition()< 5N/A (new)WorkerStateMachine.run()< 1013 (run_worker)TaskStateMachine.execute()< 1020 (_process_task_row)
NFR2: Performance

State transition overhead: < 0.1ms
No additional DB round-trips vs. current implementation
Memory per task: single TaskContext (~500 bytes)

NFR3: Observability
python# Worker metrics
worker_state = Gauge(
    "worker_state",
    "Current worker state",
    ["worker_id", "state"]
)

worker_state_transitions_total = Counter(
    "worker_state_transitions_total",
    "Worker state transitions",
    ["worker_id", "from_state", "to_state", "event"]
)

# Task metrics
task_state_transitions_total = Counter(
    "task_state_transitions_total",
    "Task state transitions",
    ["task_type", "from_state", "to_state", "event"]
)

task_state_duration_seconds = Histogram(
    "task_state_duration_seconds",
    "Time spent in each task state",
    ["task_type", "state"]
)
python# Log events
logger.info("worker_state_transition",
    worker_id=..., from_state=..., to_state=..., event=...)

logger.info("task_state_transition",
    task_id=..., task_type=..., from_state=..., to_state=..., event=...)

logger.warning("invalid_transition_attempted",
    machine=..., current_state=..., event=..., reason=...)
```

Part 4: Wire Up worker.py
Functional Requirements
FR4.1: Replace run_worker() Implementation
python# app/worker.py

from app.worker_state import WorkerStateMachine

def run_worker() -> None:
    """Main entry point for worker process."""
    from app.instance import get_instance_name

    worker_id = get_instance_name()
    state_machine = WorkerStateMachine(worker_id=worker_id)
    state_machine.run()
FR4.2: Deprecate Old Implementation

Rename current run_worker() to run_worker_legacy()
Keep _process_task_row() as _process_task_row_legacy() for reference
Add deprecation comment with removal date

FR4.3: Preserve Entry Points

if __name__ == "__main__" block unchanged
CLI entry points unchanged
Docker entrypoint unchanged


Test Cases
Regression Tests (existing tests must pass)
python# All existing tests in:
# - tests/test_worker.py
# - tests/test_worker_helpers.py
# - tests/test_worker_integration.py (if exists)
Smoke Tests
pythondef test_run_worker_creates_state_machine()
def test_run_worker_uses_instance_name_as_worker_id()
def test_worker_entrypoint_unchanged()

Verification
bash# Full regression
pytest -v

# Complexity check on new worker.py
radon cc app/worker.py -s

# Verify entrypoint works
python -c "from app.worker import run_worker; print('OK')"
```

---

### Files to Modify
```
app/worker.py           # Replace run_worker() implementation
app/worker_backup.py    # Optional: copy old implementation

Verification Criteria

 All existing 452+ tests pass
 New smoke tests pass
 run_worker() delegates to WorkerStateMachine.run()
 Cyclomatic complexity of run_worker() < 3
 No changes to CLI or Docker entrypoints


Part 5: Cleanup (Optional)
After validation period (1 week):

Remove _legacy functions
Remove worker_backup.py
Update documentation

---

## Invariants

**Worker Invariants**
```
W-INV1: Worker in RUNNING has non-null context.connection
W-INV2: Worker in SHUTTING_DOWN does not start new TaskStateMachines
W-INV3: Worker reaches STOPPED within 30s of SHUTDOWN_REQUESTED
W-INV4: Worker in STOPPED has context.connection = None
W-INV5: Only one TaskStateMachine active per worker (context.current_task_sm)
```

**Task Invariants**
```
T-INV1: Task in PROCESSING has context.lease_timeout in future (or within grace period)
T-INV2: Task in PROCESSING has context.lease_acquired_at set
T-INV3: Task in terminal state (COMPLETED, FAILED, ABANDONED) does not transition
T-INV4: Task in REPORTING has either output_data or error set
T-INV5: Task state transitions are atomic (no partial transitions)

Test Cases
Worker State Machine Tests (10 tests)
pythondef test_worker_startup_to_connecting()
def test_worker_connecting_success_to_recovering()
def test_worker_connecting_failure_retries()
def test_worker_recovery_to_running()
def test_worker_running_no_tasks_to_backing_off()
def test_worker_backoff_complete_to_recovering()
def test_worker_shutdown_from_running()
def test_worker_shutdown_from_backing_off()
def test_worker_shutdown_waits_for_active_task()
def test_worker_invalid_transition_raises_error()
Worker Invariant Tests (5 tests)
pythondef test_worker_running_has_connection()
def test_worker_shutting_down_rejects_new_tasks()
def test_worker_shutdown_timeout_forces_stop()
def test_worker_stopped_releases_connection()
def test_worker_single_active_task()
Task State Machine Tests (12 tests)
pythondef test_task_pending_to_claiming()
def test_task_claim_success_to_processing()
def test_task_claim_failure_to_failed()
def test_task_processing_success_to_reporting()
def test_task_processing_failure_to_reporting()
def test_task_reporting_success_to_completed()
def test_task_reporting_failure_to_failed()
def test_task_lease_expired_to_abandoned()
def test_task_shutdown_during_processing()
def test_task_shutdown_during_claiming()
def test_task_is_terminal_completed()
def test_task_invalid_transition_raises_error()
Task Invariant Tests (5 tests)
pythondef test_task_processing_has_valid_lease()
def test_task_processing_has_lease_acquired_time()
def test_task_terminal_state_no_transitions()
def test_task_reporting_has_output_or_error()
def test_task_transitions_are_atomic()
Integration Tests (8 tests)
pythondef test_worker_processes_single_task_to_completion()
def test_worker_processes_failing_task()
def test_worker_recovers_expired_lease_from_other_worker()
def test_worker_graceful_shutdown_completes_active_task()
def test_worker_backoff_increases_on_empty_queue()
def test_task_lease_renewal_during_long_processing()
def test_worker_reconnects_after_db_failure()
def test_notify_api_called_on_task_completion()
Regression Tests
python# All existing tests must pass:
# - tests/test_worker.py
# - tests/test_worker_helpers.py
# - tests/test_tasks.py
```

---

## Files
```
# New files
app/worker_state.py         # WorkerStateMachine, WorkerState, WorkerEvent, WorkerContext
app/task_state.py           # TaskStateMachine, TaskState, TaskEvent, TaskContext, TaskResult
tests/test_worker_state.py  # Worker SM unit tests
tests/test_task_state.py    # Task SM unit tests

# Modified files
app/worker.py               # Refactor to use WorkerStateMachine
app/worker_helpers.py       # May need minor interface adjustments
app/worker_lease.py         # Integrate with TaskStateMachine for renewal
app/metrics.py              # Add new state metrics

# Unchanged
app/worker_backup.py        # Keep as reference/rollback

Verification Criteria

 All existing tests pass (452 tests)
 40 new state machine tests pass
 Cyclomatic complexity targets met (radon cc)
 No new mypy errors
 No new ruff errors
 State metrics visible in Prometheus
 Graceful shutdown completes within 30s
 SIGTERM triggers clean shutdown
 No data loss during shutdown (task either completes or returns to pending)
-e


# ./Backlog/WORKER_HELPERS_TEST_REFACTOR.md

I need to improve the testing for the worker_helpers module. Mutant testing has detected quite a few issues. Overall goals is to improve coverage and shore up testing.

Here’s a phased requirements spec for tests for worker_helpers, tuned for AI consumption.

Phase 1 – Basic coverage & happy paths (minimum bar)

Goal: Every main function has at least one realistic, meaningful test.

For each of:

_process_subtask

_process_workflow_task

claim_next_task

the tests must:

Have one happy-path test

Function is called with a plausible row.

No dependencies fail.

Test asserts:

Returned value (if any) is not None and structurally sane.

At least one DB update happened.

Commit was called.

Use realistic data

row includes all fields the function actually reads.

No dummy placeholders like {} if the real code expects structure.

👉 Phase 1 is allowed to be pretty rough; it just guarantees the AI can “see” all main flows.

Phase 2 – State transitions & error handling (behavioral bar)

Goal: Tests pin down what must happen to tasks/subtasks in success vs failure.

_process_subtask tests MUST:

Success test

Assert final subtask status (e.g. done).

Assert parent task status is set as expected (e.g. still running or done).

Assert agent + orchestrator were called (no details yet, just that they were used).

Failure test (agent or orchestrator error)

Cause a controlled exception in agent/orchestrator.

Assert:

subtask ends in an error-like status,

parent task ends in an error-like or degraded status (whatever your rule is).

_process_workflow_task tests MUST:

Success test

Assert task status moves to a “started/running” or equivalent status.

Assert an orchestrator was created and invoked.

Failure test

Simulate bad workflow type or orchestrator failure.

Assert task ends in an error-like status.

claim_next_task tests MUST:

Subtask-first test

Scenario where both a claimable subtask and task exist.

Assert:

returned object is the subtask,

subtask got its status updated (e.g. to running).

Task fallback test

Scenario with no claimable subtasks but a claimable task.

Assert:

returned object is the task,

task got its status updated.

None test

Scenario with nothing claimable.

Assert:

function returns None,

no updates executed.

👉 After Phase 2, success vs failure behavior is nailed down at a high level.

Phase 3 – Edge cases, retries & leases (robustness bar)

Goal: Tests protect the critical scheduling semantics from regressing.

claim_next_task edge tests MUST:

Respects max_tries

Have a row with try_count == max_tries.

Assert it is not returned.

If it’s the only candidate, function returns None.

Respects leases

Have a row that looks “leased” (e.g. active leased_until / running status).

Assert it is not returned.

Updates key fields on claim

For a claimed row (subtask or task), assert:

status changed (e.g. to running),

worker_id set,

try_count incremented.

_process_subtask / _process_workflow_task edge tests MUST:

Cost / usage handling

When the agent returns usage / cost, assert it is written somewhere (task, subtask, workflow).

Distinct parent vs child updates

In an error scenario, assert that both:

the subtask row,

and the parent task row
are updated as per your rules (not just “something with status='error' happened”).

👉 After Phase 3, the main invariants around retries, leases, and parent/child behavior are guarded.

Phase 4 – Safety metrics (for this file only)

Once Phases 1–3 are satisfied:

Coverage target (local to this file)

Line coverage for worker_helpers.py ≥ 85%.

Each main branch in the three functions is exercised by at least one test (happy / error / edge).
-e


# ./docs/AGENT_REGISTRY.md

# Agent Registry

## Overview

The Agent Registry is a centralized system for managing, discovering, and configuring agents in the multi-agent workflow system. It provides three flexible approaches for agent registration:

1. **YAML Configuration** - Declarative agent definitions
2. **Auto-Discovery** - Automatic detection from filesystem
3. **Programmatic Registration** - Direct registration in code

## Quick Start

### Using the Registry

```python
from app.agents.registry_init import registry

# Get an agent (singleton)
agent = registry.get("research")

# Create a new instance
fresh_agent = registry.create_new("research")

# Check if agent exists
if registry.has("custom_agent"):
    agent = registry.get("custom_agent")

# List all agents
all_agents = registry.list_all()  # ['research', 'assessment']
```

### Worker Integration

The worker automatically uses the registry:

```python
# In app/worker_helpers.py
from app.agents import get_agent

agent = get_agent("research")  # Uses registry automatically
result = agent.execute(input_data)
```

## Configuration Methods

### 1. YAML Configuration (Recommended)

**Create `config/agents.yaml`:**
```yaml
agents:
  - name: research
    class: app.agents.research_agent.ResearchAgent
    config:
      model: gpt-4-turbo
      temperature: 0.7
    tools:
      - web_search
      - document_reader
    description: "Conducts deep research on topics"

  - name: assessment
    class: app.agents.assessment_agent.AssessmentAgent
    config:
      model: gpt-4-turbo
      temperature: 0.3
    tools:
      - fact_checker
    description: "Assesses research quality"
```

**Benefits:**
- ✅ Centralized configuration
- ✅ Version controlled
- ✅ Environment-specific configs (dev/staging/prod)
- ✅ No code changes needed

### 2. Auto-Discovery (Zero Config)

Agents are automatically discovered from `app/agents/` directory on startup.

**File naming convention:**
```
app/agents/
├── base.py              # ← Excluded (base class)
├── research_agent.py    # ← Discovered as "research"
├── assessment_agent.py  # ← Discovered as "assessment"
└── custom_agent.py      # ← Discovered as "custom"
```

**Agent type derived from filename:**
- `research_agent.py` → `"research"`
- `assessment_agent.py` → `"assessment"`
- Format: `{type}_agent.py` → `{type}`

**Benefits:**
- ✅ No configuration needed
- ✅ Just add file and restart
- ✅ Perfect for development

### 3. Programmatic Registration

Useful for testing or dynamic agent creation:

```python
from app.agents.registry_init import registry
from app.agents.research_agent import ResearchAgent

# Manual registration
registry.register(
    agent_type="custom",
    agent_class=ResearchAgent,
    config={"model": "gpt-4"},
    tools=["tool1", "tool2"],
    description="Custom agent"
)
```

## Registry Initialization

The registry initializes automatically on first import using this strategy:

```python
# app/agents/registry_init.py
# 1. Try loading from config/agents.yaml
# 2. Fall back to auto-discovery from app/agents/
# 3. Return empty registry as last resort
```

**Startup flow:**
```
Worker Starts
    ↓
Import registry_init module
    ↓
Auto-initialize registry
    ↓
Load from YAML (if exists)
    OR
Auto-discover from filesystem
    ↓
Registry ready
```

## Features

### Singleton Pattern

Agents are cached as singletons for performance:

```python
# First call creates instance
agent1 = registry.get("research")

# Second call returns same instance
agent2 = registry.get("research")

assert agent1 is agent2  # True - same object
```

**Benefits:**
- ✅ Better performance (no repeated initialization)
- ✅ Consistent state across requests
- ✅ Lower memory usage

**Create new instance when needed:**
```python
fresh_agent = registry.create_new("research")  # New instance
```

### Thread Safety

Registry operations are thread-safe:

```python
# Multiple workers can access simultaneously
with registry._lock:
    registry.register(...)  # Protected
```

### Observability

Registry emits structured logs:

```python
# On initialization
INFO: agents_discovered - agent_types=['research', 'assessment'] count=2

# On agent instantiation
INFO: agent_instantiated - agent_type=research instance_id=... is_singleton=true
```

## API Reference

### Registry Methods

#### `get(agent_type: str) -> Agent`
Get singleton agent instance.

```python
agent = registry.get("research")
```

**Raises:** `ValueError` if agent not found

#### `create_new(agent_type: str, **override_config) -> Agent`
Create fresh agent instance (not singleton).

```python
agent = registry.create_new("research", temperature=0.9)
```

#### `register(agent_type, agent_class, config=None, tools=None, description="")`
Manually register an agent.

```python
registry.register(
    agent_type="custom",
    agent_class=CustomAgent,
    config={"param": "value"},
    tools=["tool1"],
    description="Description"
)
```

#### `has(agent_type: str) -> bool`
Check if agent is registered.

```python
if registry.has("custom"):
    agent = registry.get("custom")
```

#### `list_all() -> List[str]`
List all registered agent types.

```python
agents = registry.list_all()  # ['research', 'assessment']
```

#### `get_metadata(agent_type: str) -> AgentMetadata`
Get agent metadata including config, tools, description.

```python
metadata = registry.get_metadata("research")
print(metadata.config)  # {'model': 'gpt-4-turbo', ...}
print(metadata.tools)   # ['web_search', ...]
```

#### `load_from_yaml(yaml_path: str | Path)`
Load agents from YAML file.

```python
registry.load_from_yaml("config/agents.yaml")
```

#### `discover_agents(search_path="app/agents", exclude_patterns=None)`
Auto-discover agents from filesystem.

```python
discovered = registry.discover_agents()
print(f"Found: {discovered}")  # ['research', 'assessment']
```

## Environment Configuration

### Development
```yaml
# config/agents_dev.yaml
agents:
  - name: research
    config:
      model: gpt-3.5-turbo  # Cheaper for dev
      temperature: 0.7
```

### Production
```yaml
# config/agents_prod.yaml
agents:
  - name: research
    config:
      model: gpt-4-turbo  # Best quality
      temperature: 0.7
```

### Loading Environment-Specific Config

```python
import os
env = os.getenv("ENV", "production")
registry.load_from_yaml(f"config/agents_{env}.yaml")
```

## Scaling Considerations

### Horizontal Scaling

**Multiple Workers:**
- Each worker has independent in-memory registry
- Discovered from same code on startup
- Rolling deploys create brief version skew (acceptable)

**Characteristics:**
- ✅ Self-contained workers
- ✅ No coordination needed
- ✅ Simple and reliable
- ⚠️ Brief version skew during deploys (~30-60s)

### Current Design Benefits

**Code-Based Approach:**
- ✅ **Version Control** - Git tracks all agent changes
- ✅ **Reproducible** - Code = source of truth
- ✅ **Testable** - Easy to write tests
- ✅ **Fast** - In-memory, no DB queries
- ✅ **Simple** - No database schema/migrations

## Performance

Registry operations are extremely fast:

| Operation | Latency | Notes |
|-----------|---------|-------|
| `get()` | < 0.1ms | Cached singleton |
| `create_new()` | < 1ms | New instance |
| YAML loading | ~5ms | One-time on startup |
| Auto-discovery | ~10ms | One-time on startup |

**No overhead:** Singleton pattern means zero per-request cost.

## Testing

### Unit Tests

```python
def test_agent_from_registry():
    from app.agents.registry_init import registry

    agent = registry.get("research")
    assert agent is not None

    # Test singleton
    agent2 = registry.get("research")
    assert agent is agent2
```

### Mock Agents

```python
# In tests
from tests.mocks import MockAgent

registry.register("research", MockAgent)
# Now all code using registry gets mock
```

## Troubleshooting

### "Agent not found" error
```python
ValueError: Unknown agent type: 'custom'
Available agents: ['research', 'assessment']
```

**Solutions:**
1. Check agent file exists: `app/agents/custom_agent.py`
2. Verify YAML config has agent defined
3. Check exclusion patterns in `discover_agents()`

### Agent not auto-discovered

**Check:**
- File named correctly: `{type}_agent.py`
- Class inherits from `Agent` base class
- File not in exclusion list (`base.py`, `__*`)

### Workers have different agent versions

**During deployment:**
- Normal with rolling deploys (~30-60s skew)
- Workers restart with new code version
- Eventually consistent

## Future Enhancements

Potential Phase 4 features:

- **Hot-reload** - Reload agents without restart
- **Database persistence** - Track agent usage/metadata
- **Per-tenant agents** - Custom agents per customer
- **Agent versioning** - Multiple versions simultaneously
- **Plugin marketplace** - User-uploaded agents

## Architecture

```
┌─────────────────────────────────────────────┐
│  Worker Process                             │
│  ┌───────────────────────────────────────┐  │
│  │  registry_init.py                     │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  AgentRegistry                  │  │  │
│  │  │  ├── _agents: Dict[str, Meta]   │  │  │
│  │  │  ├── _lock: RLock              │  │  │
│  │  │  └── methods...                 │  │  │
│  │  └─────────────────────────────────┘  │  │
│  │           ↓                            │  │
│  │  ┌─────────────────────────────────┐  │  │
│  │  │  AgentMetadata                  │  │  │
│  │  │  ├── agent_class                │  │  │
│  │  │  ├── config                     │  │  │
│  │  │  ├── tools                      │  │  │
│  │  │  ├── description                │  │  │
│  │  │  └── _instance (cached)         │  │  │
│  │  └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Summary

**Current State:**
- ✅ Phase 1: Programmatic registration
- ✅ Phase 2: YAML + Auto-discovery
- ✅ Phase 3: Worker integration
- ✅ Production-ready
- ✅ 52 tests, 96% coverage

**Key Features:**
- Three registration methods (YAML, auto-discovery, programmatic)
- Singleton pattern for performance
- Thread-safe operations
- Structured logging
- No database dependency
- Scales horizontally

**Best For:**
- Platform development (not SaaS customization)
- Code-driven agent definitions
- Version-controlled configurations
- Developer-centric workflows
-e


# ./docs/API_REFERENCE.md

# API Reference

Complete API documentation for the multi-agent task orchestration system.

## Base URL

```
http://localhost:8000
```

For production, use HTTPS with mTLS certificate authentication.

## Authentication

### mTLS (Mutual TLS)

API requires client certificate authentication:

```bash
curl https://localhost:8443/tasks \
  --cacert certs/ca-cert.pem \
  --cert certs/client-cert.pem \
  --key certs/client-key.pem
```

**Development:** Use HTTP on port 8000 (no auth required)
**Production:** Use HTTPS on port 8443 with certificates

## Core Endpoints

### Health Check

Check API and database health.

```http
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "database": "connected",
  "websocket_connections": 3
}
```

---

### Create Task

Submit a new task for execution.

```http
POST /tasks
Content-Type: application/json

{
  "type": "workflow:research_assessment",
  "input": {
    "topic": "renewable energy",
    "user_email": "user@example.com"
  }
}
```

**Request Fields:**
- `type` (string, required): Task type - `workflow:name`, `agent:type`, or `tool:name`
- `input` (object, required): Input data for the task
  - `user_email` (string, optional): User's email (hashed for privacy)
  - `tenant_id` (string, optional): Tenant identifier
  - `_trace_context` (object, optional): Distributed tracing context

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "workflow:research_assessment",
  "status": "pending",
  "input": {
    "topic": "renewable energy"
  },
  "output": null,
  "error": null,
  "user_id_hash": "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
  "tenant_id": null,
  "model_used": null,
  "input_tokens": null,
  "output_tokens": null,
  "total_cost": null,
  "generation_id": null,
  "created_at": "2025-12-07T15:30:00Z",
  "updated_at": "2025-12-07T15:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request`: Invalid input data
- `422 Unprocessable Entity`: Validation error

---

### Get Task

Retrieve task status and results.

```http
GET /tasks/{task_id}
```

**Path Parameters:**
- `task_id` (UUID): Task identifier

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "workflow:research_assessment",
  "status": "done",
  "input": {
    "topic": "renewable energy"
  },
  "output": {
    "findings": "Renewable energy sources include...",
    "approved": true,
    "iterations": 1
  },
  "error": null,
  "model_used": "openai/gpt-4o-mini",
  "input_tokens": 1250,
  "output_tokens": 830,
  "total_cost": 0.002145,
  "created_at": "2025-12-07T15:30:00Z",
  "updated_at": "2025-12-07T15:32:15Z"
}
```

**Error Responses:**
- `404 Not Found`: Task does not exist

---

### List Tasks

Query tasks with filters.

```http
GET /tasks?status_filter=pending&limit=50&user_id_hash=abc123
```

**Query Parameters:**
- `status_filter` (string, optional): Filter by status - `pending`, `running`, `done`, `error`
- `limit` (integer, optional): Maximum results (default: 50, max: 100)
- `user_id_hash` (string, optional): Filter by user hash
- `tenant_id` (string, optional): Filter by tenant

**Response** (200 OK):
```json
{
  "tasks": [
    { "id": "...", "type": "...", "status": "pending", ... },
    { "id": "...", "type": "...", "status": "running", ... }
  ],
  "count": 2
}
```

---

### Update Task

Manually update task status (admin use).

```http
PATCH /tasks/{task_id}
Content-Type: application/json

{
  "status": "done",
  "output": {"result": "completed"}
}
```

**Request Fields:**
- `status` (string, optional): New status
- `output` (object, optional): Task output
- `error` (string, optional): Error message

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "done",
  "output": {"result": "completed"},
  ...
}
```

**Error Responses:**
- `404 Not Found`: Task does not exist
- `422 Unprocessable Entity`: Invalid status transition

---

## Registry Endpoints

### List Agents

Get all registered agents.

```http
GET /admin/agents
```

**Response** (200 OK):
```json
{
  "agents": [
    {
      "type": "research",
      "description": "Conducts research on topics",
      "tools": ["web_search"],
      "config": {"model": "gpt-4-turbo"}
    },
    {
      "type": "assessment",
      "description": "Assesses research quality",
      "tools": ["fact_checker"],
      "config": {"model": "gpt-4-turbo"}
    }
  ]
}
```

---

### List Tools

Get all registered tools.

```http
GET /admin/tools
```

**Response** (200 OK):
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web using Brave API",
      "config": {"api_key_env": "BRAVE_API_KEY"}
    }
  ]
}
```

---

### List Workflows

Get all registered workflows.

```http
GET /admin/workflows
```

**Response** (200 OK):
```json
{
  "workflows": [
    {
      "name": "research_assessment",
      "description": "Research with quality feedback loop",
      "coordination_type": "iterative_refinement",
      "max_iterations": 3,
      "steps": [
        {"agent_type": "research", "name": "conduct_research"},
        {"agent_type": "assessment", "name": "assess_quality"}
      ]
    }
  ]
}
```

---

### Execute Agent Directly

Bypass task queue and execute agent synchronously.

```http
POST /tasks/agent
Content-Type: application/json

{
  "agent_type": "research",
  "input": {
    "topic": "climate change"
  }
}
```

**Request Fields:**
- `agent_type` (string, required): Agent type to execute
- `input` (object, required): Input data for agent

**Response** (200 OK):
```json
{
  "output": {
    "findings": "Climate change refers to...",
    "sources": ["https://..."]
  },
  "usage": {
    "input_tokens": 450,
    "output_tokens": 320,
    "total_cost": 0.001234
  }
}
```

**Error Responses:**
- `404 Not Found`: Agent type not registered
- `500 Internal Server Error`: Agent execution failed

---

## WebSocket API

Real-time task updates via WebSocket.

### Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected');
  ws.send('ping');  // Keep-alive
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Task update:', data);
};
```

### Message Format

**Server → Client:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "done",
  "output": {...},
  "timestamp": "2025-12-07T15:32:15Z"
}
```

**Events:**
- `task_created`: New task submitted
- `task_updated`: Status or output changed
- `task_completed`: Task finished (done or error)

### Keep-Alive

Send ping every 30 seconds to keep connection alive:
```javascript
setInterval(() => ws.send('ping'), 30000);
```

---

## Task Types

### Workflow Tasks

Execute multi-agent workflows defined in YAML.

**Format:** `workflow:{workflow_name}`

**Example:**
```json
{
  "type": "workflow:research_assessment",
  "input": {
    "topic": "artificial intelligence"
  }
}
```

See [WORKFLOWS.md](WORKFLOWS.md) for workflow definitions.

---

### Agent Tasks

Execute single agents directly.

**Format:** `agent:{agent_type}`

**Example:**
```json
{
  "type": "agent:research",
  "input": {
    "topic": "quantum computing"
  }
}
```

---

### Tool Tasks

Execute tools directly.

**Format:** `tool:{tool_name}`

**Example:**
```json
{
  "type": "tool:web_search",
  "input": {
    "query": "best practices for REST APIs"
  }
}
```

---

## Task Status Values

Tasks follow this lifecycle:

| Status | Description |
|--------|-------------|
| `pending` | Waiting for worker to claim |
| `running` | Being processed by worker |
| `done` | Successfully completed |
| `error` | Failed with error message |

**State transitions:**
```
pending → running → done
pending → running → error
running → pending (on lease expiry)
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message here",
  "error_code": "INVALID_AGENT_TYPE",
  "status_code": 404
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_TASK_TYPE` | 400 | Unknown task type format |
| `VALIDATION_ERROR` | 422 | Input validation failed |
| `AGENT_NOT_FOUND` | 404 | Agent type not registered |
| `WORKFLOW_NOT_FOUND` | 404 | Workflow not found |
| `TASK_NOT_FOUND` | 404 | Task ID does not exist |
| `EXECUTION_ERROR` | 500 | Agent/workflow execution failed |

---

## Rate Limiting

**Current:** No rate limiting implemented

**Best practices:**
- Limit to 100 tasks/minute per client
- Use WebSocket for updates instead of polling
- Poll at maximum once per 2 seconds if using REST

---

## Distributed Tracing

Include trace context for unified observability:

```json
{
  "type": "workflow:research_assessment",
  "input": {
    "topic": "machine learning",
    "_trace_context": {
      "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
      "span_id": "00f067aa0ba902b7"
    }
  }
}
```

The system propagates this context through all subtasks and agent executions.

See [MONITORING.md](MONITORING.md) for trace visualization.

---

## Examples

### Python Client

```python
import requests
import time

# Create task
response = requests.post('http://localhost:8000/tasks', json={
    'type': 'workflow:research_assessment',
    'input': {'topic': 'blockchain technology'}
})
task = response.json()
task_id = task['id']

# Poll for completion
while True:
    response = requests.get(f'http://localhost:8000/tasks/{task_id}')
    task = response.json()

    if task['status'] in ['done', 'error']:
        print(f"Result: {task['output']}")
        break

    time.sleep(2)
```

### cURL Examples

```bash
# Create task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"type": "agent:research", "input": {"topic": "solar energy"}}'

# Get task
curl http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000

# List pending tasks
curl "http://localhost:8000/tasks?status_filter=pending&limit=10"

# List workflows
curl http://localhost:8000/admin/workflows
```

---

## See Also

- [Workflows Guide](WORKFLOWS.md) - Create declarative workflows
- [Architecture](ARCHITECTURE.md) - System design and data flow
- [Monitoring](MONITORING.md) - Observability and debugging
-e


# ./docs/ARCHITECTURE.md

# System Architecture

This document provides a detailed technical overview of the multi-agent task orchestration system architecture.

## Overview

The system is a **distributed, event-driven task processing platform** built around these core principles:

- **Async-first**: Non-blocking I/O throughout the stack
- **State machine driven**: Explicit state transitions for tasks and workers
- **Lease-based concurrency**: Multi-worker safe task claiming
- **Observable**: Distributed tracing and metrics at every layer
- **Declarative**: Workflows defined in YAML without code

## System Components

```mermaid
graph TB
    Client[Client / Open WebUI]
    API[FastAPI Application]
    DB[(PostgreSQL)]
    Worker[Task Worker]
    AR[Agent Registry]
    TR[Tool Registry]
    WR[Workflow Registry]
    Agents[Agents]
    Tools[Tools]
    LLM[LLM APIs]

    Client -->|mTLS/REST| API
    API -->|async SQLAlchemy| DB
    Worker -->|sync psycopg2| DB
    Worker -->|get agent| AR
    Worker -->|load workflow| WR
    AR -->|instantiate| Agents
    Agents -->|use tools| TR
    TR -->|execute| Tools
    Agents -->|call| LLM

    subgraph Observability
        OTel[OpenTelemetry Collector]
        Tempo[Grafana Tempo]
        Prom[Prometheus]

        API -.->|traces/metrics| OTel
        Worker -.->|traces/metrics| OTel
        OTel -->|store| Tempo
        OTel -->|store| Prom
    end
```

## Core Services

### 1. Task API (`task-api`)

**Responsibilities:**
- Accept task creation requests via REST API
- Store tasks in PostgreSQL
- Provide task status queries
- Broadcast real-time updates via WebSocket
- Serve registry endpoints (agents, tools, workflows)

**Technology:**
- FastAPI (async web framework)
- SQLAlchemy 2.0 with asyncpg (async ORM)
- Pydantic (request/response validation)
- WebSockets (real-time updates)

**Key files:**
- `app/main.py` - Application entry point
- `app/routers/tasks.py` - Task CRUD endpoints
- `app/database.py` - Async database connection
- `app/websocket.py` - WebSocket manager

### 2. Task Worker (`task-worker`)

**Responsibilities:**
- Poll database for pending tasks
- Claim tasks with time-bound leases
- Execute tasks (agents, workflows, tools)
- Update task status and results
- Recover from failures

**Technology:**
- Synchronous Python (psycopg2 for DB)
- State machine architecture
- OpenTelemetry instrumentation
- Signal-based graceful shutdown

**Key files:**
- `app/worker.py` - Entry point
- `app/worker_state.py` - Worker state machine
- `app/task_state.py` - Task execution state machine
- `app/worker_helpers.py` - Task processing logic
- `app/worker_lease.py` - Lease management

### 3. PostgreSQL Database

**Responsibilities:**
- Persistent storage for tasks, workflows, audit logs
- ACID guarantees for task state transitions
- Indexing for efficient queries
- pgvector extension for embeddings (future use)

**Schema:** See [Database Schema](#database-schema) below

### 4. Qdrant Vector Database

**Responsibilities:**
- Vector similarity search
- Embedding storage
- Semantic search capabilities

**Usage:** Currently optional, integrated for future RAG features

### 5. Open WebUI

**Responsibilities:**
- Chat interface for users
- Tool execution (@flow, @agent, @tool commands)
- Document upload and processing

**Integration:** See [OPENWEBUI.md](OPENWEBUI.md)

## Database Schema

### Core Tables

#### tasks
Primary table for task lifecycle management.

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL,                  -- 'workflow:name', 'agent:type', 'tool:name'
    status TEXT NOT NULL DEFAULT 'pending',  -- State: pending|running|done|error
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,

    -- User tracking (privacy-preserving)
    user_id_hash VARCHAR(64),            -- SHA-256 hashed email
    tenant_id VARCHAR(100),              -- Environment identifier

    -- Cost tracking
    model_used VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_cost DECIMAL(10, 6),

    -- Tracing
    generation_id TEXT,                  -- Trace ID for distributed tracing

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now(),

    -- Worker lease
    lease_expires_at TIMESTAMP WITH TIME ZONE,
    worker_id TEXT
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_lease ON tasks(lease_expires_at) WHERE status = 'running';
CREATE INDEX idx_tasks_user_hash ON tasks(user_id_hash);
CREATE INDEX idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX idx_tasks_user_tenant ON tasks(user_id_hash, tenant_id);
```

#### subtasks
Child tasks for multi-step workflows.

```sql
CREATE TABLE subtasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL,
    step_name TEXT,
    iteration INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'pending',
    input JSONB NOT NULL,
    output JSONB,
    error TEXT,

    -- Same tracking fields as tasks
    user_id_hash VARCHAR(64),
    tenant_id VARCHAR(100),
    model_used VARCHAR(100),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_cost DECIMAL(10, 6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_subtasks_parent ON subtasks(parent_task_id);
CREATE INDEX idx_subtasks_status ON subtasks(status);
```

#### workflow_state
Tracks multi-step workflow execution state.

```sql
CREATE TABLE workflow_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    workflow_name TEXT NOT NULL,
    current_step INTEGER DEFAULT 0,
    current_iteration INTEGER DEFAULT 1,
    max_iterations INTEGER DEFAULT 3,
    converged BOOLEAN DEFAULT FALSE,
    accumulated_output JSONB,

    user_id_hash VARCHAR(64),
    tenant_id VARCHAR(100),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_workflow_parent ON workflow_state(parent_task_id);
```

#### audit_logs
Immutable audit trail for compliance and debugging.

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,     -- task_created, task_updated, etc.
    resource_id UUID NOT NULL,           -- Task or subtask ID
    user_id_hash VARCHAR(64),
    tenant_id VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT now(),
    metadata JSONB                       -- Event-specific details
);

CREATE INDEX idx_audit_user ON audit_logs(user_id_hash);
CREATE INDEX idx_audit_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_resource ON audit_logs(resource_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
```

## Execution Model

### Task Lifecycle (State Machine)

Tasks follow a strict state machine with these states:

```mermaid
stateDiagram-v2
    [*] --> PENDING: Task created
    PENDING --> RUNNING: Worker claims task
    RUNNING --> DONE: Execution succeeds
    RUNNING --> ERROR: Execution fails
    RUNNING --> PENDING: Lease expires
    DONE --> [*]
    ERROR --> [*]
```

**States:**
- `PENDING` - Waiting for worker to claim
- `RUNNING` - Being processed by worker (has active lease)
- `DONE` - Successfully completed
- `ERROR` - Failed with error message

**Lease mechanism:** When a worker claims a task, it sets `lease_expires_at` to `now() + 5 minutes`. If the worker crashes, another worker can reclaim the task after lease expiry.

See [Worker State Machine](statemachines/WORKER_STATEMACHINE.md) for detailed state diagrams.

### Worker Execution Loop

```
1. IDLE → Connect to database
2. CONNECTED → Recover expired leases
3. CONNECTED → Claim next pending task
4. PROCESSING → Execute task (agent/workflow/tool)
5. PROCESSING → Update task status (done/error)
6. PROCESSING → Release lease
7. CONNECTED → (repeat from step 3)
```

**Graceful shutdown:** Workers listen for SIGTERM/SIGINT and complete current task before exiting.

### Workflow Execution

For `workflow:*` task types, the worker delegates to the orchestrator:

```
1. Worker claims workflow task
2. Initialize workflow state in database
3. For each step in workflow definition:
   a. Create subtask for agent
   b. Execute subtask
   c. Update workflow state
   d. Check convergence (for iterative workflows)
4. Aggregate results
5. Mark parent task as done
```

**Iterative workflows:** Loop through steps multiple times until convergence check passes or max iterations reached.

## Data Flow

### Task Submission Flow

```
Client
  ↓ POST /tasks {"type": "workflow:research_assessment", "input": {...}}
API
  ↓ INSERT INTO tasks (type, status='pending', input)
Database
  ↓ Task ID returned
API
  ↓ WebSocket broadcast: task_created
Client
  ↓ Receives task ID, polls for status
```

### Task Execution Flow

```
Worker
  ↓ SELECT next pending task FOR UPDATE SKIP LOCKED
Database
  ↓ Task locked and returned
Worker
  ↓ UPDATE tasks SET status='running', lease_expires_at=now()+5min
  ↓ Execute agent/workflow/tool
  ↓ UPDATE tasks SET status='done', output=result
Database
  ↓ Task completed
API (via polling)
  ↓ WebSocket broadcast: task_updated
Client
  ↓ Receives result
```

### Distributed Tracing Flow

```
Open WebUI Tool
  ↓ Generates trace_id, injects into task.input._trace_context
API
  ↓ Stores task with trace context
Worker
  ↓ Extracts trace_id from task.input._trace_context
  ↓ Creates root span with trace_id
Orchestrator
  ↓ Creates child spans (one per subtask)
Agent
  ↓ Creates nested span for LLM call
  ↓ Exports to OpenTelemetry Collector
OTel Collector
  ↓ Forwards to Grafana Tempo
Grafana
  ↓ User views unified trace
```

## Concurrency & Scaling

### Multi-Worker Concurrency

**Lease-based task claiming** ensures tasks are processed exactly once:

```sql
-- Worker 1 and Worker 2 both try to claim
UPDATE tasks
SET status = 'running',
    lease_expires_at = now() + interval '5 minutes',
    worker_id = 'worker-1'
WHERE id = (
    SELECT id FROM tasks
    WHERE status = 'pending'
    ORDER BY created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED  -- Critical: Skip locked rows
)
RETURNING *;
```

**`FOR UPDATE SKIP LOCKED`** ensures that only one worker succeeds in claiming the task.

### Lease Recovery

If a worker crashes mid-task, the lease expires and the task becomes reclaimable:

```sql
-- Recover tasks with expired leases
UPDATE tasks
SET status = 'pending',
    lease_expires_at = NULL,
    worker_id = NULL
WHERE status = 'running'
  AND lease_expires_at < now();
```

### Horizontal Scaling

Workers are **stateless** and scale horizontally:

```bash
docker-compose up -d --scale task-worker=5
```

**Characteristics:**
- ✅ Each worker has independent in-memory registries (agents, tools, workflows)
- ✅ Database acts as coordination point
- ✅ No inter-worker communication needed
- ⚠️ Brief version skew during rolling deploys (~30-60s)

See [WORKER_SCALING.md](WORKER_SCALING.md) for details.

## User Tracking & Multi-Tenancy

### Privacy-Preserving User Tracking

User emails are **SHA-256 hashed** before storage:

```python
import hashlib

def hash_email(email: str) -> str:
    return hashlib.sha256(email.encode()).hexdigest()
```

**Flow:**
1. Client sends plain email in request body
2. API hashes immediately: `user_id_hash = hash_email(email)`
3. Only hash stored in database
4. Management UI allows lookup by email (hashes on search)

### Multi-Tenancy

The `tenant_id` field enables environment-based isolation:

- **Usage:** Set in Open WebUI tool configuration
- **Purpose:** Separate production/staging data, or multi-customer deployments
- **Queries:** All queries include `WHERE tenant_id = ?` filter

```sql
-- Get tasks for specific tenant
SELECT * FROM tasks
WHERE tenant_id = 'production'
  AND user_id_hash = '...';
```

## Registry Architecture

### Agent Registry

Agents are registered using one of three methods:

1. **YAML**: `config/agents.yaml` loaded at startup
2. **Auto-discovery**: Files in `app/agents/` automatically detected
3. **Programmatic**: `registry.register(name, class, config)`

**Singleton pattern:** Agents cached in memory for performance.

See [AGENT_REGISTRY.md](AGENT_REGISTRY.md) for details.

### Tool Registry

Tools registered similarly to agents:

```python
from app.tools.registry_init import tool_registry

tool = tool_registry.get("web_search")
result = tool.execute(query="...")
```

See [TOOL_REGISTRY.md](TOOL_REGISTRY.md) for details.

### Workflow Registry

Workflows auto-loaded from `app/workflows/*.yaml` at startup:

```python
from app.workflow_init import workflow_registry

definition = workflow_registry.get("research_assessment")
```

See [WORKFLOWS.md](WORKFLOWS.md) for details.

## Security

### mTLS Authentication

API requires client certificates for authentication:

```yaml
# docker-compose.yml
environment:
  - SSL_CA_CERT=/app/certs/ca-cert.pem
  - SSL_SERVER_CERT=/app/certs/server-cert.pem
  - SSL_SERVER_KEY=/app/certs/server-key.pem
```

**Certificate chain:**
1. CA certificate (self-signed for testing)
2. Server certificate (signed by CA)
3. Client certificate (signed by CA)

**⚠️ Production:** Use certificates from a trusted CA, not self-signed.

### Database Security

- **Network isolation:** PostgreSQL only accessible within Docker network
- **Strong passwords:** Configured in `.env`
- **Connection pooling:** Limits concurrent connections

### Secret Management

All secrets in `.env` file:
- Never committed to Git (`.gitignore` rule)
- Inject via Docker environment variables
- Rotate regularly in production

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **API** | FastAPI | Async web framework |
| **ORM** | SQLAlchemy 2.0 + asyncpg | Async database access |
| **Database** | PostgreSQL 18 | ACID-compliant storage |
| **Vector DB** | Qdrant | Embeddings and similarity search |
| **Tracing** | OpenTelemetry + Tempo | Distributed tracing |
| **Metrics** | Prometheus | Time-series metrics |
| **UI** | Streamlit | Management dashboard |
| **Chat UI** | Open WebUI | User interaction |
| **Config** | Pydantic Settings | Environment-based config |
| **Validation** | Pydantic | Request/response schemas |

## Performance Characteristics

| Operation | Latency | Notes |
|-----------|---------|-------|
| Task creation | < 10ms | INSERT + WebSocket broadcast |
| Task claim | < 20ms | SELECT FOR UPDATE SKIP LOCKED |
| Registry lookup | < 0.1ms | In-memory singleton cache |
| Agent execution | 1-30s | Depends on LLM API latency |
| Workflow (3 iterations) | 10-90s | Multiple agent calls |

## See Also

- [Worker State Machine](statemachines/WORKER_STATEMACHINE.md) - Detailed state diagrams
- [Worker Scaling](WORKER_SCALING.md) - Horizontal scaling guide
- [Development Guide](DEVELOPMENT.md) - Code quality and practices
- [API Reference](API_REFERENCE.md) - Complete API documentation
-e


# ./docs/DEVELOPMENT.md

# Development Guide

This guide covers code quality practices, development workflows, and review standards.

## Project Structure

```
agents_playground/
├── app/                        # Application code
│   ├── agents/                 # Agent implementations
│   │   ├── base.py            # Abstract Agent base class
│   │   ├── registry.py        # Agent registry
│   │   ├── registry_init.py   # Global registry singleton
│   │   ├── research_agent.py  # Research agent
│   │   └── assessment_agent.py # Assessment agent
│   ├── tools/                  # Tool implementations
│   │   ├── base.py            # Abstract Tool base class
│   │   ├── registry.py        # Tool registry
│   │   └── registry_init.py   # Global tool registry singleton
│   ├── workflows/              # YAML workflow definitions
│   ├── orchestrator/           # Workflow execution engine
│   │   ├── coordination_strategies.py  # Sequential, iterative, etc.
│   │   └── declarative_orchestrator.py
│   ├── routers/                # FastAPI route handlers
│   │   └── tasks.py           # Task CRUD endpoints
│   ├── middleware/             # FastAPI middleware
│   │   └── mtls.py            # mTLS authentication
│   ├── main.py                 # FastAPI application entry point
│   ├── worker.py               # Worker process entry point
│   ├── worker_state.py         # Worker state machine
│   ├── worker_helpers.py       # Task processing logic
│   ├── worker_lease.py         # Lease management
│   ├── task_state.py           # Task execution state machine
│   ├── tasks.py                # Task execution logic
│   ├── database.py             # Async database connection
│   ├── db_sync.py              # Sync database for worker
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── config.py               # Pydantic settings
│   ├── websocket.py            # WebSocket manager
│   ├── tracing.py              # OpenTelemetry setup
│   ├── metrics.py              # Prometheus metrics
│   └── audit.py                # Audit logging
├── config/                     # Configuration files
│   ├── agents.yaml             # Agent definitions (optional)
│   └── tools.yaml              # Tool definitions (optional)
├── docs/                       # Documentation
│   ├── QUICKSTART.md           # Quick start guide
│   ├── ARCHITECTURE.md         # System architecture
│   ├── API_REFERENCE.md        # API documentation
│   ├── MONITORING.md           # Observability guide
│   ├── TROUBLESHOOTING.md      # Common issues
│   ├── WORKFLOWS.md            # Workflow guide
│   ├── AGENT_REGISTRY.md       # Agent registry guide
│   ├── TOOL_REGISTRY.md        # Tool registry guide
│   ├── OPENWEBUI.md            # Open WebUI integration
│   ├── WORKER_SCALING.md       # Scaling guide
│   └── DEVELOPMENT.md          # This file
├── integrations/               # External integrations
│   └── openwebui/              # Open WebUI tools
│       ├── openwebui_tool.py   # @flow command
│       ├── openwebui_agent.py  # @agent command
│       ├── openwebui_tool_tool.py  # @tool command
│       └── openwebui_discover.py   # @discover command
├── monitoring/                 # Observability stack configs
│   ├── grafana/                # Grafana dashboards
│   ├── prometheus/             # Prometheus config
│   └── otel-collector-config.yaml
├── postgres-init/              # Database initialization scripts
│   └── init.sql                # Schema and initial data
├── tests/                      # Test suite
│   ├── test_worker_state.py    # Worker state machine tests
│   ├── test_task_state.py      # Task state machine tests
│   ├── test_agent_registry.py  # Registry tests
│   └── conftest.py             # Pytest fixtures
├── utils/                      # Utility scripts
│   ├── generate_certs.sh       # SSL certificate generation
│   ├── test_api.py             # API testing script
│   └── test_websocket.py       # WebSocket testing script
├── docker-compose.yml          # Service orchestration
├── Dockerfile                  # Task API/Worker container
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Python project config (Ruff, Mypy, etc.)
├── Makefile                    # Development commands
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # Project overview
```

## Quick Start

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run all quality checks
make validate
```

## Daily Commands

```bash
# Before committing
make validate          # Run all checks

# Specific checks
make lint             # Check linting
make lint-fix         # Auto-fix linting issues
make format           # Format code
make type-check       # Check types
make security         # Security scan
make test-cov         # Run tests with coverage

# See all commands
make help
```

## Tools Overview

### Ruff - Linting & Formatting
Fast Python linter and formatter (10-100x faster than traditional tools).

```bash
ruff check .          # Check for issues
ruff check --fix .    # Auto-fix issues
ruff format .         # Format code
```

### Mypy - Type Checking
Static type analysis to catch type errors.

```bash
mypy app tests
```

### Bandit - Security Scanning
Finds common security issues.

```bash
bandit -c pyproject.toml -r app
```

### Pre-commit Hooks
Automatically runs checks before each commit.

```bash
pre-commit install          # One-time setup
pre-commit run --all-files  # Manual run
```

## Workflow

### During Development

1. Write code
2. Format on save (configure IDE)
3. Run `make validate` before committing
4. Commit (pre-commit hooks run automatically)
5. Fix issues if hooks fail

### IDE Integration

#### VS Code
Add to `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

Install extensions:
- Ruff (charliermarsh.ruff)
- Mypy Type Checker (ms-python.mypy-type-checker)

## Code Review Checklist

Use this checklist for PRs and code reviews.

### Before Committing
- [ ] Run `make validate` and fix all issues
- [ ] Add/update tests for new functionality
- [ ] Check test coverage hasn't decreased
- [ ] Run the application locally

### Code Quality
- [ ] Follows project style (Ruff passes)
- [ ] No unnecessary complexity
- [ ] Functions are reasonably sized (<50 lines)
- [ ] No code duplication
- [ ] Meaningful variable/function names

### Type Safety
- [ ] New functions have type hints
- [ ] Type hints are accurate
- [ ] No `# type: ignore` without good reason

### Testing
- [ ] Tests added for new functionality
- [ ] Tests cover edge cases
- [ ] All tests pass
- [ ] Coverage meets threshold (50%+)

### Security
- [ ] No hardcoded secrets
- [ ] Input validation is present
- [ ] Bandit security scan passes

### Documentation
- [ ] Docstrings for public functions/classes
- [ ] Complex logic has comments
- [ ] README updated if needed

## Configuration

All tool configurations are in `pyproject.toml`:

- **[tool.ruff]** - Linting and formatting rules
- **[tool.mypy]** - Type checking settings
- **[tool.pytest.ini_options]** - Test configuration
- **[tool.bandit]** - Security scanning rules

## Continuous Improvement

### Best Practices

1. ✅ Run `make validate` before every commit
2. ✅ Keep pre-commit hooks enabled
3. ✅ Format code automatically on save
4. ✅ Add type hints to new functions
5. ⚠️ Don't use `--no-verify` to skip git hooks

### Gradual Improvements

As the codebase matures:
- Add type hints to existing code
- Increase test coverage target
- Enable stricter linting rules
- Add docstrings to public APIs

## Troubleshooting

### "Command not found: ruff"
```bash
pip install -r requirements-dev.txt
```

### Pre-commit hooks blocking commit?
```bash
make lint-fix
make format
git commit -m "message"  # Try again
```

### Type checking errors
```bash
# Add type: ignore for third-party libraries
import somelib  # type: ignore
```

## Resources

- **Ruff docs:** https://docs.astral.sh/ruff/
- **Mypy docs:** https://mypy.readthedocs.io/
- **Python typing:** https://docs.python.org/3/library/typing.html
- **Pre-commit:** https://pre-commit.com/
-e


# ./docs/MONITORING.md

# Monitoring & Observability

Comprehensive guide to monitoring, tracing, and debugging the multi-agent orchestration system.

## Overview

The system provides three layers of observability:

1. **Management UI** - User-friendly dashboard for task monitoring and cost analytics
2. **Distributed Tracing** - End-to-end request tracing with Grafana Tempo
3. **Metrics** - Time-series metrics with Prometheus

## Management UI

**Access:** http://localhost:8501

The Streamlit-based management interface provides four main views:

### 📊 Dashboard

Real-time overview of system activity.

**Features:**
- Recent tasks (auto-refreshes every 5 seconds)
- Task status distribution pie chart
- Active tasks by type
- Error rate trends
- Click any task ID to see details

**Use cases:**
- Monitor system health at a glance
- Spot error patterns
- Track workload distribution

---

### 🔍 Task Search

Search and inspect individual tasks.

**Features:**
- Search by task ID
- View complete input/output
- See error messages and stack traces
- Cost breakdown (tokens, model used)
- **Direct link to Grafana trace** (with time range pre-set)
- Parent/child task relationships for workflows

**Use cases:**
- Debug specific task failures
- Analyze workflow execution flow
- Review agent responses
- Check cost for individual executions

**Example workflow:**
1. User reports: "@flow command failed"
2. Get task ID from Open WebUI
3. Search in Management UI
4. Click "View Trace in Grafana"
5. See exact failure point in distributed trace

---

### 👤 User Search

Find all activity for a specific user.

**Features:**
- Search by email address (privacy-preserving hash lookup)
- View all user's tasks across tenants
- Per-user cost analytics
- Audit log trail
- Aggregate statistics (total tasks, success rate, costs)

**Use cases:**
- User support ("Why did my task fail?")
- Cost analysis per user
- Audit compliance
- Usage pattern analysis

**Privacy:** Email is hashed with SHA-256 before lookup. Only the hash is stored in the database.

---

### 💰 Cost Analytics

Cost tracking and analysis.

**Features:**
- Per-user cost breakdown
- Per-tenant cost aggregation
- Model usage statistics
- Time-series cost trends
- Token usage details (input/output)
- Workflow cost aggregation (parent + all subtasks)

**Metrics tracked:**
- `input_tokens` - Tokens sent to LLM
- `output_tokens` - Tokens received from LLM
- `total_cost` - Calculated cost based on model pricing
- `model_used` - LLM model name

**Use cases:**
- Budget monitoring
- Cost allocation by tenant
- Identify expensive workflows
- Optimize model selection

---

## Distributed Tracing

**Access:** http://localhost:3002 (Grafana)

### What is Tracing?

Distributed tracing tracks requests across multiple services, showing:
- Complete execution timeline
- Nested operations (spans)
- Duration of each step
- LLM API calls
- Iteration breakdowns for multi-step workflows

### Trace Hierarchy

Example trace for `@flow research_assessment`:

```
openwebui_tool.at_flow (28.3s)
├─ task-api.create_task (15ms)
├─ task-worker.process_workflow (28.1s)
│  ├─ orchestrator.initialize_workflow (50ms)
│  ├─ orchestrator.process_subtask:research (7.6s, iteration=1)
│  │  ├─ agent.research.execute (7.5s)
│  │  │  └─ llm.openrouter.chat_completion (7.2s)
│  │  │     ├─ input_tokens: 1250
│  │  │     ├─ output_tokens: 830
│  │  │     └─ cost: $0.002145
│  │  └─ task-worker.update_subtask (45ms)
│  ├─ orchestrator.process_subtask:assessment (1.8s, iteration=1)
│  │  ├─ agent.assessment.execute (1.7s)
│  │  │  └─ llm.openrouter.chat_completion (1.6s)
│  │  │     ├─ input_tokens: 980
│  │  │     ├─ output_tokens: 120
│  │  │     └─ cost: $0.000850
│  │  └─ task-worker.update_subtask (30ms)
│  └─ task-worker.finalize_workflow (35ms)
└─ task-api.complete_task (10ms)
```

### Finding Traces

**Method 1: From Management UI**
1. Go to Task Search
2. Enter task ID
3. Click "View Trace in Grafana" button
4. Grafana opens with trace pre-loaded

**Method 2: Direct Search in Grafana**
1. Open http://localhost:3002
2. Go to **Explore** (compass icon)
3. Select **Tempo** data source
4. Search by:
   - **Trace ID** (from task's `generation_id` field)
   - **Service** (`task-worker`, `task-api`)
   - **Time range** (task created_at to completed_at)

### Trace Context Propagation

The system propagates trace context through all layers:

```
1. Open WebUI Tool
   ↓ generates trace_id
   ↓ injects into task.input._trace_context

2. Task API
   ↓ stores task with trace context
   ↓ returns task_id

3. Worker
   ↓ claims task
   ↓ extracts trace_id from input
   ↓ creates root span with trace_id

4. Orchestrator
   ↓ creates child span for each subtask

5. Agent
   ↓ creates nested span for LLM call
   ↓ exports to OpenTelemetry Collector

6. OTel Collector
   ↓ forwards to Grafana Tempo

7. User views unified trace in Grafana
```

**Key benefit:** One trace ID links the entire request flow from Open WebUI to final result.

---

## Metrics

**Access:** http://localhost:9090 (Prometheus)

### Available Metrics

#### Task Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `tasks_created_total` | Counter | Total tasks created by type |
| `tasks_completed_total` | Counter | Completed tasks by type and status |
| `tasks_pending` | Gauge | Queue depth (pending tasks) |
| `tasks_in_flight` | Gauge | Currently processing tasks |
| `task_duration_seconds` | Histogram | Task processing time |

#### Worker Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `worker_heartbeat_timestamp` | Gauge | Last heartbeat time |
| `worker_tasks_processed_total` | Counter | Tasks processed by worker |
| `tasks_acquired_total` | Counter | Tasks claimed with lease |
| `active_leases_total` | Gauge | Number of active task leases |

#### System Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `http_requests_total` | Counter | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | Request latency |
| `db_connections_active` | Gauge | Active database connections |
| `websocket_connections_active` | Gauge | Active WebSocket connections |

### Example Queries

**Queue depth over time:**
```promql
tasks_pending
```

**Task completion rate:**
```promql
rate(tasks_completed_total[5m])
```

**Average task duration by type:**
```promql
avg(task_duration_seconds) by (task_type)
```

**Worker throughput:**
```promql
rate(worker_tasks_processed_total[1m])
```

**Error rate:**
```promql
rate(tasks_completed_total{status="error"}[5m]) /
rate(tasks_completed_total[5m])
```

---

## Audit Logging

### What Gets Logged

All operations are tracked in the `audit_logs` table:

| Event Type | Triggered When |
|------------|----------------|
| `task_created` | POST /tasks |
| `task_updated` | Task status/output changes |
| `task_completed` | Task reaches done/error state |
| `workflow_initialized` | Multi-agent workflow starts |
| `subtask_completed` | Subtask finishes |

### Querying Audit Logs

**Via Database:**
```sql
-- User's activity log
SELECT event_type, timestamp, metadata
FROM audit_logs
WHERE user_id_hash = 'abc123...'
ORDER BY timestamp DESC
LIMIT 50;

-- Tenant audit trail (last 7 days)
SELECT event_type, resource_id, timestamp, metadata
FROM audit_logs
WHERE tenant_id = 'production'
  AND timestamp > NOW() - INTERVAL '7 days';
```

**Via Management UI:**
User Search view shows related audit logs automatically.

---

## Debugging Workflows

### Multi-Agent Workflow Visibility

For workflow tasks (e.g., `workflow:research_assessment`):

**In Management UI:**
1. Search for parent task ID
2. View "Subtasks" section
3. See all iterations and agent executions
4. Click trace link to see timeline

**In Grafana:**
- Parent span shows total workflow duration
- Child spans show each subtask/iteration
- LLM calls nested within agent spans
- Clear visual timeline of execution

**Example: Research-Assessment Loop**

Trace shows:
- Iteration 1: Research → Assessment (not approved)
- Iteration 2: Research (with feedback) → Assessment (approved)
- Total: 2 iterations, 4 agent calls, ~15 seconds

---

## Troubleshooting with Traces

### Scenario 1: Task Stuck in "Running"

**Symptoms:** Task status = "running" for > 5 minutes

**Debug steps:**
1. Check worker logs: `docker-compose logs task-worker`
2. Look for task_id in logs
3. Check if worker crashed mid-task
4. In trace, check for incomplete spans

**Resolution:** Lease will expire after 5 minutes, task becomes reclaimable

---

### Scenario 2: High Latency

**Symptoms:** Task takes 30+ seconds

**Debug steps:**
1. View trace in Grafana
2. Identify slow span (usually LLM API call)
3. Check span tags for:
   - `input_tokens` - Large context?
   - `output_tokens` - Long response?
   - `model_used` - Slow model?

**Resolution:** Optimize prompt, reduce context, or switch model

---

### Scenario 3: Iterative Workflow Not Converging

**Symptoms:** Workflow hits max_iterations without approval

**Debug steps:**
1. View subtasks in Management UI
2. Check each iteration's output
3. Look for assessment feedback
4. Review convergence criteria

**Resolution:** Adjust assessment criteria or increase max_iterations

---

## Accessing Observability Services

### Local Development

```bash
# View worker logs
docker-compose logs -f task-worker

# View API logs
docker-compose logs -f task-api

# Access Grafana
open http://localhost:3002

# Access Prometheus
open http://localhost:9090

# Access Management UI
open http://localhost:8501

# Query database directly
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui
```

### Useful Database Queries

```sql
-- Recent tasks with trace context
SELECT id, type, status,
       input->'_trace_context'->>'trace_id' as trace_id
FROM tasks
ORDER BY created_at DESC
LIMIT 10;

-- Tasks by status
SELECT status, COUNT(*)
FROM tasks
GROUP BY status;

-- Expensive tasks (by token count)
SELECT id, type, input_tokens + output_tokens as total_tokens, total_cost
FROM tasks
WHERE status = 'done'
ORDER BY total_cost DESC
LIMIT 10;

-- Workflow iterations
SELECT parent_task_id, iteration, agent_type, status, total_cost
FROM subtasks
WHERE parent_task_id = 'abc123...'
ORDER BY iteration, created_at;
```

---

## OpenTelemetry Collector

### Configuration

The OTel Collector aggregates traces and metrics:

```yaml
# monitoring/otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317

exporters:
  tempo:
    endpoint: tempo:4317
  prometheus:
    endpoint: prometheus:9090

service:
  pipelines:
    traces:
      receivers: [otlp]
      exporters: [tempo]
    metrics:
      receivers: [otlp]
      exporters: [prometheus]
```

### Checking Collector Status

```bash
# View collector logs
docker-compose logs otel-collector

# Check if receiving traces
docker-compose logs otel-collector | grep -i "trace"
```

---

## Best Practices

### For Development
- ✅ Keep Management UI open while testing
- ✅ Use trace links for debugging failures
- ✅ Check worker logs for detailed execution info
- ✅ Monitor queue depth to spot backlog

### For Production
- ✅ Set up alerts on error rate metrics
- ✅ Monitor queue depth (high = need more workers)
- ✅ Track cost metrics by tenant
- ✅ Retain audit logs for compliance (7-90 days)
- ✅ Export traces to long-term storage

### Cost Optimization
- 📊 Review top 10 expensive tasks weekly
- 📊 Identify prompt optimization opportunities
- 📊 Consider cheaper models for non-critical tasks
- 📊 Track cost per tenant for billing

---

## See Also

- [Architecture](ARCHITECTURE.md) - System design and data flow
- [API Reference](API_REFERENCE.md) - API endpoints for programmatic access
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
-e


# ./docs/OPENWEBUI_TOOLS.md

# Open WebUI Tools Guide

## Available Tools

### @discover - Registry Explorer
Discover available agents, tools, and workflows.

**Usage:**
- `@discover` - Show all resources
- `@discover agents` - Show only agents
- `@discover tools` - Show only tools
- `@discover workflows` - Show only workflows

### @queue - Smart Task Queue
Submit tasks with automatic workflow selection.

**Usage:**
- `@queue research AI safety` - Auto-selects workflow
- `@queue summarize document` - Legacy task type

### @agent - Direct Agent Execution
Execute a specific agent directly.

**Usage:**
- `@agent research "your query"`
- `@agent assessment "your evaluation"`

### @workflow - Direct Workflow Execution
Execute a specific workflow by name.

**Usage:**
- `@workflow research_assessment "your topic"`
- `@workflow simple_sequential "your task"`

## Examples

### Research Workflow
```
User: @discover workflows
User: @workflow research_assessment "quantum computing trends"
  → Executes multi-agent research workflow
```

### Direct Agent Usage
```
User: @agent research "AI safety governance"
  → Executes research agent only
```
-e


# ./docs/OPENWEBUI.md

# Open WebUI Integration Guide

Complete guide for integrating the Task Management API with Open WebUI using mTLS authentication.

## Prerequisites

- Open WebUI instance running (via docker-compose)
- Task API service running with mTLS
- SSL certificates generated (CA, client cert, client key)

## Quick Setup

### 1. Environment Variables

The docker-compose configuration already includes the necessary environment variables for Open WebUI:

```yaml
services:
  open-webui:
    environment:
      - TASK_API_URL=https://host.docker.internal:8443
      - CA_CERT_PATH=/app/backend/data/certs/ca-cert.pem
      - CLIENT_CERT_PATH=/app/backend/data/certs/client-cert.pem
      - CLIENT_KEY_PATH=/app/backend/data/certs/client-key.pem
    volumes:
      - ./certs:/app/backend/data/certs:ro
```

**Environment Variables Explained:**
- `TASK_API_URL`: API endpoint (`host.docker.internal:8443` for services on host)
- `CA_CERT_PATH`: Path to CA certificate (inside container)
- `CLIENT_CERT_PATH`: Path to client certificate (inside container)
- `CLIENT_KEY_PATH`: Path to client private key (inside container)

### 2. Certificate Setup

Certificates are automatically mounted from the host `certs/` directory:
```bash
./utils/generate_certs.sh  # Generate if not already done
docker-compose up -d        # Mounts ./certs to container
```

### 3. Install the Task Queue Tool

1. Access Open WebUI at `http://localhost:3000`
2. Go to **Settings** → **Tools**
3. Click **"+ Add Tool"**
4. Copy contents of `openwebui_task_tool.py`
5. Paste into tool editor
6. Click **Save**

### 4. Configure Tool Valves (Optional)

Override environment variables via the tool's UI:

- **task_api_url**: API endpoint (default: from env var)
- **ca_cert_path**: CA certificate path
- **client_cert_path**: Client certificate path
- **client_key_path**: Client key path
- **auto_wait_for_completion**: Auto-wait for tasks (default: `true`)
- **poll_interval_seconds**: Polling frequency (default: `2`)
- **max_wait_seconds**: Max wait time (default: `300`)

## Usage

### Create and Auto-Wait for Task

Upload a file and use:
```
@flow summarize this document
```

The tool will:
1. ✅ Create the task
2. ⏳ Poll every 2 seconds
3. 📝 Return results when complete

### Check Task Status

```
@flow status 094a2531-2349-41f8-9b69-ec53c71d69fc
```

Returns current status immediately.

### Wait for Completion

```
@flow wait 094a2531-2349-41f8-9b69-ec53c71d69fc
```

Polls until task is complete (up to 5 minutes by default).

## Configuration Options

### Disable Auto-Wait

If you prefer manual status checking:
1. Set `auto_wait_for_completion` to `false` in Valves
2. Tasks will queue but not auto-wait
3. Use `@flow wait <id>` when ready

### Adjust Polling

- **Fast polling** (more responsive, more load): `poll_interval_seconds: 1`
- **Slow polling** (less load, slower): `poll_interval_seconds: 5`

### Increase Timeout

For long-running tasks:
```
max_wait_seconds: 600  # 10 minutes
```

## Network Configuration

### Using docker-compose (Recommended)

Services in the same docker-compose stack:
```yaml
TASK_API_URL=http://task-api:8000  # Internal network, no mTLS needed
```

### Open WebUI on host, Task API in container

```yaml
TASK_API_URL=https://host.docker.internal:8443  # Requires mTLS
```

### Different machines

```yaml
TASK_API_URL=https://your-server-ip:8443  # Requires mTLS
```

## Testing

### Test Connection

```
@flow status test-connection
```

**Expected response** (good - means mTLS works):
```
Task test-connection not found
```

**Connection error** (check certificates):
```
ERROR creating task: SSL certificate verify failed
```

### Test Task Creation

Upload a simple text file and run:
```
@flow summarize this file
```

Should create task and wait for completion.

## Troubleshooting

### SSL Certificate Errors

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:
- Verify CA cert path is correct
- Ensure CA cert matches server certificate
- Check certificates are readable by container
- Regenerate certificates if needed: `./utils/generate_certs.sh`

### Connection Refused

**Error**: `Connection refused`

**Solutions**:
- Verify API URL is correct
- Check task-api service is running: `docker-compose ps`
- Verify network connectivity
- For host.docker.internal, ensure Docker Desktop networking works

### Client Certificate Error

**Error**: `SSL handshake failed`

**Solutions**:
- Verify client cert and key paths
- Check certificates match CA
- Ensure client cert is signed by same CA as server
- Check file permissions in container

### Tool Not Working

**Error**: Tool doesn't respond or errors

**Solutions**:
- Check container logs: `docker-compose logs open-webui`
- Verify environment variables: `docker-compose exec open-webui env | grep TASK_API`
- Restart Open WebUI: `docker-compose restart open-webui`
- Check certificates exist in container: `docker-compose exec open-webui ls -la /app/backend/data/certs/`

## How It Works

```mermaid
sequenceDiagram
    User->>Open WebUI: @flow summarize doc
    Open WebUI->>Tool: Process command
    Tool->>API: POST /tasks (with mTLS)
    API-->>Tool: Task created (pending)
    loop Every 2 seconds
        Tool->>API: GET /tasks/{id} (with mTLS)
        API-->>Tool: Task status
    end
    API-->>Tool: Task complete
    Tool->>Open WebUI: Formatted result
    Open WebUI->>User: Display summary
```

## Key Features

✅ **mTLS Authentication**: Secure client certificate authentication
✅ **Auto-Wait**: Automatically polls for completion
✅ **Smart Polling**: Configurable interval and timeout
✅ **Formatted Output**: Pretty formatting for summaries
✅ **Error Handling**: Clear error messages
✅ **Backward Compatible**: Works with existing @flow commands

## Security Notes

- Certificates must be readable by Open WebUI process
- Use file permissions to protect private keys: `chmod 600 certs/*.pem`
- Store certificates in secure, mounted volume
- Never commit certificates to version control (.gitignore handles this)
- Certificates are mounted read-only (`:ro`) for security

## Advanced: Manual Certificate Installation

If not using docker-compose volume mounts:

```bash
# Copy certificates to running container
docker cp certs/ca-cert.pem openwebui:/app/backend/data/certs/
docker cp certs/client-cert.pem openwebui:/app/backend/data/certs/
docker cp certs/client-key.pem openwebui:/app/backend/data/certs/

# Set proper permissions
docker exec openwebui chmod 644 /app/backend/data/certs/ca-cert.pem
docker exec openwebui chmod 644 /app/backend/data/certs/client-cert.pem
docker exec openwebui chmod 600 /app/backend/data/certs/client-key.pem
```
-e


# ./docs/QUICKSTART.md

# Quick Start Guide

Get your multi-agent task orchestration system running in under 10 minutes.

## Prerequisites

Before you begin, ensure you have:
- **Docker** (version 20.10+) and **Docker Compose** (version 2.0+)
- **Git**
- An **OpenRouter API key** ([get one here](https://openrouter.ai/))

### Verify Prerequisites

```bash
docker --version
# Docker version 24.0.0 or higher

docker-compose --version
# Docker Compose version v2.0.0 or higher
```

## Step 1: Clone and Setup

```bash
# Clone the repository
git clone <repository>
cd agents_playground

# Create environment file
cp .env.example .env
```

**Expected output:** `.env` file created

## Step 2: Configure API Keys

Edit `.env` and add your OpenRouter API key:

```bash
# Open in your editor
nano .env  # or vim, code, etc.
```

Set these required variables:
```env
OPENROUTER_API_KEY=your_key_here
OPENAI_API_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
```

**💡 Tip:** Keep other defaults as-is for your first run.

## Step 3: Generate SSL Certificates

```bash
./utils/generate_certs.sh
```

**Expected output:**
```
Generating CA certificate...
Generating server certificate...
Generating client certificate...
✅ Certificates generated successfully in ./certs/
```

## Step 4: Start the Stack

```bash
docker-compose up -d
```

**Expected output:**
```
Creating network "agents_playground_default"
Creating agents_playground-postgres-1 ... done
Creating agents_playground-qdrant-1   ... done
Creating agents_playground-task-api-1 ... done
Creating agents_playground-task-worker-1 ... done
Creating agents_playground-open-webui-1 ... done
```

Wait ~30 seconds for services to initialize.

## Step 5: Verify Installation

Check that services are healthy:

```bash
# Test the API
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","websocket_connections":0}
```

Access the web interfaces:
- **Open WebUI**: http://localhost:3000 (chat interface)
- **Management UI**: http://localhost:8501 (monitoring dashboard)
- **Grafana**: http://localhost:3002 (distributed tracing)

## Step 6: Run Your First Workflow

### Option A: Via Open WebUI (Recommended)

1. Open http://localhost:3000
2. Create an account (or sign in)
3. Click **Workspace** → **Functions** in the sidebar
4. Search for "Task Queue Tool" and install it
5. In the chat, type:
   ```
   @flow research_assessment analyze the benefits of renewable energy
   ```
6. Watch the research agent gather information, then the assessment agent evaluate it!

### Option B: Via API

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "workflow:research_assessment",
    "input": {"topic": "benefits of renewable energy"}
  }'
```

**Response:**
```json
{
  "id": "abc123...",
  "type": "workflow:research_assessment",
  "status": "pending",
  ...
}
```

Check task status:
```bash
curl http://localhost:8000/tasks/abc123...
```

## Step 7: Monitor Execution

### Management UI
1. Open http://localhost:8501
2. Go to **🔍 Task Search**
3. Enter the task ID from step 6
4. View complete execution details, costs, and trace link

### Watch Worker Logs
```bash
docker-compose logs -f task-worker
```

You'll see:
- Task claimed by worker
- Research agent executing
- Assessment agent evaluating
- Final results

## What Just Happened?

You executed an **iterative refinement workflow** that:
1. **Research agent** gathered information about renewable energy
2. **Assessment agent** evaluated the research quality
3. If not approved, the cycle repeats with feedback (up to 3 iterations)
4. Results returned when quality threshold met

**Data flow:** OpenWebUI → API → PostgreSQL → Worker → Agent Registry → Research Agent → Assessment Agent → Results

## Next Steps

### Learn More
- **[Workflows Guide](WORKFLOWS.md)** - Create your own multi-agent workflows
- **[Agent Registry](AGENT_REGISTRY.md)** - Build custom agents
- **[Tool Registry](TOOL_REGISTRY.md)** - Add new tools
- **[API Reference](API_REFERENCE.md)** - Integrate programmatically

### Create Your First Workflow

```bash
# Create a new workflow file
cat > app/workflows/my_workflow.yaml << 'EOF'
name: my_workflow
description: My custom workflow
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: gather_info
  - agent_type: assessment
    name: verify_info
EOF

# Restart to load the new workflow
docker-compose restart task-api task-worker

# Use it
# In Open WebUI: @flow my_workflow analyze climate change
```

### Explore the System
- **View all workflows:** `curl http://localhost:8000/admin/workflows`
- **View all agents:** `curl http://localhost:8000/admin/agents`
- **View all tools:** `curl http://localhost:8000/admin/tools`

## Troubleshooting

### Services won't start
```bash
docker-compose logs
docker-compose ps
```

### "Database connection error"
Wait for PostgreSQL to fully initialize (~30 seconds on first run):
```bash
docker-compose logs postgres
# Look for: "database system is ready to accept connections"
```

### Worker not processing tasks
```bash
# Check worker is running
docker-compose ps task-worker

# View worker logs
docker-compose logs task-worker

# Verify worker can connect to database
docker-compose logs task-worker | grep -i "connected"
```

### Port conflicts
If ports 8000, 3000, or 8501 are in use, modify `docker-compose.yml`:
```yaml
services:
  task-api:
    ports:
      - "8001:8000"  # Change host port
```

### More help
See [Troubleshooting Guide](TROUBLESHOOTING.md) for detailed solutions.

## Clean Up (Optional)

To stop and remove everything:
```bash
# Stop services
docker-compose down

# Remove volumes (deletes database data)
docker-compose down -v
```

---

**🎉 Congratulations!** You now have a working multi-agent orchestration system. Check out the [Workflows Guide](WORKFLOWS.md) to build your own agents and workflows.
-e


# ./docs/REGISTRY_API.md

# Registry API Documentation

## Endpoints

### GET /admin/agents
Returns all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "research",
      "description": "Research agent for gathering information",
      "capabilities": ["web_search", "summarization"]
    },
    ...
  ]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/agents \
  --cert client.pem \
  --key client.key
```

### GET /admin/tools
Returns all registered tools.

**Response:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Search the web for information",
      "parameters": { ... }
    },
    ...
  ]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/tools \
  --cert client.pem \
  --key client.key
```

### GET /admin/workflows
Returns all registered workflows.

**Response:**
```json
{
  "workflows": [
    {
      "name": "research_assessment",
      "description": "Research with iterative assessment",
      "steps": ["research", "assessment"]
    },
    ...
  ]
}
```

**Example:**
```bash
curl https://localhost:8000/admin/workflows \
  --cert client.pem \
  --key client.key
```

### POST /tasks/agent
Execute an agent directly.

**Request Body:**
```json
{
  "agent_name": "research",
  "input": "quantum computing trends"
}
```

**Response:**
```json
{
  "task_id": "12345",
  "status": "pending"
}
```

**Example:**
```bash
curl -X POST https://localhost:8000/tasks/agent \
  -H "Content-Type: application/json" \
  --cert client.pem \
  --key client.key \
  -d '{"agent_name": "research", "input": "quantum computing trends"}'
```
-e


# ./docs/statemachines/WORKER_STATEMACHINE.md

# State Machine Documentation: `app/worker.py`

This document captures the stateful behavior of the worker module (`app/worker.py`), which implements a long-running loop responsible for polling, claiming, and executing tasks from the database. Documenting this state machine is essential for understanding the worker's resilience, lease management, and error handling strategies.

## 1. States

The system transitions through the following logical states at runtime:

*   **Startup** (Worker-level)
    *   The initial state where the worker initializes logging, metrics, and tracing before entering the main loop.
*   **Connecting** (Worker-level)
    *   The worker attempts to establish or re-establish a connection to the PostgreSQL database.
*   **Recovery** (Worker-level)
    *   A periodic state where the worker checks for and resets tasks held by other workers whose leases have expired.
*   **Polling** (Worker-level)
    *   The worker queries the database for the next available pending task that matches its criteria.
*   **Backoff** (Worker-level)
    *   The state entered when no tasks are found, where the worker calculates an increased sleep interval to reduce database load.
*   **Idle** (Worker-level)
    *   The worker sleeps for the calculated duration before restarting the loop.
*   **Claiming** (Task-level context)
    *   The worker attempts to atomically lock a found task by setting its status to `running` and assigning a lease.
*   **Processing** (Task-level context)
    *   The worker executes the business logic for the claimed task, delegating to `execute_task` or specific handlers.
*   **ReportingSuccess** (Task-level context)
    *   The worker updates the task status to `done`, records usage metrics, and notifies the API of success.
*   **ReportingFailure** (Task-level context)
    *   The worker updates the task status to `error`, records the exception details, and notifies the API of failure.
*   **ErrorWait** (Worker-level)
    *   A safety state where the worker sleeps briefly after an unexpected exception (e.g., DB connection failure) before retrying.

## 2. Transitions

The worker moves between states based on the following triggers:

*   **Startup → Connecting**:
    *   Trigger: `run_worker()` function entry.
*   **Connecting → Recovery**:
    *   Trigger: Database connection established successfully (and recovery interval has elapsed).
*   **Connecting → ErrorWait**:
    *   Trigger: `psycopg2.Error` or other exception during connection attempt.
*   **Recovery → Polling**:
    *   Trigger: `recover_expired_leases()` completes (or is skipped due to timer).
*   **Polling → Claiming**:
    *   Trigger: `claim_next_task()` returns a valid task row.
*   **Polling → Backoff**:
    *   Trigger: `claim_next_task()` returns `None` (no tasks found).
*   **Backoff → Idle**:
    *   Trigger: Backoff interval calculation complete.
*   **Idle → Connecting**:
    *   Trigger: Sleep interval elapses (loop restarts).
*   **Claiming → Processing**:
    *   Trigger: Successful `UPDATE` operation locking the task.
*   **Claiming → Polling**:
    *   Trigger: Claim attempt fails (e.g., task grabbed by another worker), loop restarts.
*   **Processing → ReportingSuccess**:
    *   Trigger: Task execution completes without exception.
*   **Processing → ReportingFailure**:
    *   Trigger: Exception raised during task execution.
*   **ReportingSuccess → Polling**:
    *   Trigger: Database update and API notification complete (loop restarts).
*   **ReportingFailure → Polling**:
    *   Trigger: Database update and API notification complete (loop restarts).
*   **Any State → ErrorWait**:
    *   Trigger: Unhandled `Exception` caught in the main loop.
*   **ErrorWait → Connecting**:
    *   Trigger: 5-second safety sleep completes.

## 3. Transition Table

| From | To | Trigger | Notes |
| :--- | :--- | :--- | :--- |
| Startup | Connecting | `run_worker()` entry | Initial boot. |
| Connecting | Recovery | DB Connected | Checks `last_recovery_check`. |
| Connecting | ErrorWait | Connection Failed | `psycopg2.Error`. |
| Recovery | Polling | Check Complete | Periodic lease recovery. |
| Polling | Claiming | Task Found | `claim_next_task()` returns row. |
| Polling | Backoff | No Task Found | `claim_next_task()` returns None. |
| Backoff | Idle | Interval Set | Adaptive backoff calculation. |
| Idle | Connecting | Sleep Done | Loop restarts. |
| Claiming | Processing | Lease Acquired | `UPDATE ... RETURNING` success. |
| Processing | ReportingSuccess | Execution OK | Output generated. |
| Processing | ReportingFailure | Execution Error | Exception caught. |
| ReportingSuccess | Polling | Update Done | Metrics recorded, loop restarts. |
| ReportingFailure | Polling | Update Done | Error recorded, loop restarts. |
| *Any* | ErrorWait | Exception | Global error handler. |
| ErrorWait | Connecting | Retry Sleep Done | 5s delay before reconnect. |

## 4. Terminal and Retry States

*   **Terminal States (Task)**:
    *   `done`: The task has been successfully processed and will not be picked up again.
    *   `error`: The task failed. It is terminal unless manual intervention occurs or a specific retry policy (outside this loop's scope) resets it.
*   **Loop Exits**:
    *   The worker loop (`while True`) **never exits** under normal operation. It only stops if the process is killed.
*   **Retries**:
    *   **Connection Retry**: If the DB connection fails, the worker enters `ErrorWait` and then retries `Connecting`.
    *   **Task Retry**: Handled by the `Recovery` state. If a worker crashes while holding a lease, the `Recovery` state in another worker will eventually reset the task from `running` to `pending` (if `try_count < max_tries`).

## 5. Invariants

*   **Lease Uniqueness**: Only one worker may hold a lease (be in `Processing` state) for a specific task at any given time, enforced by database row locking.
*   **Lease Timeout**: Every task in the `running` state must have a valid `lease_timeout` timestamp in the future.
*   **Status Consistency**: A task cannot transition to `done` or `error` without the `updated_at` timestamp being refreshed.
*   **Audit Completeness**: Every transition of a task to `running`, `done`, or `error` must be accompanied by an immutable `audit_logs` entry.

## 6. Visual Diagram

```mermaid
stateDiagram-v2
    [*] --> Connecting

    state "Worker Loop" as Loop {
        Connecting --> Recovery: Connected
        Recovery --> Polling: Check Done

        Polling --> Claiming: Task Found
        Polling --> Backoff: No Tasks

        Backoff --> Idle: Calc Interval
        Idle --> Connecting: Sleep Done

        Claiming --> Processing: Lease Acquired
        Claiming --> Polling: Claim Failed

        Processing --> ReportingSuccess: Success
        Processing --> ReportingFailure: Error

        ReportingSuccess --> Polling: Loop
        ReportingFailure --> Polling: Loop
    }

    Connecting --> ErrorWait: DB Error
    Loop --> ErrorWait: Unhandled Exception
    ErrorWait --> Connecting: Retry (5s)
```
-e


# ./docs/TOOL_REGISTRY.md

# Tool Registry Guide

The Tool Registry provides a standardized way for agents to access and execute external tools. It manages tool registration, instantiation, configuration, and discovery.

## Quick Start

```python
from app.tools.registry_init import tool_registry

# Get a tool instance (singleton)
search_tool = tool_registry.get("web_search")

# Execute the tool
result = search_tool.execute(query="Python tutorials")

if result["success"]:
    print(result["result"])
else:
    print(f"Error: {result['error']}")
```

## Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `calculator` | Safe mathematical expression evaluator | `expression` (str) |
| `web_search` | Search the web using Brave Search API | `query` (str), `max_results` (int) |

## Creating a New Tool

To create a custom tool, inherit from the `Tool` base class and implement the required methods.

### 1. Create Tool Class

Create a new file in `app/tools/my_tool.py`:

```python
from typing import Any
from app.tools.base import Tool

class MyTool(Tool):
    def __init__(self):
        super().__init__(
            tool_name="my_tool",
            description="Description of what my tool does"
        )

    def get_schema(self) -> dict[str, Any]:
        """Return JSON Schema for parameters."""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "First parameter"},
                "param2": {"type": "integer", "default": 10}
            },
            "required": ["param1"]
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool."""
        # 1. Validate parameters
        self.validate_params(**kwargs)

        # 2. Extract parameters
        param1 = kwargs["param1"]
        param2 = kwargs.get("param2", 10)

        # 3. Perform logic
        try:
            # ... your tool logic here ...
            result_data = f"Processed {param1} with {param2}"

            # 4. Return standard result
            return {
                "success": True,
                "result": result_data,
                "error": None,
                "metadata": {"processed": True}
            }
        except Exception as e:
            # Handle errors gracefully
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {}
            }
```

### 2. Register the Tool

You can register your tool in `config/tools.yaml`:

```yaml
tools:
  - name: my_tool
    class: app.tools.my_tool.MyTool
    config:
      some_config: value
    description: "My custom tool"
```

Or programmatically:

```python
from app.tools.registry_init import tool_registry
from app.tools.my_tool import MyTool

tool_registry.register("my_tool", MyTool)
```

## Using Tools in Agents

Agents can access tools via the `_execute_tool` method.

```python
from app.agents.base import Agent

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            agent_type="my_agent",
            tools=["web_search", "calculator"]  # Declare tools used
        )

    def execute(self, input_data, user_id_hash=None):
        # Execute a tool
        search_result = self._execute_tool("web_search", query="latest news")

        if search_result["success"]:
            # Process result
            pass

        return {"output": ...}
```

## Configuration

Tools are configured in `config/tools.yaml`. The registry automatically loads this file on startup.

```yaml
tools:
  - name: web_search
    class: app.tools.web_search.WebSearchTool
    config:
      api_key_env: BRAVE_API_KEY
      default_max_results: 5
```

## Auto-Discovery

The registry supports auto-discovery of tools in the `app/tools` directory. Any class inheriting from `Tool` (except `Tool` itself) can be automatically registered if `tool_registry.discover_tools()` is called.

## Error Handling

Tools always return a dictionary with the following structure, never raising exceptions for expected failures:

```python
{
    "success": bool,      # True if successful
    "result": Any,        # The output data (None on error)
    "error": str | None,  # Error message if failed
    "metadata": dict      # Optional metadata
}
```

Always check `result["success"]` before accessing `result["result"]`.
-e


# ./docs/TROUBLESHOOTING.md

# Troubleshooting Guide

Common issues and solutions for the multi-agent orchestration system.

## Quick Diagnostic Commands

```bash
# Check all services status
docker-compose ps

# View all logs
docker-compose logs

# Check specific service health
docker-compose logs task-api | tail -50
docker-compose logs task-worker | tail -50
docker-compose logs postgres | tail -50

# Test API connectivity
curl http://localhost:8000/health

# Check database connectivity
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui -c "SELECT 1;"
```

---

## Services Won't Start

### Symptom
```bash
docker-compose up -d
# One or more services show "Exited" or "Restarting"
```

### Diagnosis

```bash
# Check which services are failing
docker-compose ps

# View logs for failed service
docker-compose logs <service-name>
```

### Common Causes

**1. Port conflicts**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Find process using the port
lsof -i :8000  # or :3000, :5432, etc.

# Kill the process or change port in docker-compose.yml
vi docker-compose.yml
# Change: "8001:8000" instead of "8000:8000"
```

**2. Missing environment variables**
```
Error: OPENROUTER_API_KEY not set
```

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Verify required variables
grep OPENROUTER_API_KEY .env

# If missing, copy from template
cp .env.example .env
# Edit and add your API key
```

**3. Docker out of resources**
```
Error: failed to allocate memory
```

**Solution:**
```bash
# Increase Docker memory (Docker Desktop → Settings → Resources)
# Or prune old containers/images
docker system prune -a
```

---

## Database Connection Errors

### Symptom
```
ERROR: could not connect to database
psycopg2.OperationalError: could not connect to server
```

### Diagnosis

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres | grep -i ready

# Expected output:
# "database system is ready to accept connections"
```

### Solutions

**1. PostgreSQL still initializing**

First startup takes ~30 seconds. Wait and retry.

```bash
# Watch initialization
docker-compose logs -f postgres

# When ready, restart dependent services
docker-compose restart task-api task-worker
```

**2. Wrong database credentials**

```bash
# Verify DATABASE_URL in .env
grep DATABASE_URL .env

# Should match docker-compose.yml postgres config
# Format: postgresql://user:password@host:port/dbname
```

**3. Database corrupted**

```bash
# Stop all services
docker-compose down

# Remove database volume (⚠️ deletes all data)
docker volume rm agents_playground_postgres_data

# Recreate
docker-compose up -d postgres

# Wait for initialization, then start other services
docker-compose up -d
```

---

## Worker Not Processing Tasks

### Symptom
Tasks stuck in "pending" status indefinitely.

### Diagnosis

```bash
# Check worker is running
docker-compose ps task-worker

# View recent worker activity
docker-compose logs task-worker --tail=100

# Check for tasks in database
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui \
  -c "SELECT id, type, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 5;"
```

### Solutions

**1. Worker crashed or not running**

```bash
# Check worker status
docker-compose ps task-worker

# If "Exited", view logs
docker-compose logs task-worker

# Restart worker
docker-compose restart task-worker
```

**2. Worker can't claim tasks (database lock)**

```bash
# Check for long-running queries
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui -c \
  "SELECT pid, age(clock_timestamp(), query_start), query FROM pg_stat_activity WHERE state != 'idle' ORDER BY query_start;"

# Kill stuck queries if needed
# SELECT pg_terminate_backend(pid);
```

**3. Worker stuck on previous task**

```bash
# Check worker logs for current task
docker-compose logs task-worker | grep "Processing task"

# If stuck > 5 minutes, restart worker
docker-compose restart task-worker

# Lease will expire and task will be reclaimed
```

**4. No API keys configured**

```bash
# Worker fails if LLM API key missing
docker-compose logs task-worker | grep -i "api key"

# Check .env has OPENROUTER_API_KEY
grep OPENROUTER_API_KEY .env

# Add key and restart
docker-compose restart task-worker
```

---

## Workflow Failures

### Symptom
Workflow task shows status="error" with error message.

### Diagnosis

**Via Management UI:**
1. Open http://localhost:8501 → Task Search
2. Enter task ID
3. View error message and subtasks
4. Click "View Trace in Grafana"

**Via Database:**
```sql
-- Get task details
SELECT id, type, status, error, output
FROM tasks
WHERE id = 'your-task-id';

-- Get subtask failures
SELECT id, agent_type, iteration, status, error
FROM subtasks
WHERE parent_task_id = 'your-task-id'
ORDER BY iteration, created_at;
```

### Common Errors

**1. "Agent not found"**
```
ERROR: Unknown agent type: 'custom_agent'
```

**Solution:**
```bash
# Check registered agents
curl http://localhost:8000/admin/agents

# If agent missing, verify file exists
ls app/agents/custom_agent.py

# Restart to reload agents
docker-compose restart task-api task-worker
```

**2. "LLM API error"**
```
ERROR: OpenAI API error: Insufficient credits
```

**Solution:**
- Check API key has credits
- Verify API key in .env is correct
- Try different model in config/agents.yaml

**3. "Max iterations exceeded"**
```
Workflow failed: Max iterations (3) reached without convergence
```

**Solution:**
- Review assessment criteria (too strict?)
- Increase max_iterations in workflow YAML
- Check assessment feedback in subtasks

**4. "Invalid workflow definition"**
```
ERROR: Workflow 'my_workflow' not found
```

**Solution:**
```bash
# Check workflow files
ls app/workflows/

# Verify workflow loaded
curl http://localhost:8000/admin/workflows

# Check for YAML syntax errors
python -c "import yaml; yaml.safe_load(open('app/workflows/my_workflow.yaml'))"

# Restart to reload workflows
docker-compose restart task-api task-worker
```

---

## SSL/Certificate Issues

### Symptom
```
SSL: CERTIFICATE_VERIFY_FAILED
```

### mTLS Not Working

**For development:**
```bash
# Use HTTP (no SSL)
curl http://localhost:8000/health

# Skip certificate verification (testing only)
curl -k https://localhost:8443/health
```

**For production:**
```bash
# Verify certificates exist
ls -la certs/

# Regenerate if missing
./utils/generate_certs.sh

# Test with certificates
curl --cacert certs/ca-cert.pem \
     --cert certs/client-cert.pem \
     --key certs/client-key.pem \
     https://localhost:8443/health
```

---

## WebSocket Connection Issues

### Symptom
WebSocket disconnects immediately or can't connect.

### Solutions

**1. CORS issues**

Check CORS settings in `app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**2. Keep-alive not sent**

```javascript
// Send ping every 30 seconds
const ws = new WebSocket('ws://localhost:8000/ws');
setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 30000);
```

---

## High Memory Usage

### Diagnosis

```bash
# Check Docker memory usage
docker stats

# Check PostgreSQL memory
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui -c \
  "SELECT pg_size_pretty(pg_database_size('openwebui'));"
```

### Solutions

**1. Large task outputs**

```sql
-- Find large tasks
SELECT id, type, pg_column_size(output) as output_size
FROM tasks
WHERE output IS NOT NULL
ORDER BY output_size DESC
LIMIT 10;

-- Clean up old completed tasks
DELETE FROM tasks
WHERE status IN ('done', 'error')
  AND created_at < NOW() - INTERVAL '7 days';
```

**2. Too many WebSocket connections**

```bash
# Check connection count
curl http://localhost:8000/health | jq .websocket_connections

# Restart API to clear stale connections
docker-compose restart task-api
```

---

## Slow Performance

### Task Processing Slow

**Diagnosis:**
1. Check Grafana trace for the task
2. Identify slow span (usually LLM API call)
3. Review input_tokens count

**Solutions:**
- Reduce prompt length
- Use faster/cheaper model
- Optimize workflow (fewer iterations)

### Database Slow

```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan;
```

**Solutions:**
- Add missing indexes
- Vacuum analyze: `VACUUM ANALYZE tasks;`
-Increase shared_buffers in PostgreSQL config

---

## Open WebUI Integration Issues

### @flow Command Not Working

**Diagnosis:**
```bash
# Check tool is installed in Open WebUI
# Go to: http://localhost:3000 → Workspace → Functions
# Search for "Task Queue Tool"
```

**Solutions:**
- Reinstall tool from `integrations/openwebui/`
- Check TASK_API_URL in tool config
- Verify certificates mounted correctly in docker-compose.yml

### Results Not Appearing

**Check WebSocket connection:**
```javascript
// In Open WebUI tool code
console.log('WebSocket connected:', ws.readyState);
```

**Check task status:**
```bash
# Get recent tasks
curl http://localhost:8000/tasks?limit=5 | jq .
```

---

## Reset Everything

If all else fails, complete reset:

```bash
# Stop all services
docker-compose down

# Remove volumes (⚠️ deletes all data)
docker-compose down -v

# Remove certificates
rm -rf certs/*

# Regenerate certificates
./utils/generate_certs.sh

# Fresh start
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

---

## Getting Help

**Check logs first:**
```bash
docker-compose logs --tail=100
```

**Gather diagnostic info:**
```bash
# Services status
docker-compose ps > diagnostics.txt

# Recent logs
docker-compose logs --tail=500 >> diagnostics.txt

# Environment check
cat .env | grep -v "API_KEY" >> diagnostics.txt

# Database state
docker exec -it agents_playground-postgres-1 psql -U openwebui -d openwebui \
  -c "\dt" >> diagnostics.txt
```

**Useful log searches:**
```bash
# Find errors
docker-compose logs | grep -i error

# Find specific task
docker-compose logs | grep "task-id-here"

# Find worker activity
docker-compose logs task-worker | grep "Processing task"
```

---

## See Also

- [Monitoring Guide](MONITORING.md) - Observability and debugging tools
- [Architecture](ARCHITECTURE.md) - System design documentation
- [Development Guide](DEVELOPMENT.md) - Local development setup
-e


# ./docs/WORKER_SCALING.md

# Task Management API - Worker Scaling Guide

## Horizontal Scaling with Lease-Based Acquisition

The system supports running multiple worker instances concurrently using a lease-based task acquisition mechanism. Workers safely claim tasks with time-limited leases and automatically recover tasks from failed instances.

### Quick Start

**Single Worker (Default)**:
```bash
docker-compose up -d
```

**Multiple Workers**:
```bash
# Scale to 3 worker instances
docker-compose up -d --scale task-worker=3

# Verify all workers are running
docker-compose ps task-worker
```

### How It Works

- **Worker Identity**: Each worker has a unique ID (hostname:pid)
- **Lease-Based Claims**: Tasks are claimed with 5-minute leases by default
- **Automatic Recovery**: Expired leases are recovered every 30 seconds
- **Adaptive Polling**: Workers back off from 0.2s to 10s when idle
- **Retry Logic**: Failed tasks retry up to 3 times (configurable)

### Configuration

Set via environment variables in `.env` or `docker-compose.yml`:

```bash
# Lease duration (for long-running tasks)
WORKER_LEASE_DURATION_SECONDS=600  # 10 minutes

# Recovery interval
WORKER_RECOVERY_INTERVAL_SECONDS=30  # Check every 30s

# Polling intervals
WORKER_POLL_MIN_INTERVAL_SECONDS=0.2
WORKER_POLL_MAX_INTERVAL_SECONDS=10.0

# Retry settings
WORKER_MAX_RETRIES=5
```

### Monitoring

**View Active Workers**:
```sql
SELECT locked_by, COUNT(*) as active_tasks
FROM tasks
WHERE status = 'running' AND lease_timeout > NOW()
GROUP BY locked_by;
```

**Check Task Retry Status**:
```sql
SELECT id, type, try_count, max_tries, status
FROM tasks
WHERE try_count > 0
ORDER BY try_count DESC;
```

**View Stale Leases** (should be auto-recovered):
```sql
SELECT id, type, locked_by, lease_timeout
FROM tasks
WHERE status = 'running' AND lease_timeout < NOW();
```

### Metrics

Access Prometheus metrics at `http://localhost:8000/metrics`:

- `tasks_acquired_total` - Tasks claimed by each worker
- `tasks_recovered_total` - Tasks recovered from failed workers
- `worker_poll_interval_seconds` - Current polling interval
- `active_leases_total` - Active leases per worker

See full implementation details in the walkthrough documentation.
-e


# ./docs/WORKFLOWS.md

# Declarative Workflow System

The task management system supports **declarative workflows** defined in YAML, allowing you to create multi-step agent orchestrations without writing Python code.

## Quick Start

### 1. Create a Workflow

Create a YAML file in `app/workflows/`:

```yaml
# app/workflows/my_workflow.yaml
name: my_workflow
description: Custom workflow for my use case
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: gather_info
  - agent_type: assessment
    name: verify_info
```

### 2. Use It

The workflow is **automatically loaded** at startup. Use it via Open WebUI or API:

```
@flow my_workflow analyze this document
```

Or via API:
```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "type": "workflow:my_workflow",
    "input": {"topic": "AI safety"}
  }'
```

## Workflow Schema

### Required Fields

```yaml
name: workflow_name          # Must match filename
description: Human-readable description
coordination_type: sequential | iterative_refinement
max_iterations: 3            # Only used for iterative_refinement
```

### Steps

Each step specifies an agent to execute:

```yaml
steps:
  - agent_type: research     # Maps to ResearchAgent
    name: gather_info        # Human-readable step name

  - agent_type: assessment   # Maps to AssessmentAgent
    name: verify_quality
```

## Coordination Types

### Sequential

Executes steps **one after another**. Simple pipelines.

```yaml
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: step1
  - agent_type: assessment
    name: step2
```

**Flow**: Research → Assessment → Done

**Use case**: Simple multi-step processing (research, then summarize, then format).

### Iterative Refinement

Executes steps in a **loop until approved** or max iterations reached.

```yaml
coordination_type: iterative_refinement
max_iterations: 3
convergence_check: assessment_approved

steps:
  - agent_type: research      # Creates initial output
    name: create_research
  - agent_type: assessment    # Evaluates quality
    name: quality_check
```

**Flow**: Research → Assessment → (if not approved) → Research (with feedback) → Assessment → ...

**Use case**: Quality control loops (generate, critique, improve).

## Available Agents

Agents are defined in `app/agents/`:

| Agent Type | Description | Input | Output |
|------------|-------------|-------|--------|
| `research` | Conducts research on a topic | `topic`, `previous_feedback` (optional) | `{"findings": "...", "sources": [...]}` |
| `assessment` | Evaluates research quality | `research_findings`, `original_topic` | `{"approved": bool, "feedback": "..."}` |

### Adding New Agents

1. **Create agent class** in `app/agents/my_agent.py`:
   ```python
   from app.agents.base import Agent

   class MyAgent(Agent):
       def __init__(self):
           super().__init__(agent_type="my_agent")

       def execute(self, input_data, user_id_hash=None):
           # Your logic here
           return {"output": result, "usage": {...}}
   ```

2. **Register in** `app/agents/__init__.py`:
   ```python
   from app.agents.my_agent import MyAgent

   AGENT_REGISTRY = {
       "research": ResearchAgent,
       "assessment": AssessmentAgent,
       "my_agent": MyAgent,  # Add this
   }
   ```

3. **Use in workflows**:
   ```yaml
   steps:
     - agent_type: my_agent
       name: custom_step
   ```

## Convergence Checks

For `iterative_refinement`, specify when to stop iterating:

```yaml
convergence_check: assessment_approved  # Default
```

Available checks:
- `assessment_approved`: Stop when `output.approved == true`
- `quality_threshold`: Stop when `output.quality_score >= 0.8`

## Data Flow

### Sequential

Each step receives the **previous step's output**:

```yaml
steps:
  - agent_type: research
    name: step1
    # Input: workflow input
    # Output: {"findings": "..."}

  - agent_type: assessment
    name: step2
    # Input: {"previous_output": {...}, "research_findings": {...}}
    # Output: {"approved": true}
```

### Iterative Refinement

Steps iterate with **feedback**:

**Iteration 1:**
- Research agent: Gets `topic`
- Assessment agent: Gets `research_findings`

**Iteration 2 (if not approved):**
- Research agent: Gets `topic` + `previous_feedback`
- Assessment agent: Gets new `research_findings`

## Examples

### Simple Sequential Pipeline

```yaml
# app/workflows/document_pipeline.yaml
name: document_pipeline
description: Process a document through multiple stages
coordination_type: sequential
max_iterations: 1

steps:
  - agent_type: research
    name: extract_key_points
  - agent_type: assessment
    name: validate_extraction
```

### Quality Control Loop

```yaml
# app/workflows/research_assessment.yaml
name: research_assessment
description: Research with quality feedback loop
coordination_type: iterative_refinement
max_iterations: 3
convergence_check: assessment_approved

steps:
  - agent_type: research
    name: conduct_research
  - agent_type: assessment
    name: assess_quality
```

## Architecture

```
┌─────────────────┐
│  YAML Workflow  │
└────────┬────────┘
         │
         ▼
┌─────────────────────┐
│ WorkflowRegistry    │ ← Auto-loads from app/workflows/
│ (Startup)           │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ DeclarativeOrch.    │ ← Generic orchestrator
│ (Runtime)           │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ CoordinationStrategy│ ← Sequential or IterativeRefinement
│                     │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│     Agents          │ ← ResearchAgent, AssessmentAgent, etc.
│                     │
└─────────────────────┘
```

## Monitoring

### View Workflow Execution

1. **Management UI** (http://localhost:8501)
   - Search for task by ID
   - See parent task + all subtasks
   - View iteration history

2. **Grafana Traces** (http://localhost:3002)
   - Full distributed trace
   - See timing for each step
   - Identify bottlenecks

### Database Queries

```sql
-- View workflow state
SELECT * FROM workflow_state
WHERE parent_task_id = 'task-uuid';

-- View all subtasks in a workflow
SELECT * FROM subtasks
WHERE parent_task_id = 'task-uuid'
ORDER BY iteration, created_at;
```

## Debugging

### Workflow Not Loading

Check logs at startup:
```bash
docker-compose logs task-api | grep -i workflow
docker-compose logs task-worker | grep -i workflow
```

Expected output:
```
INFO: Loaded declarative workflow: my_workflow
```

### Workflow Failing

1. Check YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('app/workflows/my_workflow.yaml'))"
   ```

2. View worker logs:
   ```bash
   docker-compose logs -f task-worker
   ```

3. Check database:
   ```sql
   SELECT * FROM tasks WHERE type LIKE 'workflow:%' ORDER BY created_at DESC LIMIT 5;
   ```

## Best Practices

1. **Keep steps focused**: Each step should do one thing well
2. **Name workflows clearly**: Use snake_case matching the filename
3. **Document your workflows**: Use descriptive `description` field
4. **Test iteratively**: Start with `max_iterations: 1` for debugging
5. **Monitor costs**: Iterative workflows can use multiple LLM calls

## Advanced Topics

### Custom Coordination Strategies

Create new strategies in `app/orchestrator/coordination_strategies.py`:

```python
class ParallelStrategy(CoordinationStrategy):
    def initialize(self, parent_task_id, input_data, conn, ...):
        # Create all subtasks at once
        pass

    def process_completion(self, parent_task_id, subtask_id, output, ...):
        # Wait for all to complete
        pass
```

Register in `create_strategy()`:
```python
if definition.coordination_type == "parallel":
    return ParallelStrategy(definition)
```

### Conditional Workflows

Not yet supported, but planned:
```yaml
# Future feature
steps:
  - agent_type: research
    name: gather
    condition: "input.type == 'detailed'"
```

## Migration from Coded Orchestrators

If you have an existing Python orchestrator:

1. **Identify the pattern**: Sequential or iterative?
2. **List the steps**: What agents are involved?
3. **Create YAML**: Map steps to agent types
4. **Test side-by-side**: Keep old orchestrator while validating new one
5. **Switch**: Update task type from `coded_name` to `workflow:declarative_name`

Example: `ResearchAssessmentOrchestrator` → `research_assessment.yaml`

## See Also

- [Adding Agents](../app/agents/README.md) *(if you create this)*
- [Worker Architecture](WORKER_SCALING.md)
- [Open WebUI Integration](OPENWEBUI.md)
-e


# ./guidelines/GENERIC_STATEMACHINE_DOCUMENTATION.md

State Machine Documentation Guidelines

These instructions are for producing documentation that captures the stateful behavior of a Python module — typically one implementing a long-running loop, control flow logic, or task execution pattern — in a consistent, structured Markdown format.

Scope of Application

This format applies when a module exhibits:

A persistent or reactive loop (e.g. worker, poller, daemon)

Distinct logical states (e.g. polling, sleeping, processing, error handling)

Transitions between those states based on internal logic or external events (e.g. DB response, exception)

Required Output Structure

The generated documentation must include the following top-level sections in this order:

1. Header

Format:

# State Machine Documentation: `path/to/codefile.py`


Briefly describe what the module does and why documenting its state machine is useful.

2. States

List each logical state the system enters at runtime. For each state:

Use a clear, noun-style name (e.g. Processing, Backoff, not process_data)

Provide 1–2 sentences describing what happens in that state

Include whether it’s a task-level state, worker-level state, or both

3. Transitions

Describe how the system moves between states. Include:

A bullet-point list for each transition: State A → State B, with the trigger

Group transitions by cause if helpful (e.g., “on DB success”, “on exception”)

Avoid duplicating transition info in prose and tables (choose one as primary)

4. Transition Table

Provide a tabular summary of transitions with this format:

From	To	Trigger	Notes
Startup	Connecting	run_worker() entry	Initial connection attempt
Connecting	Recovery	DB connected	Timer-based lease check

Use this to show full system flow at a glance. Keep it consistent with prose.

5. Terminal and Retry States

Clarify:

Which states represent end-of-task (e.g. done, error)

Whether the loop itself ever exits (usually it doesn't)

How retries are triggered (e.g. lease expiry, connection retry logic)

What resets or resumes look like

6. Invariants

List systemic truths that should always hold. Examples:

“Only one worker may hold a task lease at a time.”

“Tasks in running state must have a valid lease timeout.”

“Every completed task must have a done or error status and updated timestamp.”

These are useful for both developers and incident reviewers.

Output

The result must be:

A Markdown file containing all of the above sections

File name: CODEFILE_STATEMACHINE.md — where CODEFILE is the name of the code file in UPPERCASE and without .py

Saved to: docs/statemachines/

Optional Enhancements

If structure and clarity allow, include:

A visual ASCII or Mermaid diagram of the transitions

A glossary for domain-specific terms (e.g. lease, subtask, try_count)

A short “Design Considerations” section (only if the logic is nontrivial)S
-e


# ./guidelines/GENERIC_TEST_IMPROVEMENTS.md

# Generic Test Improvement Guidelines (Mutation Testing)

## Context
```
Module: {module_path}
Current coverage: {X}%
Surviving mutants: {N}
Goal: Kill semantically meaningful mutants, ignore syntactic noise
```

---

## Phase 1: Foundation (Happy Paths)

**Goal:** Every exported function has at least one realistic test.

For each public function:
- One happy-path test with realistic input data
- Assertions on:
  - Return value structure (not just `is not None`)
  - Side effects occurred (DB writes, API calls, state changes)
  - Commits/flushes happened if transactional

**Anti-patterns to avoid:**
- Empty dicts `{}` when code expects structure
- Asserting only that "something was called" without checking what

---

## Phase 2: State Transitions & Error Handling

**Goal:** Pin down what MUST happen in success vs failure.

For each function, create paired tests:

**Success test MUST assert:**
- Final state of primary entity (status, output fields)
- Final state of related entities (parent/child relationships)
- Correct collaborators were invoked

**Failure test MUST assert:**
- Controlled exception in dependency
- Primary entity ends in error state with message
- Related entities updated appropriately
- Error notification/logging occurred

---

## Phase 3: Edge Cases & Invariants

**Goal:** Protect critical business rules from regression.

Identify and test invariants:
- **Retry semantics:** `try_count < max_tries` respected
- **Lease/lock semantics:** expired leases allow reclaim, active leases block
- **Parent/child consistency:** both updated on failure, correct propagation
- **Resource tracking:** costs, tokens, usage written to correct fields

For each invariant:
- Test the boundary condition
- Test violation is handled correctly

---

## Phase 4: Quality Gates

**Coverage:** ≥ 85% line coverage for the module

**Mutation score:** 0 survivors in covered code (untested is acceptable if mocked)

**Explicitly document:**
- Lines intentionally uncovered (and why)
- Invariants now guaranteed by tests

## Phase 5: Post-processing

**Goal:** Run complete testing and linting

Run tests and linting:
- **Run all tests:** Run all test cases
- **Run all lints:** Run all linting in pre-commit hooks
- **Fix any errors:** Fix any failing tests or lintss



---

## Mutation Categories

**Kill these (semantic):**
- Conditional flips (`==` → `!=`)
- State transitions (`status = 'done'` → `status = 'error'`)
- Return value changes
- Error handling removal

**Ignore these (syntactic noise):**
- Log message string changes
- Metric label changes
- Decorator removal (tracing, timing)
- String formatting in non-user-facing code

---

## Output Format

After improvements, document:

```markdown
## Test Summary: {module_name}

**Coverage:** {before}% → {after}%
**Tests:** {count} tests covering {behaviors}
**Uncovered:** {lines} - {reason}

### Invariants Guaranteed:
1. {invariant_1}
2. {invariant_2}
```

---

## Refactorability Notes

**Choose test style based on module layer:**

| Layer | Style | Example |
|-------|-------|---------|
| Business logic | Assert on outputs | `assert result["cost"] == 12.50` |
| Orchestration | Assert at boundaries | `mock_notifier.assert_called_with(...)` |
| Data access | Assert on SQL (intentional coupling) | `assert "status = 'done'" in sql` |

**Default to behavioral tests** (assert on outputs/boundaries). Only assert on implementation details (SQL strings, internal calls) when:

1. The implementation IS the contract (lease logic, retry semantics)
2. The module is expected to be stable
3. You document it: *"These tests are intentionally coupled to SQL structure"*

**Quick check:** If you renamed a column, should tests break?
- Business logic: No
- Data access layer: Yes (that's the point)
-e


# ./guidelines/refactor_to_state_machine.md

# Workflow: Refactor to State Machine

## Purpose

Convert code with implicit state management (nested conditionals, mode flags, status strings) into an explicit state machine with handler dispatch pattern. If provided code file is already in a state machine format, then make sure the state machine is refactored to use the instruction in this workflow.
## Trigger

Use this workflow when:
- Function cyclomatic complexity > 10 with state-like behavior
- Code has comments indicating states ("now polling", "connecting phase")
- Multiple boolean flags controlling behavior
- `if status == "..."` or `if mode == "..."` patterns
- Nested try/catch with different recovery paths

## Prerequisites

- [ ] Existing code with implicit states identified
- [ ] Existing tests for current behavior (baseline)
- [ ] Understanding of current state transitions (may need documentation)

---

## Phase 1: Document Current States

### Actions

1. **Read existing code** and identify implicit states:
   - Look for comments indicating phases
   - Look for mode/status variables
   - Look for conditional branches that represent different behaviors
   - Look for error recovery that changes behavior

2. **Create state documentation:**
   ```markdown
   ## Identified States

   | State Name | Code Signal | Description |
   |------------|-------------|-------------|
   | STARTING | Before main loop | Initializing |
   | CONNECTING | `conn = None` | Establishing connection |
   | RUNNING | Inside `while True` | Processing tasks |
   | ... | ... | ... |
   ```

3. **Document transitions:**
   ```markdown
   ## Identified Transitions

   | From | Trigger | To |
   |------|---------|-----|
   | STARTING | Initialization complete | CONNECTING |
   | CONNECTING | Connection success | RUNNING |
   | CONNECTING | Connection failure | CONNECTING (retry) |
   | ... | ... | ... |
   ```

4. **Identify invariants:**
   ```markdown
   ## Invariants

   - When processing, connection must be valid
   - When shutting down, no new tasks accepted
   - ...
   ```

### Output

State machine documentation file: `docs/STATE_MACHINE_{component}.md`

### Verification Gate

- [ ] All states identified and documented
- [ ] All transitions identified and documented
- [ ] Invariants identified

---

## Phase 2: Create Requirements Specification

### Actions

1. Create formal requirements using `refine_requirements` workflow output format
2. Include:
   - State enum with all identified states
   - Event enum with all triggers
   - Complete transition table
   - All invariants
   - Handler dispatch requirement

### Template

```markdown
# Feature: Refactor {Component} to State Machine

## Overview
Replace implicit state management in {component} with explicit state machine.

## State Machine: {Component}StateMachine

### States
- STATE_A: [description]
- STATE_B: [description]
- ... (from Phase 1 documentation)

### Events
- EVENT_X: [trigger description]
- EVENT_Y: [trigger description]
- ...

### Transitions
(Complete table from Phase 1)

### Invariants
- INV1: [from Phase 1]
- INV2: [from Phase 1]
- ...

### Implementation Constraint
Handler dispatch pattern required.
Main loop cyclomatic complexity < 5.

## Test Cases

### Transition Tests
- test_state_a_event_x_to_state_b
- ... (one per transition)

### Invariant Tests
- test_inv1_{description}
- ... (one per invariant)

### Structural Tests
- test_all_states_have_handlers
- test_handler_naming_convention
- test_run_dispatch_complexity

### Regression Tests
- All existing tests must pass
```

### Output

Requirements document: `docs/requirements/{component}_state_machine.md`

### Verification Gate

- [ ] Requirements follow SDD format
- [ ] Every state has clear description
- [ ] Every transition documented
- [ ] Handler dispatch constraint included

---

## Phase 3: Implement State Machine (Isolated)

### Actions

1. Create new file for state machine (do NOT modify original yet)
2. Implement:
   - State enum
   - Event enum
   - Transition table
   - Context dataclass
   - State machine class with:
     - `__init__` with handler dictionary
     - `transition()` method
     - `can_transition()` method
     - Handler methods (one per state)
     - Main loop using handler dispatch

### Handler Dispatch Structure

```python
class {Component}StateMachine:
    def __init__(self, ...):
        self.state = {State}.STARTING
        self.handlers = {
            {State}.STARTING: self._handle_starting,
            {State}.CONNECTING: self._handle_connecting,
            {State}.RUNNING: self._handle_running,
            # ... all states
        }

    def run(self) -> None:
        """Main loop - pure dispatch only."""
        while self.is_running():
            if self.context.shutdown_requested:
                self._request_shutdown()
            self.handlers[self.state]()

    def _handle_starting(self) -> None:
        """Handler for STARTING state."""
        # Logic extracted from original code
        self.transition({Event}.INITIALIZED)

    # ... handler for each state
```

### Constraints

- New file only, do NOT touch original code
- No integration yet (dependencies stubbed/injected)
- Each handler corresponds to one state
- Main loop is pure dispatch

### Files Created

```
app/{component}_state.py
```

### Verification Gate

```bash
# Type checking
mypy app/{component}_state.py

# Complexity check - main loop must be < 5
radon cc app/{component}_state.py -s | grep "run"

# Verify handler dispatch (no elif chains)
# Manual review or AST-based test

# Import test
python -c "from app.{component}_state import *; print('OK')"
```

**Critical:** If `run()` CC > 5, refactor before proceeding.

---

## Phase 4: Implement State Machine Tests

### Actions

1. Create test file
2. Implement:
   - Transition tests (one per transition in table)
   - Invalid transition test
   - Invariant tests (one per invariant)
   - Structural tests:
     - `test_all_states_have_handlers`
     - `test_handler_naming_convention`
     - `test_run_dispatch_complexity`

### Structural Test Templates

```python
def test_all_states_have_handlers():
    """Every state must have a handler."""
    sm = {Component}StateMachine(...)
    for state in {State}:
        assert state in sm.handlers, f"Missing handler for {state}"
        assert callable(sm.handlers[state])

def test_handler_naming_convention():
    """Handlers must follow _handle_{state} naming."""
    sm = {Component}StateMachine(...)
    for state, handler in sm.handlers.items():
        expected = f"_handle_{state.name.lower()}"
        assert handler.__name__ == expected, (
            f"Handler for {state} named {handler.__name__}, expected {expected}"
        )

def test_run_dispatch_complexity():
    """run() must use dispatch, not elif chains."""
    import ast
    import inspect

    source = inspect.getsource({Component}StateMachine.run)
    tree = ast.parse(source)

    if_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.If))
    assert if_count <= 2, (
        f"run() has {if_count} conditionals. "
        "Expected <= 2 (shutdown check only). "
        "Use handler dispatch pattern."
    )
```

### Files Created

```
tests/test_{component}_state.py
```

### Verification Gate

```bash
# All state machine tests pass
pytest tests/test_{component}_state.py -v

# Structural tests specifically
pytest tests/test_{component}_state.py -v -k "handler"
```

**Gate Rule:** All tests pass, including structural tests, before proceeding.

---

## Phase 5: Integrate with Existing Code

### Actions

1. Implement handler bodies with real logic:
   - Extract logic from original code into handlers
   - Wire up dependencies (DB, helpers, etc.)
   - Add observability (metrics, logs)

2. Keep original code intact for now

### Constraints

- Original file unchanged (can still roll back)
- Handler logic extracted, not duplicated
- All existing tests still pass

### Files Modified

```
app/{component}_state.py    # Add real logic to handlers
```

### Verification Gate

```bash
# State machine tests still pass
pytest tests/test_{component}_state.py -v

# Existing tests still pass
pytest tests/test_{component}.py -v

# Complexity still OK
radon cc app/{component}_state.py -s -n C
```

---

## Phase 6: Wire Up Entry Point

### Actions

1. Modify original module to use state machine:
   ```python
   # app/{component}.py

   from app.{component}_state import {Component}StateMachine

   def run_{component}() -> None:
       """Entry point - delegates to state machine."""
       sm = {Component}StateMachine(...)
       sm.run()

   # Keep old implementation for rollback
   def run_{component}_legacy() -> None:
       """Legacy implementation - remove after validation."""
       # ... original code
   ```

2. Update any callers to use new function (if interface unchanged, this is automatic)

### Files Modified

```
app/{component}.py    # Wire up state machine
```

### Verification Gate

```bash
# Full test suite passes
pytest tests/ -v

# Entry point works
python -c "from app.{component} import run_{component}; print('OK')"

# Original can still be called (rollback ready)
python -c "from app.{component} import run_{component}_legacy; print('OK')"
```

---

## Phase 7: Cleanup (After Validation)

### Timing

After 1 week successful operation:

### Actions

1. Remove `_legacy` functions
2. Remove old implementation code
3. Update documentation
4. Optionally merge `{component}_state.py` into `{component}.py`

### Verification Gate

```bash
# Full test suite
pytest tests/ -v

# No legacy references
grep -r "_legacy" app/  # Should return nothing
```

---

## Complexity Comparison

After refactoring, compare:

```bash
# Before (original)
radon cc app/{component}_original.py -s -a

# After (state machine)
radon cc app/{component}_state.py -s -a
```

**Expected improvement:**
- Individual functions: CC < 10 (down from > 10)
- `run()` method: CC < 5
- Average complexity: significant reduction

---

## Rollback Procedure

If issues discovered:

1. Revert entry point to use `_legacy` function
2. Investigate issues with state machine
3. Fix and re-validate
4. Re-enable state machine

Keep `_legacy` code until confident in new implementation.
-e


# ./monitoring/ui/README.md

# Management UI - Streamlit Dashboard

A real-time monitoring and analytics dashboard for the task backend system.

## Features

- 📊 **Real-time Dashboard**: Monitor task status, throughput, and system health
- 💰 **Cost Tracking**: Analyze costs by user, task type, and time period
- 🔍 **Task Search**: Detailed task inspection with input/output viewer
- 📈 **Auto-refresh**: Live updates every 10 seconds

## Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   cd monitoring/ui
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   Create a `.env` file or export variables:
   ```bash
   export DATABASE_URL="postgresql+asyncpg://openwebui:password@localhost:5432/openwebui"
   export TASK_API_URL="http://localhost:8000"
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

4. **Open browser**: Navigate to `http://localhost:8501`

### Docker Deployment

The UI is automatically deployed with the full stack:

```bash
# Start all services including management UI
docker-compose up -d management-ui

# Or start the entire stack
docker-compose up -d
```

Access the UI at: `http://localhost:8501`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://openwebui:password@postgres:5432/openwebui` | PostgreSQL connection string |
| `TASK_API_URL` | `http://task-api:8000` | Task API endpoint |
| `UI_REFRESH_INTERVAL` | `10` | Auto-refresh interval (seconds) |
| `UI_MAX_TASKS_DISPLAY` | `100` | Max tasks in dashboard table |
| `UI_COST_ALERT_THRESHOLD` | `100.0` | Monthly cost alert threshold (USD) |

## Pages

### 📊 Dashboard
- Task status overview (pending, running, done, error)
- Recent tasks table with filters
- Real-time auto-refresh
- Success/error rates

### 💰 Costs
- Cost summary metrics
- Daily cost trends chart
- Top spenders by user
- Token usage analysis
- Cost projections

### 🔍 Task Search
- Search by task ID (UUID)
- Full task details viewer
- Input/output JSON inspector
- Link to distributed traces (Grafana Tempo)

## Architecture

```
monitoring/ui/
├── app.py                     # Main Streamlit app
├── config.py                  # Configuration
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container image
├── data/
│   └── database.py           # Database client & queries
└── pages/
    ├── 1_📊_Dashboard.py     # Task monitoring
    ├── 2_💰_Costs.py         # Cost analytics
    └── 3_🔍_Task_Search.py   # Task search
```

## Development

### Adding New Queries

Add new database queries in `data/database.py`:

```python
async def get_custom_metric(self) -> dict:
    query = text("SELECT ...")
    async with self.async_session() as session:
        result = await session.execute(query)
        return dict(result.first()._mapping)
```

### Creating New Pages

Create a new file in `pages/` with format: `N_emoji_PageName.py`

Example: `pages/4_📈_Analytics.py`

```python
import streamlit as st

st.title("📈 Analytics")
# Your page content here
```

## Troubleshooting

### Database Connection Errors

**Error**: `connection refused` or `authentication failed`

**Solution**:
- Check `DATABASE_URL` environment variable
- Ensure PostgreSQL is running: `docker-compose ps postgres`
- Verify credentials in `.env` file

### No Data Showing

**Error**: UI loads but shows no tasks

**Solution**:
- Check that tasks exist: `docker exec -it postgres psql -U openwebui -c "SELECT COUNT(*) FROM tasks;"`
- Verify database migrations have run
- Check `TASK_API_URL` is correct

### Auto-refresh Not Working

**Solution**:
- Streamlit auto-refresh uses `st.rerun()` with a sleep timer
- Check browser console for errors
- Try manually refreshing with sidebar button

## Performance Notes

- **Caching**: Queries are cached with TTL (60s for costs, 10s for dashboard)
- **Large datasets**: Dashboard table is limited to `UI_MAX_TASKS_DISPLAY` rows
- **Database load**: Auto-refresh queries run every `UI_REFRESH_INTERVAL` seconds

For high-traffic systems, consider:
- Increasing cache TTL
- Using read replicas for queries
- Adding database connection pooling

## Future Enhancements

Potential features for future versions:
- [ ] WebSocket integration for real-time updates without polling
- [ ] Administrative actions (retry failed tasks, cancel running tasks)
- [ ] User authentication and RBAC
- [ ] Custom dashboards and saved views
- [ ] Export to CSV/PDF
- [ ] Email/Slack alerts for cost thresholds
- [ ] Historical analytics with time-series aggregations
-e


# ./mutants/.pytest_cache/README.md

# pytest cache directory #

This directory contains data from the pytest's cache plugin,
which provides the `--lf` and `--ff` options, as well as the `cache` fixture.

**Do not** commit this to version control.

See [the docs](https://docs.pytest.org/en/stable/how-to/cache.html) for more information.
-e


# ./mutants/tests/README.md

# Test Suite

Comprehensive test coverage for the Task Management API.

## Running Tests

### All Tests
```bash
pytest
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Specific Tests
```bash
# Specific file
pytest tests/test_api.py

# Specific test
pytest tests/test_api.py::TestTaskEndpoints::test_create_task

# By marker
pytest -m unit
```

## Test Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── test_schemas.py       # Pydantic schema tests
├── test_models.py        # SQLAlchemy model tests
├── test_api.py           # API endpoint tests
├── test_websocket.py     # WebSocket functionality tests
└── test_worker.py        # Background worker tests
```

## Fixtures

- `async_engine` - In-memory SQLite database
- `async_session` - Async database session
- `client` - Async HTTP client
- `sample_task_data` - Sample task creation payload

## Writing New Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_feature_success(client: AsyncClient):
    response = await client.get("/endpoint")
    assert response.status_code == 200
```

See [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) for code quality standards.
-e


# ./tests/README.md

# Test Suite

Comprehensive test coverage for the Task Management API.

## Running Tests

### All Tests
```bash
pytest
```

### With Coverage
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Specific Tests
```bash
# Specific file
pytest tests/test_api.py

# Specific test
pytest tests/test_api.py::TestTaskEndpoints::test_create_task

# By marker
pytest -m unit
```

## Test Structure

```
tests/
├── conftest.py           # Pytest fixtures and configuration
├── test_schemas.py       # Pydantic schema tests
├── test_models.py        # SQLAlchemy model tests
├── test_api.py           # API endpoint tests
├── test_websocket.py     # WebSocket functionality tests
└── test_worker.py        # Background worker tests
```

## Fixtures

- `async_engine` - In-memory SQLite database
- `async_session` - Async database session
- `client` - Async HTTP client
- `sample_task_data` - Sample task creation payload

## Writing New Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_feature_success(client: AsyncClient):
    response = await client.get("/endpoint")
    assert response.status_code == 200
```

See [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md) for code quality standards.
-e
