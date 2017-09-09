/*!
 * jQuery jquery.highlight - v0.3 - 10/05/2012
 * requires jquery.ba-each2.js
 *
 * Copyright (c) 2012 Fabrice Weinberg
 */
(function ($) {
	$.fn.extend({
		highlight : function (searchStrings, options) {
			var $this = $(this),
				defaultOptions = {
					onlyFirst : true,
					fuzzy : true,
					ignorePrevFounds : true,
					classCountPrefix : '_',
					className : 'jQuery_Highlight',
					ignoredChars : /\r|\n|\s/,
					ignoredTags : /(script|style|iframe|object|embed)/i,
					callback : function () {}
				},
				core = {
					searchStr: '',
					length   : 0,
					pos      : 0,
					range    : null,
					found    : false,
					count    : 1,

					search : function (str, $node) {
						this.searchStr = (options.fuzzy) ? $.trim(str) : str;
						this.length = this.searchStr.length;
						this.range = document.createRange();
						this.startSearch($node, function (range) {
							options.callback(core.surroundContent(range));
							core.count++;
						});
					},
					startSearch : function ($node, callback) {
						$node.contents().each2(function (i, jq) {
							if (core.found && options.onlyFirst) {return false; }
							if (this.nodeType === 3) {
								var	nodeText = this.textContent,
									length = nodeText.length,
									i;
								for (i = 0; i < length; i++) {
									if (core.pos > 0 && options.fuzzy) {
										if (options.ignoredChars.test(nodeText[i])) {
											continue;
										}
										if (options.ignoredChars.test(core.searchStr[core.pos])) {
											while (options.ignoredChars.test(core.searchStr[core.pos])) {
												core.pos++;
											}
										}
									}
									if (nodeText[i] === core.searchStr[core.pos]) {
										if (core.pos === 0) {
											core.range.setStart(this, i);
										}
										core.pos++;
										if (core.pos === core.length) {
											core.found = true;
											core.range.setEnd(this, ++i);
											callback(core.range);
											return false;
										}
									} else {
										core.pos = 0;
									}
								}
							} else if (!options.ignoredTags.test(this.tagName) && !((options.ignorePrevFounds === true) && typeof(this.className) === 'string' && ~this.className.indexOf(options.className))) {
								core.startSearch(jq, callback);
							}
						});
					},
					surroundContent : function (range) {
						var cont = range.extractContents(),
							$cont = $(cont).contents(),
							className = options.className + ' ' + options.classCountPrefix + core.count,
							newEl;

						$cont.each(
							function () {
								if (/(p|div)/i.test(this.tagName)) {
									$(this).wrapInner('<span class="' + className + '">');
								}
							}
						);
						newEl = document.createElement('span');
						newEl.className = className;
						newEl.appendChild(cont);
						range.insertNode(newEl);
						return newEl;
					}
				};
			options = $.extend(defaultOptions, options);
			// Start
			core.search(searchStrings, $this);
			return $this;
		}
	});
}(jQuery));
