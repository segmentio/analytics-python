#coding: utf-8

class AnalyticsJSIntector(object):
    """Inject analytics.js snippet on <head>"""
    def __init__(self, app, js_token):
        self.app = app
        self.js_token = js_token

        self.js_snippet = u"""<script type="text/javascript">
            //<![CDATA[
            var analytics=analytics||[];analytics.load=function(e){var t=document.createElement("script");t.type="text/javascript",t.async=!0,t.src=("https:"===document.location.protocol?"https://":"http://")+"d2dq2ahtl5zl1z.cloudfront.net/analytics.js/v1/"+e+"/analytics.min.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(t,n);var r=function(e){return function(){analytics.push([e].concat(Array.prototype.slice.call(arguments,0)))}},i=["identify","track","trackLink","trackForm","trackClick","trackSubmit","pageview","ab","alias","ready"];for(var s=0;s<i.length;s++)analytics[i[s]]=r(i[s])};
            analytics.load("%(token)");
            //]]>
        </script>
        """ % dict(token=self.js_token)

    def __call__(self, environ, start_response):
        app_iter = self.app(environ, start_response)

        def injected_iter():
            snippet_injected = False
            for line in app_iter:
                if not snippet_injected and u'var analytics=analytics||[];analytics.load=function(e)' in line.lower():
                    # Detected already existing snippet. Stop trying to inject.
                    snippet_injected = True

                if not snippet_injected and u'</head>' in line.lower(): # Add to the bottom of HEAD
                    line.replace(u'</head>', self.js_snippet + u'</head>')

                yield line

        return injected_iter()
