(function($) {
    $.fn.extend({
        keywordHighlight: function(options){
            var defaults = {
                highlightClass: 'highlight',
                caseSensitive: 'false'
            }
            var options = $.extend(defaults, options);

            return this.each(function(i, e) {
                var words = $(e).html().split(' ');
                var new_content = '';

                //check for inline data attributes.
                var currentKeyword = options.keyword;
                if($(e).attr("data-keyword"))
                    currentKeyword = $(e).attr("data-keyword");

                var currentHighlightClass = options.highlightClass;
                if($(e).attr("data-highlightClass"))
                    currentHighlightClass = $(e).attr("data-highlightClass");

                var currentCaseSensitive = options.caseSensitive;
                if($(e).attr("data-caseSensitive"))
                    currentCaseSensitive = $(e).attr("data-caseSensitive");


                $(words).each(function(i,e) {
                    var found = false;
                    if(currentCaseSensitive != 'true') {
                        //not case sensitive, so lowercase all and compare.
                        if(e.toLowerCase() == currentKeyword.toLowerCase())
                            found = true;
                    }
                    else
                    {
                        if(e == currentKeyword)
                            found = true;
                    }

                    if(found) {
                        //add span class around found word and add to new content
                        new_content += '<span class="' + currentHighlightClass + '">' + e + '</span>' + ' ';
                    }
                    else
                    {
                        new_content += e  + ' ';
                    }
                });
                $(this).html(new_content); //place new content back into the targetted element
            });
        }
    });
})(jQuery);
