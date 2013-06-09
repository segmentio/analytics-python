# coding: utf-8
# (c) 2013 Segment.io, Alan Justino da Silva and contributors;
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php


class ContentModifier(object):
    """WSGI middleware that changes the content on the fly"""

    ## Intended to be reimplemented by child classes:

    def response_modifier(self, app_iter):
        """Overwrite on children classes to change app_iter chunks on the fly

        Clients might not bother calling .close() as it occurs by other means
        """
        for line in app_iter:
            yield line

    def header_modifier(self, status, headers, exc_info=None):
        """Overwrite on children classes to change headers on the fly

        It SHOULD return status, headers and exc_info, modified or not

        Tip: Usually is not needed to chop 'Content-Length' as most servers
        already do it if response_modifier() acts as an iterator
        """
        ## Usage example:
        # headers.append(('X-Content-Modified', 'Yes'))
        return status, headers, exc_info

    ## No problem if reimplemented:

    def __init__(self, app):
        self.app = app
        super(ContentModifier, self).__init__()

    ## Not intended to be modified:

    def __call__(self, environ, start_response):
        app_iter = self.app(environ, self._start_response(start_response))
        modified_iter = self.response_modifier(app_iter)

        if hasattr(app_iter, 'close'):
            def closing_iter():
                for line in modified_iter:
                    yield line

                if hasattr(app_iter, 'close'):
                    app_iter.close()

            return closing_iter()

        return modified_iter

    def _start_response(self, original_start_response):
        def start_response(status, headers, exc_info=None):
            status, headers, exc_info = self.header_modifier(status, headers, exc_info)
            original_start_response(status, headers, exc_info)
        return start_response


class AnalyticsJSInjector(ContentModifier):
    "Inject analytics.js snippet on <head/>, if analytics.js not exists there already"
    def __init__(self, app, javascript_token):
        self.js_token = javascript_token
        self.js_snippet = """<script type="text/javascript">
            /* <![CDATA[ */
            var analytics=analytics||[];analytics.load=function(e){var t=document.createElement("script");t.type="text/javascript",t.async=!0,t.src=("https:"===document.location.protocol?"https://":"http://")+"d2dq2ahtl5zl1z.cloudfront.net/analytics.js/v1/"+e+"/analytics.min.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(t,n);var r=function(e){return function(){analytics.push([e].concat(Array.prototype.slice.call(arguments,0)))}},i=["identify","track","trackLink","trackForm","trackClick","trackSubmit","pageview","ab","alias","ready"];for(var s=0;s<i.length;s++)analytics[i[s]]=r(i[s])};
            analytics.load("PLACEHOLDER_FOR_JSTOKEN");
            /* ]]> */
        </script>
        """.replace('PLACEHOLDER_FOR_JSTOKEN', self.js_token)
        super(AnalyticsJSInjector, self).__init__(app)

    def response_modifier(self, app_iter):
        """Should be implemented by descendants"""
        snippet_injected = False
        for line in app_iter:
            if not snippet_injected:
                if 'var analytics=analytics||[];analytics.load=function(e)' in line.lower():
                    # Detected already existing snippet. Stop trying to inject another.
                    snippet_injected = True

                elif '<head>' in line.lower(): # Add to HEAD start
                    line = line.replace('<HEAD>', '<head>').replace('<Head>', '<head>') # Clean the tag, if needed
                    line = line.replace('<head>', '<head>' + self.js_snippet)
                    snippet_injected = True

            yield line

    def header_modifier(self, status, headers, exc_info=None):
        # Suppress content-length, as this middleware can change response length
        # and the server can calculate it on their own, by PEP 333 (WSGI)
        headers = filter(lambda header: header[0].lower() != 'content-length', headers)
        return status, headers, exc_info

if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    def sample_application(environ, start_response):
        start_response("200 OK", [("Content-type", "text/plain")])
        return ["<html><head><title>Hello World!</title></head></html>\n",]

    app = sample_application
    app = AnalyticsJSInjector(app, 'DEADBEEF')


    server = make_server('localhost', 8080, app)
    server.serve_forever()
