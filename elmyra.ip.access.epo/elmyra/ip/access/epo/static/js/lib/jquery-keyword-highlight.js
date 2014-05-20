/*
 https://github.com/alanphoon/jquery-keyword-highlight

 0.0.2 2014-05-20
 ================
 Author: Andreas Motl
 - don't replace keywords found in links

 0.0.1 2013-08-24
 ================
 Author: Alan Phoon
 - initial commit

*/

(function($) {
    $.fn.extend({
        keywordHighlight: function(options) {
            var defaults = {
                highlightClass: 'highlight',
                caseSensitive: 'false',
                contains: 'false',
            }
            var options = $.extend(defaults, options);

            var self = this;
            return this.each(function(i, e) {
                var html = $(e).html();
                if (!html) return;

                // check for inline data attributes.
                var currentKeyword = options.keyword;
                if ($(e).attr("data-keyword"))
                    currentKeyword = $(e).attr("data-keyword");

                if (currentKeyword == null) {
                    //console.warn('keywordHighlight will not highlight: ' + currentKeyword);
                    return;
                }

                var currentHighlightClass = options.highlightClass;
                if ($(e).attr("data-highlightClass"))
                    currentHighlightClass = $(e).attr("data-highlightClass");

                var currentCaseSensitive = options.caseSensitive;
                if ($(e).attr("data-caseSensitive"))
                    currentCaseSensitive = $(e).attr("data-caseSensitive");

                var currentContains = options.contains;
                if ($(e).attr("data-contains"))
                    currentContains = $(e).attr("data-contains");

                //console.log('currentKeyword:', currentKeyword);

                var html_before = html;
                var html_new = html;

                // if keyword has spaces, let's treat it as a phrase
                if (_.str.contains(currentKeyword, ' ')) {

                    // do per-phrase highlighting
                    html_new = html_before.replace(
                        new RegExp(_.str.escapeRegExp(currentKeyword), 'g'),
                        self.wrap_highlight(currentKeyword, currentHighlightClass));

                } else {

                    // do per-word highlighting
                    html_new = '';

                    var words = html.split(' ');
                    $(words).each(function(i,e) {

                        var found = false;

                        if (currentContains == 'true') {
                            if (e.toLowerCase().indexOf(currentKeyword.toLowerCase()) != -1) {
                                found = true;
                            }

                        } else if (currentCaseSensitive != 'true') {
                            // not case sensitive, so lowercase all and compare.
                            if (e.toLowerCase() == currentKeyword.toLowerCase())
                                found = true;
                        } else {
                            if (e == currentKeyword)
                                found = true;
                        }

                        // don't replace keywords found in links
                        var is_href = _.str.contains(e, 'href=');
                        //console.log('is_href:', e, is_href);
                        
                        if (found && !is_href) {
                            // add span class around found word and add to new content
                            html_new += self.wrap_highlight(e, currentHighlightClass);
                        } else {
                            html_new += e  + ' ';
                        }
                    });
                }

                if (html_new != html_before) {
                    // place new content back into the targeted element
                    $(this).html(html_new);
                }

            });
        },

        wrap_highlight: function(content, highlight_class) {
            return '<span class="' + highlight_class + '">' + content + '</span>' + ' ';
        }

    });
})(jQuery);
