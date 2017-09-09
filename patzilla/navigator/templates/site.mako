<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="$ {locale_code[:2]}" lang="$ {locale_code[:2]}">
<head>
    <title><%block name="title">
        % if page_title is not None:
            ${theme['ui.productname']} » ${page_title}
        % else:
            ${theme['ui.productname']}
        % endif
    </%block></title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>

    ## <meta name="keywords" content="${_(u'META_SITE_Keywords')}" />
    ## <meta name="description" content="${_(u'META_SITE_Description')}" />

    <meta http-equiv="X-UA-Compatible" content="IE=edge">

    <meta name="application-name" content="${theme['ui.productname']}" />
    ## +Snippets
    <meta itemprop="name" content="${theme['ui.productname']}">
    <%block name="plus_description"></%block>

    <script type="application/javascript">
## this must be rendered inline to get rid of monster url parameters as early as possible
% if request.registry.settings.get('ipsuite.production') == 'true':
<%include file="urlcleaner.min.js"/>
% else:
<%include file="urlcleaner.js"/>
% endif
    </script>

    <link rel="search" type="application/opensearchdescription+xml" title="${theme['ui.productname']}" href="/static/meta/opensearch.xml" />
    <link rel="shortcut icon" href="${url.app}/favicon.ico" />

    <!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
        <script src="${url.app}/js/html5.js"></script>
    <![endif]-->

    ## <link rel="apple-touch-icon-precomposed"
    ##       sizes="144x144" href="${url.app}/ico/apple-touch-icon-144-precomposed.png" />
    ## <link rel="apple-touch-icon-precomposed"
    ##       sizes="114x114" href="${url.app}/ico/apple-touch-icon-114-precomposed.png" />
    ## <link rel="apple-touch-icon-precomposed"
    ##       sizes="72x72" href="${url.app}/ico/apple-touch-icon-72-precomposed.png" />
    ## <link rel="apple-touch-icon-precomposed"
    ##       href="${url.app}/ico/apple-touch-icon-57-precomposed.png" />

</head>

<body>
${self.body()}
</body>
</html>
